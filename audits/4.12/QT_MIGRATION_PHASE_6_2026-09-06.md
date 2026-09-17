# Audit — Qt Migration Phase 6

Date: 2026-09-06

## Native tray architecture

PASS — Qt tray integration is implemented with `QSystemTrayIcon`, `QMenu` and `QAction`.

PASS — `audioknigi/qt/tray_controller.py` contains no Tk, ttkbootstrap, ui_kit or legacy tray-manager dependency.

PASS — stable Tk `audioknigi/tray.py` remains the legacy frontend implementation and is not imported by the Qt branch.

## Lifecycle

PASS — tray menu supports show, hide, player, queue and explicit exit.

PASS — explicit Exit is separated from ordinary window-close behavior with `_exit_requested`.

PASS — automatic tray hiding is constrained to active download/queue work when `minimize_to_tray` is enabled.

PASS — final accepted close shuts down both Qt Multimedia and the Qt tray icon.

PASS — restore preserves maximized state where the prior Qt window state provides it.

## Modal safety

PASS — hidden-window missing-media decisions restore the main window before showing the modal prompt.

PASS — direct-download errors while hidden use tray notification rather than creating a hidden modal error box.

## Settings and package surface

PASS — `minimize_to_tray` is enabled/disabled according to `QSystemTrayIcon.isSystemTrayAvailable()` and is persisted in shared settings.

PASS — `requirements-qt.txt` no longer inherits the stable Tk requirements file.

PASS — Qt requirements do not include legacy pygame/ttkbootstrap/pystray/tkinterdnd2/prismatoid/tk-uia packages.

PASS — Qt PyInstaller script explicitly excludes `pystray`, Tk and pygame and checks `QSystemTrayIcon` availability at import level.

## Regression

- Qt Phase 1–6 focused tests: **40/40 passed**.
- Tray-focused Qt + legacy checks under Xvfb: **89/89 passed**.
- Complete active suite: **552/552 passed** in non-overlapping Xvfb groups.
- `compileall`: passed.
- Byte-for-byte comparison against Phase 5: legacy `tray.py`, `app.py`, `player.py`, `downloader.py`, `actions.py`, `ui_kit.py`, `queue_manager.py` and `audioknigi_gui.py` are unchanged.

## Environment limitation

PySide6 is not installed in this execution environment. Native Windows tray rendering, notifications and NVDA/JAWS reading of the operating-system tray/context menu remain mandatory manual validation items.
