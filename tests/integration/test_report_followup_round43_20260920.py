from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import audioknigi.config.settings as settings_module
import audioknigi.diagnostics.support_bundle as support_bundle
import audioknigi.download.network as network_module
import audioknigi.knigavuhe as knigavuhe
import audioknigi.poleknig as poleknig
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.download.probe import ProbeMixin
from audioknigi.models import SearchResult
from audioknigi.providers.audioknigi_search import (
    _audioknigi_page_metadata,
    _merge_author_names,
)

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_knigavuhe_query_initials_match_in_both_directions_without_single_letter_false_positive() -> None:
    full = SearchResult(
        title="Война и мир",
        author="Лев Толстой",
        narrator="Иван Иванов",
        url="https://knigavuhe.org/book/1/",
        source="knigavuhe",
    )
    abbreviated = SearchResult(
        title="Война и мир",
        author="Л. Толстой",
        narrator="И. Иванов",
        url="https://knigavuhe.org/book/1/",
        source="knigavuhe",
    )
    assert knigavuhe._knigavuhe_matches_query(full, "Л. Толстой")
    assert knigavuhe._knigavuhe_matches_query(abbreviated, "Лев Толстой")
    assert not knigavuhe._knigavuhe_matches_query(full, "Л.")
    assert not knigavuhe._knigavuhe_matches_query(full, "А. Пушкин")


def test_knigavuhe_fallback_skips_zero_mp3_even_with_query_parameters() -> None:
    html = """
    <title>Тестовая книга</title>
    <script>
    const a = "https://cdn.example/0.mp3?token=quiet";
    const b = "https://cdn.example/1.mp3?token=real";
    </script>
    """
    book = knigavuhe._fallback_script_book(html, "https://knigavuhe.org/book/test/")
    assert book is not None
    assert [track.file for track in book.tracks] == ["https://cdn.example/1.mp3?token=real"]


def test_poleknig_js_literal_normalizer_ignores_backtick_template_text() -> None:
    raw = "[{title: `Chapter 1: true story`, enabled: true, extra: null}]"
    normalized = poleknig._normalize_js_literals_for_python(raw)
    assert "`Chapter 1: true story`" in normalized
    assert "enabled: True" in normalized
    assert "extra: None" in normalized


def test_safe_bool_uses_default_for_missing_or_empty_values_and_direct_settings_have_defaults() -> None:
    assert settings_module._safe_bool(None, True) is True
    assert settings_module._safe_bool("", True) is True
    assert settings_module._safe_bool("false", True) is False
    settings = settings_module.AppSettings()
    assert settings["language"] == settings_module.DEFAULT_SETTINGS["language"]
    assert settings["minimize_to_tray"] is True


def test_range_probe_accepts_whitespace_around_content_range_slash(monkeypatch) -> None:
    class Response:
        status_code = 206
        headers = {"content-range": "bytes 0-0 / 1234567"}

        def raise_for_status(self):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr(network_module, "get_http_session", lambda: Session())
    assert NetworkDownloadMixin()._range_info("https://cdn.example/book.mp3", "https://example/") == (True, 1234567)


def test_book_flow_rejects_missing_source_before_building_download_jobs() -> None:
    source = src("audioknigi/download/book_flow.py")
    assert 'if not str(getattr(tr, "file", "") or "").strip()' in source
    assert '"В плейлисте отсутствует адрес аудиофайла для частей: "' in source
    assert 'source_url = str(getattr(tr, "file", "") or "").strip()' in source


def test_probe_identity_accepts_ascii_en_and_em_dashes() -> None:
    probe = ProbeMixin()
    for separator in (" - ", " – ", " — "):
        book = SimpleNamespace(title=f"Лев Толстой{separator}Война и мир", author="", narrator="")
        title, author, narrator = probe._book_identity_hints(book)
        assert title == "Война и мир"
        assert author == "Лев Толстой"
        assert narrator == ""


def test_author_merge_collapses_initial_and_full_name_but_keeps_different_initials() -> None:
    assert _merge_author_names("А. Пушкин", "Александр Пушкин") == "Александр Пушкин"
    assert _merge_author_names("Пушкин Александр", "Александр Пушкин") == "Пушкин Александр"
    assert _merge_author_names("А. Иванов", "Б. Иванов") == "А. Иванов, Б. Иванов"


def test_audioknigi_narrator_fallback_stops_at_duration_field() -> None:
    html = "<html><body>Исполнитель: Иван Иванов Время звучания: 12:34 Качество: 128 kbps</body></html>"

    class Response:
        content = html.encode("utf-8")
        text = html

        def raise_for_status(self):
            return None

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    result = SearchResult(
        title="Книга",
        author="Автор",
        narrator="",
        url="https://audioknigi.com.ua/audio-1-test",
        source="audioknigi",
    )
    hydrated = _audioknigi_page_metadata(
        result,
        session_factory=lambda: Session(),
        metadata_extractor=lambda _html, _title: ("", "", ""),
        extended_metadata_extractor=lambda _html: ("", "", "", ""),
    )
    assert hydrated.narrator == "Иван Иванов"


def test_dead_browser_session_flag_and_dead_bookflow_transient_helper_are_removed() -> None:
    assert "cookies_provided =" not in src("audioknigi/core.py")
    assert "def _is_transient_error" not in src("audioknigi/download/book_flow.py")
