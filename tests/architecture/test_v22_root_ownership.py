"""Implementation ownership and root compatibility constraints (V22)."""
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "audioknigi"

PAIRS = {
    "brand": "identity.brand",
    "metadata": "identity.metadata",
    "version": "identity.version",
    "cover_fetch": "engine.cover_fetch",
    "crash_report": "diagnostics.crash_report",
    "downloader": "download.downloader",
    "i18n": "localization.i18n",
    "integrations": "connectors.audiobookshelf",
    "logging_utils": "diagnostics.logging_utils",
    "qt_runtime_audit": "qt.runtime_audit",
    "templates": "download.naming",
    "download_engine": "download.engine",
}

def test_root_compatibility_aliases_preserve_module_identity():
    for old, dest in PAIRS.items():
        assert importlib.import_module(f"audioknigi.{old}") is importlib.import_module(f"audioknigi.{dest}")

def test_root_compatibility_aliases_are_thin():
    for old, dest in PAIRS.items():
        assert (ROOT / (dest.replace('.', '/') + '.py')).is_file()
        assert len((ROOT / (old + '.py')).read_text(encoding='utf-8').splitlines()) <= 15

def test_translations_still_use_existing_catalog_directory():
    from audioknigi.i18n import LANGUAGES, STRINGS
    assert LANGUAGES.get('de') == 'Deutsch'
    assert bool(STRINGS.get('ru'))

def test_module_import_compatibility_keeps_headless_runtime():
    from audioknigi.download_engine import DownloadService
    from audioknigi.download.service import DownloadService as new_service
    assert DownloadService is new_service
