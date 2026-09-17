# Audit 6 follow-up fixes — 2026-09-11

This pass was applied to the Phase 39 Qt-only source after AUDIT5.

## Fixed

- Requests/Playwright analysis boundary in both downloader paths: successful HTTP parsing is now separated from shared-source recovery. A short/truncated source or missing Knigavuhe fallback no longer gets misclassified as an HTTP/WAF failure and no longer launches Chromium just to fail again with the same recovery error.
- Downloader active I/O registration: lazy creation of subprocess/network locks is protected by one module-level initialization lock; the WeakSet/set is still validated under the per-instance lock. This keeps standalone mixin hosts safe under concurrent registration.
- Duplicate identity matching: volatile `description` and `cover_url` (and other presentation-only fields) no longer invalidate otherwise exact metadata/history identity. Stable source URL/folder/part count plus title/author/narrator and sidecar track metadata remain the evidence.
- GUI duplicate preflight: `DownloadService.duplicate_preflight()` has a `probe_durations` option. The Qt UI uses `probe_durations=False`, so the main thread checks non-empty files + sidecar/history evidence without launching dozens of FFprobe operations. Headless/default callers retain strict duration probing.
- Required-space estimation: partial `_source_XX.mp3.part` and completed `_source_XX.mp3` files from multi-source assignments are now included instead of looking only for `_source.mp3`.
- Playwright request headers: document headers use the Python `request.headers` mapping first and fall back to callable `all_headers()` only when available.
- Knigavuhe `merged_playlist`: positional `fallback_file` mapping is allowed only when merged and primary playlist lengths are equal. A compact merged playlist can no longer be attached to unrelated chapter numbers.
- Search cancellation: Knigavuhe and PoleKnig searches now consistently raise `Cancelled` for an already-set or mid-flight cancellation event, matching `fetch_book` and the downloader/queue contract.
- Audiobookshelf integration: `ConnectionError`, timeout and other `RequestException` failures are converted to user-level errors; HTTP failures are wrapped too, with a specific API-key message for HTTP 401. Existing SSL and non-JSON diagnostics remain intact.
- Cloudflare HTTP proxy relay: ordinary one-request HTTP proxying now returns immediately when the upstream socket reaches EOF, while CONNECT tunnels retain bidirectional half-close semantics.
- PoleKnig PlayerJS fallback property scan: `playlist`/`file`/`files` matches require a property boundary, so suffixes such as `profile:` or `tempfile:` are not treated as audio properties.
- Accessibility: direct `announce()` calls from a worker thread now route through the window's `AccessibleAnnouncer` queued-signal path when available, and otherwise return instead of invoking QAccessible from the wrong thread.
- Event sounds: pending `mediaStatusChanged` callbacks are disconnected before clearing an asynchronous QMediaPlayer source during shutdown/reconfiguration.
- Qt application startup: `run_qt()` loads/migrates settings once and passes them to `create_application()`, avoiding the duplicate read/parse while keeping direct `create_application()` calls self-contained.
- Templates: an empty `{Track_Title}` now falls back to the book title instead of duplicating the track number (`01 - 01.mp3`).
- Quality settings synchronization: both advanced and easy quality combos use a valid explicit `quality_preset` first and the audio/normalization-derived value only as a migration fallback.
- Search model accessibility: vertical header DisplayRole now returns text (`str`) consistently.
- Player usability: localized file/folder dialogs, single-click chapter activation (with idempotent same-source handling), local chapter-list population from an analyzed/downloaded Book, and path-based row selection allow auto-next to work even when playback started from the Book tab rather than by opening a folder manually.
- Narration variants: the retained variants list is keyed by normalized book title+author. A different book without variants can no longer inherit the previous book's narrators.
- Main-window dialogs: resume-download, add-URL, export/backup/restore picker titles are localized.
- Deferred exit: the tray controller is shut down as soon as deferred exit begins, preventing a hidden exiting window from being restored during the five-second worker grace period.
- Book analysis short-source threshold: Qt/headless analysis now uses the same `max(15 s, expected_end * 0.001)` formula as the downloader shared-source validation.
- Help text: legacy Alt+1…5 wording was updated to the current Ctrl+1…6 navigation including the Player tab.
- Player position history: the resume store is bounded to the 2,000 most recently updated unfinished entries, while completed/start-of-track records continue to be removed eagerly.

## Reviewed but intentionally not changed

- `auto_chunk_min_kbps`: the persisted key name is historically misleading, but the current settings UI explicitly labels values as `KB/s`, and the downloader correctly converts KB/s to bytes/s with `* 1024`. Changing the arithmetic to kilobits would introduce an 8× regression. The internal local variable/comment were clarified while retaining the stored key for compatibility.
- Runtime prefix/regex overlap in `i18n.py`: some duplicate localization rules are dead/redundant but do not affect output because regexes intentionally have priority. Removing them is cosmetic and was not mixed into this functional pass.
- PoleKnig last compact chapter duration: the compact playlist itself does not provide a trustworthy final end timestamp. Keeping it unknown lets downstream probing/end-of-file behavior determine the real tail instead of inventing a value.
- Author initials vs full names: broad fuzzy equivalence (`Л. Н. Толстой` vs `Лев Николаевич Толстой`) can merge different people; this was not changed without a stronger identity signal.
- Audioknigi search labels containing a dash: the initial split remains a heuristic and page hydration replaces temporary metadata with authoritative page metadata. No unsafe author/title guessing rule was added.

## Regression coverage added

`tests/test_audit6_followup_20260911.py` covers the requests/recovery boundary, merged-playlist safety, cancellation contracts, stable duplicate identity, non-probing GUI preflight, Audiobookshelf errors, template fallback naming, settings synchronization, player auto-next/single-click contracts, narration-cache identity, synchronized long-book tolerance, ordinary HTTP relay EOF, bounded resume storage, dialog/help localization, active-I/O lazy initialization and Playwright header compatibility.

## Validation

- `python -m pytest -q`: 350 passed
- Full Parity Audit: PASS 61/61
- Qt Localization Audit: OK for ru/uk/de/en
- Qt Import Audit: OK, 46 project modules reachable and no legacy frontend path
- `python -m compileall -q audioknigi tests tools`: PASS
- `qt/main_window.py`: below 4,000 lines
