# Qt Migration Phase 4 — Queue

Date: 2026-09-06

## Goal
Move queue orchestration to the Qt branch without importing the legacy Tk `QueueMixin`.

## Implemented
- New GUI-neutral `audioknigi/services/queue_service.py`.
- Persistent `qt_queue.json` under the application data directory.
- A queue entry stores a complete `DownloadRequest` snapshot: book metadata, tracks, selected indices, output directory and naming/audio/template options.
- A task that was `running` when the process ended is restored as `interrupted / Незавершено`.
- Qt queue controls: start, pause current, resume, stop, retry, priority, move up/down, remove.
- Sequential queue execution reuses the Phase 3 `DownloadService` and its `.part`/`resume.json` behavior.
- Priority tasks are chosen before normal pending tasks.
- Failed tasks do not auto-loop. They require explicit Retry.
- Closing Qt while a queue download is active stops queue continuation and leaves the current item recoverable.

## Accessibility
Queue controls have Qt accessible names and identifiers. Queue state is presented in a standard `QTableWidget` with row selection and textual status/error columns.

## Compatibility
The legacy Tk `queue_manager.py` remains in place and is not imported by the Qt queue. The Phase 3 download engine remains shared.

## Deferred
- Player migration.
- System tray migration.
- True process-level suspension is not used. “Pause” performs a safe cancellation and resumes through the downloader's `.part`/resume mechanism.
