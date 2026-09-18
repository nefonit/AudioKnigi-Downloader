# Audit notes — Round 27 (2026-09-18)

Windows verification of Round 26 exposed the actual GUI-thread violation. The search worker returned normally, but the log recorded `SEARCH UI | event=finished_slot_enter` and `OPERATION UI | event=finish_begin` under `Dummy-1`, proving that Python mixin callbacks connected with implicit AutoConnection were running in the worker thread and directly touching Qt widgets.

## Fix

- Search progress/completion and search-thread cleanup now use explicit `Qt.ConnectionType.QueuedConnection`.
- Analysis progress/completion and analysis-thread cleanup now use explicit queued delivery.
- Every DownloadWorker callback that touches GUI state (status, log, stage, progress, transfer, missing-media dialog, history reload, request changes and completion) is explicitly queued to the GUI thread.
- Download-thread cleanup is explicitly queued.
- Audiobookshelf completion and cleanup are explicitly queued as well.
- Added a regression that rejects implicit worker-to-window `AutoConnection` patterns in these worker wiring blocks.

## Expected Windows diagnostic

After this fix, `SEARCH WORKER` records remain on a `Dummy-*` worker thread, while `SEARCH UI | event=finished_slot_enter` and all `OPERATION UI` completion records must be logged as `MainThread`.

## Verification

- Round 27 focused regressions: **5 passed**.
- Full pytest suite: **414 passed, 0 failed**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (78 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`; static UI/help/onboarding/accessibility complete).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (`passed=267`, `known_shape_incompatibilities=116`, `resolved=0`).
- `compileall`: **PASS**.
