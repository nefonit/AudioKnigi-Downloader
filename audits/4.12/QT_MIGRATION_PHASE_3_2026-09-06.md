# Audit — Qt Migration Phase 3 — 2026-09-06

## Scope

Проверена миграция реального download flow из Tk-bound запуска в PySide6/Qt Widgets без потери стабильной Tk-ветки.

## Findings and changes

- Removed direct `tkinter`, `messagebox`, `ttk` and `ui_kit` imports from `audioknigi/downloader.py`.
- Moved Tk-specific disk error and missing-media modal hooks to `ActionsMixin`.
- Kept old Tk modal ownership via `activate_modal_window`.
- Added GUI-neutral `audioknigi/download_engine.py` with callback-based status/stage/progress/transfer/history/missing-media API.
- Reused mature resume, Range, segmented download, FFmpeg, ID3, sidecar and recovery logic rather than duplicating it for Qt.
- Wired `DownloadService` to Qt `QThread`.
- Added Qt start/cancel controls, stage/progress/speed widgets, history refresh and missing-media modal decision.
- Added close-during-download cancellation flow.
- Kept `audioknigi/services/` free of legacy downloader dependency; Phase 2 architecture guard remains unchanged.
- Updated modal-ownership regression to require the Tk dialog in `actions.py` and forbid it in downloader core.

## Validation

- `tests/test_qt_migration_phase3_41231.py`: **8 passed**.
- Downloader/Tk compatibility focused suite: **242 passed**.
- Full active suite split by file groups because a single combined run exceeds the execution limit:
  - group 1: **206 passed**;
  - group 2: **181 passed**;
  - group 3a: **76 passed**;
  - group 3b: **35 passed**;
  - group 3c: **33 passed**;
  - total: **531 passed**.
- Real download smoke uses local HTTP + actual FFmpeg/FFprobe and verifies two completed MP3 files, resume cleanup and history persistence.
- `PySide6` is not installed in the audit container, so live Qt window/NVDA/JAWS runtime validation could not be performed here.
- `build_qt_exe.bat` explicitly excludes `tkinter`, `ttkbootstrap` and `tk_uia`; runtime import test confirms importing the headless engine does not load `tkinter`.

## Compatibility conclusion

The stable Tk entry point remains available and its download-specific regression coverage remains green. Qt Phase 3 now performs real downloads without constructing or importing Tk UI from the shared download path.

## Next risk area

Queue migration is the next highest-risk area because existing `QueueMixin` still owns Tk variables, table state and operation orchestration. It should consume the new `DownloadService` rather than call Tk downloader actions directly.
