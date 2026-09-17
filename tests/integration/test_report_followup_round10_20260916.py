from __future__ import annotations

import threading
from pathlib import Path

import pytest

from audioknigi.core import Cancelled
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _extract_call_argument, _usable_search_title
from audioknigi.models import Book, SearchResult, Track
from audioknigi.poleknig import _discover_narration_variants
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.services.download_request import DownloadRequest

ROOT = Path(__file__).resolve().parents[2]


def test_knigavuhe_title_filter_does_not_hide_legitimate_comment_or_review_titles():
    assert _usable_search_title("Отзыв посла")
    assert _usable_search_title("Комментарии к Галльской войне")
    assert _usable_search_title("Отзыв")
    assert not _usable_search_title("Слушать онлайн")
    assert not _usable_search_title("Отзывы (12)")


def test_knigavuhe_extract_call_argument_tracks_nested_parentheses():
    source = "BookController.enter((function(){return {id: 7};})(), {other: true});"
    assert _extract_call_argument(source) == "(function(){return {id: 7};})()"


def test_download_request_exposes_public_track_index_and_keeps_compat_alias():
    track = Track(index="7", title="x", file="https://example.invalid/7.mp3")
    assert DownloadRequest.track_index(track) == 7
    assert DownloadRequest._track_index(track) == 7


def test_poleknig_variant_discovery_propagates_preexisting_cancel():
    event = threading.Event()
    event.set()
    with pytest.raises(Cancelled):
        _discover_narration_variants("", "https://poleknig.com/books/1", {}, cancel_event=event)


class _Response:
    text = "<html><head><title>Тестовая книга</title></head><body>Исполнитель: Иван Иванов, Жанр: Фантастика</body></html>"

    def raise_for_status(self):
        return None


class _Session:
    def get(self, *args, **kwargs):
        return _Response()


def test_audioknigi_narrator_parser_stops_before_comma_metadata_field():
    result = SearchResult(
        title="Тестовая книга",
        url="https://audioknigi.com.ua/test",
        source="audioknigi.com.ua",
    )
    hydrated = _audioknigi_page_metadata(
        result,
        session_factory=lambda: _Session(),
        metadata_extractor=lambda html, title: ("", "", ""),
        extended_metadata_extractor=lambda html: ("", "", "", ""),
    )
    assert hydrated.narrator == "Иван Иванов"


def test_ui_text_can_reuse_exact_runtime_catalog_for_static_qt_labels():
    assert ui_text("en", "Озвучка {index}", index=2) == "Recording 2"
    assert ui_text("de", "доступно") == "verfügbar"
    assert ui_text("uk", "недоступно") == "недоступно"


def test_search_failure_prefix_is_localized():
    assert localize_runtime_text("en", "Поиск не выполнен: timeout") == "Search failed: timeout"
    assert localize_runtime_text("de", "Поиск не выполнен: timeout") == "Suche fehlgeschlagen: timeout"


def test_empty_history_export_message_is_localized():
    source = "История пуста — экспортировать нечего."
    assert localize_runtime_text("en", source) != source
    assert localize_runtime_text("de", source) != source


def test_round10_source_hardening_contracts_are_present():
    probe = (ROOT / "audioknigi/download/probe.py").read_text(encoding="utf-8")
    media = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    book_flow = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    workers = (ROOT / "audioknigi/qt/workers.py").read_text(encoding="utf-8")
    analysis = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    audit = (ROOT / "tools/qt_localization_audit.py").read_text(encoding="utf-8")

    assert "resolved_path = file_path.resolve()" in probe
    assert "safe_int(getattr(item, \"index\", None), -1) == track_index" in media
    assert "track_index = int(getattr(tr, \"index\", -1))" in book_flow
    assert "normalize_cover_cache(raw_cover)" in workers
    assert 'self._l("Озвучка {index}", index=idx + 1)' in analysis.replace("\n", " ") or "Озвучка {index}" in analysis
    assert '"addItem"' in audit
    assert "_leading_constant_text" in audit
