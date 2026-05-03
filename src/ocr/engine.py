"""OCR engine abstraction for CZ-Dev-RAG.

Three concrete engines are provided:

* ``MinerUEngine``  -- calls the LightRAG HTTP API; returns confidence 1.0
  (MinerU does not expose a confidence score).
* ``TesseractEngine`` -- converts PDF pages to images with ``pdf2image`` then
  runs ``pytesseract`` with the Hungarian language pack (lang="hun").
  Confidence is estimated as the fraction of recognised tokens that contain
  at least one alphabetical character (proxy for "real word ratio").
* ``AutoEngine`` -- tries MinerU first; falls back to Tesseract when the
  MinerU confidence is below a configurable threshold.

The ``get_ocr_engine`` factory reads ``OCR_ENGINE`` from the environment so
callers can be configured without code changes.
"""

from __future__ import annotations

import os
import unicodedata
from enum import StrEnum
from pathlib import Path


class OCRBackend(StrEnum):
    AUTO = "auto"
    MINERU = "mineru"
    TESSERACT = "tesseract"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class BaseOCREngine:
    """Minimal interface every engine must satisfy."""

    def extract_text(self, pdf_path: str) -> tuple[str, float]:
        """Return ``(text, confidence)`` where confidence is in ``[0, 1]``.

        Confidence semantics are engine-specific:
        * MinerU -- always ``1.0`` (engine does not expose a score).
        * Tesseract -- ratio of alphabetic tokens (rough real-word heuristic).
        * Auto -- whichever engine was ultimately used.

        Raises ``FileNotFoundError`` if *pdf_path* does not exist.
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# MinerU (via LightRAG HTTP API)
# ---------------------------------------------------------------------------


class MinerUEngine(BaseOCREngine):
    """Extract text by POSTing the PDF to the LightRAG /documents/text endpoint.

    LightRAG internally routes PDFs through MinerU for layout-aware OCR.
    The API does not expose a per-document confidence score, so we return
    ``1.0`` unconditionally when the call succeeds.

    Environment variables
    ---------------------
    LIGHTRAG_HOST : str
        Base URL of the LightRAG API server.  Defaults to
        ``http://localhost:9621``.
    """

    DEFAULT_URL = "http://localhost:9621"

    def __init__(self, lightrag_url: str | None = None) -> None:
        self._url = (lightrag_url or os.environ.get("LIGHTRAG_HOST", self.DEFAULT_URL)).rstrip("/")

    def extract_text(self, pdf_path: str) -> tuple[str, float]:
        """Upload *pdf_path* to LightRAG and return the extracted text.

        Uses multipart upload since PDFs are binary.  Returns ``(text, 1.0)``.
        """
        import httpx  # guarded import -- not required if only Tesseract is used

        path = Path(pdf_path)
        if not path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        with path.open("rb") as fh:
            files = {"file": (path.name, fh, "application/pdf")}
            with httpx.Client(timeout=300.0) as client:
                resp = client.post(f"{self._url}/documents/upload", files=files)
                resp.raise_for_status()

        data: dict[str, object] = resp.json()
        text = str(data.get("text", ""))
        return text, 1.0


# ---------------------------------------------------------------------------
# Tesseract (with Hungarian language pack)
# ---------------------------------------------------------------------------


def _word_confidence(text: str) -> float:
    """Heuristic confidence: fraction of whitespace-separated tokens that
    contain at least one Unicode letter.

    This is a deliberately simple metric -- it catches garbage output (random
    symbols, stray punctuation) without requiring a dictionary.
    """
    tokens = text.split()
    if not tokens:
        return 0.0
    real = sum(1 for t in tokens if any(unicodedata.category(c).startswith("L") for c in t))
    return real / len(tokens)


class TesseractEngine(BaseOCREngine):
    """OCR via pytesseract with the Hungarian language pack.

    Prerequisites (host-side, not in Docker):
    * ``tesseract-ocr`` binary in PATH
    * ``tesseract-ocr-hun`` language data (``hun.traineddata``)
    * ``poppler`` utilities for ``pdf2image`` (``pdfinfo``, ``pdftoppm``)

    The ``pytesseract`` and ``pdf2image`` Python packages must be installed
    (they are listed in the project dependencies).

    Parameters
    ----------
    lang:
        Tesseract language string passed to ``--lang``.  Defaults to
        ``"hun"`` for Hungarian.  Use ``"hun+eng"`` for mixed documents.
    dpi:
        Resolution used when rasterising PDF pages.  300 is the standard
        choice for printed text; higher values improve accuracy on small
        fonts at the cost of speed and memory.
    """

    def __init__(self, lang: str = "hun", dpi: int = 300) -> None:
        self._lang = lang
        self._dpi = dpi

    def extract_text(self, pdf_path: str) -> tuple[str, float]:
        """Convert each page of *pdf_path* to an image and run Tesseract.

        Returns ``(text, confidence)`` where *confidence* is the word-ratio
        heuristic computed over the concatenated output of all pages.

        Environment variables (Windows / non-standard install locations):
        - ``TESSERACT_CMD``: full path to tesseract.exe
        - ``POPPLER_PATH``: directory containing pdftoppm / pdfinfo binaries
        """
        import pytesseract  # guarded -- may not be installed in all envs
        from pdf2image import convert_from_path  # guarded

        path = Path(pdf_path)
        if not path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        tesseract_cmd = os.environ.get("TESSERACT_CMD")
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        poppler_path = os.environ.get("POPPLER_PATH")
        if poppler_path:
            images = convert_from_path(str(path), dpi=self._dpi, poppler_path=poppler_path)
        else:
            images = convert_from_path(str(path), dpi=self._dpi)

        page_texts: list[str] = []
        for image in images:
            page_text: str = pytesseract.image_to_string(image, lang=self._lang)
            page_texts.append(page_text)

        full_text = "\n".join(page_texts).strip()
        confidence = _word_confidence(full_text)
        return full_text, confidence


# ---------------------------------------------------------------------------
# Auto (MinerU with Tesseract fallback)
# ---------------------------------------------------------------------------


class AutoEngine(BaseOCREngine):
    """Try MinerU; fall back to Tesseract if confidence is below *threshold*.

    This is the default engine when ``OCR_ENGINE=auto`` (or is unset).

    Parameters
    ----------
    threshold:
        Minimum confidence required to accept the MinerU result.  When the
        MinerU result is below this value the engine re-runs Tesseract and
        returns that result instead (regardless of its own confidence).
    lightrag_url:
        Forwarded to :class:`MinerUEngine`.
    tesseract_lang:
        Forwarded to :class:`TesseractEngine`.
    tesseract_dpi:
        Forwarded to :class:`TesseractEngine`.
    """

    def __init__(
        self,
        threshold: float = 0.95,
        lightrag_url: str | None = None,
        tesseract_lang: str = "hun",
        tesseract_dpi: int = 300,
    ) -> None:
        self._threshold = threshold
        self._primary = MinerUEngine(lightrag_url=lightrag_url)
        self._fallback = TesseractEngine(lang=tesseract_lang, dpi=tesseract_dpi)

    def extract_text(self, pdf_path: str) -> tuple[str, float]:
        """Run MinerU; delegate to Tesseract when confidence is insufficient."""
        try:
            text, confidence = self._primary.extract_text(pdf_path)
            if confidence >= self._threshold and text.strip():
                return text, confidence
        except Exception:
            # MinerU unavailable (container down, network error, etc.) -- fall through.
            pass

        return self._fallback.extract_text(pdf_path)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_ocr_engine(backend: str | None = None) -> BaseOCREngine:
    """Return a configured :class:`BaseOCREngine` instance.

    Resolution order:
    1. *backend* argument (if supplied and non-empty)
    2. ``OCR_ENGINE`` environment variable
    3. ``"auto"`` (the safe default)

    Parameters
    ----------
    backend:
        One of ``"auto"``, ``"mineru"``, or ``"tesseract"``.  Case-insensitive.

    Raises
    ------
    ValueError
        When the resolved backend string is not a known :class:`OCRBackend` value.
    """
    raw = (backend or os.environ.get("OCR_ENGINE", OCRBackend.AUTO)).strip().lower()
    try:
        resolved = OCRBackend(raw)
    except ValueError as exc:
        valid = ", ".join(b.value for b in OCRBackend)
        raise ValueError(f"Unknown OCR backend {raw!r}. Valid options: {valid}") from exc

    threshold_env = os.environ.get("OCR_ACCURACY_THRESHOLD", "0.95")
    try:
        threshold = float(threshold_env)
    except ValueError:
        threshold = 0.95

    if resolved == OCRBackend.MINERU:
        return MinerUEngine()
    if resolved == OCRBackend.TESSERACT:
        return TesseractEngine()
    # AUTO
    return AutoEngine(threshold=threshold)

