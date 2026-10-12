# AudioKnigi Downloader 4.12.42 — Round 90 audit follow-up

Date: 2026-10-12

## Implemented and committed
- Crash report functions accept string paths through explicit Path conversion.
- Log sanitizer handles quoted secret values with spaces.
- Partial settings saves preserve existing preferences and do not implicitly complete onboarding.
- Output-directory button callback ignores the Qt checked argument.
- Disk preflight skips negative or uninitialized selection indices.
- A missing loudnorm first-pass JSON report falls back to single-pass normalization.
- Runtime status translations include playlist-refresh and loudness-analysis text.
- Removed a redundant skipped-parts prefix mapping; runtime regex remains authoritative.
- Added targeted regression tests.

## Reviewed, intentionally unchanged
- DownloadRequest.track_index/validate remain strict: invalid indices must raise ValueError rather than silently select the wrong chapters. Normal analysis generates valid track indices.
- Adaptive segmented-download workers may exit when no jobs remain; this alone is not a lost-work defect. No new jobs are added to that queue.
- Playwright response.body() can delay on streaming responses, but the exception path already provides a requests-based fallback.
- Source health's 404/405 classifications indicate an HTTP-reachable host, not necessarily a functioning provider.
- The QueueItem/QueueTask split is an intentional compatibility boundary pending external-API assessment.

## Still requiring dynamic validation
- support_bundle.py's broad Windows path redaction must be tested with representative multiline logs and paths with spaces before narrowing the privacy filter.
- Run the complete pytest suite, Qt accessibility self-test, and NVDA/JAWS manual acceptance on Windows. Passing test counts from Round 89 must not be applied to Round 90.
- Check that strict DownloadRequest.validate behavior, partial settings save semantics, and low-disk-space fallback remain compatible with existing callers.

Status: changes committed; full Round 90 verification not yet completed.
