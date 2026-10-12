# AudioKnigi Downloader 4.12.42 — additional independent bug hunt

Date: 2026-10-12. Baseline: Round 90, GitHub `main` commit `d81d91923eaa7a346b49515d916e76b834750a76`.

## Confirmed and reproduced bugs

1. **Credential leakage in diagnostic log redaction — high priority.**
   `audioknigi/logging_utils.py`, `sanitize_log_text` previously replaced only the first whitespace-delimited word after an unquoted `Authorization:` header; for example `Authorization: Bearer TOP.SECRET-123` became `Authorization: <hidden> TOP.SECRET-123`. `Cookie: sid=ABC; auth=SECRETTWO` retained the latter cookie. **Fix:** redact the entire authentication/cookie header value before applying general key/value patterns. Preserve the next log line.

2. **Fractional track indices silently truncated — medium priority.**
   `audioknigi/services/download_request.py`, `DownloadRequest.track_index`, used generic `safe_int`, which accepts `2.99` as `2` and `-0.2` as `0`. This could select the wrong chapter for malformed integration input. **Fix:** reject nonintegral/nonfinite numeric values (including `Decimal` and `Fraction`); retain compatibility with integral floats and ordinary integer strings.

3. **Nonfinite playback position written to JSON — medium priority.**
   `audioknigi/services/player_position_store.py` persisted `Infinity` for a playback position with unknown duration, then returned `inf` as a resume position. JSON `Infinity` is nonstandard and an infinite seek position is invalid. **Fix:** normalize nonfinite position and duration values to zero on update and read, including corrupt pre-existing position files.

## Validation

- Reproduced all three original issues using executable Python snippets against the original Round 90 ZIP.
- Added `tests/integration/test_runtime_bug_regressions.py` with parametrized redaction, track-index, and resume-position cases.
- `626 passed`: architecture, units, downloader, media, network, queue, player, services, build and localization tests (including new tests).
- `170 passed`: search, privacy, settings and previous Round 90 regression suites.
- Provider tests passed earlier on the original Round 90 but a repeat network-dependent run stalled; do not count them as freshly verified against this patch.
- `PySide6` is not installed in this Linux test environment; real Windows Qt, NVDA and JAWS acceptance testing remains outstanding.
- These are targeted fixes, not a claim that all possible bugs have been found.
