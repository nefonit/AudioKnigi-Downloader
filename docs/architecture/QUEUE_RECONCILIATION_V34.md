# V34 — Reconcile completed downloads after an abrupt shutdown

A crash can occur after valid output files and metadata have been persisted
but before Qt saves a queue task as `completed`. V33 already restores
`running` to `interrupted`; V34 closes the gap on the next manual queue run.

## Recovery algorithm

When an `interrupted` task is selected by the queue, the normal download
worker receives a one-time `recover_existing` flag. It runs the existing
`DownloadService.duplicate_preflight` in the background, with positive audio
probe checks for chapter files and the existing full-MP3 metadata/file checks.
Nothing runs automatically at application startup.

Only if all required output files and book metadata match the selected
book does it repair history with the existing idempotent `_add_history`.
After confirming a matching history entry, it removes the now-stale
`resume.json` and returns an ordinary `DownloadResult`. The existing GUI
completion callback then persists the queue task as `completed`.

If files are missing, invalid, unproven, represent only a subset of the
selected chapters, or history cannot be saved, recovery returns `None` and
the ordinary resumable downloader runs instead. No new deletion or
overwriting of audio is introduced by the reconciliation path.

Only tasks restored as `interrupted` receive this check. User-initiated
downloads and explicit retries retain the old workflow. The existing
`DownloadWorker` thread hosts all file and duration probing, so no new
synchronous disk scan is added to the NVDA/JAWS UI event loop.

## Consistency and limitations

This reconciles book outputs, `history.json`, and `qt_queue.json` through
existing tested save operations; it does not attempt a cross-file atomic
transaction (which the filesystem cannot guarantee). A second abrupt exit
is safe to reconcile again because history writing deduplicates the same
book/folder. A corrupted or incomplete output is **not** marked complete.

Full-MP3 validation uses the existing full-MP3 duplicate preflight contract
(non-empty output plus matching metadata); it is not a cryptographic
authentication of media contents. Real kill-process testing on Windows
remains a separate manual acceptance step.

Focused worker, service and task-state tests are in
`tests/unit/test_queue_reconciliation_v34.py`.
