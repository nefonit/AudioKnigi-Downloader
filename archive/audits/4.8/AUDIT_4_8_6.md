# AudioKnigi Downloader 4.8.6 — chapter timing audit

## Reported defect

For books whose PlayerJS playlist contains separate MP3 URLs but no source `start` / `end` fields, the main chapter table displayed `—` in **Начало**, **Конец**, and **Длительность** even when the MP3 files were already present and their real duration had been measured successfully.

## Root cause

`_scan_book_files()` stored the measured value in `Track.actual_duration`, but `_show_book()` rendered only `Track.start`, `Track.end`, and `Track.duration`. The UI therefore discarded timing data it already had. The total-duration labels and several M4B/sidecar paths also treated missing playlist duration as zero.

## Fix

- Added tolerant parsing for numeric, `MM:SS`, and `HH:MM:SS` playlist timing values.
- Added a best-known-duration helper: playlist duration/source range first, measured local duration as fallback.
- Added a display-only cumulative chapter timeline when source trimming coordinates are absent. `Track.start` and `Track.end` are **not** synthesized, so FFmpeg cut semantics are unchanged.
- Existing local MP3s immediately populate all three timing columns after analysis.
- Unique remote chapter files with no known duration are probed best-effort via `ffprobe` during analysis.
- Tree timing/status cells can refresh during download verification without rebuilding the whole table.
- M4B preview/metadata, sidecars, disk estimates, and completion summary now use the best known duration.

## Regression checks

- `python -m compileall -q audioknigi tests` — passed.
- Timing-specific + UI/theme regression tests — 7 passed.
- Full pytest run — 13 passed; one pre-existing `PytestCollectionWarning` for `tests/test_range.py` remains non-fatal.
- Local HTTP/MP3 smoke test confirmed the remote `ffprobe` duration probe returns a valid duration.
