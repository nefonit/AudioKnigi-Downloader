from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.config.settings import AppSettings
from audioknigi.core import safe_name
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _extract_narration_variants
from audioknigi.models import Book, SearchResult, Track
from audioknigi.services import book_analysis_service as analysis_module
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.templates import template_values

ROOT = Path(__file__).resolve().parents[2]


def test_playlist_refresh_preserves_zero_index_and_local_state():
    original_track = Track(index=0, title="Prologue", file="old.mp3", selected=True, local_status="ready")
    original_track.actual_duration = 12.0
    original_track.local_path = "saved.mp3"
    original = Book(url="https://example.invalid/book", title="Demo", tracks=[original_track])
    fresh = Book(url=original.url, title="Demo", tracks=[Track(index=0, title="Prologue", file="new.mp3")])

    class Harness(BookFlowMixin):
        runtime_language = "ru"
        def _check_cancel(self): pass
        def set_status(self, _text): pass
        def set_stage(self, *_args): pass
        def log(self, _text): pass
        def _analyze_book(self, _url): return fresh
        def _clear_stale_source_downloads(self, _book): return 0

    assert Harness()._refresh_book_media_playlist(original, [0]) == 1
    assert original.tracks[0].index == 0
    assert original.tracks[0].selected is True
    assert original.tracks[0].actual_duration == pytest.approx(12.0)
    assert original.tracks[0].local_path == "saved.mp3"


def test_sidecars_preserve_zero_index_and_unknown_timeline(tmp_path):
    class Harness(MediaProcessingMixin):
        runtime_save_sidecars = True
        def _cover_bytes(self, _book): return None
        def _log_book_flow(self, *_args, **_kwargs): pass
        def log(self, text):
            raise AssertionError(text)

    book = Book(url="https://example.invalid/book", title="Demo")
    tracks = [
        Track(index=0, title="Prologue", file="x", duration=None),
        Track(index=1, title="Chapter", file="y", duration=5),
    ]
    book.tracks = tracks
    Harness()._save_book_sidecars(book, tmp_path, tracks)

    payload = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert payload["tracks"][0]["index"] == 0
    assert payload["tracks"][0]["timeline_start"] == 0.0
    assert payload["tracks"][0]["timeline_end"] is None
    assert payload["tracks"][1]["timeline_start"] is None
    info = (tmp_path / "book_info.txt").read_text(encoding="utf-8")
    assert "00. 00:00:00–—  Prologue" in info
    assert "01. —–—  Chapter" in info


def test_appsettings_legacy_read_aliases_match_legacy_semantics():
    settings = AppSettings({"auto_chunk_min_kbytes_per_sec": 512, "normalization_mode": "two_pass"})
    assert settings["auto_chunk_min_kbps"] == 512
    assert settings.get("auto_chunk_min_kbps") == 512
    assert settings["normalize_audio"] is True
    settings["normalize_audio"] = False
    assert settings["normalize_audio"] is False
    assert settings["normalization_mode"] == "off"


def test_safe_name_already_guards_invalid_book_titles():
    # Forbidden filename characters are replaced, not removed; whitespace-only
    # names use the explicit safe fallback. Neither case can resolve to base/"".
    assert safe_name("???") == "___"
    assert safe_name("***") == "___"
    assert safe_name("   ") == "audiobook"


def test_known_narrator_does_not_fall_back_to_unknown_after_explicit_conflict(monkeypatch):
    original = Book(title="Book", author="Author", narrator="Wanted Reader", url="https://audioknigi.com.ua/audio-1")
    results = [
        SearchResult(title="Book", author="Author", narrator="", url="https://knigavuhe.org/book/unknown/", source="knigavuhe"),
        SearchResult(title="Book", author="Author", narrator="Other Reader", url="https://knigavuhe.org/book/other/", source="knigavuhe"),
    ]
    monkeypatch.setattr(analysis_module, "search_knigavuhe_books", lambda *_a, **_k: results)

    def fake_fetch(url, **_kwargs):
        narrator = "" if "unknown" in url else "Other Reader"
        return Book(title="Book", author="Author", narrator=narrator, url=url)

    monkeypatch.setattr(analysis_module, "fetch_knigavuhe_book", fake_fetch)
    assert BookAnalysisService()._knigavuhe_fallback_candidate(original) is None

    source = (ROOT / "audioknigi/download/source_analysis.py").read_text(encoding="utf-8")
    assert "saw_conflicting_narrator = True" in source
    assert "if narrator_tokens and saw_conflicting_narrator:" in source


def test_blank_track_titles_keep_unique_template_fallbacks():
    book = Book(url="https://example.invalid/book", title="Book", tracks=[Track(index=1, title=" ", file="x"), Track(index=2, title="\t", file="y")])
    assert template_values(book, book.tracks[0])["Track_Title"] == "track-01"
    assert template_values(book, book.tracks[1])["Track_Title"] == "track-02"


def test_knigavuhe_generic_div_exact_other_narrations_heading_is_recognized():
    html = '<div class="title">Другие озвучки</div><a href="/book/alt/">Reader Name</a>'
    variants = _extract_narration_variants(html, "https://knigavuhe.org/book/current/")
    assert any(item.url == "https://knigavuhe.org/book/alt/" for item in variants)


def test_runtime_template_entries_are_intentionally_formatted_by_ui_text():
    assert ui_text("en", "Найдено вариантов озвучки: {count}. Выберите чтеца.", count=3) == (
        "Narration options found: 3. Choose a narrator."
    )
    assert ui_text("en", "Озвучка {index}", index=2) == "Narration 2"


def test_new_book_flow_runtime_error_localizations_are_available():
    missing = "В плейлисте отсутствует адрес аудиофайла для частей: 0, 2. Повторите анализ книги."
    assert localize_runtime_text("en", missing) == (
        "The playlist is missing the audio-file address for parts: 0, 2. Analyze the book again."
    )
    failed = "Не удалось корректно создать 01.mp3: ожидалось 01:00, получено 00:40."
    assert localize_runtime_text("de", failed) == (
        "01.mp3 konnte nicht korrekt erstellt werden: erwartet 01:00, erhalten 00:40."
    )
    static = "Локальный исходник для нарезки не найден. Повторите анализ или загрузку книги."
    assert localize_runtime_text("uk", static).startswith("Локальний вихідний файл")


def test_support_bundle_mime_types_are_not_mistaken_for_posix_paths():
    from audioknigi.diagnostics.support_bundle import _privacy_path
    assert _privacy_path("Content-Type: application/json", collapse_whole_path=False) == "Content-Type: application/json"
    assert _privacy_path("cover: image/jpeg", collapse_whole_path=False) == "cover: image/jpeg"
    assert _privacy_path("path /secret", collapse_whole_path=False) == "path <configured-path>"


def test_reported_knigavuhe_groups_nameerror_is_not_present():
    source = (ROOT / "audioknigi/knigavuhe.py").read_text(encoding="utf-8")
    grouping = source[source.index("grouped: dict"):source.index("unique: list", source.index("grouped: dict"))]
    assert "groups[key]" not in grouping
    assert "grouped[key]" in grouping


def test_german_shortcuts_are_supported_by_help_formatter_source():
    source = (ROOT / "audioknigi/qt/help_center.py").read_text(encoding="utf-8")
    block = source[source.index("shortcut = re.compile"):source.index("return shortcut.sub", source.index("shortcut = re.compile"))]
    assert "Ctrl|Strg" in block
    assert "Shift|Umschalt" in block
    assert "Leertaste" in block


def test_existing_proxy_media_filter_folder_and_volume_guards_remain_present():
    core = (ROOT / "audioknigi/core.py").read_text(encoding="utf-8")
    health = (ROOT / "audioknigi/services/source_health_service.py").read_text(encoding="utf-8")
    lifecycle = (ROOT / "audioknigi/qt/mixins/lifecycle.py").read_text(encoding="utf-8")
    settings = (ROOT / "audioknigi/qt/mixins/settings.py").read_text(encoding="utf-8")
    accessibility = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    assert "session.trust_env = False" in core
    assert "session.trust_env = False" in health
    assert "app.removeNativeEventFilter(media_filter)" in lifecycle
    assert "def _choose_output_dir(self, _checked=False, *, target=None):" in settings
    assert "self.event_sound_manager.configure(volume=percent / 100.0)" in accessibility


def test_speed_graph_reserves_label_area_using_font_metrics():
    source = (ROOT / "audioknigi/qt/speed_graph.py").read_text(encoding="utf-8")
    assert "metrics = painter.fontMetrics()" in source
    assert "label_baseline = max(2, metrics.ascent() + 2)" in source
    assert "graph_top = max(7, metrics.height() + 4)" in source
    assert "painter.drawText(7, label_baseline" in source
