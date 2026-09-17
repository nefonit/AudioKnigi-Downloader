# Qt migration Phase 10 — Windows release-candidate acceptance gate

Date: 2026-09-06  
Version line: 4.12.31

## Goal

Phase 9 reached critical functional parity. Phase 10 does **not** silently replace the stable Tk launcher; instead it turns the Qt branch into a hash-bound Windows release candidate with a repeatable NVDA/JAWS acceptance process.

Promotion is allowed only after one exact frozen `AudioKnigiDownloader_Qt.exe` passes all automated frozen checks plus the complete manual matrix with both NVDA and JAWS.

## What was added

### 1. Hash-bound release candidate manifest

`build_qt_ci.ps1` now writes:

`dist/qt_release_candidate.json`

The manifest records:

- application version;
- migration stage (`phase-10`);
- Windows platform;
- EXE file name and size;
- SHA-256 of the exact frozen EXE;
- frozen runtime/accessibility/Playwright results;
- source/frozen import-boundary status;
- explicit `manual_screen_reader_acceptance = required` state.

The manifest is created only after the existing frozen self-tests have succeeded.

### 2. Windows acceptance runner

`run_qt_acceptance.bat` invokes `tools/qt_windows_acceptance.py` against the built EXE.

Before a manual session the runner:

1. verifies that `qt_release_candidate.json` exists;
2. verifies app version and migration stage;
3. recomputes the current EXE SHA-256;
4. rejects a manifest created for any different binary;
5. reruns the frozen runtime self-test;
6. reruns the frozen accessibility self-test;
7. reruns the Playwright → Microsoft Edge self-test.

The report is persisted incrementally as:

`dist/qt_windows_acceptance.json`

If the EXE is rebuilt, even with the same file name/version, the SHA-256 changes and old manual approvals are not carried to the new binary.

### 3. Manual NVDA and JAWS matrix

The same required matrix is completed independently with **NVDA** and **JAWS**:

1. startup / first focus;
2. Tab and Shift+Tab traversal;
3. book URL editor;
4. analysis + track table;
5. search + result table;
6. ComboBox behavior;
7. queue;
8. history;
9. settings;
10. player, including seconds-based seek semantics;
11. modal dialogs;
12. system tray hide/restore;
13. status/error announcements;
14. two-minute focus-stress pass.

A required item marked `skip` or `fail` keeps the result `INCOMPLETE`.

### 4. Passive accessibility focus trace

The normal Qt launcher accepts:

`--qt-focus-trace=<path-to-jsonl>`

`audioknigi/qt/accessibility_trace.py` connects only to Qt's existing `QApplication.focusChanged` signal. It never:

- installs an event filter;
- calls `setFocus()`;
- redirects keyboard events;
- injects screen-reader speech;
- records editor text, URLs, book names or accessible names.

Each focus record contains only diagnostic metadata such as static accessibility/object ID, widget class, window ID and visible/enabled state.

This is deliberately an observer, not a second accessibility layer.

### 5. Trace summary

After each manual reader session the acceptance report includes a summary of:

- focus transition count;
- unique destination IDs;
- focus-loss events;
- anonymous destinations;
- disabled/hidden focus destinations;
- sustained A↔B focus oscillation windows;
- JSON parse errors.

The trace summary is diagnostic evidence. The actual promotion gate remains the explicit NVDA/JAWS matrix so a heuristic cannot falsely approve or reject a release by itself.

### 6. Status-only check

`check_qt_acceptance.bat` verifies the current report against the exact current EXE and candidate manifest without rerunning the whole matrix.

Only a complete exact-hash result prints `PASS`.

## Promotion rule

Qt is eligible to become the default launcher only when all of these are true for the **same EXE SHA-256**:

- build/import boundary: pass;
- frozen runtime self-test: pass;
- frozen accessibility self-test: pass;
- frozen Playwright/Edge self-test: pass;
- all required NVDA checks: pass;
- all required JAWS checks: pass.

Phase 10 deliberately does not edit/copy/replace the stable launcher automatically. Promotion remains a separate explicit future change after the Windows evidence exists.

## Stable Tk protection

The following 14 files were compared byte-for-byte against the Phase 9 archive and remain unchanged:

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

- Full active repository suite: **591/591 passed** in non-overlapping Xvfb groups.
- Qt migration Phase 1–10 suite: **79/79 passed**.
- Phase 10 focused tests: **11/11 passed**.
- Static Qt import audit: **33 reachable project modules, 0 legacy frontend paths**.
- `compileall`: pass.
- Stable Tk byte comparison: **14/14 unchanged**.

## Environment limitation

The development environment used for this phase is Linux and cannot provide a real Windows accessibility stack. Therefore it cannot truthfully claim that NVDA or JAWS has passed.

Phase 10 supplies the exact Windows procedure and evidence format, but `qt_windows_acceptance.json` must be produced on the user's Windows machine with the real frozen EXE and real NVDA/JAWS sessions before default-launcher promotion.
