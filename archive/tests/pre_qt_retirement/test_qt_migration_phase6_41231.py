from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QT_DIR = ROOT / "audioknigi" / "qt"


def test_qt_tray_controller_is_native_and_has_no_legacy_tray_dependencies():
    text = (QT_DIR / "tray_controller.py").read_text(encoding="utf-8")
    for needle in (
        "QSystemTrayIcon",
        "QMenu",
        'QAction("Показать окно"',
        'QAction("Скрыть в трей"',
        'QAction("Открыть плеер"',
        'QAction("Открыть очередь"',
        'QAction("Выход"',
        "QSystemTrayIcon.isSystemTrayAvailable()",
        "showMessage(",
    ):
        assert needle in text
    for forbidden in ("pystray", "tkinter", "ttkbootstrap", "ui_kit"):
        assert forbidden not in text


def test_qt_main_window_wires_tray_restore_sections_and_exit_path():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    for needle in (
        "QtTrayController(self)",
        "self.tray_controller.start()",
        "def hide_to_tray(self):",
        "def restore_from_tray(self):",
        "def show_player_from_tray(self):",
        "def show_queue_from_tray(self):",
        "def request_exit(self):",
        "self._exit_requested = True",
        "self.tray_controller.shutdown()",
        "def changeEvent(self, event):",
    ):
        assert needle in text


def test_auto_tray_is_limited_to_long_download_or_queue_activity():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    assert "def _long_operation_active(self) -> bool:" in text
    assert "self._download_thread is not None and self._download_thread.isRunning()" in text
    assert "self._queue_running" in text
    assert "def _should_auto_tray(self) -> bool:" in text
    assert "if not self._exit_requested and self._should_auto_tray():" in text


def test_required_missing_media_prompt_restores_hidden_window():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    start = text.index("def _resolve_missing_media")
    end = text.index("def _download_finished", start)
    block = text[start:end]
    assert "if not self.isVisible() and self._tray_available():" in block
    assert "self.restore_from_tray()" in block


def test_qt_tray_setting_is_enabled_when_available_and_persisted():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    assert 'tray_available = self.tray_controller.available' in text
    assert 'self.minimize_to_tray_check.setEnabled(tray_available)' in text
    assert 'updated["minimize_to_tray"] = bool(self.minimize_to_tray_check.isChecked())' in text


def test_qt_requirements_no_longer_inherit_legacy_tk_player_or_pystray_stack():
    text = (ROOT / "requirements-qt.txt").read_text(encoding="utf-8")
    assert "PySide6>=6.8,<7" in text
    assert "-r requirements.txt" not in text
    for forbidden in ("pygame", "ttkbootstrap", "pystray", "tkinterdnd2", "prismatoid", "tk-uia"):
        assert forbidden not in text.lower()


def test_qt_frozen_build_excludes_legacy_pystray_and_tk_stack():
    bat = (ROOT / "build_qt_exe.bat").read_text(encoding="utf-8")
    ps = (ROOT / "build_qt_ci.ps1").read_text(encoding="utf-8")
    assert "from PySide6.QtWidgets import QSystemTrayIcon" in bat
    for module in ("pystray", "tkinter", "ttkbootstrap", "pygame"):
        assert f'"--exclude-module", "{module}"' in ps


def test_migration_stage_is_phase6_or_later():
    text = (QT_DIR / "__init__.py").read_text(encoding="utf-8")
    import re
    match = re.search(r'QT_MIGRATION_STAGE = "phase-(\d+)"', text)
    assert match and int(match.group(1)) >= 6
