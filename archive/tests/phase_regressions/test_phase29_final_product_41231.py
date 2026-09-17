from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

from audioknigi.i18n import localize_runtime_text

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_first_run_is_one_compact_dialog_before_main_window():
    onboarding = text("audioknigi/qt/onboarding.py")
    app = text("audioknigi/qt/application.py")
    assert "class QtFirstRunWizard(QDialog):" in onboarding
    assert "QWizard" not in onboarding
    for ident in ("wizard_language", "wizard_output_dir", "wizard_quality", "wizard_ui_mode", "wizard_finish"):
        assert f'identifier="{ident}"' in onboarding
    assert '"start": "Сохранить и начать"' in onboarding
    assert app.index("QtFirstRunWizard(None") < app.index("window = AudioKnigiQtWindow()")


def test_product_ui_has_four_settings_sections_and_empty_states():
    main = text("audioknigi/qt/main_window.py") + "\n" + text("audioknigi/qt/main_window_pages.py")
    player = text("audioknigi/qt/player_mixin.py")
    assert '("Основные", "Загрузка и сеть", "Внешний вид и звук", "Интеграции и резервная копия")' in main
    for ident in ("easy_empty_state", "book_empty_state", "search_empty_state", "queue_empty_state", "history_empty_state"):
        assert f'identifier="{ident}"' in main
    assert 'self.player_play_button.setProperty("role", "primary")' in player
    assert 'self.player_play_button.setMinimumHeight(44)' in player


def test_history_destructive_actions_are_context_menu_only_visually():
    main = text("audioknigi/qt/main_window.py")
    history_builder = main[main.index("def _build_history_tab"):main.index("def _show_history_context_menu")]
    assert "history_redownload_button" not in history_builder
    assert "history_delete_button" not in history_builder
    context = main[main.index("def _show_history_context_menu"):main.index("def _set_combo_data")]
    assert 'menu.addAction(self._l("Скачать заново"))' in context
    assert 'menu.addAction(self._l("Удалить запись"))' in context
    assert 'redownload_action.setObjectName("history_redownload")' in context
    assert 'delete_action.setObjectName("history_delete")' in context


def test_accessibility_contract_requires_descriptions_and_new_grouped_controls():
    audit = text("audioknigi/qt/accessibility_audit.py")
    accessibility = text("audioknigi/qt/accessibility.py")
    assert "empty accessible description" in audit
    assert '"easy_open_listen"' in audit
    for ident in ("book_empty_state", "search_empty_state", "queue_empty_state", "history_empty_state", "player_chapters"):
        assert f'"{ident}"' in audit
    assert "_default_accessible_description" in accessibility
    assert "_fallback_accessible_name" in accessibility
    assert "def ensure_accessibility_tree(root: QWidget)" in accessibility
    assert "ensure_accessibility_tree(self)" in text("audioknigi/qt/main_window.py")
    assert "ensure_accessibility_tree(self)" in text("audioknigi/qt/onboarding.py")


def test_error_log_is_always_created_and_included_in_support_report():
    logging_src = text("audioknigi/logging_utils.py")
    crash_src = text("audioknigi/crash_report.py")
    main = text("audioknigi/qt/main_window.py")
    assert 'ERROR_LOG_FILE = APP_DIR / "errors.log"' in logging_src
    assert "ERROR_LOG_FILE.touch(exist_ok=True)" in logging_src
    assert "error_handler.setLevel(logging.ERROR)" in logging_src
    assert "tail_error_log" in logging_src
    assert 'app_logger.error("CRASH | component=%s' in crash_src
    assert "exc_info=(exc_type, exc, tb)" in crash_src
    assert "tail_error_log(200)" in main
    assert "def open_error_log(self)" in main


def test_all_fixed_user_statuses_have_non_russian_localization():
    values: set[str] = set()
    for rel in ("audioknigi/qt/main_window.py", "audioknigi/downloader.py", "audioknigi/download_engine.py"):
        tree = ast.parse(text(rel))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "set_status" or not node.args:
                continue
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and re.search(r"[А-Яа-яЁё]", arg.value):
                values.add(arg.value)
    assert values
    for language in ("uk", "de", "en"):
        for source in values:
            assert localize_runtime_text(language, source) != source, (language, source)


def test_static_qt_localization_audit_passes_without_qt_runtime():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "qt_localization_audit.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "static_ui_literals=translated" in proc.stdout
    assert "help_topics=complete" in proc.stdout
    assert "onboarding=complete" in proc.stdout
    assert "accessible_names=translated" in proc.stdout


def test_fps_overlay_is_not_part_of_application_source():
    for rel in ("audioknigi/qt/main_window.py", "audioknigi/qt/application.py", "audioknigi/qt/theme.py"):
        assert "FPS 0" not in text(rel)
