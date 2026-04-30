"""OCR smoke-test harness for CZ-Dev-RAG.

For each ``sample-NN.pdf`` in *smoke_dir*, runs the configured OCR engine,
compares the output against ``sample-NN.expected.txt``, and computes
character-level accuracy as::

    accuracy = 1 - edit_distance(actual, expected) / max(len(actual), len(expected))

Exits 0 when all samples meet *threshold*; nonzero otherwise.

Usage
-----
::

    # Default: Tesseract engine, threshold 0.95, evals/ocr_smoke/
    python evals/run_ocr_smoke.py

    # Override engine and threshold:
    python evals/run_ocr_smoke.py --ocr-engine tesseract --threshold 0.80

    # Point at a custom fixture directory:
    python evals/run_ocr_smoke.py --smoke-dir /path/to/fixtures

    # Via environment:
    OCR_ENGINE=tesseract OCR_ACCURACY_THRESHOLD=0.90 python evals/run_ocr_smoke.py

Requirements (host-side)
------------------------
* ``tesseract-ocr`` binary in PATH
* ``tesseract-ocr-hun`` language data (``hun.traineddata``)
* ``poppler`` utilities for ``pdf2image`` (``pdfinfo``, ``pdftoppm``)
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import typer

# ---------------------------------------------------------------------------
# Inline the Levenshtein dependency so the import error is clear.
# ---------------------------------------------------------------------------


def _edit_distance(a: str, b: str) -> int:
    """Compute the Levenshtein edit distance between *a* and *b*.

    Uses the ``Levenshtein`` package when available for speed; falls back to
    a pure-Python implementation so the harness still works without it.
    """
    try:
        import Levenshtein

        return int(Levenshtein.distance(a, b))
    except ImportError:
        pass

    # Pure-Python O(m*n) fallback.
    m, n = len(a), len(b)
    if m == 0:
        return n
    if n == 0:
        return m
    prev = list(range(n + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * n
        for j, cb in enumerate(b, 1):
            curr[j] = min(
                curr[j - 1] + 1,
                prev[j] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            )
        prev = curr
    return prev[n]


def _char_accuracy(actual: str, expected: str) -> float:
    """Return character-level accuracy in ``[0, 1]``."""
    max_len = max(len(actual), len(expected))
    if max_len == 0:
        return 1.0
    dist = _edit_distance(actual, expected)
    return max(0.0, 1.0 - dist / max_len)


def _normalise(text: str) -> str:
    """Strip leading/trailing whitespace and collapse runs of whitespace.

    OCR engines often insert slightly different amounts of whitespace; this
    normalisation makes accuracy comparisons fairer.
    """
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

app = typer.Typer(help="Run OCR smoke tests against synthetic fixture PDFs.")


@app.command()
def main(
    ocr_engine: str = typer.Option(
        None,
        "--ocr-engine",
        envvar="OCR_ENGINE",
        help="OCR backend: auto | mineru | tesseract.  Default: tesseract.",
    ),
    threshold: float = typer.Option(
        None,
        "--threshold",
        envvar="OCR_ACCURACY_THRESHOLD",
        help="Minimum character-level accuracy (0-1).  Default: 0.95.",
        min=0.0,
        max=1.0,
    ),
    smoke_dir: Path = typer.Option(  # noqa: B008
        None,
        "--smoke-dir",
        help="Directory containing sample-NN.pdf + sample-NN.expected.txt.",
        exists=False,  # we check manually for a better error message
    ),
) -> None:
    """Run OCR smoke tests and report per-sample accuracy."""
    # Resolve defaults that cannot be set as Click defaults because they come
    # from environment variables with fallback values.
    resolved_engine: str = ocr_engine or os.environ.get("OCR_ENGINE", "tesseract")
    resolved_threshold: float = threshold if threshold is not None else float(
        os.environ.get("OCR_ACCURACY_THRESHOLD", "0.95")
    )
    resolved_dir: Path = smoke_dir or (
        Path(__file__).parent / "ocr_smoke"
    )

    if not resolved_dir.is_dir():
        typer.echo(f"ERROR: smoke-dir does not exist: {resolved_dir}", err=True)
        raise typer.Exit(code=2)

    # Collect fixtures: sample-NN.pdf paired with sample-NN.expected.txt
    pdfs = sorted(resolved_dir.glob("sample-*.pdf"))
    if not pdfs:
        typer.echo(f"No sample-*.pdf files found in {resolved_dir}", err=True)
        raise typer.Exit(code=2)

    # Import here so missing deps give a clear error at test time, not import time.
    # Support both `uv run python evals/run_ocr_smoke.py` (src in pythonpath)
    # and direct invocation without package install.
    _repo_root = Path(__file__).parent.parent
    if str(_repo_root / "src") not in sys.path:
        sys.path.insert(0, str(_repo_root / "src"))
    from ocr import get_ocr_engine

    try:
        engine = get_ocr_engine(resolved_engine)
    except ValueError as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        f"OCR smoke test  engine={resolved_engine}  threshold={resolved_threshold:.0%}"
        f"  fixtures={len(pdfs)}"
    )
    typer.echo("-" * 60)

    all_passed = True
    for pdf_path in pdfs:
        expected_path = pdf_path.with_suffix("").with_suffix(".expected.txt")
        if not expected_path.is_file():
            typer.echo(f"  SKIP  {pdf_path.name}  (no matching .expected.txt)")
            continue

        expected_text = expected_path.read_text(encoding="utf-8")

        try:
            actual_text, _confidence = engine.extract_text(str(pdf_path))
        except Exception as exc:
            typer.echo(f"  ERROR {pdf_path.name}  {exc}", err=True)
            all_passed = False
            continue

        norm_actual = _normalise(actual_text)
        norm_expected = _normalise(expected_text)
        accuracy = _char_accuracy(norm_actual, norm_expected)
        passed = accuracy >= resolved_threshold
        if not passed:
            all_passed = False

        status = "PASS" if passed else "FAIL"
        typer.echo(
            f"  {status}  {pdf_path.name}  accuracy={accuracy:.1%}"
            f"  (threshold={resolved_threshold:.0%})"
        )

    typer.echo("-" * 60)
    if all_passed:
        typer.echo("All samples passed.")
    else:
        typer.echo("One or more samples FAILED.", err=True)

    raise typer.Exit(code=0 if all_passed else 1)


if __name__ == "__main__":
    app()


