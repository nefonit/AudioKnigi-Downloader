from __future__ import annotations

from pathlib import Path

from audioknigi.knigavuhe import _extract_names
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi.services.queue_service import _normalize_queue_download_mode, _track_from_dict

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_knigavuhe_named_entity_is_terminal_for_nested_metadata_names() -> None:
    value = {
        "name": "Александр Пушкин",
        "genre": {"name": "Классика"},
        "meta": {"category": {"name": "Поэзия"}},
    }
    assert _extract_names(value) == ["Александр Пушкин"]


def test_queue_download_mode_normalizes_resume_parts_alias() -> None:
    assert _normalize_queue_download_mode("parts") == "selected"
    assert _normalize_queue_download_mode("selected") == "selected"
    assert _normalize_queue_download_mode("full_mp3") == "full_mp3"
    assert _normalize_queue_download_mode("unknown-future-value") == "selected"


def test_queue_track_selected_is_normalized_to_bool() -> None:
    assert _track_from_dict({"index": 1, "title": "A", "file": "x", "selected": "false"}).selected is False
    assert _track_from_dict({"index": 1, "title": "A", "file": "x", "selected": "0"}).selected is False
    assert _track_from_dict({"index": 1, "title": "A", "file": "x", "selected": None}).selected is False
    assert _track_from_dict({"index": 1, "title": "A", "file": "x", "selected": "true"}).selected is True


def test_audioknigi_known_coauthor_prefixes_can_be_removed_consecutively() -> None:
    title = "Александр Пушкин, Михаил Лермонтов - Стихи"
    for author in ("Александр Пушкин", "Михаил Лермонтов"):
        candidate = _strip_author_prefix_from_title(title, author)
        if candidate != title:
            title = candidate.lstrip(" ,;")
    assert title == "Стихи"


def test_easy_search_uses_all_sources_when_hidden_advanced_filters_are_off() -> None:
    source = src("audioknigi/qt/mixins/search.py")
    start = source.index("def start_search")
    end = source.index("def _search_finished", start)
    block = source[start:end]
    assert 'if not sources and self.current_ui_mode() == "easy":' in block
    assert "sources = list(source_actions)" in block
    assert block.index("sources = list(source_actions)") < block.index('self.set_status(self._l("Выберите хотя бы один сайт для поиска."')


def test_settings_save_preserves_shared_settings_object_identity() -> None:
    source = src("audioknigi/qt/mixins/settings.py")
    start = source.index("def _save_settings")
    end = source.index("def test_audiobookshelf", start)
    block = source[start:end]
    assert "self.settings.clear()" in block
    assert "self.settings.update(updated)" in block
    assert "self.settings = AppSettings.from_mapping(updated)" not in block
    assert "AppSettings" not in source.splitlines()[6]


def test_windows_url_shortcut_accepts_matching_wrapping_quotes() -> None:
    source = src("audioknigi/qt/mixins/clipboard.py")
    start = source.index('match = re.search(r"(?im)^URL=(.+)$"')
    block = source[start:start + 500]
    assert "shortcut_url = _unquote_shortcut_url(shortcut_url)" in block
    assert block.index("_unquote_shortcut_url(shortcut_url)") < block.index("valid_site_url(shortcut_url)")
    helper_start = source.index("def _unquote_shortcut_url")
    helper_end = source.index("class ClipboardUiMixin", helper_start)
    helper = source[helper_start:helper_end]
    assert "text[0] == text[-1]" in helper
    assert "return text[1:-1].strip()" in helper


def test_missing_media_decision_dialog_has_stable_main_window_parent() -> None:
    source = src("audioknigi/qt/mixins/analysis_download.py")
    start = source.index("def _resolve_missing_media")
    end = source.index("def ", start + 8)
    block = source[start:end]
    assert "box = QMessageBox(self)" in block
    assert "dialog_parent" not in block


def test_queue_drag_reorder_is_disabled_while_any_task_is_active() -> None:
    source = src("audioknigi/qt/mixins/queue.py")
    start = source.index("def _queue_drag_reordered")
    end = source.index("def toggle_queue_item_pause", start)
    block = source[start:end]
    assert "self._active_queue_task_id is not None" in block
    assert block.index("self._active_queue_task_id is not None") < block.index("self.queue_tasks.pop")


def test_native_event_filter_rejects_null_message_pointer_before_from_address() -> None:
    source = src("audioknigi/qt/media_keys.py")
    start = source.index("def nativeEventFilter")
    block = source[start:]
    assert "address = int(message)" in block
    assert "if not address:" in block
    assert "wintypes.MSG.from_address(address)" in block
    assert block.index("if not address:") < block.index("wintypes.MSG.from_address(address)")


def test_full_mp3_playlist_refresh_resynchronizes_request_indices() -> None:
    source = src("audioknigi/download_engine.py")
    start = source.index("def run_full_mp3")
    # Find the next class-level method, not the nested helper inside run_full_mp3.
    end = source.find("\n    def ", start + len("def run_full_mp3"))
    block = source[start:] if end < 0 else source[start:end]
    assert "req.book = book" in block
    assert "req.selected_indices = [" in block
    assert "req.track_index(track)" in block
    assert block.index("req.book = book") < block.index("req.selected_indices = [")


def test_all_queue_deserialization_paths_use_download_mode_normalizer() -> None:
    source = src("audioknigi/services/queue_service.py")
    assert source.count("download_mode=_normalize_queue_download_mode(data.get") >= 2
    assert "mode = _normalize_queue_download_mode(download_mode)" in source
