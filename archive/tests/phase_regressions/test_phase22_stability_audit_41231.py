from __future__ import annotations

import json
from pathlib import Path

import pytest

from audioknigi.core import DEFAULT_OUTPUT
from audioknigi.downloader import AdaptiveRangeController, DownloaderMixin
from audioknigi.knigavuhe import _book_page_search_metadata
from audioknigi.models import Book, Track
from audioknigi.poleknig import _canonical_book_url, parse_search_results
from audioknigi.services.library_service import scan_unfinished
from audioknigi.services.queue_service import task_from_dict

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_zero_speed_counts_as_slow_and_reduces_range_concurrency():
    controller = AdaptiveRangeController(8, adaptive=True, min_per_worker=100.0)
    controller.last_change = 0.0
    for _ in range(5):
        controller.observe(0.0)
    assert controller.current_workers() == 4


def test_range_transient_http_does_not_use_rangeunsupported_path():
    source = text("audioknigi/downloader.py")
    body = source[source.index("def _download_segment("):source.index("def _choose_segment_count", source.index("def _download_segment("))]
    assert "if status == 429 or 500 <= status <= 599:" in body
    assert "raise requests.HTTPError" in body
    assert "if status == 200:" in body
    assert "if status == 416:" in body


def test_verify_track_uses_effective_duration(tmp_path):
    class Dummy(DownloaderMixin):
        def _track_path(self, book, track, mode=None, *, create_folder=True):
            p = tmp_path / "01.mp3"
            p.write_bytes(b"x")
            return p
        def _probe_duration(self, path):
            return 12.0

    track = Track(index=1, title="one", file="x", duration=None, actual_duration=12.0)
    book = Book(url="https://example.test", title="b", tracks=[track])
    status, actual, _path = Dummy()._verify_track_file(book, track)
    assert status == "готово"
    assert actual == 12.0


def test_probe_audio_info_unregisters_subprocess_and_audio_info_is_cached():
    source = text("audioknigi/downloader.py")
    probe = source[source.index("def _probe_audio_info"):source.index("def _cached_probe_audio_info")]
    assert "self._unregister_active_subprocess(proc)" in probe
    cached = source[source.index("def _cached_probe_audio_info"):source.index("def _preset_target")]
    assert "stat.st_mtime_ns" in cached
    assert "self._probe_audio_info(path)" in cached
    assert "_audio_info_lock" in cached


def test_mixin_fallback_request_update_is_optional():
    source = text("audioknigi/downloader.py")
    body = source[source.index("def _process_book("):source.index("def _process_book_once")]
    assert 'req = getattr(self, "request", None)' in body
    assert "if req is not None:" in body


def test_knigavuhe_title_suffix_does_not_leak_into_author_or_narrator():
    html = "<title>Книга - автор Лев Толстой, читает Иван Иванов (слушать аудиокнигу онлайн)</title>"
    meta = _book_page_search_metadata(html)
    assert meta["title"] == "Книга"
    assert meta["author"] == "Лев Толстой"
    assert meta["narrator"] == "Иван Иванов"


def test_poleknig_direct_slug_is_canonical_and_real_title_with_dash_is_preserved():
    assert _canonical_book_url("https://poleknig.com/", "/books/12345-master-i-margarita") == "https://poleknig.com/books/12345"
    html = '<a href="/books/12345"><span>Война и мир — Том 1</span></a>'
    results = parse_search_results(html)
    assert results and results[0].title == "Война и мир — Том 1"


def test_network_dns_hardening_and_playwright_fallback_are_present():
    source = text("audioknigi/network_dns.py")
    assert '.encode("idna").decode("ascii")' in source
    assert 'low.startswith((b"connection:", b"proxy-connection:"))' in source
    assert 'filtered.append(b"Connection: close")' in source
    assert "def launch_playwright_chromium" in source
    assert 'fallback.pop("channel", None)' in source


def test_qt_runtime_audit_snapshots_sys_modules_and_application_restores_hook():
    audit = text("audioknigi/qt_runtime_audit.py")
    app = text("audioknigi/qt/application.py")
    assert "list(sys.modules.keys())" in audit
    assert "finally:\n        sys.excepthook = original_excepthook" in app


def test_queue_corrupt_track_and_missing_output_dir_are_safe():
    data = {
        "id": "1", "title": "Book", "request": {
            "book": {"url": "https://knigavuhe.org/book/test/", "title": "Book", "tracks": [{}]},
            "selected_indices": [], "output_dir": None,
        }
    }
    task = task_from_dict(data)
    assert task.request.output_dir == DEFAULT_OUTPUT.expanduser()
    assert task.request.book.tracks[0].index == 0
    assert task.request.book.tracks[0].title == ""
    assert task.request.book.tracks[0].file == ""


def test_scan_unfinished_ignores_manifest_without_selected_parts(tmp_path):
    folder = tmp_path / "book"
    folder.mkdir()
    (folder / "resume.json").write_text(json.dumps({"url": "https://example.test", "selected_indices": []}), encoding="utf-8")
    assert scan_unfinished(tmp_path) == []


def test_qt_worker_sound_marshalling_and_easy_mode_focus_are_present():
    sounds = text("audioknigi/qt/event_sounds.py")
    window = text("audioknigi/qt/main_window.py")
    assert "_queued_play = Signal(str, bool)" in sounds
    assert "QThread.currentThread() != self.thread()" in sounds
    assert "Qt.ConnectionType.QueuedConnection" in sounds
    assert 'if self.current_ui_mode() == "easy":\n                self.easy_download_button.setFocus' in window


def test_track_redownload_search_table_queue_refresh_and_close_semantics_are_hardened():
    source = text("audioknigi/qt/main_window.py")
    assert "elif action is redownload:" in source
    assert 'Path(path_text).expanduser().unlink(missing_ok=True)' in source
    assert "def _selected_search_result(self, table=None)" in source
    assert "result = self._selected_search_result(table)" in source
    assert "self.current_book = queue_task.request.book" in source
    close = source[source.index("def closeEvent("):source.index('__all__', source.index("def closeEvent("))]
    assert "self._should_auto_tray()" not in close


def test_book_analysis_cancellation_does_not_wait_for_executor_context_manager():
    source = text("audioknigi/services/book_analysis_service.py")
    body = source[source.index("unique_files ="):source.index("return Book(", source.index("unique_files ="))]
    assert "_iter_completed_cancellable(futures, self.cancel_event)" in body
    assert "pool.shutdown(wait=False, cancel_futures=True)" in body
    assert "with ThreadPoolExecutor(max_workers=2)" not in body


def test_stream_copy_uses_non_negative_timestamp_normalization():
    source = text("audioknigi/downloader.py")
    body = source[source.index("def _split_track("):source.index("def _save_book_sidecars", source.index("def _split_track("))]
    assert '["-c:a", "copy", "-avoid_negative_ts", "make_zero"]' in body


def test_full_mp3_refreshes_expired_source_and_never_tags_non_mp3_bytes_directly():
    source = text("audioknigi/download_engine.py")
    body = source[source.index("def run_full_mp3("):source.index("def run(self)", source.index("def run_full_mp3("))]
    assert "self._is_expired_media_error(exc)" in body
    assert "self._refresh_book_media_playlist(book, selected)" in body
    assert 'copy_mode, bitrate, channels = self._effective_mp3_profile(source_target)' in body
    assert 'if copy_mode:' in body
    assert '"-c:a", "libmp3lame"' in body
    assert ".full-source" in body
