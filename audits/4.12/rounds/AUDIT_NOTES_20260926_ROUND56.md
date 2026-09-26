# Round 56 — Qt lifecycle-safe delayed callbacks — 2026-09-26

Round 56 fixes a real Windows build-time traceback discovered after the Round 55 accessibility self-test.

## Root cause

Round 55 queued a zero-delay callback with:

`QTimer.singleShot(0, lambda: self._refresh_context_guidance(announce_now=True))`

During the offscreen accessibility self-test the main window could already be closed and its native `QStackedWidget` destroyed before that callback ran. The Python wrapper still existed, so `current_ui_mode()` touched a deleted Shiboken object and emitted:

`RuntimeError: libshiboken: Internal C++ object (PySide6.QtWidgets.QStackedWidget) already deleted.`

The self-test still returned success because Qt routed the callback exception to stderr instead of the command exit code.

## Fix

- Added one weak-reference based `_single_shot_if_alive(...)` helper on the Qt main window.
- The helper executes a named window method only while the Python owner still exists and suppresses only the specific Qt/Shiboken deleted-object RuntimeError. Other RuntimeError exceptions are re-raised.
- Context-guidance refresh, delayed clipboard startup checking and delayed source-health startup checking now use this lifecycle-safe scheduler.
- Existing focus transfer keeps its widget weak reference and RuntimeError guard.

## Regression coverage

- A source-contract regression verifies the unsafe guidance lambda is gone and the three startup/window callbacks use the safe scheduler.
- The accessibility self-test temporarily captures `sys.excepthook`; any asynchronous Qt callback exception now changes the self-test result to failure instead of printing a traceback while returning success.
- A subprocess regression runs the real `audioknigi_qt.py --qt-accessibility-selftest` path and fails if stderr contains `Internal C++ object`, `already deleted`, or a Python traceback.

The issue was observed in a successful Windows build after the accessibility self-test reported 141 controls and zero accessibility issues; Round 56 makes that teardown path clean rather than merely non-fatal.
