"""OCR engine abstraction for CZ-Dev-RAG.

Exports the engine enum, base class, and factory function so callers
never need to import from the internal ``engine`` submodule directly.
"""

from .engine import (
    AutoEngine,
    BaseOCREngine,
    MinerUEngine,
    OCRBackend,
    TesseractEngine,
    get_ocr_engine,
)

__all__ = [
    "AutoEngine",
    "BaseOCREngine",
    "MinerUEngine",
    "OCRBackend",
    "TesseractEngine",
    "get_ocr_engine",
]
