from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from tools import qt_windows_acceptance
from tools.undefined_global_audit import _SPECIAL_GLOBALS

ROOT = Path(__file__).resolve().parents[2]


def test_accessibility_selftest_failure_reports_details_not_partial_report():
    source = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")
    marker = 'except Exception:\n        details = "FAILED\\n" + traceback.format_exc()'
    start = source.index(marker, source.index("def _qt_accessibility_selftest"))
    end = source.index("    finally:", start)
    block = source[start:end]
    assert "_write_report(env_name, filename, details)" in block
    assert "_write_report(env_name, filename, report)" not in block


def test_acceptance_gate_accepts_bom_prefixed_ok_report(tmp_path, monkeypatch):
    output = tmp_path / "gate.txt"

    def fake_run(*args, **kwargs):
        output.write_text("\ufeffOK\nvalidated\n", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(qt_windows_acceptance.subprocess, "run", fake_run)
    result = qt_windows_acceptance._run_gate(
        tmp_path / "dummy.exe",
        "--qt-runtime-selftest",
        "AUDIOKNIGI_QT_RUNTIME_SELFTEST_REPORT",
        output,
    )
    assert result["status"] == "pass"
    assert result["report_ok"] is True


def test_undefined_global_gate_is_portable_for_windows_error_alias():
    assert "WindowsError" in _SPECIAL_GLOBALS


def test_ukrainian_legacy_literals_cover_common_search_and_book_prompts():
    literals = json.loads(
        (ROOT / "audioknigi" / "locales" / "legacy_literals.json").read_text(encoding="utf-8")
    )
    uk = literals["uk"]
    expected = {
        "Ничего не найдено.": "Нічого не знайдено.",
        "Сначала выберите книгу в результатах поиска.": "Спочатку оберіть книгу в результатах пошуку.",
        "Сначала выберите часть книги.": "Спочатку оберіть частину книги.",
        "Сначала проанализируйте книгу.": "Спочатку проаналізуйте книгу.",
    }
    for key, value in expected.items():
        assert uk.get(key) == value


def test_release_baseline_comment_and_runtime_stage_are_current():
    release = (ROOT / "requirements-release.txt").read_text(encoding="utf-8")
    qt_init = (ROOT / "audioknigi" / "qt" / "__init__.py").read_text(encoding="utf-8")
    assert "Verified published release baseline for 2026-09-15" in release
    assert 'QT_RUNTIME_STAGE = "qt-only-4.12.42"' in qt_init
