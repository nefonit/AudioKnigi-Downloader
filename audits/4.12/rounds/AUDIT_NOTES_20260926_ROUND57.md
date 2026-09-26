# Round 57 — clean accessibility self-test return flow — 2026-09-26

Round 57 fixes the Python 3.14 SyntaxWarning reported by the Windows standalone build after Round 56.

## Root cause

Round 56 correctly captured asynchronous Qt callback exceptions during accessibility teardown, but returned exit code 26 directly from a nested `finally` block. Python 3.14 warns about this because a return in `finally` can suppress an active exception.

## Fix

- The accessibility self-test now stores its provisional exit status instead of returning from the protected body.
- Qt window/application cleanup and restoration of `QT_QPA_PLATFORM` / `sys.excepthook` always finish first.
- After cleanup, captured asynchronous Qt callback errors are evaluated and can still force exit code 26.
- The success message is printed only after teardown has completed without captured callback errors.
- There is no return statement inside the self-test cleanup `finally` blocks.

## Regression coverage

- Compile `audioknigi_qt.py` with `SyntaxWarning` promoted to an error.
- Run the real offscreen accessibility self-test with `PYTHONWARNINGS=error::SyntaxWarning`.
- Reject SyntaxWarning, Python traceback, or deleted-Shiboken-object output.
- Verify the asynchronous-error decision occurs after the cleanup `finally` region.

This preserves the Round 56 strict failure gate while making the Python 3.14 build log clean.
