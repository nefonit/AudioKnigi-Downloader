import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_tool(name, *args, timeout=60):
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / name), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def test_full_parity_audit_passes_modular_layout():
    proc = run_tool("full_parity_audit.py", "--root", str(ROOT), "--require-legacy-retired")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS 61/61" in proc.stdout


def test_localization_audit_passes_modular_layout():
    proc = run_tool("qt_localization_audit.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "static_ui_literals=translated" in proc.stdout


def test_exception_audit_has_no_unreviewed_bare_pass():
    proc = run_tool("exception_audit.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS" in proc.stdout


def test_unused_import_audit_passes_refactored_layers():
    proc = run_tool("unused_import_audit.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "UNUSED IMPORT AUDIT: OK" in proc.stdout


def test_undefined_global_audit_catches_split_module_name_errors():
    proc = run_tool("undefined_global_audit.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "UNDEFINED GLOBAL AUDIT: OK" in proc.stdout


def test_archived_behavioral_regressions_have_no_new_failures():
    proc = run_tool("historical_regression_audit.py", timeout=300)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "HISTORICAL REGRESSION: PASS" in proc.stdout
