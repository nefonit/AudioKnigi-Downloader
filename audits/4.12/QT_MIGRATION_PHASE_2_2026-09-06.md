# Audit — Qt Migration Phase 2 — 2026-09-06

- Added GUI-independent book analysis service.
- Added Qt analysis worker with cancellation/progress signals.
- Added QAbstractTableModel/QTableView selected-track UI.
- Added GUI-independent DownloadRequest contract for Phase 3.
- Kept stable Tk entrypoint and DownloaderMixin untouched.
- Added Phase 2 regression tests focused on GUI separation and playlist parsing.

## Verification

- `tests/test_qt_migration_phase1_41231.py` + `tests/test_qt_migration_phase2_41231.py` + architecture/search/source/modal group: **28 passed, 1 skipped**.
- knigavuhe/poleknig/book-flow regression group: **30 passed**.
- `python -m compileall -q audioknigi audioknigi_qt.py`: passed.
- Byte-for-byte comparison against Phase 1: unchanged `audioknigi/downloader.py`, `audioknigi/actions.py`, `audioknigi/ui_kit.py`, `audioknigi_gui.py`.
- PySide6 is not installed in the build container, so a live Qt-window smoke test was not possible here; Qt source was syntax/static tested and remains covered by the separate Windows runtime step.
