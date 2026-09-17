# Qt build bootstrap fix — 2026-09-06

## Problem
`build_qt_exe.bat` correctly detected CPython 3.14.7 x64 with `py -3.14`, but the venv creation branch used `%BASE_MODE%` inside the same parenthesized CMD block where `BASE_MODE` was assigned. CMD expands `%VAR%` before executing the block, so the comparisons saw the old empty value and `.venv-qt` was never created.

## Fix
- Enabled delayed environment-variable expansion in `build_qt_exe.bat`.
- Changed the three venv creation comparisons from `%BASE_MODE%` to `!BASE_MODE!`.
- Added a diagnostic line showing which Python discovery route was selected.
- Stable Tk `.venv` and build outputs remain untouched.

## Verified environment from user machine
- CPython 3.14.7
- 64-bit AMD64
- `C:\Users\serio\AppData\Local\Programs\Python\Python314\python.exe`
