from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping, MutableMapping
import tempfile

import pytest

from audioknigi import core
from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.templates import render_track_filename
from audioknigi.sources import normalize_supported_url
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict
from audioknigi.services.download_request import DownloadRequest
from audioknigi.qt.full_parity import inventory_parity_complete, full_parity_complete

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase16_or_newer_stage_declared():
    stage = text("audioknigi/qt/__init__.py")
    assert 'QT_MIGRATION_STAGE = "phase-' in stage
    number = int(stage.split('QT_MIGRATION_STAGE = "phase-', 1)[1].split('"', 1)[0])
    assert number >= 17


def test_mapping_dataclass_advertises_mapping_not_mutable_mapping():
    book = Book(url="https://example.invalid", title="Book")
    assert isinstance(book, Mapping)
    assert not isinstance(book, MutableMapping)
    assert len(book) == len(Book.__dataclass_fields__)


def test_track_filename_replaces_metadata_audio_extension_with_output_extension():
    book = Book(url="https://example.invalid", title="Book")
    track = Track(index=1, title="Hacker.mp3", file="https://example.invalid/1.mp3")
    assert render_track_filename("{Track_Title}", book, track) == "Hacker.mp3"
    track.title = "Chapter.m4a"
    assert render_track_filename("{Track_Title}", book, track) == "Chapter.mp3"
    assert render_track_filename("{Track_Number}.mp3", book, track) == "01.mp3"


def test_supported_urls_get_stable_https_identity():
    assert normalize_supported_url("http://m.knigavuhe.org/book/demo?ref=x") == "https://knigavuhe.org/book/demo/"
    assert normalize_supported_url("http://poleknig.com/books/123/?ref=x") == "https://poleknig.com/books/123"


def test_http_session_is_long_lived_until_profile_refresh():
    first = core.get_http_session()
    second = core.get_http_session()
    assert first is second
    core.refresh_http_session_profile()
    third = core.get_http_session()
    assert third is not first
    third.close()


def test_queue_roundtrip_uses_model_to_dict_and_preserves_templates(tmp_path):
    book = Book(url="https://poleknig.com/books/1", title="One", tracks=[Track(1, "A", "https://x/1.mp3")])
    request = DownloadRequest(
        book=book, selected_indices=[1], output_dir=tmp_path,
        use_templates=True, folder_template="{Author}/{Book_Title}", track_template="{Track_Number}-{Track_Title}.mp3",
    )
    from audioknigi.services.queue_service import QueueStore
    task = QueueStore.new_task(request)
    data = task_to_dict(task)
    restored = task_from_dict(data)
    assert restored.request.folder_template == request.folder_template
    assert restored.request.track_template == request.track_template
    assert restored.request.book.tracks[0].title == "A"
    assert "asdict(" not in text("audioknigi/services/queue_service.py")


def test_legacy_flat_queue_item_is_preserved_not_silently_dropped():
    task = task_from_dict({
        "url": "https://knigavuhe.org/book/example/",
        "title": "Legacy",
        "selected_indices": [1, 2],
        "folder_template": "{Book_Title}",
        "track_template": "{Track_Number}.mp3",
    })
    assert task.title == "Legacy"
    assert task.status_code == "needs_analysis"
    assert task.paused is True
    assert task.request.book.url.startswith("https://")


def test_duplicate_preflight_requires_ready_not_merely_existing():
    source = text("audioknigi/download_engine.py")
    assert 'scan.get("ready", 0) == scan.get("total", 0)' in source


def test_resume_manifest_write_failure_is_not_silent():
    source = text("audioknigi/download_engine.py")
    assert "if not save_json(path, manifest):" in source
    assert "raise OSError" in source


def test_subprocess_registry_is_weak_and_ffprobe_unregisters():
    engine = text("audioknigi/download_engine.py")
    downloader = text("audioknigi/downloader.py")
    assert "self._active_subprocesses = weakref.WeakSet()" in engine
    assert "self._unregister_active_subprocess(proc)" in downloader


def test_partial_cleanup_includes_assembling_file():
    source = text("audioknigi/downloader.py")
    assert 'part.with_name(part.name + ".assembling")' in source


def test_ffmpeg_split_and_measure_use_same_input_side_seek():
    source = text("audioknigi/downloader.py")
    start = source.index("def _split_track")
    split = source[start:start + 5000]
    assert 'cmd += ["-ss", str(start)]\n            cmd += ["-i", str(source_path)]' in split
    measure = source[source.index("def _measure_loudnorm"):source.index("def _normalization_filter_for_track")]
    assert 'cmd += ["-ss", str(start)]\n            cmd += ["-i", str(source_path)]' in measure


def test_search_providers_are_not_wrapped_in_second_executor():
    source = text("audioknigi/services/search_service.py")
    body = source[source.index("def search_all_sources"):source.index("__all__", source.index("def search_all_sources"))]
    assert "ThreadPoolExecutor" not in body
    assert "cancel_event" in body


def test_accessible_announcer_does_not_restart_active_polite_timer():
    source = text("audioknigi/qt/accessibility.py")
    assert "if not self._timer.isActive():" in source
    assert "QThread.currentThread() != self.thread()" in source
    assert "QItemSelectionModel.SelectionFlag.ClearAndSelect" in source


def test_theme_preserves_scaled_font():
    source = text("audioknigi/qt/theme.py")
    assert "preserved_font = app.font()" in source
    assert "app.setFont(preserved_font)" in source


def test_speed_graph_filters_non_finite_values():
    source = text("audioknigi/qt/speed_graph.py")
    assert "math.isfinite" in source


def test_track_bulk_toggle_invalidates_accessible_text_role():
    source = text("audioknigi/qt/track_model.py")
    assert "Qt.ItemDataRole.AccessibleTextRole" in source[source.index("def set_all_selected"):]


def test_player_resume_not_cleared_from_provisional_duration_and_end_restarts():
    source = text("audioknigi/qt/player_controller.py")
    duration = source[source.index("def _on_duration_changed"):source.index("def _on_playback_state_changed")]
    assert "store.clear" not in duration
    play = source[source.index("def play(self)"):source.index("def pause(self)")]
    assert "EndOfMedia" in play and "setPosition(0)" in play


def test_focus_trace_bare_flag_is_explicit_error():
    source = text("audioknigi/qt/accessibility_trace.py")
    assert '--qt-focus-trace требует путь' in source


def test_application_does_not_show_then_maximize_and_uses_captured_hook():
    source = text("audioknigi/qt/application.py")
    assert "original_excepthook = sys.excepthook" in source
    fragment = source[source.index("window = AudioKnigiQtWindow()"):source.index("app.exec()") ]
    assert "window.showMaximized()" in fragment
    assert "else:\n        window.show()" in fragment
    assert "window.show()\n    window.showMaximized()" not in fragment


def test_event_sounds_do_not_swap_one_player_source_per_event():
    source = text("audioknigi/qt/event_sounds.py")
    assert "self._players" in source
    play = source[source.index("def play(self, event"):source.index("def shutdown")]
    assert "self.player.setSource" not in play


def test_full_parity_inventory_is_not_runtime_acceptance():
    assert inventory_parity_complete() is True
    assert full_parity_complete() is False
    assert full_parity_complete(runtime_validated=True) is True


def test_playwright_cookie_persistence_invalidates_sessions():
    source = text("audioknigi/core.py")
    persist = source[source.index("def persist_browser_session"):source.index("def persist_browser_cookies")]
    assert "refresh_http_session_profile()" in persist


def test_i18n_split_progress_uses_translation_key():
    source = text("audioknigi/downloader.py")
    assert '"status_splitting_progress"' in source
    assert 'f"Разделение {current}' not in source


def test_proxy_relay_preserves_reverse_data_after_half_close():
    import socket
    import threading
    from audioknigi.network_dns import _relay_bidirectional

    client, relay_left = socket.socketpair()
    relay_right, server = socket.socketpair()
    thread = threading.Thread(target=_relay_bidirectional, args=(relay_left, relay_right), daemon=True)
    thread.start()
    try:
        client.sendall(b"request")
        client.shutdown(socket.SHUT_WR)
        assert server.recv(7) == b"request"
        server.sendall(b"response")
        server.shutdown(socket.SHUT_WR)
        assert client.recv(8) == b"response"
        thread.join(2.0)
        assert not thread.is_alive()
    finally:
        for sock in (client, relay_left, relay_right, server):
            try:
                sock.close()
            except OSError:
                pass


def test_queue_store_keeps_legacy_flat_item(tmp_path):
    import json
    path = tmp_path / "qt_queue.json"
    path.write_text(json.dumps([{"url": "https://poleknig.com/books/9", "title": "Old"}]), encoding="utf-8")
    tasks = QueueStore(path).load()
    assert len(tasks) == 1
    assert tasks[0].status_code == "needs_analysis"


def test_http_pool_no_arbitrary_24_use_rotation():
    source = text("audioknigi/core.py")
    body = source[source.index("def get_http_session"):source.index("def refresh_http_session_profile")]
    assert "uses >= 24" not in body
    assert "profile_generation" in body
    assert "pool_maxsize=32" in source


def test_download_single_metrics_reset_is_in_finally():
    source = text("audioknigi/downloader.py")
    start = source.index("def _download_single")
    body = source[start:source.index("def _download_segment", start)]
    assert "finally:" in body
    assert "self.record_transfer_metrics(0, 0)" in body


def test_close_after_cancel_sets_explicit_exit_intent():
    source = text("audioknigi/qt/main_window.py")
    helper = source[source.index("def _begin_deferred_exit"):source.index("def closeEvent")]
    assert "self._exit_requested = True" in helper
    assert "self._cancel_all_workers_for_exit()" in helper
    close = source[source.index("def closeEvent"):]
    assert close.count("self._begin_deferred_exit()") >= 3
    cancel = source[source.index("def _request_download_cancel"):source.index("def cancel_download")]
    assert "box.reject()" in cancel and "box.close()" not in cancel
