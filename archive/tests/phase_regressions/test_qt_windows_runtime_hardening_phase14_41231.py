from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
QT = ROOT / "audioknigi" / "qt"


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase14_removes_pyside_findchildren_tuple_startup_crash():
    main = text("audioknigi/qt/main_window.py")
    assert "findChildren((QTableView, QTableWidget))" not in main
    assert "self.findChildren(QTableView)" in main


def test_theme_uses_explicit_qstyle_factory_objects():
    theme = text("audioknigi/qt/theme.py")
    assert "QStyleFactory" in theme
    assert 'QStyleFactory.create("Fusion")' in theme
    assert "QApplication.setStyle(fusion)" in theme
    assert 'QApplication.setStyle("Fusion")' not in theme
    assert "QApplication.setStyle(_SYSTEM_STYLE_NAME)" not in theme


def test_accessible_announcement_assertive_mode_has_binding_fallback():
    accessibility = text("audioknigi/qt/accessibility.py")
    assert 'getattr(QAccessible, "AnnouncementPoliteness", None)' in accessibility
    assert 'getattr(politeness_enum, "Assertive", None)' in accessibility
    assert "except (AttributeError, TypeError):" in accessibility


def test_missing_media_cancel_closes_modal_and_unblocks_worker():
    main = text("audioknigi/qt/main_window.py")
    for needle in (
        'prompt.resolve("stop")',
        "self._active_missing_prompt",
        "self._active_missing_box",
        "cancel_watch = QTimer(box)",
        "box.reject()",
        "def _request_download_cancel(self)",
    ):
        assert needle in main


def test_queue_clear_drops_stale_selection_before_model_reset():
    main = text("audioknigi/qt/main_window.py")
    clear = main[main.index("    def clear_queue(self):"):main.index("    @Slot()\n    def start_queue", main.index("    def clear_queue(self):"))]
    assert clear.index("self.queue_table.clearSelection()") < clear.index("self.queue_tasks.clear()")
    assert "self.queue_table.setCurrentCell(-1, -1)" in clear
    assert "selection_model = self.queue_table.selectionModel()" in main


def test_keyboard_seek_updates_label_and_commits_position():
    player = text("audioknigi/qt/player_mixin.py")
    block = player[player.index("    def _player_seek_preview"):player.index("    @Slot(int)\n    def _player_volume_changed", player.index("    def _player_seek_preview"))]
    assert "self.player_time_label.setText" in block
    assert "self.player_seek_slider.hasFocus()" in block
    assert "self.player_controller.seek(int(value) * 1000)" in block


def test_player_stop_does_not_race_zero_timer_seek():
    controller = text("audioknigi/qt/player_controller.py")
    stop = controller[controller.index("    def stop(self)"):controller.index("    def seek(self", controller.index("    def stop(self)"))]
    play = controller[controller.index("    def play(self)"):controller.index("    def pause(self)", controller.index("    def play(self)"))]
    assert "QTimer.singleShot(0" not in stop
    assert "self._resume_after_stop_ms" in stop
    assert "self.player.setPosition(self._resume_after_stop_ms)" in play


def test_settings_fields_are_not_reassigned_after_update_dict():
    main = text("audioknigi/qt/main_window.py")
    block = main[main.index("    def _settings_from_ui"):main.index("    def _save_settings", main.index("    def _settings_from_ui"))]
    for key in ("player_volume", "player_rate", "minimize_to_tray"):
        assert block.count(f'"{key}"') == 1
        assert f'updated["{key}"]' not in block


def test_dynamic_modal_accessibility_ids_have_explicit_contract():
    audit = text("audioknigi/qt/accessibility_audit.py")
    assert "DYNAMIC_ACCESSIBLE_IDS" in audit
    for identifier in ("missing_media_dialog", "missing_media_stop", "missing_media_skip"):
        assert f'"{identifier}"' in audit


def test_playwright_analysis_locals_are_initialized_and_guarded():
    analysis = text("audioknigi/services/book_analysis_service.py")
    for needle in (
        'html_text = ""',
        'page_title = ""',
        'playlist_url = ""',
        "playlist_response = None",
        'raise SiteStructureChanged("Playwright не получил плейлист")',
        "context.close()",
    ):
        assert needle in analysis


def test_track_model_accepts_checkstate_and_editrole_checkbox_values():
    model = text("audioknigi/qt/track_model.py")
    assert "role not in (Qt.ItemDataRole.CheckStateRole, Qt.ItemDataRole.EditRole)" in model
    assert "isinstance(value, bool)" in model
    assert "isinstance(value, Qt.CheckState)" in model


def test_windows_build_runs_full_window_selftest_before_pyinstaller():
    build = text("build_qt_ci.ps1")
    preflight = build.index('Source Qt window/accessibility preflight (offscreen)')
    pyinstaller = build.index('"-m", "PyInstaller"')
    assert preflight < pyinstaller
    assert '& $PythonExe "audioknigi_qt.py" "--qt-accessibility-selftest"' in build
