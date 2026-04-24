# OCR Smoke-Test Fixtures

This directory contains synthetic PDF fixtures for the OCR smoke-test harness
(`evals/run_ocr_smoke.py`).

## What is here

| File | Purpose |
|------|---------|
| `sample-01.pdf` / `sample-01.expected.txt` | Short clean text -- basic end-to-end smoke |
| `sample-02.pdf` / `sample-02.expected.txt` | Diacritics-heavy text (extended Latin placeholder) |
| `sample-03.pdf` / `sample-03.expected.txt` | Simple table with column headers |
| `sample-04.pdf` / `sample-04.expected.txt` | Longer multi-line paragraph |
| `sample-05.pdf` / `sample-05.expected.txt` | Two-page document (page-boundary test) |
| `_generate_fixtures.py` | One-off generator that produced the PDFs above |

## Current fixture status: SYNTHETIC STUBS

The committed PDFs were generated with `fpdf2` and contain **ASCII-safe
transliterated Hungarian text** (e.g., `Arvizturoe` instead of `Árvíztűrő`).
This means:

* The smoke harness _can_ run without any real scans.
* It exercises the end-to-end pipeline (PDF → image → Tesseract → accuracy
  comparison) but does **not** test real Hungarian diacritic recognition.

## How to replace with real scans (recommended for production)

For meaningful Hungarian OCR accuracy testing, replace the stubs with
public-domain Hungarian text PDFs:

1. **Magyar Elektronikus Könyvtár (MEK)** — https://mek.oszk.hu  
   Hundreds of public-domain Hungarian books in PDF format.  Good candidates:
   - Petőfi Sándor poems (clear printed text, consistent font)
   - Any 20th-century typed/printed document

2. **Hungaricana** — https://hungaricana.hu  
   Digitised historical Hungarian documents (newspapers, official records).
   Useful for testing OCR on older or handwritten-style fonts.

3. **Project Gutenberg** — https://www.gutenberg.org  
   Search for `language:hu` -- smaller selection but clean scans.

### Replacement procedure

```bash
# 1. Download a real PDF (e.g. from MEK) to evals/ocr_smoke/
# 2. Extract its text to the expected file -- use pdftotext (poppler) on
#    a clean, selectable-text PDF, or manually transcribe a short excerpt:
pdftotext -layout real-sample.pdf real-sample.expected.txt

# 3. Rename to match the fixture naming convention:
mv real-sample.pdf sample-01.pdf
mv real-sample.expected.txt sample-01.expected.txt

# 4. Run the smoke harness to check the baseline accuracy:
python evals/run_ocr_smoke.py --threshold 0.80

# 5. Commit the new fixtures.
```

> **Important:** Do NOT commit files containing real client data.
> Only public-domain or synthetic content belongs in `evals/ocr_smoke/`.

## Running the smoke harness

### Prerequisites (host-side)

The Tesseract engine requires binaries and language data that are **not** in
Docker -- install them on the host where the harness runs:

**Ubuntu / Debian / WSL:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-hun poppler-utils
```

**macOS (Homebrew):**
```bash
brew install tesseract
# Install Hungarian language data:
# Download hun.traineddata from https://github.com/tesseract-ocr/tessdata_fast
# and place it in $(brew --prefix tesseract)/share/tessdata/
```

**Windows (native):**
1. Download the Tesseract installer from
   https://github.com/UB-Mannheim/tesseract/wiki
2. During installation, select the Hungarian language pack
   (`Tesseract > Additional language data > hun`)
3. Add the Tesseract install directory to PATH
4. Install poppler for Windows: https://github.com/oschwartz10612/poppler-windows/releases/
   and add its `bin/` to PATH

### Running

```bash
# From repo root -- uses Tesseract by default:
python evals/run_ocr_smoke.py

# Override engine / threshold:
python evals/run_ocr_smoke.py --ocr-engine tesseract --threshold 0.80

# Via environment variables:
OCR_ENGINE=tesseract OCR_ACCURACY_THRESHOLD=0.90 python evals/run_ocr_smoke.py
```

Exit code 0 = all samples passed; nonzero = one or more failed.
