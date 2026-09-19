# Round 7 audit notes — 2026-09-16

This round was applied on top of `REPORT_FIXES_ROUND6_20260915`. Every report item was checked against the current source rather than accepted mechanically.

## Confirmed defects fixed

- **Two-pass normalization + SSD parallel split:** parallel single-source splitting is disabled for `two_pass` loudnorm so two measurement/transcode pipelines do not compete on the same source and produce cancellation noise.
- **loudnorm JSON parsing:** the parser now scans a bounded 128 KiB stderr tail backwards (maximum 64 candidate braces) instead of repeatedly slicing the entire diagnostic stream for every `{`.
- **Sliding speed meter reset:** a backwards aggregate byte counter clears pre-reset samples instead of mixing two transfer epochs.
- **Segmented Range root-cause preservation:** only the first worker error is retained; peer socket errors caused by coordinator cancellation no longer displace the original failure/fallback signal.
- **Analysis cancellation cleanup:** duration-probe executor shutdown now waits for already-running ffprobe workers after cancellation; pending jobs are still cancelled.
- **Playwright playlist capture:** when multiple `.pl.txt` requests are observed, the latest captured request is used rather than an early redirect/intermediate request.
- **Queue selection recovery:** an explicit serialized `selected_indices=[]` now remains `[]`; it can no longer silently become `None` (which means “all tracks”) and download the whole book.
- **Restricted books:** `DownloadRequest.validate()` reports a rights-restriction error instead of the misleading “analyze the book first” message when the book is intentionally restricted and has no tracks.
- **Legacy localized track states:** Ukrainian/German persisted status strings are normalized back to canonical `missing/present/ready/damaged` values.
- **Audioknigi title/author boundary:** a parsed author prefix is stripped only when followed by an explicit `-`, `–`, `—`, or `:` separator; titles such as `Александр I` are preserved.
- **Windows media-key HWND typing:** RegisterHotKey/UnregisterHotKey now receive an explicit `wintypes.HWND` while the raw integer handle is retained for storage.
- **Speed graph:** rendering still uses a non-zero scale floor, but the displayed peak is the true peak (so an idle `[0, 0]` graph no longer reports a fake `0.1 MB/s`).
- **Normalize quality preset:** the UI no longer stores the contradictory `audio_preset=copy` + `normalization_mode=two_pass`; normalize mode uses `128k_stereo` as the explicit encode profile (while runtime still clamps channels/bitrate to the source where appropriate).
- **Emergency process exit:** best-effort geometry/settings/player-position persistence is attempted before the last-resort `os._exit(0)` path.
- **Dropped multi-URL queue:** cancelling analysis of one dropped URL schedules the next pending URL instead of leaving the remainder stranded in memory.
- **Windows `.url` files:** URL shortcuts are decoded as UTF-16 BOM, UTF-8 BOM/UTF-8, then CP1251/CP1252 fallback instead of destructive UTF-8 `errors=ignore` only.
- **Search cancellation UX:** visible cancel buttons were added to both Advanced and Easy search progress rows and wired to the existing cancellation event.
- **Output-folder synchronization:** wiring/sync now tolerates a partially constructed UI in tests/alternate embedding.
- **Clipboard prompting:** automatic clipboard confirmation is deferred while the application is inactive and retried through the existing `ApplicationActive` hook; it no longer opens a modal over unrelated foreground applications.
- **Narration switching accessibility:** the automatic narration-switch path suppresses the misleading intermediate “URL changed; re-analyze manually” accessible warning because re-analysis is already scheduled.
- **Very short track resume:** the edge guard is proportional on short tracks (and remains 3 seconds for normal chapters), allowing meaningful resume positions in short intros/chapters without retaining near-start/end positions.
- **Localization:** German HTTP download terminology now uses `Range`; Ukrainian progress/help wording and German smartphone wording were corrected; the new search-cancel label is translated for EN/DE/UK.

## Report items intentionally not changed

- `support_bundle._tail()` contains redundant UTF-8 recovery logic, but its final `errors="ignore"` decode already emits valid UTF-8; the alleged FileNotFound/ZIP failure does not follow from the cited code.
- `SlidingSpeedMeter` already removes **all** expired samples in its `while` loop; the report’s “one sample per update” statement is incorrect. Only the real counter-reset case was fixed.
- `%` in ffprobe `-read_intervals` is passed with `shell=False`, so Windows `cmd.exe` environment expansion does not apply. Existing subprocess timeouts already bound pathological seeks.
- The historic setting name `auto_chunk_min_kbps` was documented as mislabeled while UI/runtime semantics were KB/s; blindly dividing migrated values by eight would corrupt existing settings.
- `next_runnable_index()` does not create the claimed automatic infinite retry loop: ordinary failures leave runnable statuses only through explicit retry flows.
- Backup restore already reloads the in-memory queue and player-position store in the Qt restore workflow, so the reported immediate overwrite scenario was not reproduced.
- Missing-media modal closure already resolves the decision to `stop` in `finally`, including window-close paths; the claimed permanent worker wait is not present in current code.
- `QueueTableWidget.dropEvent()` does not call the base implementation, so the claimed second internal row move does not occur.
- History-table sorting is not enabled in the current UI, so the reported sorted-view/index mismatch is not currently reachable.
- The hidden compatibility download buttons are covered by the project’s accessibility contract and the full localization/accessibility audits pass; no speculative restructuring was made.
- The proposed WMF stop/play zero-timer change was **not** kept: an existing Windows-hardening regression specifically protects the current seek/play ordering, while the new report supplied no reproducible failing case.
- Synchronous Playwright `page.goto()` cannot be safely interrupted mid-call without a larger architecture change; current timeout/cancellation checks were retained rather than replacing them with an unverified workaround.

## Verification

- `pytest`: **257 passed, 0 failed**
- Historical regression audit: **271 passed**, no unexpected regressions
- Exception audit: **PASS** (`reviewed_broad_exception_passes=112`)
- Undefined-global audit: **OK (77 modules)**
- Unused-import audit: **OK (32 implementation modules)**
- Qt localization audit: **OK** (`ru, uk, de, en`)
- Full parity audit: **PASS 61/61**
- Static Qt import-boundary audit: **OK (73 project modules, no legacy frontend path)**

The Windows/PyInstaller runtime self-test still cannot be executed in this Linux container; static/import/test coverage is green and the final Windows build should be re-run with `build_qt_exe.bat`.
