from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
QT_DIR = ROOT / "audioknigi" / "qt"


def test_phase8_uses_debounced_native_announcements_without_focus_hooks():
    text = (QT_DIR / "accessibility.py").read_text(encoding="utf-8")
    for needle in (
        "QAccessibleAnnouncementEvent",
        "class AccessibleAnnouncer",
        "self._timer.setSingleShot(True)",
        "self._timer.start(self.polite_delay_ms)",
        "if assertive:",
        "class AccessibleAnnouncer(QObject)",
        "def focus_table_row(",
        "view.setCurrentIndex(index)",
    ):
        assert needle in text
    for forbidden in ("FocusIn", "focusInEvent", "installEventFilter", "eventFilter("):
        assert forbidden not in text


def test_search_and_track_models_expose_accessible_cell_text():
    tracks = (QT_DIR / "track_model.py").read_text(encoding="utf-8")
    search = (QT_DIR / "search_model.py").read_text(encoding="utf-8")
    assert "Qt.ItemDataRole.AccessibleTextRole" in tracks
    assert '"Скачать: выбрано"' in tracks
    assert '"Скачать: не выбрано"' in tracks
    assert "Qt.ItemDataRole.AccessibleTextRole" in search
    assert 'return f"{label}: {value or \'нет данных\'}"' in search


def test_tables_receive_current_rows_before_focus_after_explicit_operations():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    assert "focus_table_row(self.track_table, 0, column=0, focus=True)" in text
    assert "focus_table_row(self.search_table, 0, column=1, focus=True)" in text
    assert "focus_table_row(self.queue_table, len(self.queue_tasks) - 1, column=1, focus=True)" in text


def test_keyboard_only_track_toggle_and_search_activation_are_wired():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    for needle in (
        'QShortcut(QKeySequence("Space"), self.track_table',
        "self._toggle_current_track_from_keyboard",
        'QShortcut(QKeySequence("Return"), self.search_table',
        'QShortcut(QKeySequence("Enter"), self.search_table',
        "self.use_selected_result",
        "Qt.ShortcutContext.WidgetWithChildrenShortcut",
    ):
        assert needle in text


def test_player_seek_value_is_screen_reader_friendly_seconds_not_milliseconds():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    assert "self.player_seek_slider.setSingleStep(5)" in text
    assert "self.player_seek_slider.setPageStep(30)" in text
    assert "self.player_controller.seek(self.player_seek_slider.value() * 1000)" in text
    assert "position_seconds = max(0, int(round(position / 1000.0)))" in text
    assert "duration_seconds = max(0, int(round(duration / 1000.0)))" in text
    assert "Значение задаётся в секундах" in text


def test_dynamic_player_action_and_missing_media_modal_have_accessible_semantics():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    assert 'setAccessibleName("Пауза воспроизведения" if playing else "Воспроизвести")' in text
    assert 'identifier="missing_media_stop"' in text
    assert 'identifier="missing_media_skip"' in text
    assert "box.setEscapeButton(stop_button)" in text


def test_queue_and_history_cells_publish_header_value_accessible_text():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    assert "row_summary = self._queue_row_summary(row)" in text
    assert ('accessible_text = row_summary if col == 1 else f"{headers[col]}: {value}"' in text or "accessible_text = row_summary if col == 2 else f\"{headers[col]}: {value or 'нет'}\"" in text)
    assert "row_summary = self._history_row_summary(row)" in text
    assert ('accessible_text = row_summary if col == 1 else' in text or 'accessible_text = row_summary if col == 2 else' in text)
    assert '"Да" if task.priority else "Нет"' in text
    assert 'task.last_error or "нет"' in text


def test_accessibility_contract_audit_has_required_ids_and_focusability_check():
    text = (QT_DIR / "accessibility_audit.py").read_text(encoding="utf-8")
    for needle in (
        "REQUIRED_ACCESSIBLE_IDS",
        "FOCUSABLE_ACCESSIBLE_IDS",
        '"book_tracks"',
        '"search_results"',
        '"queue_table"',
        '"player_seek"',
        "widget.accessibleName()",
        "Qt.FocusPolicy.NoFocus",
        "duplicate widget id",
    ):
        assert needle in text
    for forbidden in ("tkinter", "ttkbootstrap", "pygame", "pystray"):
        assert forbidden not in text.lower()


def test_frozen_accessibility_selftest_is_part_of_entrypoint_and_build_gate():
    entry = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")
    build = (ROOT / "build_qt_ci.ps1").read_text(encoding="utf-8")
    for needle in (
        '"--qt-accessibility-selftest"',
        "AUDIOKNIGI_QT_ACCESSIBILITY_SELFTEST_REPORT",
        "qt_accessibility_frozen_selftest.txt",
        "audit_accessibility_window(window)",
        'os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")',
    ):
        assert needle in entry
    for needle in (
        "Frozen Qt accessibility contract self-test",
        "--qt-accessibility-selftest",
        "qt_accessibility_frozen_selftest.txt",
        "AUDIOKNIGI_QT_ACCESSIBILITY_SELFTEST_REPORT",
    ):
        assert needle in build


def test_accessibility_help_is_discoverable_and_no_manual_focusin_layer_returns():
    text = (QT_DIR / "main_window.py").read_text(encoding="utf-8")
    assert 'QAction("Доступность и горячие клавиши…", self)' in text
    assert 'accessibility_help.setShortcut(QKeySequence("F1"))' in text
    assert "Tab и Shift+Tab используют штатный порядок фокуса Qt" in text
    assert "не устанавливает собственные перехватчики событий фокуса" in text


def test_migration_stage_is_phase8():
    text = (QT_DIR / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'QT_MIGRATION_STAGE = "phase-(\d+)"', text)
    assert match and int(match.group(1)) >= 8
