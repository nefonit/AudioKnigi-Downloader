# Qt Migration Phase 8 — Accessibility Hardening and Windows Acceptance Gate

Date: 2026-09-06

## Goal

Harden the PySide6/Qt Widgets interface specifically for keyboard and screen-reader use before making the Qt launcher the default. Phase 8 deliberately avoids rebuilding a custom screen-reader/focus layer. It continues to rely on native Qt accessibility roles, values, names and announcements, while fixing concrete keyboard/focus semantics around tables, progress messages, modal decisions and the player.

The stable Tk launcher remains available and unchanged.

## Changes

### 1. Polite announcements no longer flood speech

`audioknigi/qt/accessibility.py` now contains `AccessibleAnnouncer`.

- normal status messages are debounced before `QAccessibleAnnouncementEvent` is sent;
- multiple worker messages arriving in a short burst collapse to the latest polite message;
- exact rapid duplicates are suppressed;
- assertive/error messages bypass the debounce and are announced immediately;
- no `FocusIn`, event-filter, Prism, NVDA or JAWS-specific focus hook is installed.

The visual `QStatusBar` still updates immediately; only the spoken live announcement is coalesced.

### 2. A focused table always has a current cell

`focus_table_row()` sets a real current index, selects the row, scrolls it into view and only then moves keyboard focus.

This is used after explicit user operations that naturally transition into a result list:

- successful book analysis → first track;
- successful search → first result/title cell;
- explicit “Add to queue” → newly added queue item;
- restoring/opening the queue from tray keeps or establishes a current row.

This addresses the case where assistive technology receives focus on a table whose model has just been reset but has no current accessible child.

### 3. Tables expose explicit accessible cell text

`TrackTableModel` and `SearchResultsModel` now return `Qt.ItemDataRole.AccessibleTextRole`.

Examples:

- `Скачать: выбрано` / `Скачать: не выбрано`;
- `Название: ...`;
- `Длительность: ...`;
- `Источник: ...`.

Queue and history `QTableWidgetItem` cells similarly expose `Header: value` accessibility text. Empty/error/priority states use spoken values such as `нет`, `Нет` rather than an ambiguous empty cell.

### 4. Keyboard-only table actions

Phase 8 adds direct keyboard commands without replacing Qt's normal Tab/arrow navigation:

- track table: **Space** toggles the download check state of the current row even when the current cell is not the checkbox column;
- search results: **Enter/Return** activates the current result;
- **F1** opens the built-in accessibility/hotkey help;
- `Ctrl+1…Ctrl+6`, `Ctrl+L`, `Ctrl+F`, Tab and Shift+Tab remain available.

The shortcuts use `WidgetWithChildrenShortcut`, so they are scoped to the relevant table rather than becoming global key interceptors.

### 5. Player seek value is now screen-reader meaningful

The seek slider previously stored milliseconds. A screen reader could therefore expose values such as `53000` for 53 seconds.

Phase 8 changes the UI slider to seconds:

- Arrow step: 5 seconds;
- Page Up/Page Down step: 30 seconds;
- the controller boundary still converts to milliseconds for `QMediaPlayer.setPosition()`;
- displayed time remains formatted through `fmt_time()`.

The Play/Pause button also changes its accessible name with state: `Воспроизвести` ↔ `Пауза воспроизведения`.

### 6. Required missing-media modal is explicit and safe

The 404/410 decision dialog now gives both dynamic buttons explicit accessible IDs/names and uses `Остановить загрузку` as both the default and Escape action. Pressing Escape can therefore never silently mean “skip”.

### 7. Frozen accessibility contract self-test

A new module, `audioknigi/qt/accessibility_audit.py`, defines the persistent accessibility contract for the Qt window.

It checks:

- required persistent accessibility IDs exist;
- no required ID is duplicated;
- every required control has a non-empty accessible name;
- interactive controls are keyboard-focusable.

`audioknigi_qt.py` now supports:

```text
--qt-accessibility-selftest
```

The self-test creates the Qt window with the offscreen platform and writes `qt_accessibility_frozen_selftest.txt` (or the path supplied in `AUDIOKNIGI_QT_ACCESSIBILITY_SELFTEST_REPORT`).

`build_qt_ci.ps1` runs this check against the **finished frozen EXE** after the runtime-boundary self-test and before the Playwright/Edge self-test. A missing/renamed/non-focusable required control therefore breaks the Windows build instead of reaching a user silently.

## What the automated test does NOT prove

The frozen accessibility self-test verifies the UI contract, not NVDA/JAWS speech output. It cannot prove:

- exact spoken wording produced by a specific NVDA/JAWS release;
- whether a screen reader chooses to announce a Qt state/value in the preferred order;
- behavior of Windows UI Automation bridges under the user's real desktop/session;
- tray speech, notification-center behavior or audio ducking;
- interaction with a user's screen-reader verbosity/settings.

Those require manual acceptance on the actual Windows build.

## Windows NVDA/JAWS acceptance checklist

Run the finished `dist\AudioKnigiDownloader_Qt.exe` separately with NVDA and JAWS.

### Startup and global navigation

1. Launch the EXE and verify the main window/title is announced.
2. Traverse with Tab and Shift+Tab; confirm there are no focus traps or invisible focus targets.
3. Use Ctrl+1…Ctrl+6 and verify each tab is announced.
4. Use Ctrl+L and Ctrl+F; verify the target editor receives focus and its current value can be read.
5. Press F1 and verify the help dialog is modal and readable.

### Search

1. Run a valid search.
2. Confirm focus moves to the first result and the first book/title is announced, not only “table”.
3. Use Up/Down between rows and Left/Right between cells.
4. Press Enter on a result; verify the book URL editor receives focus.
5. Verify all cell values include useful header/state context.

### Book/track table

1. Analyze a book and verify focus lands on the first track.
2. Navigate rows/cells using arrows.
3. Press Space while current cell is any column; confirm the current track toggles selected/unselected.
4. Confirm selected state is announced.
5. Use Select all/Clear all and confirm status speech is concise rather than a long burst of worker messages.

### Queue/history

1. Add a book to queue and verify the new item becomes the current row.
2. Verify status, attempts, priority, part count and error cells are understandable.
3. Exercise Up/Down task movement and retry/resume controls.
4. Refresh history and verify cells expose header/value semantics.

### Player

1. Open a downloaded MP3.
2. Verify Play changes to accessible `Pause` while playing and back to `Play` afterward.
3. Focus the position slider and use arrows/Page Up/Page Down; verify values are seconds rather than millisecond-sized numbers.
4. Verify volume and rate controls announce their current value.
5. Stop/reopen and verify resume position behavior.

### Modals and tray

1. Trigger a validation/error dialog and verify the main window cannot be operated behind it.
2. For missing media, verify Escape maps to Stop, not Skip.
3. Hide a long-running task to tray and restore it.
4. Trigger a decision-required state while hidden and verify the main window returns before the modal prompt.
5. Verify tray actions and notifications with both NVDA and JAWS.

## Verification in this environment

- Test collection: **571 tests**.
- Complete active suite executed in non-overlapping Xvfb groups: **571/571 passed**.
- Qt migration Phase 1–8 focused suite: **59/59 passed**.
- Phase 8/7/6 accessibility-build subset: **27/27 passed**.
- Python compile checks: pass.

This Linux environment has no PySide6/Windows desktop/NVDA/JAWS, so the frozen accessibility self-test and the manual acceptance matrix still have to be run on Windows.

## Promotion criterion

Do not switch the default launcher from Tk to Qt until:

1. `build_qt_exe.bat` completes;
2. `qt_runtime_frozen_selftest.txt` reports `OK`;
3. `qt_accessibility_frozen_selftest.txt` reports `OK`;
4. `playwright_edge_qt_frozen_selftest.txt` reports `OK`;
5. the checklist above passes with NVDA;
6. the checklist above passes with JAWS;
7. any discovered control/focus/value issues are added as automated regressions where possible.
