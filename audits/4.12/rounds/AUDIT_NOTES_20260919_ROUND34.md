# Audit notes — Round 34 (2026-09-19)

Round 34 validates the 2026-09-19 audit against Round 33 and prioritizes the user-observed PoleKnig annotation regression.

## Confirmed and fixed

- PoleKnig now prefers visible synopsis/annotation content over SEO meta descriptions such as “скачать/слушать аудиокнигу…”. JSON-LD/meta are only fallback sources and SEO-like descriptions are rejected.
- Standalone one-file-per-chapter audio is no longer trimmed by rounded metadata duration via FFmpeg -t; with no start/end slicing boundary the physical file is processed to EOF.
- Segmented cancellation closes active network I/O and gives worker threads a bounded grace period to release Windows .seg/.part handles.
- Retained full-source suffixes use URL extension, container and codec consistently; extensionless M4A/AAC no longer falls back to generic .audio.
- Knigavuhe restricted pages consistently return metadata-only Book(restricted=True); download validation still blocks restricted content.
- BookController.enter parsing now requires an actual call instead of scanning ahead from assignments.
- Broken-source fallback removes the obsolete old-source resume manifest before switching books.
- Persisted boolean settings normalize string/number forms explicitly.
- Cover sidecars use atomic binary writes.
- Audioknigi author-prefix cleanup handles reordered/expanded person names without stripping unrelated dashed titles.
- Failed search providers report an error status instead of “source processed”.
- Queue drop coordinates use the event’s viewport coordinates directly.
- Opening a local player file from Easy mode reveals the Advanced Player tab.
- Easy mode disables the previous-book Download action when input no longer identifies the analyzed book.
- Retry-all skips queue tasks that still require analysis.
- Deferred search rendering aborts during exit to avoid touching deleted Qt objects.
- Keyboard Shift+F10 on the chapter table selects the first row when no current row exists.
- Dynamic source/fallback/skip messages received runtime regex translations; German narration terminology is aligned to Sprecherfassung.
- Help text now matches case-insensitive template tokens introduced in Round 33.

## Reviewed and intentionally unchanged

- PoleKnig short-title fuzzy compatibility remains conservative to avoid false-positive variant merging.
- Output_Dir remains intentionally relative inside folder templates; expanding the absolute base would duplicate the root.
- DNS negative caching remains bounded by its normal short TTL.
- Queue-cover Base64 persistence is architectural/performance work and was not mixed into this correctness round.
- Audioknigi pagination/provider parallelism remain separate feature/performance work without a verified pagination contract.
- Explicit Path(.) remains a valid service-level output path; empty settings are already normalized to DEFAULT_OUTPUT before request construction.
- The missing-media dialog already closes when the worker resolves its prompt, including timeout.
- Live UI scaling and first-run stereo wording remain UX policy choices rather than reproduced correctness defects.

## Verification

- Round 34 focused regressions: 20 passed locally.
- Current pytest suite excluding the historical wrapper: 482 passed, 0 failed.
- Historical wrapper test: 1 passed.
- Effective current pytest contract: 483 passed, 0 failed.
- Historical regression audit: PASS (passed=264, known_shape_incompatibilities=119, resolved=0).
- Qt localization audit: OK (ru, uk, de, en).
- Exception audit: PASS (reviewed_broad_exception_passes=107).
- Undefined-global audit: OK (79 modules).
- Unused-import audit: OK (32 implementation modules).
- Full parity: PASS 61/61.
- compileall: PASS.
