"""Offline regressions for V37 Qt, media and catalogue boundary handling."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.models import Book, Track
from audioknigi.qt.main_window import AudioKnigiQtWindow
from audioknigi.qt.media_keys import WindowsMediaKeyFilter
from audioknigi.qt.workers import DownloadWorker
from audioknigi.services.search_relevance import _matching_token


class _Button:
    def __init__(self):
        self.text_value = ""
        self.enabled = False

    def setText(self, value):
        self.text_value = value

    def setAccessibleName(self, _value):
        pass

    def setEnabled(self, enabled):
        self.enabled = bool(enabled)


def test_easy_action_reads_input_when_no_argument_is_given():
    url = "https://knigavuhe.org/book/sample/"
    download = _Button()
    stub = SimpleNamespace(
        easy_action_button=_Button(),
        easy_download_button=download,
        easy_input=SimpleNamespace(text=lambda: url),
        current_book=Book(url=url, title="Book", tracks=[
            Track(index=1, title="Chapter", file="https://cdn.example.test/chapter.mp3")
        ]),
        _l=lambda value: value,
        _book_url_is_stale=False,
    )
    AudioKnigiQtWindow._update_easy_action_text(stub)
    assert download.enabled
    AudioKnigiQtWindow._update_easy_action_text(stub, "not an URL")
    assert not download.enabled


def test_native_event_filter_returns_a_real_bool(monkeypatch):
    import audioknigi.qt.media_keys as media_keys
    monkeypatch.setattr(media_keys.os, "name", "posix")
    flt = WindowsMediaKeyFilter(SimpleNamespace())
    assert flt.nativeEventFilter(b"", 0) is False


def test_request_snapshot_skips_uncopyable_qt_cover():
    class Uncopyable:
        def __deepcopy__(self, _memo):
            raise AssertionError("native cover should never be deep-copied")

    request = SimpleNamespace(
        book=SimpleNamespace(cover_cache=Uncopyable(), title="Book"),
        selected_indices=[1],
    )
    snapshot = DownloadWorker._snapshot_request(request)
    assert snapshot is not request
    assert snapshot.book is not request.book
    assert snapshot.book.cover_cache is None
    assert request.book.cover_cache is not None


@pytest.mark.parametrize("wanted,candidate,expected", [
    ("sherlock", "sherlok", True),
    ("sherlok", "sherlock", True),
    ("catalogue", "catalogu", True),
    ("son", "slon", False),
    ("cat", "car", False),
])
def test_latin_catalogue_typo_tolerance_is_restricted(wanted, candidate, expected):
    assert _matching_token(wanted, candidate) is expected


def test_librivox_multiple_creators_become_author_string(monkeypatch):
    from audioknigi.providers.sources_ext import librivox
    payload = {
        "metadata": {
            "title": "Sample Work", "creator": ["Writer One", "Writer Two"],
            "collection": ["librivoxaudio"],
        },
        "files": [{"name": "chapter.mp3", "format": "128Kbps MP3", "length": "120"}],
    }
    monkeypatch.setattr(librivox, "_request", lambda *_a, **_kw: SimpleNamespace(json=lambda: payload))
    book = librivox.fetch_librivox("https://archive.org/details/sample")
    assert book.author == "Writer One, Writer Two"


def test_detailed_health_check_handles_unknown_dns_times(monkeypatch):
    from audioknigi.services import source_health_service as health

    class Socket:
        def close(self):
            pass

    class TLS:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def settimeout(self, _value):
            pass

        def sendall(self, _data):
            pass

        def recv(self, _count):
            return b"HTTP/1.1 200 OK\r\n"

    class SSLContext:
        def wrap_socket(self, _socket, *, server_hostname):
            return TLS()

    monkeypatch.setattr(health, "_connect_target_with_info", lambda *_a, **_kw: (
        Socket(), {"dns_ms": None, "tcp_ms": None, "address": "127.0.0.1"}
    ))
    monkeypatch.setattr(health.ssl, "create_default_context", lambda: SSLContext())
    monkeypatch.setattr(health, "note_http_response", lambda *_a: None)

    item = health._probe_source_detailed_once("example.test", timeout=1.0)
    assert item.reachable
    assert item.status_code == 200
    assert item.dns_ms is None
    assert item.tcp_ms is None


def test_player_and_queue_track_indices_have_safe_fallbacks():
    root = Path(__file__).resolve().parents[2] / "audioknigi" / "qt"
    player = (root / "player_mixin.py").read_text(encoding="utf-8")
    queue = (root / "mixins/queue.py").read_text(encoding="utf-8")
    assert 'index = safe_int(getattr(track, "index", None), row + 1)' in player
    assert "int(getattr(track, 'index'" not in player
    assert 'safe_int(getattr(track, "index", None), position)' in queue
    assert "[int(track.index)" not in queue


def test_shortcuts_are_retained_and_search_focus_uses_visible_table():
    root = Path(__file__).resolve().parents[2] / "audioknigi" / "qt"
    shortcuts = (root / "mixins/accessibility_ui.py").read_text(encoding="utf-8")
    search = (root / "mixins/search.py").read_text(encoding="utf-8")
    assert "self._widget_shortcuts.append(menu_shortcut)" in shortcuts
    assert "self._widget_shortcuts.extend([track_menu, history_menu, queue_menu])" in shortcuts
    assert "target = self.easy_search_table if self.current_ui_mode()" in search
    assert "self._search_source_actions[provider.key]" in search


def test_window_constructor_is_inside_cleanup_scope():
    source = (Path(__file__).resolve().parents[2] / "audioknigi/qt/application.py").read_text(encoding="utf-8")
    start = source.index("    window = None\n    focus_tracer = None\n    try:\n", source.index("def run_qt"))
    end = source.index("    finally:\n        sys.excepthook", start)
    assert "window = AudioKnigiQtWindow()" in source[start:end]
    assert "return int(app.exec())" in source[start:end]
