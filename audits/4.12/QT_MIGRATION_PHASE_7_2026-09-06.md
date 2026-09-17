# Audit — Qt Migration Phase 7

Date: 2026-09-06

## Runtime boundary

PASS — Qt source runtime has a machine-checkable import boundary.

PASS — `tools/qt_import_audit.py --verbose` walks the graph from `audioknigi_qt.py` and reaches 29 project modules with no path into the stable Tk frontend.

PASS — `audioknigi/qt_runtime_audit.py` can detect loaded legacy project modules and legacy-only third-party modules without importing PySide6 or Tk.

PASS — `run_qt.bat` runs the boundary audit before application startup.

## Dependency isolation

PASS — `requirements-qt.txt` contains Qt runtime dependencies and no PyInstaller or legacy UI/player/tray/accessibility packages.

PASS — `requirements-qt-build.txt` adds PyInstaller only for build environments.

PASS — `pyproject.toml` common dependencies are backend-only; `legacy` and `qt` extras are separate.

PASS — `pip install .[qt]` no longer semantically inherits pygame/ttkbootstrap/pystray/plyer/tkinterdnd2/Prismatoid/tk-uia through mandatory project dependencies.

PASS — stable `requirements.txt` is unchanged.

## Frozen build hardening

PASS (static) — Qt build uses isolated `.venv-qt`.

PASS (static) — Qt PyInstaller pipeline is one-file/windowed and bundles resolved real FFmpeg/FFprobe binaries.

PASS (static) — Playwright Chromium cache is removed and installed Microsoft Edge is the compact-browser target.

PASS (static) — PyInstaller explicitly excludes both legacy third-party packages and legacy `audioknigi` frontend modules.

PASS (static) — build checks PyInstaller `Analysis-00.toc` for forbidden frozen modules.

PASS (static) — finished EXE is required to pass `--qt-runtime-selftest` and `--playwright-edge-selftest` with report files.

NOT EXECUTED — native Windows PyInstaller build, because the current environment is Linux and has neither PySide6 nor Windows PowerShell.

## Stable branch protection

PASS — byte-for-byte comparison against Phase 6 confirms no changes to stable Tk launcher, app/actions/accessibility/ui/player/queue/tray/downloader/storage modules, stable requirements, or stable EXE build scripts.

## Regression

- Complete active collection: **560 tests**.
- Complete suite in non-overlapping Xvfb groups: **560/560 passed**.
- Qt Phase 1–7 focused tests: **48/48 passed**.
- Static Qt import audit: **PASS** (29 reachable project modules; no legacy frontend path).

## Remaining acceptance gate

The Qt branch should not become the default launcher until a Windows frozen build passes manual NVDA and JAWS acceptance. Required coverage includes search/results, book/track selection, queue state, player transport/seek/rate, settings, modal ownership, tray restore/exit, progress announcements and keyboard traversal.
