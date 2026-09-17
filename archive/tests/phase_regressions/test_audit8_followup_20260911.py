from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from audioknigi.core import Cancelled
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.downloader import DownloaderMixin
from audioknigi.knigavuhe import parse_book_html
from audioknigi.models import Book, SearchResult, Track
from audioknigi.poleknig import _parse_playlist_objects
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.search_service import _iter_completed_cancellable
from audioknigi.templates import template_values

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_ffprobe_read_intervals_keeps_seconds_separator_syntax():
    source = text("audioknigi/downloader.py")
    block = source[source.index("def _local_audio_has_packets_near"):source.index("def _probe_remote_duration", source.index("def _local_audio_has_packets_near"))]
    # ffprobe syntax is START%+DURATION: '%' is the interval separator, not a percentage sign.
    assert '"-read_intervals", f"{start:.3f}%+{span:.3f}"' in block
    assert 'f"{start:.3f}+{span:.3f}"' not in block


def test_direct_download_request_inherits_template_settings_when_omitted(tmp_path):
    book = Book(url="https://example.test/book", title="Book", tracks=[Track(1, "One", "https://example.test/1.mp3")])
    request = DownloadRequest(book=book, selected_indices=[1], output_dir=tmp_path)
    engine = _DownloadEngine(
        request,
        {
            "use_templates": True,
            "folder_template": "{Author}/{Book_Title}",
            "track_template": "{Track_Number} - {Track_Title}.mp3",
        },
        threading.Event(),
        DownloadCallbacks(),
    )
    assert engine.runtime_use_templates is True
    assert engine.runtime_folder_template == "{Author}/{Book_Title}"
    assert engine.runtime_track_template == "{Track_Number} - {Track_Title}.mp3"


def test_downloader_mixin_defaults_match_engine_defaults():
    assert DownloaderMixin.runtime_embed_tags is True
    assert DownloaderMixin.runtime_delete_source is True


def test_full_mp3_refresh_recomputes_target_from_refreshed_title():
    source = text("audioknigi/download_engine.py")
    block = source[source.index("def run_full_mp3"):source.index("def run(", source.index("def run_full_mp3"))]
    refresh = block.index("self._refresh_book_media_playlist(book, selected)")
    assert block.index("target = self._full_mp3_target(book, folder)", refresh) > refresh
    assert block.index("source_target = folder / f\".{title_name}.full-source\"", refresh) > refresh


def test_parallel_source_failure_closes_other_active_network_io():
    source = text("audioknigi/downloader.py")
    block = source[source.index("with ThreadPoolExecutor(max_workers=max_workers)"):]
    block = block[:block.index("source_downloads_complete")]
    assert "pending.cancel()" in block
    assert "self._cancel_active_network_io()" in block


def test_proxy_shutdown_and_write_loop_are_bounded():
    source = text("audioknigi/network_dns.py")
    shutdown = source[source.index("def shutdown_cloudflare_playwright_proxy"):source.index("def cloudflare_ffmpeg_input_args")]
    relay = source[source.index("def _relay_bidirectional"):source.index("def _read_http_head")]
    assert "thread is not None and thread.is_alive()" in shutdown
    assert "time.monotonic() - stalled_since >= 20.0" in relay


def test_knigavuhe_skips_invalid_primary_without_user_index_gaps():
    payload = {
        "book": {"name": "Book"},
        "playlist": [
            {"file": "https://cdn.test/1.mp3", "title": "One"},
            {"title": "broken"},
            {"file": "https://cdn.test/3.mp3", "title": "Three"},
        ],
        "merged_playlist": [
            {"file": "https://mirror.test/1.mp3"},
            {"file": "https://mirror.test/broken.mp3"},
            {"file": "https://mirror.test/3.mp3"},
        ],
    }
    book = parse_book_html(f"<script>BookController.enter({json.dumps(payload)});</script>", "https://knigavuhe.org/book/test/")
    assert [track.index for track in book.tracks] == [1, 2]
    assert [track.title for track in book.tracks] == ["One", "Three"]


def test_poleknig_list_playlist_skips_invalid_rows_without_index_gaps():
    value = json.dumps([
        {"file": "a.mp3", "title": "One"},
        {"title": "broken"},
        {"file": "c.mp3", "title": "Three"},
    ])
    tracks = _parse_playlist_objects(value, "https://poleknig.com/books/1")
    assert [track.index for track in tracks] == [1, 2]
    assert [track.title for track in tracks] == ["One", "Three"]


def test_accessibility_trace_write_is_non_invasive_on_io_error():
    source = text("audioknigi/qt/accessibility_trace.py")
    block = source[source.index("def _write"):source.index("def _focus_changed")]
    assert "except (OSError, ValueError):" in block


def test_path_unknown_author_is_stable_across_ui_languages():
    book = Book(url="https://example.test", title="Book")
    assert template_values(book, language="ru")["Author"] == "Без автора"
    assert template_values(book, language="en")["Author"] == "Без автора"
    assert template_values(book, language="de")["Author"] == "Без автора"


def test_search_service_cancellation_is_typed_and_immediate():
    event = threading.Event(); event.set()
    generator = _iter_completed_cancellable([], event)
    # Empty futures finish without consulting cancellation; use one inert sentinel Future.
    from concurrent.futures import Future
    generator = _iter_completed_cancellable([Future()], event)
    with pytest.raises(Cancelled):
        next(generator)


def test_ui_followup_fixes_are_present_without_qt_runtime_imports():
    main = text("audioknigi/qt/main_window.py")
    player = text("audioknigi/qt/player_mixin.py")
    settings = text("audioknigi/qt/settings_sync.py")
    menu = text("audioknigi/qt/localized_context_menu.py")
    sounds = text("audioknigi/qt/event_sounds.py")
    assert 'self.easy_cover_label.setText(self._l("Нет обложки"))' in main
    paste = main[main.index("def paste_book_url"):main.index("def _set_clipboard_text")]
    assert 'self._play_event_sound("link_pasted")' in paste
    redownload = main[main.index("def history_redownload"):main.index("def history_delete")]
    assert 'self.set_ui_mode("advanced", persist=False)' in redownload
    switch = player[player.index("def _player_switch_chapter"):player.index("def media_play_pause")]
    assert "current_path" in switch and "_select_player_chapter_path(target)" in switch
    assert 'getattr(self, "output_edit", None)' in player
    assert 'str(data.get("segment_count") or "auto")' in settings
    assert 'cursor.insertText("")' in menu
    assert "pair = (player, output)" in sounds


def test_unknown_source_narrator_does_not_choose_between_different_readers(monkeypatch):
    import audioknigi.services.book_analysis_service as mod

    service = BookAnalysisService()
    source = Book(url="https://audioknigi.com.ua/audio-1", title="Same Book", author="Author", narrator="")
    monkeypatch.setattr(mod, "search_knigavuhe_books", lambda *_args, **_kwargs: [
        SearchResult(title="Same Book", url="https://knigavuhe.org/book/a/", author="Author", narrator="Reader A"),
        SearchResult(title="Same Book", url="https://knigavuhe.org/book/b/", author="Author", narrator="Reader B"),
    ])
    def fetch(url, cancel_event=None):
        reader = "Reader A" if url.endswith("/a/") else "Reader B"
        return Book(url=url, title="Same Book", author="Author", narrator=reader, tracks=[Track(1, "1", url + "1.mp3")])
    monkeypatch.setattr(mod, "fetch_knigavuhe_book", fetch)
    assert service._knigavuhe_fallback_candidate(source) is None
