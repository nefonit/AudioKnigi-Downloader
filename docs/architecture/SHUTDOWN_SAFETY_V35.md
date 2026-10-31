# V35 — Safe shutdown across worker threads and persisted user state

## Addressed shutdown hazards

- **Audiobookshelf test worker:** the close handler already waited for
  download, analysis and search QThreads, but could accept a close while
  the Audiobookshelf connection-test thread was still running. On Qt this
  can destroy a live QThread and abort the interpreter. This thread now
  participates in the same confirmation and bounded cooperative shutdown
  as all other background workers. A timed-out worker still aborts the
  close and restores the main window; no `terminate()` is used.
- **Final queue state:** the app previously persisted settings and playback
  position during accepted exit, but did not perform a final queue save.
  V35 writes the queue (using the V33 last-good snapshot mechanism) before
  settings and the player's forced position save. An interrupted task
  remains `running` on disk only until QueueStore reloads it as
  `interrupted`; completed tasks keep their saved status.
- **Independent failure handling:** a failed queue or settings save does
  not prevent saving the other data. An exception shutting down one
  player/audio/tray controller no longer prevents cleanup of the others.
  Failures are logged, not mistaken for successful persistence.

## Compatibility

- Confirmation defaults to **No**. Declining to close does not modify
  user state or discard a worker.
- Live download/search/analysis/Audiobookshelf workers are never forcibly
  terminated. A timeout cancels the exit instead of silently killing them.
- No new background polling, auto-started downloads or changes to queue
  ordering, player resume schema, settings schema, NVDA/JAWS controls or
  player audio implementation.
- New regression tests use fake events and background-thread doubles,
  and check that user data flush happens only when a close is accepted.

## Limits

A real OS `TerminateProcess` or power outage bypasses Python's close
handler. V33 and V34 provide separate disk-side recovery mechanisms for
that case; V35 cannot promise a final save from a killed process. Manual
Windows force-kill and NVDA/JAWS acceptance testing remain outstanding.
