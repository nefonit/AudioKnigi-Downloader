"""Regression tests for confirmed Round 90 audit findings."""

import json

from audioknigi.brand import DISPLAY_NAME
from audioknigi.config.settings import save_app_settings
from audioknigi.crash_report import crash_report_is_current, read_current_crash_report
from audioknigi.logging_utils import sanitize_log_text
from audioknigi.metadata import APP_VERSION


def test_crash_report_accepts_string_path(tmp_path):
    report = tmp_path / "last_crash_report.txt"
    report.write_text(f"{DISPLAY_NAME} {APP_VERSION}\nTraceback detail\n", encoding="utf-8")
    assert crash_report_is_current(str(report))
    assert "Traceback detail" in read_current_crash_report(str(report))


def test_log_secret_redaction_hides_quoted_spaces():
    sanitized = sanitize_log_text('{"password": "my secret phrase", "token": "abc def"}')
    assert "my secret phrase" not in sanitized
    assert "abc def" not in sanitized
    assert "<hidden>" in sanitized


def test_partial_settings_save_does_not_complete_onboarding(tmp_path):
    path = tmp_path / "settings.json"
    assert save_app_settings({"language": "ru"}, path=path)
    assert json.loads(path.read_text(encoding="utf-8"))["first_run_complete"] is False
    assert save_app_settings({"language": "de"}, path=path)
    assert json.loads(path.read_text(encoding="utf-8"))["first_run_complete"] is False
