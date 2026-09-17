from __future__ import annotations

"""Strict full user-capability audit for retiring the legacy Tk UI.

This module intentionally does not import PySide6.  It validates the frozen
legacy capability inventory against concrete Qt/backend source evidence.  The
release gate may retire the old UI only when every capability passes.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audioknigi.qt.full_parity import FULL_PARITY_ITEMS
from tools.source_bundle import read_source_bundle, source_paths


QT_EVIDENCE = {
    "first_run": [("audioknigi/qt/onboarding.py", "class QtFirstRunWizard"), ("audioknigi/qt/main_window.py", "maybe_show_first_run_wizard")],
    "language": [("audioknigi/qt/main_window.py", "language_combo"), ("audioknigi/i18n.py", '"de":'), ("audioknigi/i18n.py", '"en":')],
    "easy_mode": [("audioknigi/qt/main_window.py", "_build_easy_page"), ("audioknigi/qt/main_window.py", "ui_mode_easy")],
    "advanced_mode": [("audioknigi/qt/main_window.py", "main_tabs"), ("audioknigi/qt/main_window.py", "ui_mode_advanced")],
    "universal_input": [("audioknigi/qt/main_window.py", "easy_universal_action"), ("audioknigi/qt/main_window.py", "Название, автор или ссылка")],
    "url_drag_drop": [("audioknigi/qt/main_window.py", "def dropEvent"), ("audioknigi/qt/main_window.py", 'suffix.lower() == ".url"')],
    "clipboard": [("audioknigi/qt/main_window.py", "_application_state_changed"), ("audioknigi/qt/main_window.py", "clipboard_auto_check")],
    "search": [("audioknigi/qt/workers.py", "search_all_sources"), ("audioknigi/qt/main_window.py", "def start_search")],
    "search_actions": [("audioknigi/qt/main_window.py", "_show_search_context_menu"), ("audioknigi/qt/main_window.py", "copy_selected_url")],
    "search_availability": [("audioknigi/qt/search_model.py", '("Статус", "availability")')],
    "analysis": [("audioknigi/qt/workers.py", "BookAnalysisService"), ("audioknigi/qt/main_window.py", "def start_analysis")],
    "book_metadata": [("audioknigi/qt/main_window.py", "book_description"), ("audioknigi/qt/main_window.py", "effective_track_duration")],
    "cover": [("audioknigi/qt/main_window.py", "book_cover_label"), ("audioknigi/qt/main_window.py", "loadFromData")],
    "narrations": [("audioknigi/qt/main_window.py", "narration_combo"), ("audioknigi/qt/main_window.py", "select_first_available_narration")],
    "track_columns": [("audioknigi/qt/track_model.py", '"Начало"'), ("audioknigi/qt/track_model.py", '"Конец"'), ("audioknigi/qt/track_model.py", '"Источник"')],
    "hide_source": [("audioknigi/qt/main_window.py", "hide_source_check"), ("audioknigi/qt/main_window.py", "setColumnHidden")],
    "track_actions": [("audioknigi/qt/main_window.py", "_show_track_context_menu"), ("audioknigi/qt/main_window.py", "download_selected_track_only")],
    "download_all": [("audioknigi/qt/main_window.py", "def start_download_all"), ("audioknigi/qt/main_window.py", "download_all_button")],
    "download_selected": [("audioknigi/qt/main_window.py", "def start_download"), ("audioknigi/qt/main_window.py", "selected_indices")],
    "full_mp3": [("audioknigi/qt/main_window.py", "start_full_mp3"), ("audioknigi/download_engine.py", "download_full_mp3")],
    "duplicate_preflight": [("audioknigi/qt/main_window.py", "duplicate_preflight(request, probe_durations=False)"), ("audioknigi/download_engine.py", "class DuplicatePreflight")],
    "resume": [("audioknigi/qt/main_window.py", "continue_unfinished"), ("audioknigi/services/library_service.py", "scan_unfinished")],
    "disk_space": [("audioknigi/downloader.py", "def _check_disk_space")],
    "progress": [("audioknigi/qt/main_window.py", "download_progress"), ("audioknigi/qt/main_window.py", "download_stage_label")],
    "speed_graph": [("audioknigi/qt/speed_graph.py", "class SpeedGraphWidget"), ("audioknigi/qt/main_window.py", "speed_graph.add_speed")],
    "session_log": [("audioknigi/qt/main_window.py", "session_log"), ("audioknigi/qt/main_window.py", "worker.log.connect")],
    "quality": [("audioknigi/qt/main_window.py", "easy_quality_combo"), ("audioknigi/qt/main_window.py", "quality_combo")],
    "download_settings": [("audioknigi/qt/main_window.py", "segment_count_combo"), ("audioknigi/qt/main_window.py", "normalization_combo"), ("audioknigi/qt/main_window.py", "bandwidth_spin")],
    "templates": [("audioknigi/qt/main_window.py", "folder_template_edit"), ("audioknigi/qt/main_window.py", "track_template_edit")],
    "audiobookshelf": [("audioknigi/qt/main_window.py", "test_audiobookshelf"), ("audioknigi/integrations.py", "audiobookshelf_get_libraries")],
    "event_sounds": [("audioknigi/qt/event_sounds.py", "QMediaPlayer"), ("audioknigi/qt/main_window.py", "_play_event_sound")],
    "event_sound_settings": [("audioknigi/qt/main_window_pages.py", "event_sounds_check"), ("audioknigi/qt/main_window_pages.py", "event_sound_volume_slider"), ("audioknigi/qt/main_window_pages.py", "preview_event_sound")],
    "theme": [("audioknigi/qt/theme.py", "def apply_theme"), ("audioknigi/qt/main_window.py", "theme_combo")],
    "scale": [("audioknigi/qt/application.py", 'settings.get("scale"'), ("audioknigi/qt/main_window.py", "scale_spin")],
    "large_mode": [("audioknigi/qt/main_window.py", "large_mode_check"), ("audioknigi/qt/application.py", 'settings.get("large_mode"')],
    "geometry": [("audioknigi/qt/main_window.py", "restoreGeometry"), ("audioknigi/qt/main_window.py", "saveGeometry")],
    "queue": [("audioknigi/services/queue_service.py", "class QueueStore"), ("audioknigi/qt/main_window.py", "_build_queue_tab")],
    "queue_add": [("audioknigi/qt/main_window.py", "add_current_to_queue"), ("audioknigi/qt/main_window.py", "_queue_urls_dropped")],
    "queue_pause": [("audioknigi/qt/main_window.py", "pause_queue_current"), ("audioknigi/qt/main_window.py", "toggle_queue_item_pause")],
    "queue_retry": [("audioknigi/qt/main_window.py", "retry_queue_selected"), ("audioknigi/qt/main_window.py", "retry_all_failed")],
    "queue_priority": [("audioknigi/qt/main_window.py", "toggle_queue_priority")],
    "queue_reorder_buttons": [("audioknigi/qt/main_window.py", "move_queue_selected")],
    "queue_reorder_drag": [("audioknigi/qt/workers.py", "rowsReordered"), ("audioknigi/qt/main_window.py", "_queue_drag_reordered")],
    "queue_columns": [("audioknigi/qt/main_window.py", '"Обложка", "№", "Книга", "Статус", "Пауза"'), ("audioknigi/qt/main_window.py", '"URL"')],
    "history": [("audioknigi/qt/main_window.py", "history_redownload"), ("audioknigi/qt/main_window.py", "history_delete"), ("audioknigi/qt/main_window.py", "history_clear")],
    "history_cover": [("audioknigi/qt/main_window.py", 'item.get("cover_file"'), ("audioknigi/qt/main_window.py", "setIcon")],
    "history_export": [("audioknigi/qt/main_window.py", "export_library"), ("audioknigi/services/library_service.py", "export_history")],
    "backup": [("audioknigi/qt/main_window.py", "create_backup"), ("audioknigi/qt/main_window.py", "restore_backup")],
    "player": [("audioknigi/qt/player_controller.py", "class QtPlayerController"), ("audioknigi/qt/main_window.py", "player_seek_slider")],
    "last_completed": [("audioknigi/qt/main_window.py", "open_last_completed_folder"), ("audioknigi/qt/main_window.py", "listen_last_completed_book")],
    "tray": [("audioknigi/qt/tray_controller.py", "QSystemTrayIcon"), ("audioknigi/qt/main_window.py", "hide_to_tray")],
    "help": [("audioknigi/qt/help_center.py", "class QtHelpCenter"), ("audioknigi/qt/main_window.py", "show_context_help")],
    "crash_report": [("audioknigi/qt/application.py", "build_report"), ("audioknigi/qt/main_window.py", "copy_last_crash_report")],
    "screen_reader_test": [("audioknigi/qt/accessibility_audit.py", "audit_accessibility_window"), ("audioknigi/qt/main_window.py", "Ctrl+Shift+F12")],
    "hotkeys": [("audioknigi/qt/main_window.py", 'QKeySequence(f"Alt+{number}")'), ("audioknigi/qt/main_window.py", "QTabWidget already implements Ctrl+Tab"), ("audioknigi/qt/main_window.py", 'QKeySequence("Shift+F10")')],
    "dependencies": [("audioknigi/qt/main_window.py", "_dependency_status_text"), ("audioknigi/qt/main_window.py", "resolve_executable")],
    "safe_shutdown": [("audioknigi/qt/main_window.py", "def closeEvent"), ("audioknigi/qt/main_window.py", "Скачивание выполняется"), ("audioknigi/qt/main_window.py", "Анализ выполняется")],
    "modal_dialogs": [("audioknigi/qt/main_window.py", "ApplicationModal"), ("audioknigi/qt/main_window.py", "setModal(True)")],
    "context_menus": [("audioknigi/qt/main_window.py", "_show_search_context_menu"), ("audioknigi/qt/main_window.py", "_show_track_context_menu")],
    "output_actions": [("audioknigi/qt/main_window.py", "open_output_folder"), ("audioknigi/qt/main_window.py", "open_last_completed_folder")],
    "completion_notifications": [("audioknigi/qt/main_window.py", "download_complete"), ("audioknigi/qt/main_window.py", "_notify_tray_if_hidden")],
}

LEGACY_UI_PATHS = (
    "audioknigi_gui.py",
    "audioknigi/app.py",
    "audioknigi/actions.py",
    "audioknigi/accessibility.py",
    "audioknigi/dnd.py",
    "audioknigi/help_center.py",
    "audioknigi/onboarding.py",
    "audioknigi/player.py",
    "audioknigi/queue_manager.py",
    "audioknigi/search.py",
    "audioknigi/storage.py",
    "audioknigi/tray.py",
    "audioknigi/ui_kit.py",
    "audioknigi/event_sounds.py",
    "audioknigi/event_bus.py",
    "audioknigi/library_visuals.py",
    "audioknigi/notifications.py",
    "audioknigi/ui_state.py",
    "audioknigi/visuals.py",
    "audioknigi/ui",
)


def audit(root: Path, *, require_legacy_retired: bool = False) -> dict:
    root = Path(root)
    declared = {item.key for item in FULL_PARITY_ITEMS}
    evidence_keys = set(QT_EVIDENCE)
    issues: list[str] = []
    if declared != evidence_keys:
        issues.append("manifest/evidence key mismatch: missing=" + ",".join(sorted(declared - evidence_keys)) + "; extra=" + ",".join(sorted(evidence_keys - declared)))
    passed = []
    for item in FULL_PARITY_ITEMS:
        failures = []
        for rel, marker in QT_EVIDENCE.get(item.key, []):
            bundle_paths = source_paths(root, rel)
            if not any(path.is_file() for path in bundle_paths):
                failures.append(f"missing source bundle {rel}")
                continue
            try:
                source = read_source_bundle(root, rel)
            except Exception as exc:
                failures.append(f"cannot read {rel}: {exc}")
                continue
            if marker not in source:
                failures.append(f"missing marker {marker!r} in {rel}")
        if failures:
            issues.append(f"{item.key}: " + "; ".join(failures))
        else:
            passed.append(item.key)
    legacy_present = [rel for rel in LEGACY_UI_PATHS if (root / rel).exists()]
    if require_legacy_retired and legacy_present:
        issues.append("legacy UI still present: " + ", ".join(legacy_present))
    return {
        "ok": not issues,
        "total": len(FULL_PARITY_ITEMS),
        "passed": len(passed),
        "passed_keys": passed,
        "issues": issues,
        "legacy_ui_present": legacy_present,
        "legacy_retired_required": bool(require_legacy_retired),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--require-legacy-retired", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = audit(Path(args.root), require_legacy_retired=args.require_legacy_retired)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"FULL PARITY: {'PASS' if result['ok'] else 'FAIL'} {result['passed']}/{result['total']}")
        for issue in result["issues"]:
            print(" -", issue)
        if result["legacy_ui_present"]:
            print("legacy UI present:", ", ".join(result["legacy_ui_present"]))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
