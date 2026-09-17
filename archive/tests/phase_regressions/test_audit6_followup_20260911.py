from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest
import requests

from audioknigi.core import Cancelled
from audioknigi.downloader import DownloaderMixin
from audioknigi.download_engine import _DownloadEngine, DownloadCallbacks
from audioknigi.models import Book, Track
from audioknigi.services.download_request import DownloadRequest

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_requests_success_recovery_error_does_not_launch_playwright():
    book = Book(url="https://audioknigi.com.ua/audio-test", title="Test", tracks=[Track(index=1, title="1", file="https://cdn/a.mp3")])

    class Host(DownloaderMixin):
        cancel_event = threading.Event()
        runtime_playwright_fallback_enabled = True
        playwright_called = False

        def _analyze_book_requests(self, _url):
            return book

        def _recover_short_audioknigi_source(self, _book):
            raise RuntimeError("short source")

        def _analyze_book_playwright(self, _url, _error=None):
            self.playwright_called = True
            return book

    host = Host()
    with pytest.raises(RuntimeError, match="short source"):
        host._analyze_book(book.url)
    assert not host.playwright_called


def test_knigavuhe_merged_playlist_is_not_positional_fallback_when_sizes_differ():
    from audioknigi.knigavuhe import parse_book_html

    payload = {
        "book": {"name": "Book"},
        "playlist": [
            {"url": "https://cdn/p1.mp3", "title": "1"},
            {"url": "https://cdn/p2.mp3", "title": "2"},
            {"url": "https://cdn/p3.mp3", "title": "3"},
        ],
        "merged_playlist": [{"url": "https://cdn/merged.mp3"}],
    }
    html = f"<script>BookController.enter({json.dumps(payload)});</script>"
    book = parse_book_html(html, "https://knigavuhe.org/book/test/")
    assert [track.fallback_file for track in book.tracks] == ["", "", ""]


def test_provider_searches_raise_cancelled_for_pre_cancelled_event():
    from audioknigi.knigavuhe import search as search_knigavuhe
    from audioknigi.poleknig import search as search_poleknig

    event = threading.Event(); event.set()
    with pytest.raises(Cancelled):
        search_knigavuhe("test", cancel_event=event)
    with pytest.raises(Cancelled):
        search_poleknig("test", cancel_event=event)


def test_sidecar_duplicate_identity_ignores_description_and_cover_url(tmp_path):
    book = Book(
        url="https://audioknigi.com.ua/audio-test",
        title="Title", author="Author", narrator="Reader",
        description="new description", cover_url="https://cdn/new.jpg?token=2",
        tracks=[Track(index=1, title="One", file="https://cdn/1.mp3", duration=10.0)],
    )
    payload = {
        "source_url": book.url,
        "title": book.title, "author": book.author, "narrator": book.narrator,
        "description": "old description", "cover_url": "https://cdn/old.jpg?token=1",
        "tracks": [{"index": 1, "title": "One", "start": None, "end": None, "duration": 10.0}],
    }
    (tmp_path / "metadata.json").write_text(json.dumps(payload), encoding="utf-8")
    req = DownloadRequest(book=book, selected_indices=[1], output_dir=tmp_path)
    engine = _DownloadEngine(req, {}, threading.Event(), DownloadCallbacks())
    assert engine._sidecar_metadata_matches_book(book, tmp_path) is True


def test_gui_duplicate_preflight_has_non_probing_mode(tmp_path):
    book = Book(url="https://audioknigi.com.ua/audio-test", title="Book", tracks=[Track(index=1, title="1", file="https://cdn/1.mp3")])
    req = DownloadRequest(book=book, selected_indices=[1], output_dir=tmp_path)
    engine = _DownloadEngine(req, {}, threading.Event(), DownloadCallbacks())
    engine._probe_duration = lambda _path: (_ for _ in ()).throw(AssertionError("ffprobe should not run"))
    folder = engine._book_folder(book)
    folder.mkdir(parents=True, exist_ok=True)
    engine._track_path(book, book.tracks[0]).write_bytes(b"not-empty")
    # No metadata evidence means it is not an exact duplicate, but the presence
    # scan itself must remain lightweight and avoid duration probing.
    result = engine.duplicate_preflight(probe_durations=False)
    assert result.exact_duplicate is False


def test_audiobookshelf_wraps_request_and_http_errors(monkeypatch):
    import audioknigi.integrations as mod

    class Session:
        def get(self, *a, **k):
            raise requests.exceptions.ConnectTimeout("offline")
    monkeypatch.setattr(mod, "get_http_session", lambda: Session())
    with pytest.raises(RuntimeError, match="Не удалось подключиться"):
        mod.audiobookshelf_get_libraries("http://localhost:13378", "key")

    class Response:
        status_code = 401
        def raise_for_status(self):
            err = requests.exceptions.HTTPError("401")
            err.response = self
            raise err
    class Session401:
        def get(self, *a, **k): return Response()
    monkeypatch.setattr(mod, "get_http_session", lambda: Session401())
    with pytest.raises(RuntimeError, match="API key"):
        mod.audiobookshelf_get_libraries("http://localhost:13378", "bad")


def test_empty_track_title_uses_book_title_in_template():
    from audioknigi.templates import render_track_filename
    book = Book(url="https://example.test/book", title="My Book", tracks=[])
    track = Track(index=1, title="", file="")
    assert render_track_filename("{Track_Number} - {Track_Title}.mp3", book, track) == "01 - My Book.mp3"


def test_quality_preset_is_consistent_for_both_settings_combos():
    source = text("audioknigi/qt/settings_sync.py")
    assert 'explicit_quality = str(data.get("quality_preset", "")' in source
    assert 'self._set_combo_data(self.quality_combo, quality)' in source
    assert 'self._set_combo_data(self.easy_quality_combo, quality)' in source


def test_player_context_populates_autonext_files_and_single_click_activation():
    source = text("audioknigi/qt/player_mixin.py")
    assert "itemClicked.connect(self._player_chapter_activated)" in source
    assert "local_book_files.append(local)" in source
    assert "self._player_book_files = local_book_files" in source
    assert "self._select_player_chapter_path(next_path)" in source


def test_narration_variant_cache_is_keyed_to_book_identity():
    source = text("audioknigi/qt/main_window.py")
    block = source[source.index("narration_key ="):source.index("if self._resume_selected_indices", source.index("narration_key ="))]
    assert "self._known_narration_variants = (narration_key" in block
    assert "self._known_narration_variants[0] == narration_key" in block
    assert "self._known_narration_variants = None" in block


def test_book_analysis_recovery_uses_same_long_book_tolerance_and_is_after_http_fallback():
    source = text("audioknigi/services/book_analysis_service.py")
    recover = source[source.index("def _recover_short_audioknigi_source"):source.index("def analyze", source.index("def _recover_short_audioknigi_source"))]
    assert "tolerance = max(15.0, expected_end * 0.001)" in recover
    analyze = source[source.index("def analyze"):source.index("@staticmethod", source.index("def analyze"))]
    request_call = analyze.index("book = self._analyze_audioknigi_requests(normalized)")
    except_pos = analyze.index("except Exception as exc:")
    recover_pos = analyze.index("book = self._recover_short_audioknigi_source(book)")
    assert request_call < except_pos < recover_pos


def test_http_proxy_plain_mode_exits_when_upstream_closes():
    source = text("audioknigi/network_dns.py")
    assert "return_when_right_closes" in source
    assert "if return_when_right_closes and source is right" in source
    assert "_relay_bidirectional(client, upstream, return_when_right_closes=True)" in source


def test_position_store_is_bounded():
    source = text("audioknigi/services/player_position_store.py")
    assert "_POSITION_CACHE_MAX = 2000" in source
    assert "def _prune_locked" in source


def test_shortcuts_and_file_dialogs_are_localized():
    i18n = text("audioknigi/i18n.py")
    assert "Ctrl+1…6 — Book / Search / Queue / History / Settings / Player" in i18n
    player = text("audioknigi/qt/player_mixin.py")
    assert 'self._l("Выберите папку с аудиокнигой")' in player
    assert 'self._l("Открыть аудиофайл")' in player
    main = text("audioknigi/qt/main_window.py")
    assert 'self._l("Продолжить загрузку")' in main
    assert 'self._l("Добавить URL в очередь")' in main


def test_threadsafe_active_io_lazy_init_and_playwright_header_fallback_are_present():
    source = text("audioknigi/downloader.py")
    assert "_ACTIVE_IO_INIT_LOCK = threading.Lock()" in source
    assert source.count("with _ACTIVE_IO_INIT_LOCK:") >= 2
    assert 'headers = getattr(request, "headers", None)' in source
    assert 'all_headers = getattr(request, "all_headers", None)' in source
