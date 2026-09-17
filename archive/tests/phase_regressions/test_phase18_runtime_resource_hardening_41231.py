from __future__ import annotations

from concurrent.futures import Future
from pathlib import Path
import threading

import pytest

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def make_request(tmp_path, *, url="https://audioknigi.com.ua/audio-1", tracks=None):
    from audioknigi.models import Book, Track
    from audioknigi.services.download_request import DownloadRequest

    tracks = tracks or [Track(1, "One", "https://media.example/one.mp3")]
    return DownloadRequest(
        book=Book(url=url, title="Book", tracks=tracks),
        selected_indices=[int(tracks[0].index)],
        output_dir=tmp_path,
    )


def test_real_service_filenames_and_queue_analysis_export_exist():
    from audioknigi.services.queue_service import task_requires_analysis

    assert callable(task_requires_analysis)
    assert (ROOT / "audioknigi/services/queue_service.py").is_file()
    assert (ROOT / "audioknigi/services/search_service.py").is_file()
    assert not list(ROOT.rglob("text/x-python"))


def test_ffmpeg_helpers_unregister_finished_processes(monkeypatch, tmp_path):
    import audioknigi.downloader as downloader
    from audioknigi.download_engine import _DownloadEngine

    class Proc:
        returncode = 0
        def communicate(self, timeout=None):
            return None, "ok"
        def poll(self):
            return self.returncode
        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(downloader.subprocess, "Popen", lambda *a, **k: Proc())
    engine = _DownloadEngine(make_request(tmp_path), {}, threading.Event(), None)
    engine._run_ffmpeg(["ffmpeg", "-version"])
    assert len(engine._active_subprocesses) == 0
    assert engine._run_ffmpeg_capture(["ffmpeg", "-version"]) == "ok"
    assert len(engine._active_subprocesses) == 0


def test_range_segment_reacquires_http_session_for_each_subrequest(monkeypatch, tmp_path):
    import audioknigi.downloader as downloader
    from audioknigi.download_engine import _DownloadEngine

    calls = []

    class Response:
        status_code = 206
        def __init__(self, start, end, payload):
            self.headers = {"content-range": f"bytes {start}-{end}/4"}
            self.payload = payload
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def raise_for_status(self):
            return None
        def iter_content(self, chunk_size=None):
            yield self.payload
        def close(self):
            return None

    class Session:
        def __init__(self, number):
            self.number = number
        def get(self, url, headers=None, stream=True, timeout=None):
            start = int(headers["Range"].split("=", 1)[1].split("-", 1)[0])
            calls.append((self.number, start))
            if start == 0:
                return Response(0, 1, b"ab")
            return Response(2, 3, b"cd")

    count = {"value": 0}
    def get_session():
        count["value"] += 1
        return Session(count["value"])

    monkeypatch.setattr(downloader, "get_http_session", get_session)
    engine = _DownloadEngine(make_request(tmp_path), {}, threading.Event(), None)
    seg = tmp_path / "x.seg"
    result = engine._download_segment("https://x/file", seg, 0, 3, "https://x/", lambda *_a, **_k: None)
    assert result == 4
    assert seg.read_bytes() == b"abcd"
    assert calls == [(1, 0), (2, 2)]


def test_source_fallback_updates_request_and_result_book(monkeypatch, tmp_path):
    from audioknigi.download_engine import _DownloadEngine
    from audioknigi.downloader import SharedSourceTimelineError
    from audioknigi.models import Book, Track

    request = make_request(tmp_path, tracks=[Track(1, "One", "https://bad/all.mp3", start=0, end=10)])
    fallback = Book(
        url="https://knigavuhe.org/book/good/",
        title="Book",
        tracks=[Track(1, "One", "https://good/1.mp3")],
    )
    engine = _DownloadEngine(request, {}, threading.Event(), None)
    attempts = {"n": 0}

    def process_once(book, selected, status):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise SharedSourceTimelineError({"expected_end": 10, "actual_duration": 5, "reason": "short"})
        assert book is fallback
        return str(tmp_path)

    monkeypatch.setattr(engine, "_process_book_once", process_once)
    monkeypatch.setattr(engine, "_knigavuhe_fallback_candidate", lambda _book: fallback)
    monkeypatch.setattr(engine, "_populate_missing_track_durations", lambda _book: 0)
    monkeypatch.setattr(engine, "_log_book_flow", lambda *a, **k: None)
    monkeypatch.setattr(engine, "log", lambda *a, **k: None)

    folder = engine._process_book(request.book, {1}, None)
    assert folder == str(tmp_path)
    assert engine.request.book is fallback
    assert engine.request.selected_indices == [1]


def test_persist_browser_session_has_one_profile_condition_block():
    source = text("audioknigi/core.py")
    body = source[source.index("def persist_browser_session"):source.index("def persist_browser_cookies")]
    assert body.count("if cleaned or safe_headers:") == 1
    assert "refresh_http_session_profile()" in body


def test_mapping_field_cache_is_safe_for_non_dataclass_base():
    from audioknigi.models import MappingDataclass, _dataclass_field_names
    assert _dataclass_field_names(MappingDataclass) == ()
    assert len(MappingDataclass()) == 0


def test_supported_url_requires_concrete_book_page():
    from audioknigi.sources import is_supported_url

    assert is_supported_url("https://audioknigi.com.ua/audio-123-title/")
    assert is_supported_url("https://knigavuhe.org/book/demo/")
    assert is_supported_url("https://poleknig.com/books/123")
    assert is_supported_url("audioknigi.com.ua:8080/audio-123/")
    assert not is_supported_url("https://audioknigi.com.ua/about")
    assert not is_supported_url("https://knigavuhe.org/genres/")
    assert not is_supported_url("https://poleknig.com/authors/12")


def test_queue_serializer_tolerates_none_track_lists(tmp_path):
    from audioknigi.models import Book
    from audioknigi.services.download_request import DownloadRequest
    from audioknigi.services.queue_service import QueueTask, task_to_dict

    book = Book(url="https://knigavuhe.org/book/x/", title="X")
    book.tracks = None  # type: ignore[assignment]
    book.narration_variants = None  # type: ignore[assignment]
    task = QueueTask("id", DownloadRequest(book, [], tmp_path), "X", status_code="needs_analysis")
    data = task_to_dict(task)
    assert data["request"]["book"]["tracks"] == []
    assert data["request"]["book"]["narration_variants"] == []


def test_accessible_announcer_followup_uses_base_delay():
    source = text("audioknigi/qt/accessibility.py")
    flush = source[source.index("def _flush"):source.index("def _deliver")]
    assert "self._timer.start(self.polite_delay_ms)" in flush
    assert "400" not in flush


def test_system_sound_worker_is_daemon_and_executor_free():
    source = text("audioknigi/qt/event_sounds.py")
    assert "daemon=True" in source
    assert "ThreadPoolExecutor" not in source
    assert "self._system_shutdown.is_set()" in source
    assert "put_nowait" in source


def test_close_event_rechecks_without_second_hidden_modal():
    source = text("audioknigi/qt/main_window.py")
    close = source[source.index("def closeEvent"):source.index("__all__", source.index("def closeEvent"))]
    assert "if self._exit_requested:" in close
    assert "self._schedule_exit_poll()" in close
    assert "QTimer.singleShot(_EXIT_POLL_MS, self._poll_deferred_exit)" in source
    assert close.index("if self._exit_requested:") < close.index("if self._thread_is_running(self._download_thread)")


def test_missing_media_cancel_rejects_without_forced_close_and_handles_deleted_cpp_object():
    source = text("audioknigi/qt/main_window.py")
    cancel = source[source.index("def _request_download_cancel"):source.index("def cancel_download")]
    assert "box.reject()" in cancel
    assert "box.close()" not in cancel
    resolve = source[source.index("def _resolve_missing_media"):source.index("def _download_finished")]
    assert "clicked_button = None" in resolve
    assert resolve.count("except RuntimeError") >= 2


def test_needs_analysis_task_cannot_receive_priority():
    source = text("audioknigi/qt/main_window.py")
    states = source[source.index("def _update_queue_action_states"):source.index("def _update_history_action_states")]
    assert "needs_analysis = bool(task and task_requires_analysis(task))" in states
    assert "not needs_analysis" in states
    toggle = source[source.index("def toggle_queue_priority"):source.index("def move_queue_selected")]
    assert "if task_requires_analysis(task):" in toggle


def test_output_dialog_relies_on_single_sync_assignment():
    source = text("audioknigi/qt/main_window.py")
    chooser = source[source.index("def _choose_output_dir"):source.index("def _preview_theme")]
    assert chooser.count(".setText(selected)") == 1


def test_knigavuhe_and_poleknig_cancel_pools_without_waiting():
    knig = text("audioknigi/knigavuhe.py")
    pole = text("audioknigi/poleknig.py")
    assert "pool.shutdown(wait=False, cancel_futures=True)" in knig
    assert "pool.shutdown(wait=False, cancel_futures=True)" in pole
    assert "wait(pending, timeout=0.10, return_when=FIRST_COMPLETED)" in knig
    assert "wait(pending, timeout=0.10, return_when=FIRST_COMPLETED)" in pole


def test_out_variable_claim_is_not_a_real_unbound_path():
    source = text("audioknigi/downloader.py")
    body = source[source.index("def _split_track"):source.index("def _save_book_sidecars")]
    assert body.index("out = self._track_path(book, track)") < body.index("try:\n            self._run_ffmpeg")


def test_poleknig_analysis_and_downloader_propagate_cancel_event():
    analysis = text("audioknigi/services/book_analysis_service.py")
    downloader = text("audioknigi/downloader.py")
    pole = text("audioknigi/poleknig.py")
    assert "fetch_poleknig_book(normalized, cancel_event=self.cancel_event)" in analysis
    assert "fetch_poleknig_book(url, cancel_event=self.cancel_event)" in downloader
    assert "def fetch_book(url: str, cancel_event=None)" in pole
    assert "cancel_event=cancel_event" in pole[pole.index("def fetch_book"):pole.index("class _BookLinkParser")]
