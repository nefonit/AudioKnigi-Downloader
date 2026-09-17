# Qt Migration Phase 5 — Qt Multimedia Player

Date: 2026-09-06

## Goal
Move the mini-player functionality to the Qt branch without importing the legacy Tk `PlayerMixin` or `pygame` into the Qt GUI.

## Architecture

Phase 5 adds two deliberately separate layers:

- `audioknigi/services/player_position_store.py` — GUI-independent resume-position persistence;
- `audioknigi/qt/player_controller.py` — Qt Multimedia controller based on `QMediaPlayer` + `QAudioOutput`.

The stable Tk player remains unchanged in `audioknigi/player.py` and continues to use pygame. The Qt entrypoint does not import that legacy player.

## Shared resume compatibility

`PlayerPositionStore` intentionally preserves the legacy `player_positions.json` contract:

- canonical key = resolved file path converted to lowercase;
- `position` in seconds;
- `duration` in seconds;
- `file` basename;
- `updated` timestamp.

Positions below 3 seconds are removed. Positions within the last 3 seconds of a completed file are removed. Therefore a file played in Tk can resume in Qt and a file played in Qt can resume in Tk on the next application launch.

## Qt player UI

A sixth `Плеер` tab was added without changing the existing Ctrl+1…Ctrl+5 mapping. Ctrl+6 opens the player.

Available controls:

- `Открыть аудиофайл…` (`Ctrl+O` through the File menu);
- `Воспроизвести / Пауза`;
- `Стоп` with resume-position preservation;
- `С начала` which seeks to zero and clears stale resume state;
- seek slider;
- volume slider 0–100;
- playback rate 0.75×, 1×, 1.25×, 1.5×, 1.75×, 2×;
- current file, current/total time and playback-state labels.

The Book tab also gains `Воспроизвести выбранную`. It is enabled only when the selected `Track.local_path` points to an existing downloaded file. Double-clicking a row uses the same action.

## Accessibility

All player controls are standard Qt Widgets and receive explicit accessible names/identifiers through `configure_accessible`:

- play/pause;
- stop;
- restart;
- seek;
- volume;
- playback rate;
- current file/time/status.

The position signal updates visual state without forcing focus or generating continuous speech announcements. User actions and significant player state changes use the existing Qt status/announcement path.

## Shutdown and errors

Before the Qt window is finally accepted for close, the player persists its current position and stops the media backend. Media errors are reported through Qt `QMediaPlayer.errorOccurred` and a Qt modal error dialog.

## Settings

The shared `settings.json` now also stores:

- `player_volume`;
- `player_rate`.

## Verification

- Active test suite executed in five non-overlapping groups: **544 passed**.
- Qt migration Phase 1–5 subset: **32 passed**.
- Legacy player/audio/shutdown focused subset under Xvfb: **14 passed**.
- `compileall` / `py_compile`: passed.
- Import test confirms `player_position_store.py` loads without Tk or PySide6.
- Static checks confirm the Qt player controller imports Qt Multimedia and does not import pygame/Tk.
- Byte comparison against Phase 4 confirms these legacy files are unchanged: `player.py`, `downloader.py`, `actions.py`, `ui_kit.py`, `queue_manager.py`, `services/queue_service.py`, `audioknigi_gui.py`.

## Manual Windows validation still required

PySide6 is not installed in the execution environment, so live Qt Multimedia playback and NVDA/JAWS behavior cannot be exercised here. Validate on Windows using `run_qt.bat`, especially:

1. MP3 playback through the normal Windows audio output;
2. NVDA/JAWS naming of player buttons, seek slider, volume and rate;
3. keyboard seeking and focus order;
4. pause/close/relaunch resume behavior;
5. playback-rate behavior with the packaged Qt multimedia backend;
6. frozen `build_qt_exe.bat` multimedia deployment.

## Next phase

- system tray migration;
- optional library/history-to-player shortcuts;
- further removal of Tk-only dependencies from the Qt packaging surface.
