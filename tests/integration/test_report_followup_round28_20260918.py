from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_worker_ui_relay_is_real_qobject_owned_by_main_window() -> None:
    relay = _source("audioknigi/qt/worker_ui_relay.py")
    main = _source("audioknigi/qt/main_window.py")
    assert "class WorkerUiRelay(QObject):" in relay
    assert "super().__init__(owner)" in relay
    assert "self._worker_ui_relay = WorkerUiRelay(self)" in main


def test_search_callbacks_route_through_qobject_relay() -> None:
    source = _source("audioknigi/qt/mixins/search.py")
    assert "worker.progress.connect(self._worker_ui_relay.search_progress, Qt.ConnectionType.QueuedConnection)" in source
    assert "worker.finished.connect(self._worker_ui_relay.search_finished, Qt.ConnectionType.QueuedConnection)" in source
    assert "thread.finished.connect(self._worker_ui_relay.search_thread_finished, Qt.ConnectionType.QueuedConnection)" in source


def test_relay_forwards_search_callbacks_to_existing_ui_handlers() -> None:
    relay = _source("audioknigi/qt/worker_ui_relay.py")
    assert "owner._search_progress_changed(percent, message)" in relay
    assert "owner._search_finished(outcome)" in relay
    assert "owner._clear_search_thread()" in relay
    assert "event=search_finished_dispatch" in relay


def test_analysis_download_and_abs_callbacks_all_use_relay() -> None:
    analysis = _source("audioknigi/qt/mixins/analysis_download.py")
    settings = _source("audioknigi/qt/mixins/settings.py")
    for slot in (
        "analysis_progress", "analysis_finished", "analysis_thread_finished",
        "download_status", "download_log", "download_stage", "download_progress",
        "download_transfer", "download_missing_media", "download_history_changed",
        "download_request_changed", "download_finished", "download_thread_finished",
    ):
        assert f"self._worker_ui_relay.{slot}" in analysis
    assert "self._worker_ui_relay.audiobookshelf_finished" in settings
    assert "self._worker_ui_relay.audiobookshelf_thread_finished" in settings
