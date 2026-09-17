from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from audioknigi.qt import QT_MIGRATION_STAGE
from audioknigi.qt.acceptance_contract import (
    ACCEPTANCE_SCHEMA,
    MANUAL_CHECKS,
    REQUIRED_AUTOMATED_GATES,
    REQUIRED_SCREEN_READERS,
    acceptance_complete,
    acceptance_issues,
    load_report,
    save_report,
    sha256_file,
    summarize_focus_trace,
)


ROOT = Path(__file__).resolve().parents[1]


def _passing_report(exe_hash: str = "abc", version: str = "4.12.31") -> dict:
    checks = {check.key: {"status": "pass"} for check in MANUAL_CHECKS if check.required}
    return {
        "schema": ACCEPTANCE_SCHEMA,
        "app_version": version,
        "migration_stage": "phase-10",
        "platform": "windows",
        "exe_sha256": exe_hash,
        "automated": {gate: {"status": "pass"} for gate in REQUIRED_AUTOMATED_GATES},
        "screen_readers": {
            reader: {"checks": dict(checks)} for reader in REQUIRED_SCREEN_READERS
        },
    }


def test_phase10_stage_and_acceptance_matrix_are_explicit():
    assert int(QT_MIGRATION_STAGE.removeprefix("phase-")) >= 11
    assert REQUIRED_SCREEN_READERS == ("nvda", "jaws")
    assert REQUIRED_AUTOMATED_GATES == ("runtime", "accessibility", "playwright_edge")
    assert len(MANUAL_CHECKS) >= 12
    keys = [check.key for check in MANUAL_CHECKS]
    assert len(keys) == len(set(keys))
    assert {"tabs", "analysis_tracks", "search", "combobox", "queue", "player", "modal", "tray", "focus_stress"} <= set(keys)


def test_phase10_acceptance_requires_exact_hash_all_gates_and_both_screen_readers():
    report = _passing_report()
    assert acceptance_complete(report, app_version="4.12.31", exe_sha256="abc")
    assert not acceptance_issues(report, app_version="4.12.31", exe_sha256="abc")

    broken = json.loads(json.dumps(report))
    broken["screen_readers"]["jaws"]["checks"]["modal"]["status"] = "skip"
    issues = acceptance_issues(broken, app_version="4.12.31", exe_sha256="abc")
    assert "jaws check not passed: modal" in issues

    assert not acceptance_complete(report, app_version="4.12.31", exe_sha256="different")
    assert "EXE SHA-256 mismatch" in acceptance_issues(report, app_version="4.12.31", exe_sha256="different")


def test_phase10_acceptance_report_round_trip_and_sha256(tmp_path: Path):
    exe = tmp_path / "candidate.exe"
    exe.write_bytes(b"phase10-candidate")
    digest = sha256_file(exe)
    assert len(digest) == 64
    report_path = tmp_path / "acceptance.json"
    report = _passing_report(exe_hash=digest)
    save_report(report_path, report)
    assert not (tmp_path / "acceptance.json.tmp").exists()
    loaded = load_report(report_path)
    assert loaded["exe_sha256"] == digest


def test_phase10_focus_trace_is_passive_and_privacy_minimized():
    path = ROOT / "audioknigi" / "qt" / "accessibility_trace.py"
    text = path.read_text(encoding="utf-8")
    assert "app.focusChanged.connect" in text
    assert "--qt-focus-trace" in text
    assert '"event": "focus_changed"' in text
    # Diagnostics must never become another focus-management layer.
    assert ".setFocus(" not in text
    assert "eventFilter" not in text
    assert "installEventFilter" not in text
    # Do not record editor values, URLs, book titles, or accessible text/names.
    assert "accessibleName(" not in text
    assert "toPlainText(" not in text
    assert ".text()" not in text


def test_phase10_application_wires_optional_trace_without_changing_normal_startup():
    text = (ROOT / "audioknigi" / "qt" / "application.py").read_text(encoding="utf-8")
    assert "extract_focus_trace_argument" in text
    assert "install_focus_trace" in text
    assert "clean_argv, trace_path" in text
    assert "focus_tracer.close()" in text
    run_bat = (ROOT / "run_qt.bat").read_text(encoding="utf-8")
    assert "audioknigi_qt.py %*" in run_bat


def test_phase10_build_produces_hash_bound_release_candidate_manifest():
    text = (ROOT / "build_qt_ci.ps1").read_text(encoding="utf-8")
    for needle in (
        "Get-FileHash -LiteralPath $exe -Algorithm SHA256",
        "qt_release_candidate.json",
        "exe_sha256 = $exeHash",
        'migration_stage = $migrationStage',
        'runtime = "pass"',
        'accessibility = "pass"',
        'playwright_edge = "pass"',
        'manual_screen_reader_acceptance = "required"',
    ):
        assert needle in text
    bat = (ROOT / "build_qt_exe.bat").read_text(encoding="utf-8")
    assert "run_qt_acceptance.bat" in bat


def test_phase10_windows_acceptance_runner_rejects_manifest_for_another_binary(tmp_path: Path):
    tool = ROOT / "tools" / "qt_windows_acceptance.py"
    spec = importlib.util.spec_from_file_location("phase10_acceptance_tool", tool)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

    exe = tmp_path / "AudioKnigiDownloader_Qt.exe"
    exe.write_bytes(b"candidate-a")
    manifest = {
        "schema": ACCEPTANCE_SCHEMA,
        "app_version": module.APP_VERSION,
        "migration_stage": QT_MIGRATION_STAGE,
        "platform": "windows",
        "exe_sha256": sha256_file(exe),
        "automated": {
            "runtime": "pass",
            "accessibility": "pass",
            "playwright_edge": "pass",
            "import_boundary": "pass",
            "frozen_module_boundary": "pass",
        },
    }
    path = tmp_path / "qt_release_candidate.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert module.validate_candidate_manifest(path, exe)["exe_sha256"] == manifest["exe_sha256"]

    exe.write_bytes(b"candidate-b")
    try:
        module.validate_candidate_manifest(path, exe)
    except ValueError as exc:
        assert "exe_sha256" in str(exc)
    else:
        raise AssertionError("manifest from another EXE hash must be rejected")


def test_phase10_acceptance_runner_is_incremental_and_does_not_promote_automatically():
    text = (ROOT / "tools" / "qt_windows_acceptance.py").read_text(encoding="utf-8")
    for needle in (
        "validate_candidate_manifest",
        "run_automated_gates",
        "run_manual_reader",
        "save_report(report_path, report)",
        'f"--qt-focus-trace={trace}"',
        'choices=("nvda", "jaws", "both")',
        'report["status"] = "pass" if acceptance_complete',
    ):
        assert needle in text
    for forbidden in ("shutil.copy", "os.replace(exe", "audioknigi_gui.py"):
        assert forbidden not in text


def test_phase10_acceptance_batch_is_separate_from_normal_qt_launcher():
    text = (ROOT / "run_qt_acceptance.bat").read_text(encoding="utf-8")
    assert "qt_windows_acceptance.py" in text
    assert "qt_windows_acceptance.json" in text
    assert "AudioKnigiDownloader_Qt.exe" in text
    assert "NVDA/JAWS" in text


def test_phase10_focus_trace_summary_flags_focus_loss_hidden_and_oscillation(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    rows = []
    for ident in ("a", "b", "a", "b", "a", "b"):
        rows.append({"event": "focus_changed", "new": {"id": ident, "class": "QPushButton", "enabled": True, "visible": True}})
    rows.append({"event": "focus_changed", "new": None})
    rows.append({"event": "focus_changed", "new": {"id": "hidden", "class": "QLineEdit", "enabled": False, "visible": False}})
    trace.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    summary = summarize_focus_trace(trace)
    assert summary["focus_events"] == 8
    assert summary["unique_ids"] == 3
    assert summary["lost_focus"] == 1
    assert summary["disabled_destinations"] == 1
    assert summary["hidden_destinations"] == 1
    assert summary["rapid_oscillation_windows"] >= 1


def test_phase10_status_batch_checks_exact_candidate_without_rerunning_matrix():
    text = (ROOT / "check_qt_acceptance.bat").read_text(encoding="utf-8")
    assert "qt_windows_acceptance.py --status" in text
    assert "AudioKnigiDownloader_Qt.exe" in text
    assert "qt_windows_acceptance.json" in text


def test_phase10_frozen_module_audit_ignores_excludes_but_rejects_real_legacy_module(tmp_path: Path):
    tool = ROOT / "tools" / "qt_frozen_module_audit.py"
    spec = importlib.util.spec_from_file_location("phase10_frozen_module_audit", tool)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

    # Analysis._GUTS contains an `excludes` list in addition to collected TOCs.
    # Merely seeing the forbidden name in the serialized file must not fail.
    metadata_only = (
        ["audioknigi_qt.py"],
        [],
        [],
        [],
        {},
        ["tkinter", "_tkinter", "audioknigi.app"],
        [],
        False,
        {},
        0,
        [],
        [],
        "3.14.7",
        [("audioknigi_qt.py", "audioknigi_qt.py", "PYSOURCE")],
        [("audioknigi.qt.application", "audioknigi/qt/application.py", "PYMODULE")],
        [],
        [],
        [],
        [],
        [],
    )
    toc = tmp_path / "Analysis-00.toc"
    toc.write_text(repr(metadata_only), encoding="utf-8")
    assert module.audit_analysis_toc(toc) == []

    leaked = list(metadata_only)
    leaked[14] = list(metadata_only[14]) + [
        ("tkinter", "C:/Python314/Lib/tkinter/__init__.py", "PYMODULE")
    ]
    toc.write_text(repr(tuple(leaked)), encoding="utf-8")
    leaks = module.audit_analysis_toc(toc)
    assert [item[0] for item in leaks] == ["tkinter"]
