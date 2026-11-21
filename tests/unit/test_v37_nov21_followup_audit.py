"""V37 November audit: test verified migration, source, player and locale regressions."""
from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.config.settings import migrate_settings
from audioknigi.engine.core import extract_extended_metadata_from_html, extract_metadata_from_html
from audioknigi.i18n import localize_runtime_text
from audioknigi.parsers import akniga, poleknig
from audioknigi.providers import audioknigi_search
from audioknigi.providers.sources_ext import librivox, yakniga
from audioknigi.qt.player_controller import QtPlayerController
from audioknigi.qt.player_mixin import PlayerUiMixin
from audioknigi.qt.help_formatter import _format_help_body_html


@pytest.mark.parametrize("value", [None, "", "   "])
def test_migrate_legacy_true_with_blank_mode(value):
    settings, _ = migrate_settings({"normalization_mode": value, "normalize_audio": True})
    assert settings["normalization_mode"] == "single"


@pytest.mark.parametrize("mode,expected", [("off", "off"), ("two_pass", "two_pass")])
def test_explicit_normalization_mode_overrides_legacy_boolean(mode, expected):
    settings, _ = migrate_settings({"normalization_mode": mode, "normalize_audio": True})
    assert settings["normalization_mode"] == expected


def test_jsonld_html_entities_are_unescaped_once_only():
    html = (
        '<script type="application/ld+json">'
        '{"@type":"Book","name":"A &amp;lt; B",'
        '"author":{"@type":"Person","name":"Ms &amp;lt; X"},'
        '"description":"An &amp;lt; sign appears in this book."}'
        '</script>'
    )
    title, author, _cover = extract_metadata_from_html(html)
    description, *_ = extract_extended_metadata_from_html(html)
    assert title == "A &lt; B"
    assert author == "Ms &lt; X"
    assert "An &lt; sign" in description


def test_poleknig_description_strips_script_and_style_text():
    html = (
        '<div class="book-description"><p>Герой встречает друзей и отправляется '
        'в путешествие по дальним городам, открывая загадки прошлого.</p>'
        '<script>SECRET_PAYLOAD_TOKEN_MARKER</script>'
        '<style>.SECRET_CSS_TOKEN_MARKER{display:none}</style></div>'
    )
    description = poleknig._poleknig_description_from_html(html)
    assert "Герой встречает" in description
    assert "SECRET_PAYLOAD_TOKEN_MARKER" not in description
    assert "SECRET_CSS_TOKEN_MARKER" not in description


@pytest.mark.parametrize("declared", [None, ""])
def test_audioknigi_search_uses_cyrillic_decoder_without_declared_charset(monkeypatch, declared):
    html = "<div>Привет, аудиокнига</div>"
    captured = []
    resp = SimpleNamespace(
        content=html.encode("windows-1251"), encoding=declared,
        apparent_encoding="windows-1251", url="https://audioknigi.com.ua/search/",
    )
    resp.raise_for_status = lambda: None
    monkeypatch.setattr(
        audioknigi_search, "get_http_session",
        lambda: SimpleNamespace(get=lambda *_a, **_kw: resp),
    )
    monkeypatch.setattr(
        audioknigi_search, "parse_audioknigi_results",
        lambda text, *_a, **_kw: captured.append(text) or [],
    )
    monkeypatch.setattr(audioknigi_search, "_group_audioknigi_recordings", lambda results, **_kw: results)
    assert audioknigi_search.search_audioknigi("Привет") == []
    assert captured == [html]


def test_librivox_lucene_metacharacters_are_escaped(monkeypatch):
    captured = {}
    monkeypatch.setattr(librivox, "_check_cancel", lambda *_a: None)
    def request(_url, **kwargs):
        captured["query"] = kwargs["params"]["q"]
        return SimpleNamespace(json=lambda: {"response": {"docs": []}})
    monkeypatch.setattr(librivox, "_request", request)
    monkeypatch.setattr(librivox, "_librivox_search_from_catalogue", lambda *_a, **_kw: [])
    assert librivox.search_librivox('Poem (2024): "A/B"') == []
    escaped = r'Poem \(2024\)\: \"A\/B\"'
    assert captured["query"].count(escaped) == 2
    assert captured["query"].startswith("collection:librivoxaudio AND (")


def test_yakniga_alias_slashes_are_percent_encoded(monkeypatch):
    item = {"aliasName": "part/one", "authorAlias": "author/name"}
    monkeypatch.setattr(yakniga._compat, "_yakniga_payload", lambda *_a: {"search": [item]})
    monkeypatch.setattr(
        yakniga, "_yakniga_book",
        lambda _item, url: SimpleNamespace(title="Book", url=url, author="Author", narrator="Reader"),
    )
    monkeypatch.setattr(yakniga, "_dedupe_results", lambda x: x)
    entries = yakniga.search_yakniga("Book")
    assert len(entries) == 1
    assert "/author%2Fname/part%2Fone" in entries[0].url


def test_akniga_browser_uses_redirected_canonical_book_url(monkeypatch):
    page = SimpleNamespace(
        url="https://akniga.org/canonical-book/?from=old",
        on=lambda *_a: None,
        goto=lambda *_a, **_kw: None,
        content=lambda: '<div data-bid="7"></div><script>LIVESTREET_SECURITY_KEY = "secret";</script>',
    )
    context = SimpleNamespace(new_page=lambda: page, close=lambda: None)
    browser = SimpleNamespace(new_context=lambda **_kw: context, close=lambda: None)
    monkeypatch.setattr(akniga, "launch_playwright_chromium", lambda *_a, **_kw: browser)
    monkeypatch.setattr(akniga, "_api_data", lambda *_a: {"tracks": []})
    monkeypatch.setattr(akniga, "_find_hls", lambda *_a: "https://cdn.example.org/playlist.m3u8")
    monkeypatch.setattr(akniga, "_parse_api_book", lambda url, *_a: url)
    result = akniga._fetch_using_browser(
        SimpleNamespace(chromium=object()),
        "https://akniga.org/old-book/", None, use_system_dns=False,
    )
    assert result == "https://akniga.org/canonical-book/"


def test_first_loaded_resume_is_guarded_from_premature_periodic_save():
    calls = []
    fake_player = SimpleNamespace(
        duration=lambda: 100_000, isSeekable=lambda: True,
        setPosition=lambda ms: calls.append(("seek", ms)),
        play=lambda: calls.append(("play",)),
    )
    stub = SimpleNamespace(
        current_path=Path("book.mp3"), player=fake_player,
        _pending_resume_ms=36_000, _pending_autoplay=True,
        _resume_applied=False, _last_seek_target_ms=0, _last_seek_at=0.0,
        store=SimpleNamespace(clear=lambda *_a: pytest.fail("resume should not be cleared")),
    )
    QtPlayerController._apply_resume_and_autoplay(stub)
    assert calls == [("seek", 36_000), ("play",)]
    assert stub._last_seek_target_ms == 36_000
    assert stub._last_seek_at > 0


def test_incomplete_audio_folder_uses_actual_file_chapter_number(tmp_path):
    from PySide6.QtWidgets import QApplication, QListWidget
    app = QApplication.instance() or QApplication([])

    class Label:
        def __init__(self):
            self.value = ""
        def setText(self, value):
            self.value = str(value)
        def setPixmap(self, _pix):
            pass

    first = tmp_path / "01 - First.mp3"
    third = tmp_path / "03 - Third.mp3"
    first.write_bytes(b"1")
    third.write_bytes(b"3")
    metadata = {"title": "Book", "tracks": [
        {"index": 1, "title": "Opening"},
        {"index": 2, "title": "Missing chapter"},
        {"index": 3, "title": "Final chapter"},
    ]}
    opened = []
    stub = SimpleNamespace(
        _player_audio_files=lambda *_: [first, third],
        _player_folder_metadata=lambda *_: metadata,
        _player_folder_cover=lambda *_: None,
        _load_player_file=lambda *a, **_kw: opened.extend(a),
        _l=lambda text, **kw: text.format(**kw),
        player_book_title_label=Label(), player_book_meta_label=Label(),
        player_cover_label=Label(), player_chapter_list=QListWidget(),
    )
    PlayerUiMixin.load_book_folder(stub, tmp_path, autoplay=False)
    assert stub.player_chapter_list.count() == 2
    assert "Opening" in stub.player_chapter_list.item(0).text()
    assert "Final chapter" in stub.player_chapter_list.item(1).text()
    assert "Missing chapter" not in stub.player_chapter_list.item(1).text()
    assert opened == [first]
    assert app is not None


def test_stopped_state_updates_player_status():
    class Button:
        def setEnabled(self, *_a): pass
        def setText(self, *_a): pass
        def setAccessibleName(self, *_a): pass
    class Label:
        value = ""
        def setText(self, text):
            self.value = text
    label = Label()
    stub = SimpleNamespace(
        player_controller=SimpleNamespace(has_source=lambda: True),
        player_play_button=Button(), player_stop_button=Button(),
        player_restart_button=Button(), player_back_button=Button(), player_forward_button=Button(),
        player_status_label=label, _l=lambda txt: txt,
    )
    PlayerUiMixin._player_state_changed(stub, "stopped")
    assert "остановлен" in label.value


def test_help_formats_plain_shift_tab_as_keyboard_shortcut():
    markup = _format_help_body_html("Help", "Use Shift+Tab or Umschalt+Tab to go back.")
    assert "<kbd>Shift+Tab</kbd>" in markup
    assert "<kbd>Umschalt+Tab</kbd>" in markup


@pytest.mark.parametrize("language,expected", [
    ("en", "complete MP3 file"), ("de", "vollständige MP3"), ("uk", "повний MP3"),
])
def test_ffmpeg_output_error_has_runtime_translation(language, expected):
    assert expected in localize_runtime_text(language, "FFmpeg не создал полный MP3.")


@pytest.mark.parametrize("language,expected", [
    ("en", "Not enough disk space"), ("de", "Nicht genug Speicherplatz"), ("uk", "Недостатньо місця"),
])
def test_generic_disk_space_error_is_localized(language, expected):
    message = "Недостаточно места. Нужно ~2 GB, свободно 1 GB."
    assert expected in localize_runtime_text(language, message)


def test_runtime_hls_and_range_messages_are_localized():
    assert "HLS: restored" in localize_runtime_text("en", "HLS: восстановлено 5 готовых сегментов из кэша.")
    assert "Range segment" in localize_runtime_text("en", "Не готов Range-сегмент part01.mp3.")


def test_legacy_proxy_translation_preserves_only_specified_proxy():
    from audioknigi.i18n import ui_text
    source = "Используется только указанный вами работающий прокси. DNS сам по себе не заменяет VPN или WARP. Пароли прокси не сохраняются."
    assert "Only the working proxy you specify" in ui_text("en", source)
