from pathlib import Path

from audioknigi.metadata import APP_VERSION
from audioknigi.version import __version__
from audioknigi.providers import SourceProvider
from audioknigi.downloader import DownloaderMixin

ROOT = Path(__file__).resolve().parents[2]


def test_version_has_one_canonical_value():
    assert APP_VERSION == __version__


def test_main_window_is_composed_from_mixins():
    source = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    assert "AnalysisDownloadUiMixin" in source
    assert "QueueUiMixin" in source
    assert "LifecycleUiMixin" in source


def test_downloader_facade_points_to_split_package():
    source = (ROOT / "audioknigi/downloader.py").read_text(encoding="utf-8")
    assert "Compatibility facade" in source
    assert hasattr(DownloaderMixin, "_process_book_once")


def test_localization_python_file_does_not_embed_giant_language_tables():
    source = (ROOT / "audioknigi/i18n.py").read_text(encoding="utf-8")
    assert "legacy_literals.json" in source
    assert "messages.json" in source
    assert source.count('"Нет обложки"') == 0


def test_diagnostics_docs_and_architecture_docs_exist():
    assert (ROOT / "docs/architecture/PROJECT_STRUCTURE.md").is_file()
    assert (ROOT / "docs/user/DIAGNOSTICS.md").is_file()
    assert (ROOT / "docs/development/SETTINGS_SCHEMA.md").is_file()
