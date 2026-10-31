# V33 — Restore queue and download history after interrupted application writes

## Identified failure mode

The application already atomically writes `qt_queue.json` and `history.json`.
An active queue task is normalized from `running` to `interrupted` on
reload, so its in-progress status is not mistaken for a completed task.

Before V33, invalid primary JSON could make `load_json(..., [])` return an
empty list. A subsequent save could overwrite the damaged queue or history.

## Recovery contract

`services/state_recovery.py` writes `qt_queue.lastgood.json` and
`history.lastgood.json` after successful primary saves. These snapshots
are atomic, best-effort copies of the most recently persisted valid list.
The primary JSON schema, on-disk names and public service APIs are unchanged.

On load:
- A valid primary list is authoritative, including an intentionally cleared
  queue or history.
- A missing primary remains empty; deleted state is not resurrected.
- For corrupt JSON or the wrong top-level type, original bytes are preserved
  as `<stem>.corrupt-<12hex>.json`. A valid mirror is returned in memory.
  Reading never silently replaces the primary file.
- Without a valid mirror, original damaged bytes still remain available and
  an empty list is returned.
- If the snapshot update fails after a primary save succeeds, the primary
  save still reports success. A mirror can be older than the latest changes.

The download engine's history insertion and duplicate lookup now use the
same recovery-aware reader while holding the existing history lock. Queue
task statuses, selection, ordering, disabled tasks, and library history UI
remain unchanged. The application never auto-starts queued downloads on
startup.

A cleanly crashed/stopped task recorded as `running` is restored to
`interrupted`; completed tasks remain completed. The existing source resume
manifests and V29–V32 segment integrity operate independently.

## Limits and tests

This is local corruption recovery, not a substitute for a user-created
backup. Tests in `tests/unit/test_state_recovery_v33.py` exercise valid
and missing files, malformed JSON with exact-byte preservation, invalid
mirrors, intentionally empty states, queue task status transitions,
history recovery, and failure of either primary or mirror save.
