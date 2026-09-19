# Audit notes — Round 28 (2026-09-18)

Round 27 correctly kept worker code off the GUI thread, but Windows verification showed the opposite failure mode: search stayed visually at 5% while the worker completed all providers and returned 115 results. Only `thread.finished` cleanup reached the main thread; queued connections targeting Python mixin methods did not reliably deliver progress/completion callbacks.

## Fix

- Added `WorkerUiRelay(QObject)`, instantiated as a child of the main window on the GUI thread.
- Search, analysis, download and Audiobookshelf worker signals now target typed slots on that real QObject with `Qt.ConnectionType.QueuedConnection`.
- Relay slots call the existing mixin UI handlers only after Qt has delivered the signal on the relay's GUI-thread affinity.
- Thread-finished cleanup callbacks use the same relay.
- Added a `WORKER UI RELAY | event=search_finished_dispatch` diagnostic marker.
- Updated Round 27 regression coverage to forbid bypassing the QObject relay and added Round 28 relay-specific tests.

## Expected Windows diagnostic

During search, `SEARCH WORKER` remains on `Dummy-*`. Progress should advance beyond 5%. At completion, `WORKER UI RELAY | event=search_finished_dispatch`, `SEARCH UI | event=finished_slot_enter`, and `OPERATION UI` completion records should all be `MainThread`.

## Verification

- Round 27+28 focused regressions: **9 passed**.
- Full pytest suite: **418 passed, 0 failed**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`; static UI/help/onboarding/accessibility complete).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (`passed=267`, `known_shape_incompatibilities=116`, `resolved=0`).
- `compileall`: **PASS**.
