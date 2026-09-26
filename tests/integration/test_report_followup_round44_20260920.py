from __future__ import annotations

import base64
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import audioknigi.config.settings as settings_module
import audioknigi.core as core
import audioknigi.diagnostics.support_bundle as support_bundle
import audioknigi.services.player_position_store as position_module
from audioknigi.models import Book
from audioknigi.providers.audioknigi_search import (
    _matches_query,
    _response_html_text,
    parse_audioknigi_results,
)
from audioknigi.services.player_position_store import PlayerPositionStore
from audioknigi.services.queue_service import _book_to_dict

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_partial_direct_app_settings_constructor_supplies_missing_defaults_without_changing_explicit_mapping() -> None:
    settings = settings_module.AppSettings({"language": "en", "scale": "125"})
    assert settings["language"] == "en"
    # Direct construction is now the same normalization boundary as persisted
    # settings, so explicit numeric strings are canonicalized too.
    assert settings["scale"] == 125
    assert settings["theme"] == settings_module.DEFAULT_SETTINGS["theme"]
    assert settings["minimize_to_tray"] is True
    assert "theme" in settings.keys()
    assert len(settings) >= len(settings_module.DEFAULT_SETTINGS)


def test_support_log_sanitizer_redacts_paths_and_common_credentials(monkeypatch) -> None:
    monkeypatch.setattr(support_bundle.os, "name", "nt", raising=False)
    monkeypatch.setattr(support_bundle.Path, "home", classmethod(lambda cls: Path(r"C:\\Users\\Alice")))
    raw = (
        b"open C:\\Users\\Alice\\Documents\\book.mp3\r\n"
        b"Authorization: Bearer TOP.SECRET-123\r\n"
        b"https://example.test/file?token=URLSECRET&part=1\r\n"
        b"api_key=KEYSECRET\r\n"
    )
    cleaned = support_bundle._sanitize_log_bytes(raw).decode("utf-8")
    assert "Alice" not in cleaned
    assert "TOP.SECRET-123" not in cleaned
    assert "URLSECRET" not in cleaned
    assert "KEYSECRET" not in cleaned
    assert "<redacted>" in cleaned


def test_atomic_temp_names_include_per_call_monotonic_token() -> None:
    common = src("audioknigi/download/common.py")
    assert common.count("time.monotonic_ns()") >= 2


def test_ffmpeg_helpers_close_subprocess_pipes_in_finally() -> None:
    media = src("audioknigi/download/media.py")
    assert media.count("_close_subprocess_pipes(proc)") >= 2
    for name in ("def _run_ffmpeg(", "def _run_ffmpeg_capture("):
        start = media.index(name)
        end = media.find("\n    def ", start + len(name))
        block = media[start:] if end < 0 else media[start:end]
        assert "_close_subprocess_pipes(proc)" in block


def test_audioknigi_initial_query_matches_full_person_name_but_not_unrelated_person() -> None:
    assert _matches_query("Война и мир", "Л. Толстой Война", author="Лев Толстой")
    assert _matches_query("Война и мир", "Лев Толстой Война", author="Л. Толстой")
    assert not _matches_query("Война и мир", "А. Пушкин Война", author="Лев Толстой")
    assert not _matches_query("Война и мир", "Л.", author="Лев Толстой")


def test_audioknigi_parser_accepts_relative_audio_href_without_leading_slash() -> None:
    html = '<a href="audio-12345-test-book">Тестовая книга</a>'
    results = parse_audioknigi_results(html, "https://audioknigi.com.ua/search?q=test", "Тестовая")
    assert len(results) == 1
    assert results[0].url == "https://audioknigi.com.ua/audio-12345-test-book"


def test_audioknigi_response_decoder_uses_declared_legacy_encoding_after_utf8_fails() -> None:
    text = "Александр Пушкин"
    response = SimpleNamespace(
        content=text.encode("cp1251"),
        encoding="windows-1251",
        apparent_encoding="windows-1251",
        text="",
    )
    assert _response_html_text(response) == text


def test_large_queue_cover_is_not_embedded_but_small_thumbnail_is() -> None:
    large = Book(
        url="https://example.test/book",
        title="Book",
        cover_url="https://example.test/cover.jpg",
        cover_cache=(b"x" * (300 * 1024), "image/jpeg"),
    )
    large_data = _book_to_dict(large)
    assert large_data["cover_cache_b64"] == ""
    assert large_data["cover_cache_mime"] == ""
    assert large_data["cover_url"] == large.cover_url

    small_payload = b"small-cover"
    small = Book(url="https://example.test/small", title="Small", cover_cache=(small_payload, "image/jpeg"))
    small_data = _book_to_dict(small)
    assert base64.b64decode(small_data["cover_cache_b64"]) == small_payload
    assert small_data["cover_cache_mime"] == "image/jpeg"


def test_player_position_store_preserves_write_order_without_blocking_state_reads(monkeypatch, tmp_path) -> None:
    writes: list[float] = []
    first_started = threading.Event()
    release_first = threading.Event()

    def fake_load_json(_path, default):
        return dict(default)

    def fake_save_json(_path, payload):
        position = float(next(iter(payload.values()))["position"])
        if position == 10.0:
            first_started.set()
            assert release_first.wait(timeout=2.0)
        writes.append(position)
        return True

    monkeypatch.setattr(position_module, "load_json", fake_load_json)
    monkeypatch.setattr(position_module, "save_json", fake_save_json)
    store = PlayerPositionStore(tmp_path / "positions.json")
    media = tmp_path / "book.mp3"

    first = threading.Thread(target=lambda: store.update(media, 10.0, 100.0))
    second = threading.Thread(target=lambda: store.update(media, 20.0, 100.0))
    first.start()
    assert first_started.wait(timeout=2.0)
    second.start()

    deadline = time.monotonic() + 1.0
    while store.saved_seconds(media, duration=100.0) != 20.0 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert store.saved_seconds(media, duration=100.0) == 20.0

    release_first.set()
    first.join(timeout=2.0)
    second.join(timeout=2.0)
    assert not first.is_alive() and not second.is_alive()
    assert writes[-1] == 20.0


def test_system_sound_worker_observes_shutdown_even_without_sentinel() -> None:
    source = src("audioknigi/qt/event_sounds.py")
    worker_start = source.index("def _system_sound_worker")
    worker_end = source.index("def play_system", worker_start)
    worker = source[worker_start:worker_end]
    assert "if self._system_shutdown.is_set():" in worker
    assert "if flag is None:" in worker
    assert worker.count("if self._system_shutdown.is_set():") >= 2


def test_accessibility_trace_disconnects_focus_signal_before_stream_close() -> None:
    source = src("audioknigi/qt/accessibility_trace.py")
    start = source.index("def close(self)")
    end = source.index("def extract_focus_trace_argument", start)
    block = source[start:end]
    assert "self.app.focusChanged.disconnect(self._focus_changed)" in block
    assert block.index("focusChanged.disconnect") < block.index("stream.close()")


def test_player_persists_recent_seek_target_when_backend_position_is_stale() -> None:
    source = src("audioknigi/qt/player_controller.py")
    assert "def _position_for_persistence_ms" in source
    assert "self._last_seek_target_ms = target" in source
    stop_start = source.index("def stop(self)")
    stop_end = source.index("def seek(self", stop_start)
    stop_block = source[stop_start:stop_end]
    assert "position = self._position_for_persistence_ms()" in stop_block
    assert "explicit_seconds=position / 1000.0" in stop_block


def test_persist_browser_session_does_not_refresh_requests_pool_for_identical_material(monkeypatch) -> None:
    cookies = [{
        "name": "cf_clearance", "value": "abc", "domain": ".example.test", "path": "/",
        "expires": -1, "secure": True,
    }]
    profile = {"headers": {"User-Agent": "UA"}, "cookies_saved": 1, "saved_at": 1}
    saves = []
    refreshes = []

    monkeypatch.setattr(core, "_load_persisted_profile", lambda: dict(profile))
    monkeypatch.setattr(core, "load_json", lambda path, default=None: list(cookies) if path == core.COOKIE_FILE else default)
    monkeypatch.setattr(core, "save_json", lambda path, payload: saves.append((path, payload)) or True)
    monkeypatch.setattr(core, "refresh_http_session_profile", lambda: refreshes.append(True))

    core.persist_browser_session(cookies, {"User-Agent": "UA"})
    assert saves == []
    assert refreshes == []

    core.persist_browser_session(cookies, {"User-Agent": "UA-2"})
    assert any(path == core.SESSION_PROFILE_FILE for path, _payload in saves)
    assert refreshes == [True]
