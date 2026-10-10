# Round 83 — external audit follow-up

Applied confirmed, low-risk findings from the 2026-10-10 follow-up review:

- support-bundle POSIX redaction now preserves HTTP request targets such as `GET /search` and `POST /api/books/42` while retaining privacy-first masking for real local absolute paths;
- `AppSettings.__delitem__` now maps legacy write aliases (`normalize_audio`, `auto_chunk_min_kbps`) to their canonical stored keys, matching the existing legacy-write contract;
- German persisted boolean values `ja` / `nein` are recognized by settings and queue deserialization, including `Track.selected`;
- download-domain missing-media exceptions normalize track indices safely instead of calling raw `int()` on booleans/malformed values;
- `restore_backup()` snapshots `history.json` under `HISTORY_LOCK`, matching the lock discipline already used for backup/history writes;
- `QueueTask.url` now fails closed to an empty string for malformed legacy tasks without a usable book object;
- full-MP3 naming removes a leading `{Track_Number}` token from ordinary per-track custom templates, avoiding meaningless `01 - Book.mp3` whole-book names;
- a failed retained-source `shutil.copy2()` removes a partially copied final target while keeping the complete hidden source available for retry;
- switching from Easy to Advanced UI while an Easy-only blocking operation is active releases the central/menu block, while switching back to Easy reapplies it;
- `focus_table_row()` treats a deleted Qt wrapper as a stale delayed UI callback and returns `False` instead of letting `RuntimeError` escape;
- settings synchronization chooses the nearest supported player rate for legacy/nonstandard values instead of leaving a fresh combo box at its first 0.75× entry.

Reviewed and intentionally unchanged:

- Windows directory-like diagnostic redaction continues to prefer over-redaction to accidental path disclosure;
- support-bundle destination semantics (existing directory versus file-style path) are part of the current API and were not changed without a migration contract;
- `AppSettings.__contains__` remains canonical-storage membership by design; direct alias reads after the canonical key itself is deleted may raise `KeyError`, as ordinary `MutableMapping.__getitem__` semantics allow;
- shared-source tracks with a missing/non-increasing middle boundary deliberately raise `SharedSourceTimelineError`; existing regressions protect this integrity rule because reading to EOF would duplicate/corrupt later chapters;
- repair downloads are already keyed by source URL in `repaired_sources`, so multiple damaged chapters from one source reuse one repair source rather than creating an unbounded series of files;
- the runtime book pipeline intentionally requires typed `Track` objects even though selected boundary helpers accept Mapping-compatible data;
- surname-only versus initialled author identities stay conservative to avoid merging unrelated people who share a surname;
- Playwright `response.body()` is already guarded and followed by the requests fallback;
- template path fallbacks remain language-stable by design so changing UI language does not rename existing library folders;
- the `Signal(object, object, object)` event-sound configuration warning was not reproducible and is not changed speculatively;
- `CircularSearchProgress.stop()` sets `_active = False`; delayed `showEvent()` therefore cannot restart its timer under the reported sequence;
- dependency-status internal sentinel text is replaced by localized output before display;
- queue context-menu reorder behavior has existing bounds checks and no reproduced crash;
- dependency pinning/CI policy is intentionally deferred to the separate repository/CI hardening stage rather than mixed into this runtime audit round.
