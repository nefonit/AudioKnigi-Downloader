from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = ROOT / "audioknigi_qt.py"


def test_qt_entrypoint_compiles_with_syntaxwarnings_as_errors():
    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "error::SyntaxWarning",
            "-m",
            "py_compile",
            str(ENTRYPOINT),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    assert result.returncode == 0, combined
    assert "SyntaxWarning" not in combined


def test_accessibility_selftest_is_warning_and_traceback_free_after_cleanup():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONWARNINGS"] = "error::SyntaxWarning"
    result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "--qt-accessibility-selftest"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    assert result.returncode == 0, combined
    assert "QT ACCESSIBILITY SELFTEST: OK" in combined
    assert "SyntaxWarning" not in combined
    assert "Traceback (most recent call last)" not in combined
    assert "Internal C++ object" not in combined


def test_async_callback_failure_check_runs_after_finally():
    source = ENTRYPOINT.read_text(encoding="utf-8")
    finally_pos = source.index("    finally:\n", source.index("def _qt_accessibility_selftest"))
    async_check_pos = source.index("    if async_callback_errors:", finally_pos)
    playwright_pos = source.index("\ndef _playwright_edge_selftest", async_check_pos)

    assert finally_pos < async_check_pos < playwright_pos
    finally_tail = source[finally_pos:async_check_pos]
    assert "return 26" not in finally_tail
    assert "return 0" not in finally_tail
