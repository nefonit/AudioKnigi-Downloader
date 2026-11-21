"""Offline regressions for privacy, cancellation and provider boundaries."""
from __future__ import annotations

from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup

from audioknigi.core import Cancelled
from audioknigi.diagnostics.support_bundle import _sanitize_log_bytes, sanitized_settings
from audioknigi.models import NarrationVariant
from audioknigi.parsers import knigavuhe, poleknig
from audioknigi.providers.sources_ext import uknig, akniga_catalog
from audioknigi.providers.audioknigi_search import _clean_audioknigi_description_candidate


def test_support_logs_mask_urls_and_preserve_line_structure():
    raw = b"URL=https://internal.example/private/123?token=topsecret, next\nsee https://cdn.example/book/55."
    clean = _sanitize_log_bytes(raw).decode("utf-8")
    assert "internal.example" not in clean
    assert "cdn.example" not in clean
    assert "topsecret" not in clean
    assert clean.count("<URL>") == 2
    assert "\n" in clean


def test_nested_plugin_settings_mask_unknown_url_keys():
    result = sanitized_settings({
        "plugin": {"callback": "https://private.example.local/tenant/999"},
        "deep": [{"endpoint": "URL https://internal.test/user?id=7"}],
    })
    assert "private.example.local" not in str(result)
    assert "internal.test" not in str(result)
    assert "<URL>" in str(result)


class _FakePool:
    def __init__(self, *args, **kwargs):
        self._future = Future()
        self._future.set_exception(Cancelled("cancelled"))

    def submit(self, *_args, **_kwargs):
        return self._future


@pytest.mark.parametrize("provider_module", [knigavuhe, poleknig])
def test_paged_search_does_not_swallow_cancelled_future(monkeypatch, provider_module):
    monkeypatch.setattr(provider_module, "ThreadPoolExecutor", _FakePool)
    monkeypatch.setattr(provider_module, "_shutdown_pool_now", lambda *_args: None)
    monkeypatch.setattr(
        provider_module, "_iter_completed_cancellable",
        lambda futures, _event: iter(futures),
    )
    monkeypatch.setattr(provider_module, "_search_last_page", lambda *_args: 2)
    monkeypatch.setattr(
        provider_module, "_fetch_search_page",
        lambda *_args, **_kw: SimpleNamespace(text="<html></html>", url="https://example.invalid/"),
    )
    monkeypatch.setattr(provider_module, "parse_search_results", lambda *_args: [])
    with pytest.raises(Cancelled):
        provider_module.search("Test book")


def test_knigavuhe_merge_preserves_known_availability():
    url = "https://knigavuhe.org/book/123/"
    items = knigavuhe._merge_narration_variants(
        [NarrationVariant(url=url, narrator="Reader", available=None)],
        [NarrationVariant(url=url, narrator="Reader", available=True)],
    )
    assert len(items) == 1
    assert items[0].available is True


def test_poleknig_nested_description_keeps_text_after_child_div():
    html = (
        '<div class="book-description">'
        "<div>First paragraph explains the central characters and their plans in the story.</div>"
        "<p>Second paragraph describes what happens later and must not be discarded "
        "when the inner div is closed, because it belongs to the same book synopsis.</p>"
        "</div>"
    )
    desc = poleknig._poleknig_description_from_html(html)
    assert "First paragraph" in desc and "Second paragraph" in desc


def test_uknig_search_rejects_external_book_links(monkeypatch):
    html = (
        '<div class="book-item"><a href="https://evil.example/books/123">External</a></div>'
        '<div class="book-item"><a href="https://uknig.com/books/123#comments">Local</a></div>'
    )
    monkeypatch.setattr(uknig, "_soup", lambda *_a: BeautifulSoup(html, "html.parser"))
    results = uknig.search_uknig("Book")
    assert len(results) == 1
    assert results[0].title == "Local"
    assert "evil.example" not in results[0].url
    assert "#comments" not in results[0].url


def test_akniga_card_book_urls_are_canonical():
    item = BeautifulSoup(
        '<div class="content__main__articles--item"><a href="http://akniga.org/example-book/?ref=home"><img alt="Example Book"></a></div>',
        "html.parser",
    )
    result = akniga_catalog._akniga_search_card(item)
    assert result is not None
    assert result.url.startswith("https://akniga.org/")


def test_audioknigi_description_preserves_ordinary_recommendations():
    original = (
        "Главный герой получает важные рекомендации от друга, "
        "а затем отправляется в далёкое путешествие. "
        "В следующих главах он сталкивается с неожиданными событиями "
        "и постепенно узнаёт правду о своём прошлом."
    )
    assert "важные рекомендации от друга" in _clean_audioknigi_description_candidate(original)
    assert "постепенно узнаёт правду" in _clean_audioknigi_description_candidate(original)


def test_player_resume_after_stop_protects_async_seek_from_save_timer():
    from audioknigi.qt.player_controller import PlayerController

    class FakePlayer:
        def __init__(self):
            self.seeks = []
            self.started = False

        def mediaStatus(self):
            return None

        def position(self):
            return 0

        def setPosition(self, value):
            self.seeks.append(value)

        def play(self):
            self.started = True

    player = FakePlayer()
    stub = SimpleNamespace(
        current_path=Path("chapter.mp3"),
        player=player,
        _at_end=False,
        _resume_after_stop_ms=12_000,
        _last_seek_target_ms=0,
        _last_seek_at=0.0,
    )
    PlayerController.play(stub)
    assert player.seeks == [12_000]
    assert stub._last_seek_target_ms == 12_000
    assert stub._last_seek_at > 0
    assert player.started


def test_seekable_one_second_audio_is_not_disabled():
    from audioknigi.qt.player_mixin import PlayerUiMixin

    class Slider:
        def __init__(self):
            self.enabled = None

        def maximum(self):
            return 1

        def setEnabled(self, enabled):
            self.enabled = bool(enabled)

    slider = Slider()
    PlayerUiMixin._player_seekable_changed(SimpleNamespace(player_seek_slider=slider), True)
    assert slider.enabled is True


def test_playwright_waits_for_response_not_just_request():
    root = Path(__file__).resolve().parents[2]
    source = (root / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    block = source.split("for _attempt in range(32):", 1)[1].split("html_text = page.content()", 1)[0]
    assert "if captured_responses:" in block
    assert "if captured:" not in block
