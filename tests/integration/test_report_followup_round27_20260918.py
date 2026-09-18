from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_search_worker_gui_callbacks_are_explicitly_queued_to_main_qt_thread() -> None:
    source = _source("audioknigi/qt/mixins/search.py")
    assert "worker.progress.connect(self._search_progress_changed, Qt.ConnectionType.QueuedConnection)" in source
    assert "worker.finished.connect(self._search_finished, Qt.ConnectionType.QueuedConnection)" in source
    assert "thread.finished.connect(self._clear_search_thread, Qt.ConnectionType.QueuedConnection)" in source


def test_analysis_worker_gui_callbacks_are_explicitly_queued() -> None:
    source = _source("audioknigi/qt/mixins/analysis_download.py")
    assert "worker.progress.connect(self._analysis_progress_message, Qt.ConnectionType.QueuedConnection)" in source
    assert "worker.finished.connect(self._analysis_finished, Qt.ConnectionType.QueuedConnection)" in source
    assert "thread.finished.connect(self._clear_analysis_thread, Qt.ConnectionType.QueuedConnection)" in source


def test_download_worker_never_calls_gui_handlers_directly_from_worker_thread() -> None:
    source = _source("audioknigi/qt/mixins/analysis_download.py")
    handlers = (
        "_download_status", "_append_log", "_download_stage", "_download_progress_changed",
        "_download_transfer", "_resolve_missing_media", "_load_history",
        "_download_request_changed", "_download_finished",
    )
    for handler in handlers:
        assert f"connect(self.{handler}, Qt.ConnectionType.QueuedConnection)" in source
    assert "thread.finished.connect(self._clear_download_thread, Qt.ConnectionType.QueuedConnection)" in source


def test_audiobookshelf_worker_gui_callbacks_are_explicitly_queued() -> None:
    source = _source("audioknigi/qt/mixins/settings.py")
    assert "from PySide6.QtCore import QThread, QTimer, Slot, Qt" in source
    assert "worker.finished.connect(self._audiobookshelf_finished, Qt.ConnectionType.QueuedConnection)" in source
    assert "thread.finished.connect(self._clear_abs_thread, Qt.ConnectionType.QueuedConnection)" in source


def test_no_known_worker_to_window_gui_connection_uses_implicit_auto_connection() -> None:
    for relative in (
        "audioknigi/qt/mixins/search.py",
        "audioknigi/qt/mixins/analysis_download.py",
        "audioknigi/qt/mixins/settings.py",
    ):
        source = _source(relative)
        for line in source.splitlines():
            stripped = line.strip()
            if "worker." in stripped and ".connect(self." in stripped:
                assert "Qt.ConnectionType.QueuedConnection" in stripped, (relative, stripped)
            if "thread.finished.connect(self." in stripped:
                assert "Qt.ConnectionType.QueuedConnection" in stripped, (relative, stripped)
