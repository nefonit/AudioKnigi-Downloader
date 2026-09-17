from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi import downloader as downloader_module
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.downloader import DownloaderMixin
from audioknigi.logging_utils import log_exception
from audioknigi.models import Book, Track
from audioknigi.poleknig import _book_page_metadata, _search_last_page
from audioknigi.services.download_request import DownloadRequest


ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class _Limiter:
    def consume(self, _size, _event):
        return None


class _Response:
    def __init__(self, status_code: int, headers=None, chunks=()):
        self.status_code = status_code
        self.headers = dict(headers or {})
        self._chunks = list(chunks)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"unexpected raise_for_status for {self.status_code}")

    def iter_content(self, chunk_size=0):
        yield from self._chunks


class _Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class _SingleDownloadDummy(DownloaderMixin):
    def __init__(self):
        self.cancel_event = threading.Event()

    def _check_cancel(self):
        return None

    def _get_bandwidth_limiter(self):
        return _Limiter()

    def _register_active_network_response(self, _response):
        return None

    def _unregister_active_network_response(self, _response):
        return None

    def set_progress(self, _value):
        return None

    def set_status(self, _value):
        return None

    def record_transfer_metrics(self, *_args):
        return None


def test_http_416_bad_partial_is_deleted_and_restarted(monkeypatch, tmp_path):
    target = tmp_path / "chapter.mp3"
    part = tmp_path / "chapter.mp3.part"
    part.write_bytes(b"oversized")
    session = _Session([
        _Response(416, {"content-range": "bytes */3"}),
        _Response(200, {"content-length": "3"}, [b"abc"]),
    ])
    monkeypatch.setattr(downloader_module, "get_http_session", lambda: session)

    result = _SingleDownloadDummy()._download_single("https://example.invalid/a.mp3", target, "")

    assert result == target
    assert target.read_bytes() == b"abc"
    assert len(session.calls) == 2
    assert "Range" in session.calls[0][1]["headers"]
    assert "Range" not in session.calls[1][1]["headers"]


def test_delete_existing_outputs_only_removes_selected_tracks(tmp_path):
    tracks = [Track(index=i, title=str(i), file=f"https://example.invalid/{i}.mp3") for i in range(1, 4)]
    book = Book(url="https://poleknig.com/books/1", title="Book", tracks=tracks)
    request = DownloadRequest(book=book, selected_indices=[2, 3], output_dir=tmp_path)
    engine = _DownloadEngine(request, {}, threading.Event(), DownloadCallbacks())
    paths = {i: tmp_path / f"{i}.mp3" for i in range(1, 4)}
    for path in paths.values():
        path.write_bytes(b"x")
    engine._track_path = lambda _book, track, create_folder=False: paths[track.index]

    assert engine.delete_existing_outputs() == 2
    assert paths[1].exists()
    assert not paths[2].exists()
    assert not paths[3].exists()


def test_full_mp3_reports_empty_source_precisely(tmp_path):
    book = Book(
        url="https://poleknig.com/books/1",
        title="Book",
        tracks=[Track(index=1, title="1", file="")],
    )
    request = DownloadRequest(book=book, selected_indices=[1], output_dir=tmp_path)
    engine = _DownloadEngine(request, {}, threading.Event(), DownloadCallbacks())
    with pytest.raises(ValueError, match="нет доступных аудиофайлов"):
        engine.run_full_mp3()
    source = text("audioknigi/download_engine.py")
    body = source[source.index("def run_full_mp3"):source.index("def run(self)")]
    assert 'self.set_stage(3, "Обработка полного MP3")' in body


def test_repair_source_cache_is_keyed_by_source_url():
    source = text("audioknigi/downloader.py")
    body = source[source.index("def _process_book_once"):source.index("def _is_transient_error")]
    assert "repaired_sources: dict[str, Path] = {}" in body
    assert "repaired_sources.get(source_key_value)" in body
    assert "repaired_sources[source_key_value] = src" in body


def test_log_exception_detects_default_recursion_error(monkeypatch):
    captured = []
    from audioknigi import logging_utils

    monkeypatch.setattr(logging_utils.app_logger, "log", lambda *args, **kwargs: captured.append((args, kwargs)))
    try:
        raise RecursionError("deep")
    except RecursionError:
        log_exception("recursive-default")
    assert captured
    assert "RecursionError" in captured[0][0][1]
    assert "deep" in str(captured[0][0])


def test_knigavuhe_authorless_same_titles_are_not_collapsed_by_empty_author_key():
    source = text("audioknigi/knigavuhe.py")
    body = source[source.index("authors_by_title:"):source.index("unique: list[SearchResult]", source.index("authors_by_title:"))]
    assert "elif len(known_authors) == 1:" in body
    assert "elif len(known_authors) <= 1:" not in body


def test_poleknig_preserves_coauthors_and_trims_pagination_query():
    html = '''
    <html><h1>Двенадцать стульев</h1>
      <a href="/authors/10">Ильф</a>
      <a href="/authors/11">Петров</a>
    </html>
    '''
    meta = _book_page_metadata(html, "https://poleknig.com/books/1")
    assert meta["author"] == "Ильф, Петров"
    pagination = '<a href="/index.php?q=%D0%9F%D1%83%D1%88%D0%BA%D0%B8%D0%BD&p=4">4</a>'
    assert _search_last_page(pagination, "  Пушкин  ") == 4


def test_network_relay_handles_peer_reset_on_recv():
    source = text("audioknigi/network_dns.py")
    body = source[source.index("def _relay_bidirectional"):source.index("def _read_http_head")]
    assert "except (ConnectionResetError, BrokenPipeError, OSError):" in body


def test_player_and_onboarding_defensive_guards_are_present():
    controller = text("audioknigi/qt/player_controller.py")
    assert "or self._at_end" in controller[controller.index("def save_position"):controller.index("def suspend_position_persistence")]
    player = text("audioknigi/qt/player_mixin.py")
    selected = player[player.index("def _selected_track"):player.index("def _update_selected_track_player_button")]
    assert "if selection_model is None:" in selected
    onboarding = text("audioknigi/qt/onboarding.py")
    assert 'self.cancel_button.setAccessibleDescription("")' in onboarding
    assert 'self.start_button.setAccessibleDescription("")' in onboarding


def test_main_window_is_split_below_four_thousand_lines_and_transient_menus_are_disposable():
    main = text("audioknigi/qt/main_window.py")
    assert len(main.splitlines()) < 4000
    assert "MainWindowPagesMixin" in main
    assert "SettingsSyncMixin" in main
    assert main.count("transient_menu(") >= 4
    helper = text("audioknigi/qt/menu_utils.py")
    assert "WA_DeleteOnClose" in helper
