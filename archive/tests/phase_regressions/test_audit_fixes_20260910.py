from __future__ import annotations

from pathlib import Path
import threading


def test_download_result_excludes_tracks_skipped_during_processing(monkeypatch, tmp_path):
    from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
    from audioknigi.models import Book, Track
    from audioknigi.services.download_request import DownloadRequest

    book = Book(
        url="https://example.test/book",
        title="Book",
        tracks=[Track(index=i, title=str(i), file=f"https://cdn.test/{i}.mp3") for i in (1, 2, 3)],
    )
    request = DownloadRequest(book=book, selected_indices=[1, 2, 3], output_dir=tmp_path)
    engine = _DownloadEngine(request, {}, threading.Event(), DownloadCallbacks())

    def fake_process(*_args, **_kwargs):
        engine._last_process_skipped_indices = [2]
        return tmp_path / "Book"

    monkeypatch.setattr(engine, "_process_book", fake_process)
    result = engine.run()

    assert result.selected_indices == [1, 3]
    assert result.skipped_indices == [2]
    # The request still describes the original user selection; the result is
    # the authoritative record of what actually completed.
    assert request.selected_indices == [1, 2, 3]


def test_full_mp3_uses_track_fallback_and_removes_resume_manifest(monkeypatch, tmp_path):
    from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
    from audioknigi.models import Book, Track
    from audioknigi.services.download_request import DownloadRequest

    book = Book(
        url="https://example.test/book",
        title="Book",
        tracks=[Track(
            index=1,
            title="Chapter",
            file="https://cdn.test/main.mp3",
            fallback_file="https://mirror.test/main.mp3",
        )],
    )
    request = DownloadRequest(book=book, selected_indices=[1], output_dir=tmp_path, audio_preset="copy")
    engine = _DownloadEngine(
        request,
        {"embed_tags": False, "save_sidecars": False},
        threading.Event(),
        DownloadCallbacks(),
    )
    engine._write_resume_manifest(book, [1])
    resume = engine._resume_manifest_path(book, create=False)
    assert resume.exists()

    calls = []

    def fake_download(primary, fallback, target, referer):
        calls.append((primary, fallback, referer))
        Path(target).write_bytes(b"mp3")
        return Path(target)

    monkeypatch.setattr(engine, "_download_source_with_fallback", fake_download)
    monkeypatch.setattr(engine, "_cached_probe_audio_info", lambda _path: {"codec": "mp3"})
    monkeypatch.setattr(engine, "_effective_mp3_profile", lambda _path: (True, None, None))
    monkeypatch.setattr(engine, "_disk_free_for_path", lambda _path: 10**9)
    monkeypatch.setattr(engine, "_save_book_sidecars", lambda *_a, **_k: None)
    monkeypatch.setattr(engine, "_scan_audiobookshelf_after_book", lambda: None)
    monkeypatch.setattr(engine, "_add_history", lambda *_a, **_k: None)

    result = engine.run_full_mp3()

    assert calls == [("https://cdn.test/main.mp3", "https://mirror.test/main.mp3", book.url)]
    assert result.target_file and result.target_file.exists()
    assert not resume.exists()


def test_mapping_dataclass_serializes_set_and_frozenset():
    from audioknigi.models import MappingDataclass

    assert set(MappingDataclass._plain_value({1, 2})) == {1, 2}
    assert set(MappingDataclass._plain_value(frozenset({"a", "b"}))) == {"a", "b"}


def test_poleknig_js_decode_handles_escaped_slashes_and_unicode_and_filters_noise():
    from audioknigi.poleknig import _decode_js_string, _tracks_from_playerjs

    assert _decode_js_string(r'"https:\/\/cdn.test\/\u0410.mp3"') == "https://cdn.test/А.mp3"
    html = r'''<html>
      <a href="https://cdn.test/sample.mp3">sample</a>
      <a href="https://cdn.test/beep.wav">beep</a>
      <a href="https://cdn.test/chapter-01.mp3">chapter</a>
    </html>'''
    tracks = _tracks_from_playerjs(html, "https://poleknig.com/books/1")
    assert [track.file for track in tracks] == ["https://cdn.test/chapter-01.mp3"]


def test_i18n_keeps_filename_template_literal_and_translates_stage():
    from audioknigi.i18n import ui_text

    template = "Доступно: {Author} {Book_Title} {Year} {Genre} {Narrator} {Track_Number} {Track_Title}"
    assert ui_text("en", template, unrelated="value") == "Available: {Author} {Book_Title} {Year} {Genre} {Narrator} {Track_Number} {Track_Title}"
    assert ui_text("en", "Этап") == "Stage"
    assert ui_text("de", "Этап") == "Schritt"


def test_knigavuhe_groups_authorless_recording_with_single_known_author(monkeypatch):
    import audioknigi.knigavuhe as kv
    from audioknigi.models import SearchResult

    rows = [
        SearchResult(title="Мастер и Маргарита", author="Михаил Булгаков", narrator="", url="https://knigavuhe.org/book/a/", source="knigavuhe.org"),
        SearchResult(title="Мастер и Маргарита", author="", narrator="Иван Чтецов", url="https://knigavuhe.org/book/b/", source="knigavuhe.org"),
    ]

    class Response:
        text = "<html></html>"
        url = kv.SEARCH_URL

    monkeypatch.setattr(kv, "_fetch_search_page", lambda *_a, **_k: Response())
    monkeypatch.setattr(kv, "_search_last_page", lambda _html: 1)
    monkeypatch.setattr(kv, "parse_search_results", lambda *_a, **_k: rows)
    monkeypatch.setattr(kv, "_hydrate_search_result_titles", lambda items, *_a, **_k: items)

    result = kv.search("мастер")
    assert len(result) == 1
    assert result[0].author == "Михаил Булгаков"
    assert result[0].narrator == "Иван Чтецов"
    assert result[0].variant_count == 2


def test_book_analysis_decodes_playlist_bytes_as_utf8(monkeypatch):
    import audioknigi.services.book_analysis_service as module
    from audioknigi.services.book_analysis_service import BookAnalysisService

    playlist_bytes = "Часть 01".encode("utf-8")

    class Response:
        def __init__(self, *, text="", content=b"", status_code=200):
            self.text = text
            self.content = content
            self.status_code = status_code
            self.url = "https://example.test"
        def raise_for_status(self):
            return None

    class Session:
        def __init__(self):
            self.calls = 0
        def get(self, *_args, **_kwargs):
            self.calls += 1
            if self.calls == 1:
                return Response(text="<html>book</html>", content=b"<html>book</html>")
            return Response(text="Ð§Ð°ÑÑÑ 01", content=playlist_bytes)

    session = Session()
    monkeypatch.setattr(module, "get_http_session", lambda: session)
    service = BookAnalysisService(cancel_event=threading.Event())
    monkeypatch.setattr(service, "_looks_like_protection", lambda *_a: False)
    monkeypatch.setattr(service, "_extract_playlist_url", lambda _html: "https://cdn.test/book.pl.txt")
    monkeypatch.setattr(service, "_extract_page_title", lambda _html: "Book")
    captured = {}
    monkeypatch.setattr(service, "_parse_playlist_data", lambda **kwargs: captured.update(kwargs) or kwargs)

    service._analyze_audioknigi_requests("https://audioknigi.com.ua/audio-1-test")
    assert captured["playlist_text"] == "Часть 01"



def test_user_agents_track_current_stable_chrome_generation():
    from audioknigi.core import USER_AGENTS

    assert [ua.split("Chrome/", 1)[1].split(".", 1)[0] for ua in USER_AGENTS] == ["153", "152", "151"]


def test_unknown_source_name_is_language_neutral():
    from audioknigi.sources import source_name

    assert source_name("https://example.org/book") == "example.org"
    assert source_name("") == "—"

def test_direct_recursion_error_logging_uses_safe_non_traceback_path(monkeypatch):
    import audioknigi.logging_utils as logging_utils

    calls = []
    monkeypatch.setattr(logging_utils.app_logger, "log", lambda *args, **kwargs: calls.append((args, kwargs)))
    logging_utils.log_exception("audit-test", RecursionError("boom"))
    assert len(calls) == 1
    assert calls[0][1].get("exc_info") is None
    assert "RecursionError" in str(calls[0][0])


def test_remote_duration_cancel_happens_before_ffprobe_spawn(monkeypatch):
    import pytest
    import audioknigi.services.book_analysis_service as module
    from audioknigi.core import Cancelled
    from audioknigi.services.book_analysis_service import BookAnalysisService

    cancel = threading.Event()
    cancel.set()
    service = BookAnalysisService(cancel_event=cancel)
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("Popen must not run")))
    with pytest.raises(Cancelled):
        service._probe_remote_duration("https://cdn.test/chapter.mp3")


def test_qt_and_proxy_hardening_contracts_are_present():
    root = Path(__file__).resolve().parents[1]
    read = lambda rel: (root / rel).read_text(encoding="utf-8")

    media_keys = read("audioknigi/qt/media_keys.py")
    assert "QTimer.singleShot(0, callback)" in media_keys
    assert "QTimer.singleShot(0, self.window, callback)" not in media_keys

    player = read("audioknigi/qt/player_controller.py")
    assert "max(0, int(self.player.duration())) / 1000.0" in player
    player_mixin = read("audioknigi/qt/player_mixin.py")
    assert 'getattr(self, "_show_volume_tooltip", None)' in player_mixin
    accessibility = read("audioknigi/qt/accessibility.py")
    assert "QPlainTextEdit" in accessibility and "QTextEdit" in accessibility
    sounds = read("audioknigi/qt/event_sounds.py")
    assert "_output.setVolume(self.volume)" in sounds

    main = read("audioknigi/qt/main_window.py")
    changed = main[main.index("def _book_url_changed"):main.index("def _update_narration_combo")]
    assert "self.current_book = None" not in changed
    assert "self.track_model.set_book(None)" not in changed
    assert "_book_url_is_stale" in changed
    assert "self.easy_download_button.setEnabled(enabled)" in changed

    downloader = read("audioknigi/downloader.py")
    assert "float(end) > float(start)" in downloader
    engine = read("audioknigi/download_engine.py")
    assert "os.path.normcase(os.path.abspath" in engine

    dns = read("audioknigi/network_dns.py")
    assert 'request_line.split(None, 2)' in dns
