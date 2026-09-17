# AudioKnigi Downloader 4.12.19 — Duplicate Guard & Cancel

## Duplicate detection

The manual advanced-mode “Проверить скачанные файлы” button was removed. `download_selected()` is now the single preflight entry point used by simple mode, advanced mode and automatic download after analysis.

A duplicate modal is shown only when all book parts are selected, the requested output mode is already complete, and metadata identifies the same book/source. `metadata.json` is preferred when available; a matching `history.json` record is a fallback when sidecars were disabled. Partial selections bypass this dialog intentionally.

## Cancel behavior

`cancel_current()` is idempotent. The first click sets the shared cancellation event, disables both cancel buttons, changes their label to “ОТМЕНЯЮ…”, logs the request, and closes currently registered streaming HTTP responses. Download loops preserve `.part`/segment data and raise `Cancelled` rather than converting a cancel-triggered network close into a network error. FFprobe duration subprocesses poll the same cancellation event and are killed promptly. FFmpeg already had cooperative cancellation and retains it.

A provider-page connection that is still inside the underlying blocking `requests.get()` connection/read establishment cannot be force-killed portably by Python; cancellation is checked immediately before/after those calls so later work cannot continue after the request returns.
