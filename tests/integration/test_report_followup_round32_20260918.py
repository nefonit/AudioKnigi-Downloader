from __future__ import annotations

import json
from pathlib import Path

from audioknigi.core import Cancelled, load_json
from audioknigi.services.queue_service import _parse_selected_indices_payload
from audioknigi.templates import template_values
from audioknigi.models import Book, Track

ROOT = Path(__file__).resolve().parents[2]


def src(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cancelled_is_not_runtimeerror_and_stream_copy_fallback_cannot_swallow_it() -> None:
    assert not issubclass(Cancelled, RuntimeError)


def test_support_bundle_sanitizes_path_objects() -> None:
    source = src("audioknigi/diagnostics/support_bundle.py")
    assert 'isinstance(value, (str, Path))' in source
    assert '_privacy_path(str(value))' in source


def test_segmented_wait_closes_active_io_on_cancel_path() -> None:
    source = src("audioknigi/download/network.py")
    start = source.index("cancelled_peers_for_error = False")
    block = source[start:start + 1200]
    assert "try:" in block and "finally:" in block
    assert "if any(thread.is_alive() for thread in threads):" in block
    assert "self._cancel_active_network_io()" in block


def test_missing_track_title_uses_unique_track_number_not_book_title() -> None:
    book = Book(url="https://example", title="Book", tracks=[Track(index=1, title="", file="a"), Track(index=2, title="", file="b")])
    assert template_values(book, book.tracks[0])["Track_Title"] == "track-01"
    assert template_values(book, book.tracks[1])["Track_Title"] == "track-02"


def test_load_json_accepts_utf8_bom(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps({"ok": True}).encode("utf-8"))
    assert load_json(path, {}) == {"ok": True}


def test_queue_selected_indices_reject_json_booleans() -> None:
    assert _parse_selected_indices_payload([True, False, 2, "3"]) == [2, 3]


def test_audioknigi_html_paths_decode_content_as_utf8_sig() -> None:
    provider = src("audioknigi/providers/audioknigi_search.py")
    analysis = src("audioknigi/services/book_analysis_service.py")
    assert 'content.decode("utf-8-sig", errors="replace")' in provider
    assert 'content.decode("utf-8-sig", errors="replace")' in analysis


def test_knigavuhe_analysis_fallback_uses_clean_identity_hint() -> None:
    source = src("audioknigi/services/book_analysis_service.py")
    assert "def _book_identity_hints" in source
    assert "title_hint, author_hint, narrator_hint = self._book_identity_hints(book)" in source
    assert "search_knigavuhe_books(title_hint" in source


def test_settings_page_honors_persisted_quality_preset_and_localizes_abs_id() -> None:
    source = src("audioknigi/qt/main_window_pages.py")
    assert 'explicit_quality = str(self.settings.get("quality_preset", "") or "").strip()' in source
    assert 'name=self._l("ID библиотеки Audiobookshelf")' in source


def test_player_fields_initialized_and_context_delete_restores_focus() -> None:
    main = src("audioknigi/qt/main_window.py")
    menu = src("audioknigi/qt/localized_context_menu.py")
    for field in ("_last_player_chapter_activation", "_player_book_folder", "_player_book_files", "_player_local_metadata"):
        assert f"self.{field}" in main
    assert menu.count("widget.setFocus(Qt.FocusReason.OtherFocusReason)") >= 2


def test_analysis_refreshes_player_button_after_model_reset() -> None:
    source = src("audioknigi/qt/mixins/analysis_download.py")
    assert "self.track_model.set_book(book)\n        self._update_selected_track_player_button()" in source
    assert "self.track_model.set_book(self.current_book)\n        self._update_selected_track_player_button()" in source


def test_localization_followups_present_and_german_uses_du_sprecherfassung() -> None:
    exact = json.loads((ROOT / "audioknigi/locales/runtime_exact.json").read_text(encoding="utf-8"))
    legacy = json.loads((ROOT / "audioknigi/locales/legacy_literals.json").read_text(encoding="utf-8"))
    assert exact["Выберите озвучку"]["de"] == "Sprecherfassung auswählen"
    assert exact["Выберите чтеца перед анализом книги"]["de"].startswith("Wähle ")
    assert "Wählen Sie" not in exact["Найдено вариантов озвучки: {count}. Выберите чтеца."]["de"]
    for key in ("Завершаю поиск", "Найден исправный резервный источник knigavuhe.org.", "Анализ отменён.", "Не удалось проанализировать книгу."):
        assert key in exact
    for key in ("Дата", "Попытки", "Частей", "Папка"):
        assert all(key in legacy[lang] for lang in ("de", "en", "uk"))
    assert legacy["en"]["Range от размера:"] == "Range min. file size:"


def test_german_help_engine_grammar_fixed() -> None:
    source = src("audioknigi/qt/help_center.py")
    assert "die Download-Engine ist jedoch dieselbe" in source
    assert "der Download-Engine ist jedoch derselbe" not in source


def test_reported_save_json_and_queue_serialization_are_already_supported() -> None:
    core = src("audioknigi/core.py")
    models = src("audioknigi/models.py")
    assert "def save_json(path, data, *, raise_errors=False):" in core
    assert "class MappingDataclass" in models and "def to_dict" in models


def test_runtime_localization_regex_precedes_prefixes() -> None:
    source = src("audioknigi/i18n.py")
    regex = source.index("for pattern, variants in _PHASE29_RUNTIME_REGEX")
    prefix = source.index("for prefix, variants in _PHASE29_RUNTIME_PREFIXES.items()")
    assert regex < prefix
