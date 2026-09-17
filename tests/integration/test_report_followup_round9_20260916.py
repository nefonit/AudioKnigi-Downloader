from __future__ import annotations

import json
from pathlib import Path

import pytest

from audioknigi.core import load_browser_context_profile
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.download_engine import _DownloadEngine
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, Track
from audioknigi.network_dns import _parse_proxy_authority
from audioknigi.providers.audioknigi_search import _split_audioknigi_title
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.queue_service import task_from_dict

ROOT = Path(__file__).resolve().parents[2]


def test_proxy_authority_preserves_unbracketed_numeric_ipv6():
    assert _parse_proxy_authority("::1", 443) == ("::1", 443)
    assert _parse_proxy_authority("[2001:db8::1]:8443", 443) == ("2001:db8::1", 8443)
    assert _parse_proxy_authority("example.org:8080", 80) == ("example.org", 8080)
    with pytest.raises(ValueError):
        _parse_proxy_authority("[2001:db8::1", 443)


def test_full_mp3_default_template_without_literal_extension_uses_book_title(tmp_path):
    engine = _DownloadEngine.__new__(_DownloadEngine)
    engine.runtime_use_templates = True
    engine.runtime_track_template = "{Track_Number}"
    book = Book(url="https://example.test/book", title="My Book", tracks=[Track(index=1, title="One", file="x")])
    assert engine._full_mp3_target(book, tmp_path).name == "My Book.mp3"


def test_browser_profile_adapter_filters_expired_cookies(monkeypatch):
    import audioknigi.core as core

    now = 2_000_000_000
    monkeypatch.setattr(core.time, "time", lambda: now)

    def fake_load(path, default):
        if path == core.SESSION_PROFILE_FILE:
            return {"headers": {"User-Agent": "UA", "Accept-Language": "de-DE", "X-Secret": "no"}}
        if path == core.COOKIE_FILE:
            return [
                {"name": "good", "value": "1", "domain": ".example.test", "path": "/", "expires": now + 50, "secure": True},
                {"name": "expired", "value": "2", "domain": ".example.test", "expires": now - 1},
                {"name": "no-domain", "value": "3"},
            ]
        return default

    monkeypatch.setattr(core, "load_json", fake_load)
    headers, cookies = load_browser_context_profile()
    assert headers == {"User-Agent": "UA", "Accept-Language": "de-DE"}
    assert [item["name"] for item in cookies] == ["good"]
    assert cookies[0]["expires"] == pytest.approx(now + 50)


def test_audioknigi_dash_parser_rejects_series_and_numeric_prefixes():
    assert _split_audioknigi_title("Иван Автор — Тестовая книга") == ("Тестовая книга", "Иван Автор")
    assert _split_audioknigi_title("S.T.A.L.K.E.R. — Тени Чернобыля") == ("S.T.A.L.K.E.R. — Тени Чернобыля", "")
    assert _split_audioknigi_title("1984 — Часть 1") == ("1984 — Часть 1", "")
    assert _split_audioknigi_title("Александр I — эпоха") == ("Александр I — эпоха", "")


def test_playlist_parser_accepts_whitespace_before_bom_and_prefers_precise_boundaries():
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    playlist = "  \n\ufeff" + json.dumps([
        {"file": "one.mp3", "title": "One", "start": 0, "end": 60.45, "duration": 60},
        {"file": "two.mp3", "title": "Two", "start": 60.45, "end": 120.9, "duration": 60},
    ])
    book = service._parse_playlist_data(
        url="https://audioknigi.com.ua/audio-1",
        html_text="<title>Demo</title>",
        page_title="Demo",
        playlist_url="https://audioknigi.com.ua/list.pl.txt",
        playlist_text=playlist,
    )
    assert len(book.tracks) == 2
    assert book.tracks[0].duration == pytest.approx(60.45)
    assert book.tracks[1].duration == pytest.approx(60.45)


def test_split_track_infers_next_start_when_current_duration_missing(tmp_path):
    commands = []

    class Dummy(MediaProcessingMixin):
        runtime_normalization_mode = "off"
        runtime_embed_tags = False

        def _track_path(self, _book, track):
            return tmp_path / f"{track.index}.mp3"

        def _effective_mp3_profile(self, _source):
            return True, None, None

        def _run_ffmpeg(self, cmd, timeout=0):
            commands.append(list(cmd))

        def _write_id3(self, *args, **kwargs):
            return None

        def _cached_probe_audio_info(self, _source):
            return {}

    first = Track(index=1, title="One", file="source", start=10, end=None, duration=None)
    second = Track(index=2, title="Two", file="source", start=25, end=None, duration=None)
    book = Book(url="https://example.test", title="Demo", tracks=[first, second])
    source = tmp_path / "source.mp3"
    source.write_bytes(b"x")
    Dummy()._split_track(book, first, source)
    assert commands
    cmd = commands[0]
    assert "-ss" in cmd and cmd[cmd.index("-ss") + 1] == "10"
    assert "-t" in cmd and float(cmd[cmd.index("-t") + 1]) == pytest.approx(15.0)


def test_legacy_queue_without_template_flag_preserves_global_inheritance():
    task = task_from_dict({"url": "https://knigavuhe.org/book/1", "title": "Legacy"})
    assert task.request.use_templates is None
    assert task.request.folder_template is None
    assert task.request.track_template is None


def test_dynamic_generic_error_prefix_is_localized():
    assert localize_runtime_text("en", "Ошибка: Таймаут соединения") == "Error: Таймаут соединения"
    assert localize_runtime_text("de", "Ошибка: Таймаут соединения") == "Fehler: Таймаут соединения"


def test_round9_source_hardening_contracts():
    network = (ROOT / "audioknigi" / "download" / "network.py").read_text(encoding="utf-8")
    assert 'part.name + ".segments.json"' in network
    assert '"url": str(url or "")' in network
    assert '"total_size": int(total_size)' in network

    player = (ROOT / "audioknigi" / "qt" / "player_controller.py").read_text(encoding="utf-8")
    assert "self._resume_after_stop_ms > 0" in player
    assert "PlaybackState.StoppedState" in player

    pages = (ROOT / "audioknigi" / "qt" / "main_window.py").read_text(encoding="utf-8")
    assert "self._easy_input_is_stale = easy_stale" in pages

    access = (ROOT / "audioknigi" / "qt" / "mixins" / "accessibility_ui.py").read_text(encoding="utf-8")
    assert "window_ref = weakref.ref(self)" in access

    media = (ROOT / "audioknigi" / "download" / "media.py").read_text(encoding="utf-8")
    assert 'clean_graph = str(filter_complex).strip().rstrip(";").rstrip()' in media

    accessibility_audit = (ROOT / "audioknigi" / "qt" / "accessibility_audit.py").read_text(encoding="utf-8")
    required_block = accessibility_audit.split("REQUIRED_ACCESSIBLE_IDS = (", 1)[1].split(")\n\n", 1)[0]
    focusable_block = accessibility_audit.split("FOCUSABLE_ACCESSIBLE_IDS = (", 1)[1].split(")\n", 1)[0]
    for identifier in ("cancel_search", "easy_cancel_search", "toggle_session_log"):
        assert f'"{identifier}"' in required_block
        assert f'"{identifier}"' in focusable_block
    for identifier in ("download_book", "download_full_mp3", "add_book_to_queue"):
        assert f'"{identifier}"' in required_block
        assert f'"{identifier}"' not in focusable_block
