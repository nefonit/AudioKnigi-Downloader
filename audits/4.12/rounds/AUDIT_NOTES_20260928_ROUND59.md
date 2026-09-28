# Round 59 — external-audit hardening — 2026-09-28

Round 59 reviews the uploaded multi-part static audit against the actual post-Round-58 main branch. The report mixes current findings with stale snapshots and theoretical/style observations, so changes were made only where the present source still had a concrete failure mode or where a small defensive hardening was low risk.

## Confirmed and fixed

- Diagnostic privacy now collapses configured POSIX absolute paths and redacts embedded Linux/macOS paths, including filenames containing spaces. URLs remain intact.
- Sidecar cover data is normalized immediately before unpacking.
- Adaptive Range concurrency is sampled at most once per reporting interval, preventing simultaneous forced worker reports from counting as multiple slow/fast observations.
- `tag_jobs` is initialized before the MP3 branch.
- AudioKnigi detail hydration accepts cancellation, uses bounded HTTP timeouts, shares the common response decoder, supports partial initial expansion such as `А. С. Пушкин` vs `Александр Пушкин`, and rejects pure dotted acronyms without rejecting longer human initial forms.
- Human chapter labels such as `Chapter_01`, `Track-01`, `Part_1`, and `CD1_01` are no longer treated as disposable machine slugs.
- Player-position timestamps are persisted as timezone-aware UTC ISO 8601 values.
- Qt event-sound configuration is marshalled to the QObject's thread before touching QAudioOutput/QMediaPlayer objects.
- Track selection emits all data roles so Windows accessibility caches refresh; a reusable selected-index setter was added.
- Single-track download/re-download snapshots its request without destroying the user's previous chapter selection.
- Narration switches preserve "all selected" across different chapter counts, preserve explicit indices only for equal chapter geometry, and otherwise require an explicit re-selection instead of silently applying old indices to a different split.
- Queue deletion clears the stale pre-delete selection before rebuilding the table, avoiding duplicate rapid focus restoration.
- Crash-report hooks cannot replace the original unhandled exception if report generation itself fails.
- The player suppresses duplicate EndOfMedia and treats immediate zero-duration EndOfMedia as a playback error instead of auto-advancing rapidly across broken chapters.
- The local DNS proxy accepts both CRLF and LF-only HTTP header separators.
- The Qt accessibility self-test uses the stable no-argument `QCoreApplication.sendPostedEvents()` overload.
- Persisted custom advanced audio/normalization values are not overwritten merely while settings controls are synchronized.
- Changelog literal `\n\n` artifacts are converted to real Markdown breaks; the 4.12.42 heading is marked updated through 2026-09-28; release dependency-baseline wording is clarified.
- Runtime exact translation objects use consistent `de`, `en`, `uk` key order.

## Reviewed but not treated as current bugs

Examples include the reported BandwidthLimiter zero-capacity loop (nonzero rates have a minimum 64 KiB capacity), boolean selected-index rejection (intentional validation), duplicate runtime-exact sound keys (not present in current main), media-key HWND truncation (current code already uses pointer-width `c_void_p`/HWND), missing-media close deadlock (current lifecycle resolves the prompt/cancel event before bounded waits), global exception-hook leakage (hooks are restored in `finally`), and several localization/style/facade observations that do not create a runtime failure.

## Regression coverage

`tests/integration/test_external_review_hardening_20260928.py` covers POSIX support-bundle privacy, initial matching, cancellation-before-HTTP, meaningful playlist labels, UTC player timestamps, LF-only proxy requests, source-level Qt/thread/selection contracts, changelog formatting, and runtime translation consistency.
