from __future__ import annotations

from pathlib import Path

from audioknigi.qt import QT_MIGRATION_STAGE

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "audioknigi" / "qt" / "main_window.py"
RUNNER = ROOT / "tools" / "qt_windows_acceptance.py"


def test_phase11_stage_and_live_nvda_feedback_are_explicit():
    assert int(QT_MIGRATION_STAGE.removeprefix("phase-")) >= 11
    text = MAIN.read_text(encoding="utf-8")
    for needle in (
        "def _wire_live_accessibility_feedback",
        "combo.textHighlighted.connect",
        "combo.textActivated.connect",
        "def _announce_combo_value",
        "def _announce_player_volume",
        "def _announce_player_seek_value",
        "Позиция {seconds} секунд",
        "Громкость {int(value)} процентов",
    ):
        assert needle in text
    for forbidden in ("FocusIn", "focusInEvent", "installEventFilter", "eventFilter("):
        assert forbidden not in text


def test_phase11_queue_and_history_have_whole_row_screen_reader_summaries():
    text = MAIN.read_text(encoding="utf-8")
    for needle in (
        "def _queue_row_summary",
        "def _history_row_summary",
        "AccessibleDescriptionRole",
        "self._update_queue_action_states()",
        "self._update_history_action_states()",
        '"Снять приоритет с выбранной задачи" if task.priority else "Назначить приоритет выбранной задаче"',
    ):
        assert needle in text


def test_phase11_settings_scroll_wrapper_does_not_take_tab_focus():
    text = MAIN.read_text(encoding="utf-8")
    assert "scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)" in text
    assert 'identifier="settings_scroll"' in text


def test_phase11_message_boxes_are_explicit_application_modal_and_escape_safe():
    text = MAIN.read_text(encoding="utf-8")
    for needle in (
        "def _show_message",
        "def _ask_yes_no",
        "box.setWindowModality(Qt.WindowModality.ApplicationModal)",
        "box.setModal(True)",
        "box.setEscapeButton(QMessageBox.StandardButton.No)",
        'identifier="modal_yes"',
        'identifier="modal_no"',
        'identifier="missing_media_dialog"',
    ):
        assert needle in text
    for forbidden in (
        "QMessageBox.question(",
        "QMessageBox.information(",
        "QMessageBox.warning(",
        "QMessageBox.critical(",
    ):
        assert forbidden not in text


def test_phase11_acceptance_runner_resumes_only_failed_checks_and_records_details():
    text = RUNNER.read_text(encoding="utf-8")
    for needle in (
        "def _manual_status",
        "Повторяем только непройденные пункты",
        "if check.key not in pending_keys",
        "Кратко опишите проблему",
        'parser.add_argument("--retest-all"',
        "except KeyboardInterrupt:",
        "Уже введённые результаты сохранены",
        "retest_all=args.retest_all",
    ):
        assert needle in text
    bat = (ROOT / "run_qt_acceptance.bat").read_text(encoding="utf-8")
    assert "%*" in bat
