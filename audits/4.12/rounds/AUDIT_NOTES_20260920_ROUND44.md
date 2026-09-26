# Round 44 — Persistence, privacy and cancellation hardening follow-up (2026-09-20)

Round 44 reviews the second external audit after Round 43. As with the previous pass, findings were checked against the current code rather than applied mechanically. Confirmed runtime defects received focused regressions; speculative or already-covered findings were left unchanged.

## Confirmed fixes

- `AppSettings` direct partial mappings now preserve their explicit Mapping shape/value contract while missing documented settings can still be read safely from `DEFAULT_SETTINGS`. This avoids ordinary-key `KeyError` without changing the established equality and UI-scale migration behavior of partial mappings. A zero-argument `AppSettings()` still materializes the full default mapping.
- Support-bundle log files are sanitized before they enter the ZIP. Embedded Windows paths, Authorization/Cookie headers, bearer credentials, and common `token`/`api_key`/`password`/`secret` assignments are redacted in addition to the existing settings sanitization.
- Atomic text/byte writes now add a per-call `time.monotonic_ns()` token to temporary filenames, preventing same-process/same-thread retries from colliding with a stale temp file.
- FFmpeg execution helpers close their subprocess pipes deterministically in `finally`, matching the existing ffprobe cleanup path.
- Audioknigi relevance matching now supports query initials against full author/narrator names while preventing a lone one-letter query or an unrelated initial from becoming a false positive.
- Audioknigi search parsing accepts relative `audio-*` links without a leading slash and retains the canonical host/path validation after `urljoin`.
- Audioknigi response decoding preserves the existing UTF-8/BOM path while honoring explicitly declared legacy encodings (and apparent encoding in the detail-page helper), avoiding Cyrillic corruption on non-UTF-8 responses.
- Player-position persistence now serializes the state mutation and JSON write under the same lock, so an older slow snapshot cannot overwrite a newer resume position on disk.
- Large source cover images are no longer embedded into `qt_queue.json`: only cover payloads up to 256 KiB are persisted inline. The source `cover_url` remains available for re-fetch, and small thumbnails retain the existing offline queue-preview behavior.
- The Windows system-sound worker now observes its shutdown event both while waiting on an empty queue and after dequeuing a sound, so it cannot remain alive solely because a shutdown sentinel was lost/raced.
- Accessibility focus tracing disconnects late Qt focus/about-to-quit callbacks before closing its diagnostic stream.
- Qt player seek persistence now remembers a recent requested seek target and uses it when the Windows multimedia backend has not yet reported the asynchronous new position. Immediate Stop/Shutdown after `+30/-30`, slider seek, or chapter navigation therefore cannot save a stale pre-seek position.
- Browser-session persistence compares cookies/headers with the already persisted material. Re-saving identical Playwright session data no longer tears down healthy thread-local requests pools; changed session material still invalidates them immediately.

## Reviewed and intentionally unchanged

- Package-relative imports in `audioknigi.config`, `audioknigi.diagnostics`, and provider adapters match the actual directory hierarchy; the reported `ImportError` scenarios assumed a different package layout.
- Qt accessibility self-test teardown already closes the window/controllers and flushes deferred deletes; changing QPA environment variables after an existing `QApplication` is intentionally avoided.
- A `Path` object cannot retain whether its original textual spelling ended in `/` or `\\`. String destinations with trailing separators remain the explicit directory form; ambiguous non-existing `Path("name")` behavior was not redefined.
- The segmented downloader already checks cancellation/peer abort after request-layer failures and performs bounded shutdown of active responses; no speculative long-running worker rewrite was introduced without a reproducible stuck transfer.
- The loudnorm JSON parser intentionally scans bounded stderr backwards with `JSONDecoder.raw_decode`; replacing it with a broad regex would be less structurally reliable.
- Cross-provider fallback for a partially selected chapter set remains conservative because chapter indices from different providers are not guaranteed to represent the same logical chapters.
- Duration caches mutate only while holding their dedicated locks; the reported concurrent dictionary-iteration race does not occur in the current code.
- Provider registry imports are not cyclic at module import time because `BookAnalysisService` is imported lazily inside adapter methods.
- Queue empty-selection semantics, library symlink walking, partial-provider search warnings, operation-dialog lifetime, track-model row summaries, and worker request ownership were checked against current code and did not match the reported failure modes.
- Localization duplicates/wording observations are maintenance/content cleanup items rather than runtime correctness defects and were not mixed into this hardening patch.
- Multi-file remote-size prefetch, full-MP3 disk estimation, and the language-stable `{Author}` filesystem placeholder remain deliberate performance/path-identity policies.

## Verification

- Round 44 focused regressions: **13 passed**.
- Full pytest suite: **560 passed, 0 failed**.
- Historical regression audit: **PASS** (`passed=256`, `known_shape_incompatibilities=127`, `resolved=0`).
- Full parity: **PASS 61/61**.
- Qt import audit: **OK** (75 project modules reachable, no legacy frontend path).
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- `compileall`: **PASS**.
