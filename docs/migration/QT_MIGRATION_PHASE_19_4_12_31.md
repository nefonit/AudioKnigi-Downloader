# Qt Migration Phase 19 — single-download recovery and crash-safe fallback persistence

Phase 19 is a Qt-only hardening release based on the post-Phase-18 audit. It does not restore any retired Tk code and keeps the full 61/61 capability inventory.

## Confirmed fixes

1. `_download_single()` again calls `get_http_session()` before `session.get()`. This was a real Phase 18 regression and would crash every non-segmented transfer.
2. `DownloadCallbacks` now exposes `request_changed`. When the downloader switches from a damaged Audioknigi shared source to a Knigavuhe fallback, the worker emits a deep-copied request snapshot and Qt immediately persists it into the active queue task. This closes the crash/power-loss window between fallback selection and `_download_finished()`.
3. Loudnorm JSON extraction uses `json.JSONDecoder.raw_decode()` and selects decoded dictionaries containing `input_i`; arbitrary braces in diagnostic text no longer confuse the parser.
4. The Windows system-sound worker consumes and acknowledges its sentinel, shutdown drains stale queued cues, and cached Qt multimedia objects are scheduled with `deleteLater()`.
5. `MappingDataclass._plain_value()` serializes nested ordinary dataclasses field-by-field.
6. `create_application()` independently strips the private focus-trace CLI option.
7. Deferred exit is centralized. Confirming exit cancels all active workers, hides once, and polls until all QThreads stop. Cleanup slots do not reactivate controls while exit is pending.
8. PoleKnig generic-search request timeout is bounded to `(6, 15)` for faster cancellation.

## Findings intentionally not changed

- `is_supported_url()` already validates concrete book paths in Phase 18; author/genre/service pages are rejected.
- `task_requires_analysis` exists and is exported.
- `text/x-python` was a MIME marker in an external dump, not a repository filename.
- `_split_track()` assigns `out` before entering the FFmpeg fallback block; `_track_path()` failure exits the function and cannot reach a read of an unbound `out`.
- Current PoleKnig book pages use numeric `/books/<id>` URLs. No speculative slug pattern was added.
- A final compact timeline item with a start marker but no following marker intentionally trims from its start to the physical EOF because the source format provides no later boundary.
- `_relay_bidirectional()` socket ownership remains with its caller/socketserver; TIME_WAIT is an OS TCP state, not a leaked Python socket reference.

## Verification

- active Qt-only tests: 103/103 PASS
- strict full parity: 61/61 PASS
- Qt import boundary: 39 project modules / 0 legacy frontend paths
- `compileall`: PASS
- native Windows PySide6/NVDA/JAWS validation remains required for the final executable
