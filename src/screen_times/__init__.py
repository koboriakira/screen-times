"""
screen_times - macOS screen OCR logger using Vision Framework

A tool for capturing screenshots, performing OCR, and logging screen activities.
"""

__version__ = "0.1.0"

from .screenshot import take_screenshot, get_active_window
from .ocr import perform_ocr
from .jsonl_manager import JsonlManager
from .screen_ocr_logger import ScreenOCRLogger, ScreenOCRConfig, ScreenOCRResult

__all__ = [
    "take_screenshot",
    "get_active_window",
    "perform_ocr",
    "JsonlManager",
    "ScreenOCRLogger",
    "ScreenOCRConfig",
    "ScreenOCRResult",
    "__version__",
]
