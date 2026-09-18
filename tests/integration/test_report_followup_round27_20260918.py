from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_search_worker_gui_callbacks_are_explicitly_queued_to_main_qt_thread() -> None:
    source = _source("audioknigi/qt/mixins/search.py")
    assert "worker.progress.connect(self._worker_ui_relay.search_progress, Qt.ConnectionType.QueuedConnection)" in source
    assert "worker.finished.connect(self._worker_ui_relay.search_finished, Qt.ConnectionType.QueuedConnection)" in source
    assert "thread.finished.connect(self._worker_ui_relay.search_thread_finished, Qt.ConnectionType.QueuedConnection)" in source


def test_analysis_worker_gui_callbacks_are_explicitly_queued() -> None:
    source = _source("audioknigi/qt/mixins/analysis_download.py")
    assert "worker.progress.connect(self._worker_ui_relay.analysis_progress, Qt.ConnectionType.QueuedConnection)" in source
    assert "worker.finished.connect(self._worker_ui_relay.analysis_finished, Qt.ConnectionType.QueuedConnection)" in source
    assert "thread.finished.connect(self._worker_ui_relay.analysis_thread_finished, Qt.ConnectionType.QueuedConnection)" in source


def test_download_worker_never_calls_gui_handlers_directly_from_worker_thread() -> None:
    source = _source("audioknigi/qt/mixins/analysis_download.py")
    relay_slots = (
        "download_status", "download_log", "download_stage", "download_progress",
        "download_transfer", "download_missing_media", "download_history_changed",
        "download_request_changed", "download_finished",
    )
    for slot in relay_slots:
        assert f"connect(self._worker_ui_relay.{slot}, Qt.ConnectionType.QueuedConnection)" in source
    assert "thread.finished.connect(self._worker_ui_relay.download_thread_finished, Qt.ConnectionType.QueuedConnection)" in source

def test_audiobookshelf_worker_gui_callbacks_are_explicitly_queued() -> None:
    source = _source("audioknigi/qt/mixins/settings.py")
    assert "from PySide6.QtCore import QThread, QTimer, Slot, Qt" in source
    assert "worker.finished.connect(self._worker_ui_relay.audiobookshelf_finished, Qt.ConnectionType.QueuedConnection)" in source
    assert "thread.finished.connect(self._worker_ui_relay.audiobookshelf_thread_finished, Qt.ConnectionType.QueuedConnection)" in source


def test_no_known_worker_to_window_gui_connection_bypasses_qobject_relay() -> None:
    for relative in (
        "audioknigi/qt/mixins/search.py",
        "audioknigi/qt/mixins/analysis_download.py",
        "audioknigi/qt/mixins/settings.py",
    ):
        source = _source(relative)
        for line in source.splitlines():
            stripped = line.strip()
            if "worker." in stripped and ".connect(self." in stripped:
                assert "self._worker_ui_relay." in stripped, (relative, stripped)
                assert "Qt.ConnectionType.QueuedConnection" in stripped, (relative, stripped)
            if "thread.finished.connect(self." in stripped:
                assert "self._worker_ui_relay." in stripped, (relative, stripped)
                assert "Qt.ConnectionType.QueuedConnection" in stripped, (relative, stripped)
