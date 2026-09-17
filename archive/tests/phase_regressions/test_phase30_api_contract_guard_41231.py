from __future__ import annotations

import ast
from pathlib import Path

from audioknigi.i18n import LANGUAGES, localize_runtime_text, tr, ui_text
from audioknigi.logging_utils import ERROR_LOG_FILE, tail_error_log

ROOT = Path(__file__).resolve().parents[1]


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_i18n_public_api_required_by_qt_modules_is_importable_and_callable():
    assert {"ru", "uk", "de", "en"}.issubset(LANGUAGES)
    assert callable(tr)
    assert callable(ui_text)
    assert callable(localize_runtime_text)
    assert ui_text("de", "Книга") == "Buch"
    assert localize_runtime_text("en", "Книга") == "Book"


def test_i18n_exports_the_qt_localization_contract():
    src = _text("audioknigi/i18n.py")
    tree = ast.parse(src)
    definitions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert {"tr", "ui_text", "localize_runtime_text"}.issubset(definitions)
    assert '__all__ = ["LANGUAGES", "STRINGS", "tr", "ui_text", "localize_runtime_text"]' in src


def test_logging_diagnostics_api_required_by_main_window_is_available():
    assert ERROR_LOG_FILE.name == "errors.log"
    assert callable(tail_error_log)
    assert isinstance(tail_error_log(3), str)
    src = _text("audioknigi/logging_utils.py")
    assert 'ERROR_LOG_FILE = APP_DIR / "errors.log"' in src
    assert "def tail_error_log(max_lines: int = 200) -> str:" in src
    assert '"sanitize_log_text", "tail_error_log",' in src


def test_accessibility_language_property_is_kept_in_sync_by_main_window():
    src = _text("audioknigi/qt/main_window.py")
    change = src[src.index("    def change_language(self):"):src.index("    @staticmethod\n    def _normalize_drop_values")]
    assert 'app.setProperty("audioknigi_language", code)' in change
    init = src[src.index("    def __init__(self):"):src.index("    def _build_ui(self):")]
    assert 'app.setProperty("audioknigi_language", self.language)' in init


def test_accessibility_import_contract_matches_i18n_public_api():
    src = _text("audioknigi/qt/accessibility.py")
    assert "from ..i18n import localize_runtime_text, ui_text" in src
    assert 'app.property("audioknigi_language")' in src
