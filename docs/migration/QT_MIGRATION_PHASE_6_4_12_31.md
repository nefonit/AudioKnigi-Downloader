# Qt Migration Phase 6 — Native System Tray

Date: 2026-09-06

## Goal

Move system-tray behavior in the Qt branch to Qt itself and remove the legacy tray backend from the Qt runtime/package surface.

## Architecture

Phase 6 adds `audioknigi/qt/tray_controller.py`, based only on standard Qt classes:

- `QSystemTrayIcon`;
- `QMenu`;
- `QAction`;
- `QIcon`.

The stable Tk implementation in `audioknigi/tray.py` remains unchanged. The Qt tray controller does not import Tk, ttkbootstrap, ui_kit or the legacy tray manager.

## Tray menu

The Qt tray menu provides:

- `Показать окно`;
- `Скрыть в трей`;
- `Открыть плеер`;
- `Открыть очередь`;
- `Выход`.

Single-click/double-click tray activation restores the main window. Restoring also returns the previous maximized state when possible.

## Automatic tray behavior

The existing `minimize_to_tray` preference is now active in Qt. To retain the stable application's semantics, automatic hiding is limited to a long download/queue operation. During such work:

- minimizing the main window hides it to the tray;
- pressing the window close button hides it to the tray instead of cancelling the job;
- the download/queue continues in the background.

`Файл → Скрыть в системный трей` remains available for a manual hide at any time when the OS tray is available.

`Файл → Выход` and the tray `Выход` command are explicit exit paths and therefore bypass automatic tray hiding. Existing safe-shutdown confirmation remains in force for active search/analysis/download work.

## Modal safety

A missing-media 404/410 requires a user choice. If that event occurs while the main window is hidden, Phase 6 first restores the window and then presents the Qt modal prompt. This prevents an invisible modal dialog from blocking a worker indefinitely.

## Notifications

Qt-native tray messages are used for significant hidden-window events, including:

- download completion;
- direct-download error;
- queue completion;
- queue task error;
- first manual/automatic hide reminder.

Routine progress updates stay in the application status/progress controls and are not turned into notification spam.

## Settings and packaging

`requirements-qt.txt` is now standalone instead of inheriting `requirements.txt`. The Qt install path contains the dependencies required by the Qt branch but no longer installs the legacy GUI/player/tray stack solely because of `-r requirements.txt`.

`build_qt_exe.bat` now:

- verifies `QSystemTrayIcon` together with Qt Multimedia;
- explicitly excludes `pystray` in addition to the existing Tk/pygame exclusions.

The stable Tk requirements and build remain unchanged.

## Verification

- Complete active suite collected: **552 tests**.
- Complete suite executed in non-overlapping Xvfb groups because one monolithic run exceeds the execution-time cap: **552/552 passed**.
- Qt migration Phase 1–6 focused subset: **40/40 passed**.
- Tray-focused legacy + Qt regression subset under Xvfb: **89/89 passed**.
- Python `compileall`: passed.
- Static architecture check: `qt/tray_controller.py` contains no legacy GUI/tray imports.
- Byte comparison against Phase 5 confirms the stable Tk tray/app/player/downloader/actions/ui/queue entry files are unchanged.

## Manual Windows validation still required

PySide6 is not installed in the execution environment, so native Windows tray behavior and NVDA/JAWS interaction must still be validated on the target machine:

1. tray icon visibility and context-menu keyboard navigation;
2. restore from normal and maximized states;
3. minimize/close-to-tray during an active queue;
4. direct download while hidden;
5. missing-media modal restoration from tray;
6. notification delivery under Windows Focus Assist settings;
7. explicit Exit while a download is active;
8. frozen PyInstaller tray icon/resources.

## Next phase

The next migration phase should concentrate on removing remaining legacy-only dependencies from the Qt packaging/runtime path and on Windows NVDA/JAWS end-to-end validation before considering the Qt branch production-ready.
