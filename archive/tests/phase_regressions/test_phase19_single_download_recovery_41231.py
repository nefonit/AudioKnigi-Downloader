from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def make_request(tmp_path, *, tracks=None):
    from audioknigi.models import Book, Track
    from audioknigi.services.download_request import DownloadRequest

    tracks = tracks or [Track(1, "One", "https://media.example/one.mp3")]
    return DownloadRequest(
        book=Book(url="https://audioknigi.com.ua/audio-1", title="Book", tracks=tracks),
        selected_indices=[int(tracks[0].index)],
        output_dir=tmp_path,
    )


def test_single_download_reacquires_declared_http_session(monkeypatch, tmp_path):
    import audioknigi.downloader as downloader
    from audioknigi.download_engine import _DownloadEngine

    calls = []

    class Response:
        status_code = 200
        headers = {"content-length": "4"}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def raise_for_status(self):
            return None
        def iter_content(self, chunk_size=None):
            yield b"data"
        def close(self):
            return None

    class Session:
        def get(self, url, **kwargs):
            calls.append((url, kwargs))
            return Response()

    monkeypatch.setattr(downloader, "get_http_session", lambda: Session())
    engine = _DownloadEngine(make_request(tmp_path), {}, threading.Event(), None)
    target = tmp_path / "single.mp3"
    assert engine._download_single("https://media.example/book.mp3", target, "https://example/") == target
    assert target.read_bytes() == b"data"
    assert len(calls) == 1


def test_loudnorm_json_is_decoded_structurally_not_by_brace_regex(monkeypatch, tmp_path):
    from audioknigi.download_engine import _DownloadEngine

    engine = _DownloadEngine(make_request(tmp_path), {}, threading.Event(), None)
    stderr = '''debug path={C:\\Books\\{odd}}\n[Parsed_loudnorm] {\n"input_i" : "-20.10",\n"input_tp" : "-2.00",\n"input_lra" : "5.20",\n"input_thresh" : "-30.00",\n"output_i" : "-15.90",\n"output_tp" : "-1.40",\n"output_lra" : "5.10",\n"output_thresh" : "-25.90",\n"normalization_type" : "dynamic",\n"target_offset" : "-0.10"\n}\n'''
    monkeypatch.setattr(engine, "_run_ffmpeg_capture", lambda *a, **k: stderr)
    filt = engine._measure_loudnorm(tmp_path / "{source}.mp3")
    assert "measured_I=-20.10" in filt
    assert "offset=-0.10" in filt


def test_fallback_notifies_request_change_for_crash_safe_queue_persistence(monkeypatch, tmp_path):
    from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
    from audioknigi.downloader import SharedSourceTimelineError
    from audioknigi.models import Book, Track

    request = make_request(tmp_path, tracks=[Track(1, "One", "https://bad/all.mp3", start=0, end=10)])
    fallback = Book(
        url="https://knigavuhe.org/book/good/",
        title="Fallback Book",
        tracks=[Track(1, "One", "https://good/1.mp3")],
    )
    snapshots = []
    callbacks = DownloadCallbacks(request_changed=lambda req: snapshots.append(req.book.url))
    engine = _DownloadEngine(request, {}, threading.Event(), callbacks)
    attempts = {"n": 0}

    def process_once(book, selected, status):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise SharedSourceTimelineError({"expected_end": 10, "actual_duration": 5, "reason": "short"})
        return str(tmp_path)

    monkeypatch.setattr(engine, "_process_book_once", process_once)
    monkeypatch.setattr(engine, "_knigavuhe_fallback_candidate", lambda _book: fallback)
    monkeypatch.setattr(engine, "_populate_missing_track_durations", lambda _book: 0)
    monkeypatch.setattr(engine, "_log_book_flow", lambda *a, **k: None)
    monkeypatch.setattr(engine, "log", lambda *a, **k: None)

    engine._process_book(request.book, {1}, None)
    assert snapshots == [fallback.url]


def test_qt_worker_persists_request_change_before_download_finishes():
    workers = text("audioknigi/qt/workers.py")
    main = text("audioknigi/qt/main_window.py")
    assert "request_changed = Signal(object)" in workers
    assert "request_changed=lambda request: self.request_changed.emit(copy.deepcopy(request))" in workers
    assert "worker.request_changed.connect(self._download_request_changed)" in main
    slot = main[main.index("def _download_request_changed"):main.index("def _download_finished")]
    assert "queue_task.request = request" in slot
    assert "self._persist_queue()" in slot


def test_supported_url_stays_restricted_to_book_pages():
    from audioknigi.sources import is_supported_url

    assert is_supported_url("https://audioknigi.com.ua/audio-123/")
    assert is_supported_url("https://knigavuhe.org/book/example/")
    assert is_supported_url("https://poleknig.com/books/223511")
    assert not is_supported_url("https://audioknigi.com.ua/user/admin/")
    assert not is_supported_url("https://knigavuhe.org/author/ivan-ivanov/")
    assert not is_supported_url("https://poleknig.com/authors/42")


def test_event_sound_sentinel_balances_queue_and_players_are_deleted():
    source = text("audioknigi/qt/event_sounds.py")
    worker = source[source.index("def _system_sound_worker"):source.index("def play_system")]
    assert "while True:" in worker
    assert worker.index("if flag is None:") < worker.index("task_done()")
    stop = source[source.index("def _stop_players"):source.index("def shutdown")]
    assert "player.deleteLater()" in stop
    assert "output.deleteLater()" in stop
    shutdown = source[source.index("def shutdown"):source.index("__all__")]
    assert "get_nowait()" in shutdown
    assert "put_nowait(None)" in shutdown


def test_standard_nested_dataclass_survives_to_dict():
    from audioknigi.models import MappingDataclass

    @dataclass
    class Child:
        value: int

    assert MappingDataclass._plain_value(Child(7)) == {"value": 7}


def test_create_application_sanitizes_internal_focus_trace_args_even_when_called_directly():
    source = text("audioknigi/qt/application.py")
    body = source[source.index("def create_application"):source.index("def run_qt")]
    assert "extract_focus_trace_argument(raw_argv)" in body
    assert "QApplication(clean_argv)" in body
    assert "QApplication(list(sys.argv" not in body


def test_close_exit_uses_single_polling_path_and_cancels_all_workers():
    source = text("audioknigi/qt/main_window.py")
    close = source[source.index("def _cancel_all_workers_for_exit"):source.index("__all__", source.index("def closeEvent"))]
    assert "self._request_download_cancel()" in close
    assert "self._analysis_cancel.set()" in close
    assert "self._search_cancel.set()" in close
    assert "self._schedule_exit_poll()" in close
    assert "QTimer.singleShot(_EXIT_POLL_MS, self._poll_deferred_exit)" in close
    assert "finished.connect(self.close)" not in close


def test_clear_worker_slots_do_not_reenable_ui_during_exit():
    source = text("audioknigi/qt/main_window.py")
    for name, next_name in [
        ("def _clear_analysis_thread", "def cancel_analysis"),
        ("def _clear_download_thread", "def start_search"),
        ("def _clear_search_thread", "def _show_search_context_menu"),
    ]:
        body = source[source.index(name):source.index(next_name, source.index(name))]
        assert "if self._exit_requested:" in body


def test_poleknig_search_timeout_is_bounded_for_cancellation():
    source = text("audioknigi/poleknig.py")
    body = source[source.index("def _fetch_search_page"):source.index("def _query_matches_metadata")]
    assert "timeout=(6, 15)" in body
    assert "timeout=(10, 35)" not in body


def test_phase19_stage_will_be_current_after_packaging():
    # Updated during Phase 19 finalization; this test intentionally forces the
    # release stage to move with the code changes.
    source = text("audioknigi/qt/__init__.py")
    assert 'QT_MIGRATION_STAGE = "phase-39"' in source
