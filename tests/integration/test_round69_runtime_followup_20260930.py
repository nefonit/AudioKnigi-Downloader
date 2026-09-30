from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from audioknigi import poleknig
from audioknigi.core import Cancelled
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.errors import MissingMediaSourceError
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.models import SearchResult
from audioknigi.providers import audioknigi_search

ROOT = Path(__file__).resolve().parents[2]


def test_missing_media_source_is_expired_even_without_cause_chain():
    exc = MissingMediaSourceError(
        "media disappeared",
        source_url="https://cdn.invalid/a.mp3",
        track_indices=[1],
    )
    assert exc.__cause__ is None
    assert BookFlowMixin._is_expired_media_error(exc) is True


def test_fallback_download_skips_empty_primary_and_uses_fallback_once(tmp_path):
    class Harness(NetworkDownloadMixin):
        cancel_event = threading.Event()

        def __init__(self):
            self.calls = []

        def _download_with_resume(self, url, target, referer):
            self.calls.append((url, Path(target), referer))
            return Path(target)

        def log(self, _text):
            pass

    target = tmp_path / "source.mp3"
    harness = Harness()
    result = harness._download_source_with_fallback(
        "", " https://cdn.invalid/fallback.mp3 ", target, "ref"
    )
    assert result == target
    assert [item[0] for item in harness.calls] == ["https://cdn.invalid/fallback.mp3"]


def test_audioknigi_hydration_propagates_cancelled(monkeypatch):
    source = SearchResult(
        title="Demo Book",
        author="Demo Author",
        narrator="",
        url="https://audioknigi.com.ua/demo",
        source="audioknigi.com.ua",
    )

    def cancelled(*_args, **_kwargs):
        raise Cancelled("cancelled")

    monkeypatch.setattr(audioknigi_search, "_audioknigi_page_metadata", cancelled)
    with pytest.raises(Cancelled):
        audioknigi_search._group_audioknigi_recordings([source])


def test_operation_cancel_has_context_specific_translation():
    main_window = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    assert 'cancel_text=tr(self.language, "cancel_operation")' in main_window

    messages = json.loads((ROOT / "audioknigi/locales/messages.json").read_text(encoding="utf-8"))
    assert messages["en"]["cancel_operation"] == "Cancel"
    assert messages["de"]["cancel_operation"] == "Abbrechen"
    assert messages["ru"]["cancel_operation"] == "Отменить"
    assert messages["uk"]["cancel_operation"] == "Скасувати"

    # The editor context menu intentionally keeps the Undo/Redo semantic pair.
    legacy = json.loads((ROOT / "audioknigi/locales/legacy_literals.json").read_text(encoding="utf-8"))
    assert legacy["en"]["Отменить"] == "Undo"
    assert legacy["en"]["Повторить"] == "Redo"


def test_german_shortcut_names_are_consistent():
    messages = json.loads((ROOT / "audioknigi/locales/messages.json").read_text(encoding="utf-8"))
    legacy = json.loads((ROOT / "audioknigi/locales/legacy_literals.json").read_text(encoding="utf-8"))
    assert "Tab / Umschalt+Tab" in messages["de"]["help_shortcuts_body"]
    assert "Tab / Shift+Tab" not in messages["de"]["help_shortcuts_body"]
    key = 'Анализ завершён. Стрелками просмотрите части; пробел меняет выбор. Затем Tab до «Скачать книгу» или нажмите Ctrl+D.'
    assert "Strg+D" in legacy["de"][key]
    assert "Ctrl+D" not in legacy["de"][key]


def test_poleknig_meta_parser_handles_multiline_attributes_without_dotall():
    html = '<html><head><meta property="og:description"\n content="Line one\nLine two"></head></html>'
    assert poleknig._extract_meta_content(html, "og:description") == "Line one Line two"


def test_health_and_main_http_sessions_share_proxy_isolation_policy():
    core_source = (ROOT / "audioknigi/core.py").read_text(encoding="utf-8")
    health_source = (ROOT / "audioknigi/services/source_health_service.py").read_text(encoding="utf-8")
    build_block = core_source[core_source.index("def build_http_session"):core_source.index("def get_http_session")]
    assert "session.trust_env = False" in build_block
    assert "session.trust_env = False" in health_source
