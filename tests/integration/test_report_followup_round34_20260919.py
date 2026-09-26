from __future__ import annotations

import json
from pathlib import Path

import pytest

from audioknigi.config.settings import migrate_settings
from audioknigi.download_engine import _DownloadEngine
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.models import Book, Track
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi.services.download_request import DownloadRequest

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_poleknig_prefers_real_visible_annotation_over_seo_meta_description() -> None:
    html = """
    <html><head>
      <title>«Крыса» Автор: слушать аудиокнигу</title>
      <meta name="description" content="Скачать аудиокнигу Автор Крыса бесплатно и слушать аудиокнигу онлайн">
      <meta property="og:image" content="/cover.jpg">
    </head><body>
      <h1>Крыса</h1>
      <a href="/authors/12-author">Автор</a>
      <div class="book-description">
        Настоящая аннотация книги рассказывает о герое, который оказывается перед трудным выбором.
        Это содержательное описание сюжета, а не служебный текст страницы для поисковых систем.
      </div>
    </body></html>
    """
    meta = _book_page_metadata(html, "https://poleknig.com/books/1")
    assert meta["description"].startswith("Настоящая аннотация книги")
    assert "Скачать аудиокнигу" not in meta["description"]


def test_poleknig_drops_seo_description_if_no_real_annotation_exists() -> None:
    html = """
    <html><head><meta name="description" content="Скачать аудиокнигу Автор Крыса и слушать аудиокнигу онлайн"></head>
    <body><h1>Крыса</h1><a href="/authors/12-author">Автор</a></body></html>
    """
    assert _book_page_metadata(html, "https://poleknig.com/books/1")["description"] == ""


def test_standalone_track_is_not_trimmed_by_rounded_metadata_duration() -> None:
    source = src("audioknigi/download/media.py")
    block = source[source.index("def _split_track"):source.index("def _save_book_sidecars")]
    assert "elif start is None and end is None:" in block
    assert "process the complete source to EOF" in block


def test_segmented_cancel_closes_sockets_then_waits_for_file_handles() -> None:
    source = src("audioknigi/download/network.py")
    block = source[source.index("cancelled_peers_for_error = False"):source.index("if errors:", source.index("cancelled_peers_for_error = False"))]
    assert "self._cancel_active_network_io()" in block
    assert "thread.join(timeout=min(1.0, remaining))" in block
    assert "event=segmented_cancel_workers_lingering" in block


def test_full_mp3_retained_source_suffix_uses_container_and_codec() -> None:
    assert _DownloadEngine._retained_source_suffix("https://x/source", {"codec": "mp3"}) == ".mp3"
    assert _DownloadEngine._retained_source_suffix("https://x/source", {"codec": "aac", "format_name": "mov,mp4,m4a,3gp,3g2,mj2"}) == ".m4a"
    assert _DownloadEngine._retained_source_suffix("https://x/source", {"codec": "flac"}) == ".flac"
    assert _DownloadEngine._retained_source_suffix("https://x/source.ogg", {"codec": "vorbis"}) == ".ogg"


def test_knigavuhe_js_call_parser_does_not_scan_past_assignment() -> None:
    assert _extract_call_argument('BookController.enter = function(x) {}; foo({"wrong": 1});') == ""
    assert '"ok": 1' in _extract_call_argument('BookController.enter   ({"ok": 1}, true);')


def test_shared_source_fallback_removes_old_resume_manifest_before_switch() -> None:
    source = src("audioknigi/download/book_flow.py")
    block = source[source.index("fallback_attempted = True"):source.index("book = fallback")]
    assert "self._remove_resume_manifest(book)" in block


def test_string_false_boolean_settings_are_not_truthy() -> None:
    normalized, _changed = migrate_settings({
        "first_run_complete": "false",
        "embed_tags": "0",
        "save_sidecars": "no",
        "delete_source": "off",
        "clipboard_auto": "true",
    })
    assert normalized["first_run_complete"] is False
    assert normalized["embed_tags"] is False
    assert normalized["save_sidecars"] is False
    assert normalized["delete_source"] is False
    assert normalized["clipboard_auto"] is True


def test_cover_sidecar_is_written_atomically() -> None:
    common = src("audioknigi/download/common.py")
    media = src("audioknigi/download/media.py")
    assert "def atomic_write_bytes" in common
    assert 'atomic_write_bytes(folder / ("cover" + ext), data)' in media


def test_dynamic_runtime_messages_and_german_narration_term_are_localized() -> None:
    patterns = json.loads((ROOT / "audioknigi/locales/runtime_regex.json").read_text(encoding="utf-8"))
    mapping = {pattern: variants for pattern, variants in patterns}
    assert mapping[r"^Озвучка (\d+)$"]["de"] == "Sprecherfassung {0}"
    for pattern in (
        r"^Ошибка источника (.+)$",
        r"^Найден исправный резервный источник knigavuhe\.org\. Переключаю загрузку автоматически: (.+)\.$",
        r"^Удалены временные файлы устаревшего источника: (.+)\.$",
        r"^Плейлист обновлён: частей (.+), изменённых аудиоссылок (.+)\. Повторяю загрузку один раз\.$",
        r"^Пользователь пропустил недоступные части: (.+)\. Остальные выбранные части продолжаю скачивать\.$",
    ):
        assert pattern in mapping


def test_audioknigi_author_prefix_handles_reordered_full_name() -> None:
    assert _strip_author_prefix_from_title("Лев Толстой - Война и мир", "Толстой Лев Николаевич") == "Война и мир"
    assert _strip_author_prefix_from_title("Метро 2033 — Тёмные туннели", "Дмитрий Глуховский") == "Метро 2033 — Тёмные туннели"


def test_dot_output_directory_remains_a_valid_explicit_path_contract() -> None:
    source = src("audioknigi/services/download_request.py")
    # Path("") is indistinguishable from an intentionally supplied Path(".").
    # build_download_request already normalizes an empty settings value to
    # DEFAULT_OUTPUT before constructing this request, so the service contract
    # must continue allowing an explicit current-directory Path.
    assert 'if not str(self.output_dir).strip():' in source

def test_search_status_distinguishes_provider_errors() -> None:
    source = src("audioknigi/services/search_service.py")
    assert "provider_failed = False" in source
    assert 'f"Ошибка источника {provider.display_name}"' in source


def test_queue_drop_uses_viewport_relative_event_position_directly() -> None:
    source = src("audioknigi/qt/workers.py")
    block = source[source.index("def dropEvent"):source.index("super().dropEvent", source.index("def dropEvent"))]
    assert "self.rowAt(int(event.position().y()))" in block
    assert "mapFrom" not in block


def test_opening_player_from_easy_mode_reveals_advanced_player_tab() -> None:
    source = src("audioknigi/qt/player_mixin.py")
    block = source[source.index("def _load_player_file"):source.index("@staticmethod", source.index("def _load_player_file"))]
    assert 'if self.current_ui_mode() == "easy":' in block
    assert 'self.set_ui_mode("advanced")' in block


def test_easy_download_is_disabled_for_new_text_query() -> None:
    source = src("audioknigi/qt/main_window.py")
    block = source[source.index("def _update_easy_action_text"):source.index("def _set_operation_ui_blocked")]
    assert "matches_current = bool(incoming_url and current_url and incoming_url == current_url)" in block
    assert "easy_stale = bool(is_url and not matches_current)" in block
    assert "and matches_current" in block


def test_retry_all_failed_skips_tasks_requiring_analysis() -> None:
    source = src("audioknigi/qt/mixins/queue.py")
    block = source[source.index("def retry_all_failed"):source.index("def clear_queue")]
    assert 'if task.status_code == "error" and not task_requires_analysis(task):' in block


def test_search_deferred_render_is_safe_during_exit() -> None:
    source = src("audioknigi/qt/mixins/search.py")
    block = source[source.index("def _apply_search_outcome"):source.index("def _focus_search_result_after_render")]
    assert 'if getattr(self, "_exit_requested", False):' in block
    assert "event=result_render_skipped" in block


def test_keyboard_track_context_menu_selects_first_row_when_needed() -> None:
    source = src("audioknigi/qt/mixins/clipboard.py")
    block = source[source.index("def _show_track_context_menu"):source.index("def open_selected_track_file")]
    assert 'elif pos is None and not self.track_table.currentIndex().isValid() and self.track_model.rowCount() > 0:' in block
    assert "focus_table_row(self.track_table, 0, focus=False)" in block


def test_audit_items_intentionally_left_unchanged_have_existing_safety_contracts() -> None:
    templates = src("audioknigi/templates.py")
    analysis = src("audioknigi/qt/mixins/analysis_download.py")
    i18n = src("audioknigi/i18n.py")
    # Output_Dir remains deliberately relative inside folder templates.
    assert 'values = template_values(book, output_dir="", language=language)' in templates
    # Missing-media modal already watches prompt.event, including worker timeout.
    assert "if prompt.event.is_set()" in analysis
    # ui_text formats exact placeholder entries before display; the narration count
    # entry is therefore not a runtime_exact bug in its current call path.
    assert "return value.format(**kwargs)" in i18n
