"""Generate synthetic Hungarian fixture PDFs for the OCR smoke-test harness.

Run once to regenerate the fixtures:
    cd <repo-root>
    python evals/ocr_smoke/_generate_fixtures.py   # or: uv run python ...

This script is NOT part of the test suite -- it is a one-off generator.
The generated PDFs are committed to the repo as binary fixtures so the smoke
harness can run without re-generating them.

Font strategy
-------------
fpdf2 >= 2.8 no longer bundles DejaVu fonts.  We auto-detect a suitable
Unicode TTF from the host OS (Arial on Windows, DejaVu/Liberation on Linux).
If no font is found the generator falls back to ASCII-safe text that the
built-in Helvetica font can render.  All expected.txt files use the same
ASCII-safe text so that OCR accuracy comparisons remain valid.
"""

from __future__ import annotations

import sys
from pathlib import Path

SMOKE_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Font discovery
# ---------------------------------------------------------------------------

_FONT_CANDIDATES = [
    # Windows
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/calibri.ttf"),
    # Linux / WSL
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    # macOS
    Path("/Library/Fonts/Arial.ttf"),
    Path("/System/Library/Fonts/Helvetica.ttc"),
]


def _find_unicode_font() -> Path | None:
    for candidate in _FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _make_pdf(font_path: Path | None):  # type: ignore[return]
    """Return an FPDF instance with a Unicode-capable font (or Helvetica fallback)."""
    from fpdf import FPDF  # type: ignore[import]

    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    if font_path is not None:
        pdf.add_font("Unicode", fname=str(font_path))
        pdf.add_font("Unicode", style="B", fname=str(font_path))
        pdf._unicode_font = True  # type: ignore[attr-defined]
    else:
        pdf._unicode_font = False  # type: ignore[attr-defined]
    return pdf


def _set_font(pdf, bold: bool = False) -> None:  # type: ignore[type-arg]
    if pdf._unicode_font:  # type: ignore[attr-defined]
        pdf.set_font("Unicode", style="B" if bold else "", size=13)
    else:
        pdf.set_font("Helvetica", style="B" if bold else "", size=13)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def sample_01(font: Path | None) -> None:
    """Short clean text -- basic smoke test."""
    text = "Udvozoljuk a CZ Dev oldalon. Ez egy teszt dokumentum."
    pdf = _make_pdf(font)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    _set_font(pdf)
    pdf.multi_cell(0, 10, text)
    pdf.output(str(SMOKE_DIR / "sample-01.pdf"))
    (SMOKE_DIR / "sample-01.expected.txt").write_text(text, encoding="utf-8")
    print("sample-01 done")


def sample_02(font: Path | None) -> None:
    """Diacritics placeholder text -- tests extended Latin rendering."""
    # ASCII-safe version so built-in Helvetica fallback also works.
    text = (
        "Arvizturoe tukorfurogep. "
        "A kovetkezo szavak ekezetes betuket tartalmaznak: "
        "eloezo, oeszi, fuetesi, toezsde, koenyoekloe, szoeloe, fueruesz."
    )
    pdf = _make_pdf(font)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    _set_font(pdf)
    pdf.multi_cell(0, 10, text)
    pdf.output(str(SMOKE_DIR / "sample-02.pdf"))
    (SMOKE_DIR / "sample-02.expected.txt").write_text(text, encoding="utf-8")
    print("sample-02 done")


def sample_03(font: Path | None) -> None:
    """Simple table with headers."""
    rows = [
        ("Nev", "Osszeg", "Statusz"),
        ("Kovacs Bela", "150 000 Ft", "Aktiv"),
        ("Nagy Anna", "85 500 Ft", "Lejart"),
        ("Szabo Peter", "210 000 Ft", "Aktiv"),
    ]
    col_widths = [52, 46, 36]

    pdf = _make_pdf(font)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    _set_font(pdf, bold=True)
    for cell, w in zip(rows[0], col_widths, strict=False):
        pdf.cell(w, 9, cell, border=1)
    pdf.ln()

    _set_font(pdf, bold=False)
    for row in rows[1:]:
        for cell, w in zip(row, col_widths, strict=False):
            pdf.cell(w, 8, cell, border=1)
        pdf.ln()

    pdf.output(str(SMOKE_DIR / "sample-03.pdf"))
    lines = ["\t".join(r) for r in rows]
    expected = "\n".join(lines)
    (SMOKE_DIR / "sample-03.expected.txt").write_text(expected, encoding="utf-8")
    print("sample-03 done")


def sample_04(font: Path | None) -> None:
    """Longer paragraph -- tests multi-line wrapping and word integrity."""
    text = (
        "A CZ Dev ugynokseg egyedi szoftvereket fejleszt olyan alapitoknak, "
        "akik kinoettek a no-code megoldasokat. "
        "Csapatunk ket foeoebol all: Czaban Tamas Budapestrol, "
        "aki a backend fejlesztessel, adatfeldolgozassal es a Python "
        "oekorendszerrel foglalkozik, valamint Czaban Zsombor, "
        "aki a frontend fejlesztesert es a felhasznaloi elmeny tervezesert felel. "
        "Referenciamunkank a BEMER CRM rendszer, amely felvaltotta a korabbi "
        "tablazatkezelo megoldast, es automatizalta a berleti "
        "szerzoedesek nyilvantartasat. "
        "Az ugynokseg weboldala a czaban.dev cimen erheto el."
    )
    pdf = _make_pdf(font)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    _set_font(pdf)
    pdf.multi_cell(0, 8, text)
    pdf.output(str(SMOKE_DIR / "sample-04.pdf"))
    (SMOKE_DIR / "sample-04.expected.txt").write_text(text, encoding="utf-8")
    print("sample-04 done")


def sample_05(font: Path | None) -> None:
    """Two-page document -- tests page-boundary handling."""
    page1_title = "Elso oldal"
    page1_body = (
        "Ez a dokumentum ket oldalbol all. "
        "Az elso oldal rovid bevezeto szoveget tartalmaz."
    )
    page2_title = "Masodik oldal"
    page2_body = (
        "A masodik oldalon folytatodik a szoveg. "
        "Az oldalvaltas helyes kezelese fontos az OCR motor szamara."
    )

    pdf = _make_pdf(font)
    pdf.set_auto_page_break(auto=False)

    pdf.add_page()
    _set_font(pdf, bold=True)
    pdf.cell(0, 12, page1_title, new_x="LMARGIN", new_y="NEXT")
    _set_font(pdf, bold=False)
    pdf.multi_cell(0, 8, page1_body)

    pdf.add_page()
    _set_font(pdf, bold=True)
    pdf.cell(0, 12, page2_title, new_x="LMARGIN", new_y="NEXT")
    _set_font(pdf, bold=False)
    pdf.multi_cell(0, 8, page2_body)

    pdf.output(str(SMOKE_DIR / "sample-05.pdf"))
    expected = (
        f"{page1_title}\n{page1_body}\n"
        f"{page2_title}\n{page2_body}"
    )
    (SMOKE_DIR / "sample-05.expected.txt").write_text(expected, encoding="utf-8")
    print("sample-05 done")


if __name__ == "__main__":
    font = _find_unicode_font()
    if font:
        print(f"Using font: {font}")
    else:
        print("No Unicode TTF found -- using built-in Helvetica (ASCII only)", file=sys.stderr)

    sample_01(font)
    sample_02(font)
    sample_03(font)
    sample_04(font)
    sample_05(font)
    print("All fixtures generated.")

