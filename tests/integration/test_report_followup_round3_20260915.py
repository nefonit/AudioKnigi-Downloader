from __future__ import annotations

import json
from pathlib import Path

import pytest

from audioknigi import core
from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.download.probe import ProbeMixin
from audioknigi.download_engine import DownloadService, _DownloadEngine
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, Track
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.search_service import search_all_sources

ROOT = Path(__file__).resolve().parents[2]


def test_duplicate_preflight_requires_ready_when_duration_probe_enabled(monkeypatch, tmp_path):
    book = Book(
        url="https://knigavuhe.org/book/demo/",
        title="Demo",
        tracks=[Track(index=1, title="One", file="https://cdn.invalid/1.mp3")],
    )
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    monkeypatch.setattr(
        _DownloadEngine,
        "_scan_book_files",
        lambda self, _book, create_folder=False: {"ready": 0, "existing": 1, "damaged": 0, "total": 1},
    )
    result = DownloadService().duplicate_preflight(request, probe_durations=True)
    assert result.exact_duplicate is False
    assert result.evidence == "files-incomplete"


def test_header_only_browser_profile_preserves_cookie_count(monkeypatch):
    writes = []
    monkeypatch.setattr(core, "_load_persisted_profile", lambda: {"headers": {}, "cookies_saved": 7})
    monkeypatch.setattr(core, "save_json", lambda path, payload: writes.append((path, payload)) or True)
    monkeypatch.setattr(core, "refresh_http_session_profile", lambda: None)
    core.persist_browser_session(None, {"User-Agent": "UA"})
    profile = [payload for path, payload in writes if path == core.SESSION_PROFILE_FILE][-1]
    assert profile["cookies_saved"] == 7


def test_protocol_relative_cover_is_normalized_without_referer(monkeypatch):
    import audioknigi.cover_fetch as module

    seen = {}

    class Response:
        headers = {"content-type": "image/jpeg"}
        def raise_for_status(self): pass
        def iter_content(self, chunk_size=0): return iter([b"image"])
        def close(self): pass

    class Session:
        def get(self, url, **kwargs):
            seen["url"] = url
            return Response()

    monkeypatch.setattr(module, "get_http_session", Session)
    assert fetch_cover_bytes("//poleknig.com/cover.jpg") == (b"image", "image/jpeg")
    assert seen["url"] == "https://poleknig.com/cover.jpg"


def test_support_bundle_redacts_two_slash_unc_path():
    from audioknigi.diagnostics.support_bundle import _privacy_path
    assert _privacy_path(r"\\server\private\books") == "<configured-path>"


def test_runtime_exact_tolerates_non_mapping_entry(monkeypatch):
    import audioknigi.i18n as module
    monkeypatch.setitem(module._PHASE29_RUNTIME_EXACT, "Malformed", "not-a-dict")
    assert module.localize_runtime_text("en", "Malformed") == "Malformed"


def test_probe_filename_does_not_duplicate_audio_extension(tmp_path):
    class Dummy(ProbeMixin):
        runtime_use_templates = False
        runtime_naming_mode = "number_title"
    book = Book(url="https://example.invalid", title="Book", tracks=[])
    track = Track(index=1, title="01_intro.mp3", file="x")
    assert Dummy()._track_filename(book, track) == "01 - 01_intro.mp3"


def test_unknown_remote_size_still_estimates_nonzero_disk_space(tmp_path):
    class Dummy(ProbeMixin):
        runtime_audio_preset = "copy"
        def _book_folder(self, book, create=False):
            return tmp_path / "book"
    track = Track(index=1, title="One", file="https://cdn.invalid/1.mp3", duration=60.0)
    book = Book(url="https://example.invalid", title="Book", tracks=[track], remote_size=0)
    assert Dummy()._estimate_required_space(book) > 0


def test_search_short_query_uses_localizable_error():
    outcome = search_all_sources("ab")
    assert outcome.errors == ["Введите минимум 3 символа для поиска."]


def test_playlist_url_and_track_numbering_are_hardened():
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    assert service._extract_playlist_url('<script>"//cdn.example/a.pl.txt"</script>') == "https://cdn.example/a.pl.txt"
    assert service._extract_playlist_url('<script>"/media/a.pl.txt"</script>') == "/media/a.pl.txt"
    playlist = json.dumps([
        {"file": "1.mp3", "title": "One"},
        {"title": "ad"},
        {"file": "3.mp3", "title": "Three"},
    ])
    book = service._parse_playlist_data(
        url="https://audioknigi.com.ua/book/1",
        html_text="<title>Demo</title>",
        page_title="Demo",
        playlist_url="https://cdn.example/a.pl.txt",
        playlist_text=playlist,
    )
    assert [track.index for track in book.tracks] == [1, 2]


def test_dynamic_search_status_and_completed_duration_are_localized():
    assert localize_runtime_text("en", "Найдено 12 книг, источников: 3.") == "Found 12 books, sources: 3."
    assert localize_runtime_text("de", "Найдено 2 книг.") == "2 Bücher gefunden."
    assert localize_runtime_text("uk", "Часть источников недоступна.") == "Частина джерел недоступна."
    assert localize_runtime_text("en", "Определена длительность частей: 4/4") == "Part durations determined: 4/4"


def test_accessibility_followups_are_present_in_ui_sources():
    pages = (ROOT / "audioknigi/qt/main_window_pages.py").read_text(encoding="utf-8")
    assert 'localized_accessible_name = str(label or "").rstrip(":：").strip()' in pages
    player = (ROOT / "audioknigi/qt/player_mixin.py").read_text(encoding="utf-8")
    assert "current = self.track_table.currentIndex()" in player
    dialogs = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    assert dialogs.count('identifier="duplicate_dialog"') >= 2
    assert 'identifier="duplicate_open_folder"' in dialogs


def test_ffmpeg_capture_timeout_cleanup_is_guarded():
    source = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    block = source[source.index("def _run_ffmpeg_capture"):source.index("def _probe_audio_info")]
    marker = 'if remaining <= 0:'
    timeout_block = block[block.index(marker):block.index('try:', block.index(marker) + len(marker)) + 120]
    assert "proc.communicate(timeout=5)" in timeout_block
    assert "except Exception" in timeout_block
