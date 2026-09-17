from __future__ import annotations

import json
from pathlib import Path

from audioknigi.qt import QT_MIGRATION_STAGE
from audioknigi.qt.acceptance_contract import ACCEPTANCE_SCHEMA, MANUAL_CHECKS, REQUIRED_AUTOMATED_GATES, REQUIRED_SCREEN_READERS
from audioknigi.qt.promotion_contract import (
    PROMOTION_SCHEMA,
    create_promotion,
    promotion_complete,
    promotion_issues,
    save_promotion,
)

ROOT = Path(__file__).resolve().parents[1]


def _accepted_report(exe_hash: str) -> dict:
    checks = {check.key: "pass" for check in MANUAL_CHECKS if check.required}
    return {
        "schema": ACCEPTANCE_SCHEMA,
        "app_version": __import__("audioknigi.version", fromlist=["__version__"]).__version__,
        "exe_sha256": exe_hash,
        "platform": "windows",
        "automated": {gate: "pass" for gate in REQUIRED_AUTOMATED_GATES},
        "screen_readers": {reader: {"checks": dict(checks)} for reader in REQUIRED_SCREEN_READERS},
    }


def test_phase12_stage_and_safe_launcher_files_exist():
    assert QT_MIGRATION_STAGE in {"phase-12", "phase-13"}
    for name in (
        "run.bat",
        "promote_qt_launcher.bat",
        "rollback_to_legacy.bat",
        "check_default_launcher.bat",
        "PHASE12_NEXT_STEPS.txt",
        "tools/qt_launcher_promotion.py",
        "audioknigi/qt/promotion_contract.py",
    ):
        assert (ROOT / name).is_file(), name


def test_phase12_promotion_requires_exact_accepted_exe_hash(tmp_path: Path):
    exe = tmp_path / "AudioKnigiDownloader_Qt.exe"
    exe.write_bytes(b"accepted qt exe")
    from audioknigi.qt.acceptance_contract import sha256_file

    report = _accepted_report(sha256_file(exe))
    report_path = tmp_path / "qt_windows_acceptance.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    marker = create_promotion(exe_path=exe, acceptance_report_path=report_path, require_windows=True)
    assert marker["schema"] == PROMOTION_SCHEMA
    assert marker["exe_sha256"] == sha256_file(exe)
    assert promotion_complete(marker, report, exe_path=exe, require_windows=True)

    exe.write_bytes(b"rebuilt qt exe")
    assert not promotion_complete(marker, report, exe_path=exe, require_windows=True)
    assert any("SHA-256" in issue for issue in promotion_issues(marker, report, exe_path=exe, require_windows=True))


def test_phase12_promotion_is_blocked_when_jaws_or_nvda_is_not_complete(tmp_path: Path):
    exe = tmp_path / "AudioKnigiDownloader_Qt.exe"
    exe.write_bytes(b"candidate")
    from audioknigi.qt.acceptance_contract import sha256_file

    report = _accepted_report(sha256_file(exe))
    report["screen_readers"]["jaws"]["checks"][MANUAL_CHECKS[0].key] = "fail"
    report_path = tmp_path / "qt_windows_acceptance.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    try:
        create_promotion(exe_path=exe, acceptance_report_path=report_path, require_windows=True)
    except ValueError as exc:
        assert "NVDA/JAWS acceptance" in str(exc)
    else:
        raise AssertionError("promotion unexpectedly succeeded")


def test_phase12_default_run_bat_has_fail_closed_legacy_fallback():
    text = (ROOT / "run.bat").read_text(encoding="utf-8")
    assert "tools\\qt_launcher_promotion.py --status --quiet" in text
    assert "dist\\AudioKnigiDownloader_Qt.exe" in text
    assert "dist\\AudioKnigiDownloader.exe" in text
    assert "audioknigi_gui.py" in text
    assert "if not errorlevel 1" in text


def test_phase12_rollback_only_removes_promotion_marker():
    text = (ROOT / "rollback_to_legacy.bat").read_text(encoding="utf-8")
    assert "qt_launcher_promotion.json" in text
    assert "del /q" in text
    for forbidden in (
        "AudioKnigiDownloader_Qt.exe\" del",
        "qt_windows_acceptance.json\" del",
        "settings.json\" del",
        "history.json\" del",
    ):
        assert forbidden not in text


def test_phase12_promotion_marker_can_be_written_atomically(tmp_path: Path):
    target = tmp_path / "qt_launcher_promotion.json"
    marker = {
        "schema": PROMOTION_SCHEMA,
        "app_version": "x",
        "migration_stage": "phase-12",
        "exe_sha256": "abc",
    }
    save_promotion(target, marker)
    assert json.loads(target.read_text(encoding="utf-8"))["exe_sha256"] == "abc"
    assert not target.with_suffix(target.suffix + ".tmp").exists()


def test_phase12_qt_promotion_contract_has_no_pyside_or_legacy_ui_imports():
    text = (ROOT / "audioknigi/qt/promotion_contract.py").read_text(encoding="utf-8")
    for forbidden in (
        "import PySide6",
        "from PySide6",
        "import tkinter",
        "from tkinter",
        "ui_kit",
        "audioknigi.app",
        "audioknigi.actions",
    ):
        assert forbidden not in text
