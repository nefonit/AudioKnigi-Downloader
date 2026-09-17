from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget


REQUIRED_ACCESSIBLE_IDS = (
    "main_window",
    "main_tabs",
    "status_bar",
    "book_url",
    "paste_book_url",
    "unfinished_status",
    "continue_unfinished",
    "analyze_book",
    "cancel_analysis",
    "download_book",
    "download_options",
    "download_full_mp3",
    "add_book_to_queue",
    "cancel_download",
    "analysis_progress",
    "download_stage",
    "download_progress",
    "download_speed",
    "book_summary",
    "narration_variant",
    "narration_first_available",
    "select_all_tracks",
    "clear_all_tracks",
    "play_selected_track",
    "book_tracks",
    "search_query",
    "search_button",
    "cancel_search",
    "search_progress",
    "search_results",
    "search_empty_state",
    "use_search_result",
    "copy_search_url",
    "queue_start",
    "queue_pause",
    "queue_resume",
    "queue_stop",
    "queue_retry",
    "queue_priority",
    "queue_up",
    "queue_down",
    "queue_remove",
    "queue_add_url",
    "queue_clear",
    "queue_table",
    "queue_empty_state",
    "history_table",
    "history_empty_state",
    "refresh_history",
    "history_open_folder",
    "history_export",
    "settings_sections",
    "settings_stack",
    "output_dir",
    "browse_output",
    "quality_preset",
    "naming_mode",
    "embed_tags",
    "save_sidecars",
    "delete_source",
    "playwright_fallback",
    "clipboard_auto",
    "audio_preset",
    "normalization_mode",
    "parallel_processing",
    "segment_count",
    "segment_threshold",
    "auto_chunk_threshold",
    "bandwidth_limit",
    "use_templates",
    "folder_template",
    "track_template",
    "abs_enabled",
    "abs_url",
    "abs_api_key",
    "abs_library_id",
    "abs_test",
    "theme",
    "ui_scale",
    "minimize_to_tray",
    "save_settings",
    "create_backup",
    "restore_backup",
    "player_file",
    "player_open_book",
    "player_open_file",
    "player_play_pause",
    "player_stop",
    "player_restart",
    "player_seek",
    "player_time",
    "player_volume",
    "player_volume_value",
    "player_rate",
    "player_status",
    "player_chapters",
    # Phase 13/15 full-parity controls
    "ui_mode_easy",
    "ui_mode_advanced",
    "ui_mode_stack",
    "easy_universal_input",
    "easy_paste",
    "easy_action",
    "easy_search_progress",
    "easy_quality",
    "easy_output_dir",
    "easy_choose_folder",
    "easy_search_results",
    "easy_use_result",
    "easy_copy_url",
    "easy_book_summary",
    "easy_empty_state",
    "easy_download",
    "easy_open_listen",
    "easy_another_book",
    "clear_book_input",
    "book_output_dir",
    "book_choose_output",
    "book_open_output",
    "download_all",
    "book_cover",
    "easy_book_cover",
    "book_empty_state",
    "book_description",
    "session_log",
    "toggle_session_log",
    "easy_cancel_search",
    "queue_item_pause",
    "queue_retry_all",
    "event_sounds_enabled",
    "event_sound_volume",
    "event_sound_volume_value",
    "preview_event_sound",
    "preview_system_sound",
    "language",
    "ui_mode",
    "large_mode",
    "hide_source",
)

# Widgets created only while the missing-media modal is open are audited as a
# separate dynamic contract. They cannot be part of REQUIRED_ACCESSIBLE_IDS,
# because the main-window frozen self-test intentionally runs with no modal open.
DYNAMIC_ACCESSIBLE_IDS = (
    "missing_media_dialog",
    "missing_media_stop",
    "missing_media_skip",
    "modal_message",
    "modal_ok",
    "modal_question",
    "modal_yes",
    "modal_no",
)

# Informational labels/progress indicators are intentionally not keyboard-focusable.
FOCUSABLE_ACCESSIBLE_IDS = (
    "main_tabs",
    "book_url",
    "paste_book_url",
    "continue_unfinished",
    "analyze_book",
    "cancel_analysis",
    "download_options",
    "cancel_download",
    "narration_variant",
    "narration_first_available",
    "select_all_tracks",
    "clear_all_tracks",
    "play_selected_track",
    "book_tracks",
    "search_query",
    "search_button",
    "cancel_search",
    "search_results",
    "use_search_result",
    "copy_search_url",
    "queue_start",
    "queue_pause",
    "queue_resume",
    "queue_stop",
    "queue_retry",
    "queue_priority",
    "queue_up",
    "queue_down",
    "queue_remove",
    "queue_add_url",
    "queue_clear",
    "queue_table",
    "history_table",
    "refresh_history",
    "history_open_folder",
    "history_export",
    "settings_sections",
    "output_dir",
    "browse_output",
    "quality_preset",
    "naming_mode",
    "embed_tags",
    "save_sidecars",
    "delete_source",
    "playwright_fallback",
    "clipboard_auto",
    "audio_preset",
    "normalization_mode",
    "parallel_processing",
    "segment_count",
    "segment_threshold",
    "auto_chunk_threshold",
    "bandwidth_limit",
    "use_templates",
    "folder_template",
    "track_template",
    "abs_enabled",
    "abs_url",
    "abs_api_key",
    "abs_library_id",
    "abs_test",
    "theme",
    "ui_scale",
    "minimize_to_tray",
    "save_settings",
    "create_backup",
    "restore_backup",
    "ui_mode_easy",
    "ui_mode_advanced",
    "easy_universal_input",
    "easy_paste",
    "easy_action",
    "easy_quality",
    "easy_output_dir",
    "easy_choose_folder",
    "easy_search_results",
    "easy_use_result",
    "easy_copy_url",
    "easy_download",
    "easy_open_listen",
    "easy_another_book",
    "clear_book_input",
    "book_output_dir",
    "book_choose_output",
    "book_open_output",
    "download_all",
    "session_log",
    "toggle_session_log",
    "easy_cancel_search",
    "queue_item_pause",
    "queue_retry_all",
    "event_sounds_enabled",
    "event_sound_volume",
    "preview_event_sound",
    "preview_system_sound",
    "language",
    "ui_mode",
    "large_mode",
    "hide_source",
    "player_open_book",
    "player_open_file",
    "player_play_pause",
    "player_stop",
    "player_restart",
    "player_seek",
    "player_volume",
    "player_rate",
)

@dataclass
class AccessibilityAuditResult:
    checked: int = 0
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def report(self) -> str:
        lines = [
            "OK" if self.ok else "FAILED",
            f"checked={self.checked}",
            f"issues={len(self.issues)}",
        ]
        lines.extend(f"issue={issue}" for issue in self.issues)
        return "\n".join(lines) + "\n"


def audit_accessibility_window(window: QWidget) -> AccessibilityAuditResult:
    result = AccessibilityAuditResult()
    widgets = [window, *window.findChildren(QWidget)]
    by_id: dict[str, list[QWidget]] = {}
    for widget in widgets:
        identifier = str(widget.objectName() or "").strip()
        if identifier:
            by_id.setdefault(identifier, []).append(widget)

    for identifier in REQUIRED_ACCESSIBLE_IDS:
        matches = by_id.get(identifier, [])
        result.checked += 1
        if not matches:
            result.issues.append(f"missing widget id: {identifier}")
            continue
        if len(matches) > 1:
            result.issues.append(f"duplicate widget id: {identifier} ({len(matches)})")
            continue
        widget = matches[0]
        if not str(widget.accessibleName() or "").strip():
            result.issues.append(f"empty accessible name: {identifier}")

    for identifier in FOCUSABLE_ACCESSIBLE_IDS:
        matches = by_id.get(identifier, [])
        if len(matches) != 1:
            continue
        widget = matches[0]
        if widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
            result.issues.append(f"not keyboard focusable: {identifier}")
        if not str(widget.accessibleDescription() or "").strip():
            result.issues.append(f"empty accessible description: {identifier}")

    return result


__all__ = [
    "AccessibilityAuditResult",
    "DYNAMIC_ACCESSIBLE_IDS",
    "FOCUSABLE_ACCESSIBLE_IDS",
    "REQUIRED_ACCESSIBLE_IDS",
    "audit_accessibility_window",
]
