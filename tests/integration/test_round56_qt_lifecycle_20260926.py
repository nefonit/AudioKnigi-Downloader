from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def test_delayed_window_callbacks_use_lifecycle_safe_scheduler():
    source = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")

    assert "def _single_shot_if_alive" in source
    assert '"Internal C++ object" in message and "already deleted" in message' in source
    assert 'self._single_shot_if_alive(300, "_schedule_clipboard_prompt_check")' in source
    assert 'self._single_shot_if_alive(900, "_start_source_health_check")' in source
    assert 'self._single_shot_if_alive(0, "_refresh_context_guidance", announce_now=True)' in source
    assert 'QTimer.singleShot(0, lambda: self._refresh_context_guidance' not in source


def test_accessibility_selftest_promotes_async_callback_exceptions_to_failure():
    source = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")
    assert "capture_async_callback_error" in source
    assert "sys.excepthook = capture_async_callback_error" in source
    assert "Asynchronous Qt callback exception:" in source
    assert "return 26" in source


def test_qt_accessibility_selftest_has_no_deleted_qt_callback_traceback():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        [sys.executable, str(ROOT / "audioknigi_qt.py"), "--qt-accessibility-selftest"],
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
    assert "Internal C++ object" not in combined
    assert "already deleted" not in combined
    assert "Traceback (most recent call last)" not in combined
