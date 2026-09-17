# Qt Migration Phase 7 — Clean Runtime and Windows EXE Build Boundary

Date: 2026-09-06

## Goal

Make the PySide6 branch independently installable and buildable without carrying the stable Tk frontend dependency stack into the Qt process or frozen executable.

Phase 7 does not replace the stable Tk launcher. It hardens the parallel Qt branch so the next validation work can happen against a reproducible Windows EXE rather than a mixed development environment.

## Dependency split

`pyproject.toml` now separates dependencies into three surfaces:

- common backend dependencies: `requests`, `playwright`, `Pillow`, `mutagen`;
- `legacy` extra: pygame, ttkbootstrap, pystray, plyer, tkinterdnd2, Prismatoid and tk-uia;
- `qt` extra: PySide6 only on top of the common backend.

Therefore:

```powershell
pip install .[legacy]
```

installs the stable Tk frontend dependency set, while:

```powershell
pip install .[qt]
```

installs the Qt frontend without inheriting legacy GUI/player/tray/screen-reader bridge packages.

The existing `requirements.txt` remains unchanged for the stable Tk release path.

The Qt files are also split by purpose:

- `requirements-qt.txt` — source/runtime dependencies;
- `requirements-qt-build.txt` — includes the runtime file plus PyInstaller.

## Runtime-boundary audit

Phase 7 adds `tools/qt_import_audit.py` and the standard-library-only runtime definition in `audioknigi/qt_runtime_audit.py`.

The static tool starts at `audioknigi_qt.py`, parses Python imports, follows every reachable in-project module and fails if the graph reaches a stable Tk frontend module such as:

- `audioknigi.app`;
- `audioknigi.actions`;
- `audioknigi.accessibility`;
- `audioknigi.player`;
- `audioknigi.queue_manager`;
- `audioknigi.search`;
- `audioknigi.storage`;
- `audioknigi.tray`;
- `audioknigi.ui` / `audioknigi.ui_kit`.

It also rejects direct Qt-runtime paths to legacy-only third-party modules such as tkinter, pygame, pystray, plyer, Prism/tk-uia, tkinterdnd2 and ttkbootstrap.

At Phase 7 the audit reaches 29 project modules and reports no legacy frontend path.

Run it manually with:

```powershell
py tools\qt_import_audit.py --verbose
```

`run_qt.bat` executes the audit before opening the Qt application.

## Frozen runtime self-test

`audioknigi_qt.py` now supports:

```text
--qt-runtime-selftest
```

The self-test imports the actual Qt runtime surface, including:

- `QMediaPlayer` / `QAudioOutput`;
- `QSystemTrayIcon`;
- the Qt main window;
- book-analysis/download/search services.

It then checks `sys.modules` through `assert_qt_runtime_clean()` and fails if any legacy-only frontend/runtime module was loaded.

For a windowed PyInstaller build the result is written to `qt_runtime_frozen_selftest.txt` (or to the path supplied by `AUDIOKNIGI_QT_RUNTIME_SELFTEST_REPORT`).

## Playwright frozen self-test

The Qt entry point also implements:

```text
--playwright-edge-selftest
```

It proves that the frozen Playwright driver can launch the installed stable Microsoft Edge channel. The Qt compact build deliberately does not bundle Playwright Chromium.

## Isolated build environment

`build_qt_exe.bat` now uses its own:

```text
.venv-qt
```

It never reuses the stable `.venv` build environment.

The build is pinned to the same project Windows build interpreter policy: CPython 3.14.7 x64.

The BAT entry point:

1. creates/validates `.venv-qt`;
2. installs only `requirements-qt-build.txt`;
3. runs the static Qt import audit;
4. verifies Qt Multimedia and system-tray imports;
5. delegates the actual frozen build to `build_qt_ci.ps1`.

## `build_qt_ci.ps1`

The new PowerShell pipeline builds:

```text
dist\AudioKnigiDownloader_Qt.exe
```

as a one-file/windowed executable.

It performs the following checks and packaging work:

- validates Python 3.14.7 x64;
- validates PyInstaller/PySide6 imports;
- reruns the static Qt import audit;
- resolves real `ffmpeg.exe` and `ffprobe.exe` binaries and rejects Chocolatey bin shims;
- bundles FFmpeg and FFprobe into the one-file EXE;
- removes local Playwright browser cache before collection;
- verifies installed Microsoft Edge through Playwright;
- collects the Playwright Python/Node driver but not Chromium;
- copies PySide6 and Playwright distribution metadata required by frozen self-tests;
- explicitly excludes legacy Tk/player/tray/accessibility modules and packages;
- inspects PyInstaller `Analysis-00.toc` and fails if a forbidden legacy module leaked into the frozen graph;
- runs the frozen Qt runtime self-test;
- runs the frozen Playwright/Edge self-test.

## Stable Tk branch

The following stable files were compared byte-for-byte against Phase 6 and remain unchanged:

- `audioknigi_gui.py`;
- `audioknigi/app.py`;
- `audioknigi/actions.py`;
- `audioknigi/accessibility.py`;
- `audioknigi/ui_kit.py`;
- `audioknigi/player.py`;
- `audioknigi/queue_manager.py`;
- `audioknigi/tray.py`;
- `audioknigi/downloader.py`;
- `audioknigi/storage.py`;
- `requirements.txt`;
- `build_exe.bat`;
- `build_exe_fixed.bat`;
- `build_ci.ps1`.

## Verification

- Test collection: **560 tests**.
- Complete active suite executed in non-overlapping Xvfb groups: **560/560 passed**.
- Qt migration Phase 1–7 focused suite: **48/48 passed**.
- Static Qt import graph: **PASS**, 29 project modules reachable, no legacy frontend path.
- Python compile checks: pass after Phase 7 source changes.

## Environment limitation

This execution environment is Linux, has no PySide6 installed and has no Windows PowerShell runtime. Therefore the Windows one-file EXE itself cannot be produced or launched here.

Phase 7 adds the build-time and frozen-runtime guards needed for that validation, but the following still must be run on the target Windows machine:

1. `build_qt_exe.bat` end to end;
2. inspect `dist\qt_runtime_frozen_selftest.txt`;
3. inspect `dist\playwright_edge_qt_frozen_selftest.txt`;
4. launch the finished Qt EXE with NVDA;
5. repeat with JAWS;
6. validate tray/menu/modals, Qt Multimedia playback and active download/queue shutdown behavior in the frozen build.

## Next phase

Phase 8 should be Windows accessibility acceptance/hardening: run the actual frozen Qt build with NVDA and JAWS, record control-by-control behavior, fix any UI Automation/name/state/focus problems, and only then consider switching the default launcher from Tk to Qt.
