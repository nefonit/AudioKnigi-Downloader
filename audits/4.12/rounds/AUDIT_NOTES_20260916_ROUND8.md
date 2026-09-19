# Round 8 build notes — 2026-09-16

This round is based on `REPORT_FIXES_ROUND7_20260916` and addresses the Windows build log in `Вставленный текст(20260916-151450).txt`.

## Confirmed build failure

The source Qt/accessibility preflight now passes on the user's Windows machine (`QT ACCESSIBILITY SELFTEST: OK (134 controls, qt-only-4.12.42)`). The next step hangs before the PyInstaller CLI starts, while importing `PyInstaller.compat`:

- PyInstaller 6.22.2 calls `platform.win32_ver()` during import to determine Windows 10/11 flags.
- CPython 3.14's `platform.win32_ver()` prefers a WMI query.
- The supplied traceback stops inside `platform._wmi_query(... Win32_OperatingSystem ...)` and ends only after `KeyboardInterrupt`.

This is a build-environment/runtime probe problem, not an application startup or Qt accessibility failure.

## Fix

Added `tools/pyinstaller_bootstrap.py` and changed `build_qt_ci.ps1` to invoke PyInstaller through it.

On Windows with Python 3.14+, the bootstrap sets CPython's private `platform._wmi` handle to `None` **before importing PyInstaller**. This does not fabricate a Windows version. It makes CPython's existing `platform.win32_ver()` take its built-in non-WMI fallback (`sys.getwindowsversion()` / `ver`) immediately, avoiding the WMI call that hung on the reported machine.

The bootstrap is deliberately narrow:

- no change on non-Windows;
- no change on Python < 3.14;
- no monkeypatch of `platform.win32_ver()` itself;
- PyInstaller arguments and build contents are unchanged.

`build_qt_exe.bat` now also checks that the bootstrap file exists before starting the build. A bootstrap self-test runs immediately before the real PyInstaller invocation.

## Verification in this environment

The Windows/PyInstaller executable build cannot be executed in this Linux container. The new regression tests verify that:

- the bootstrap can be imported without PyInstaller installed;
- the WMI bypass is installed before importing `PyInstaller.__main__`;
- the standard `platform.win32_ver()` function is not replaced;
- the PowerShell build no longer calls `python -m PyInstaller` directly;
- the batch entry point requires the bootstrap file.

The full Python and static quality suites are re-run after this build-script-only change.

## Verification

- Targeted Round 8 build-bootstrap regressions: **5 passed**
- Full pytest suite: **262 passed, 0 failed**
- Historical regression audit: **PASS** (`270 passed`, `113 known shape incompatibilities`; the one new incompatibility is the intentionally removed direct `python -m PyInstaller` invocation)
- Exception audit: **PASS** (`reviewed_broad_exception_passes=112`)
- Undefined-global audit: **OK (77 modules)**
- Unused-import audit: **OK (32 implementation modules)**
- Qt localization audit: **OK** (`ru, uk, de, en`)
- Full parity audit: **PASS 61/61**
- Static Qt import-boundary audit: **OK (73 project modules, no legacy frontend path)**

The actual Windows one-file PyInstaller build cannot be executed in this Linux container. On the user's Windows machine the source Qt accessibility preflight already passes; the next build should now proceed past the WMI point that previously blocked PyInstaller import.
