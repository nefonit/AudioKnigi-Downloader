# Round 87 audit follow-up — 2026-10-10

## Confirmed fixes

- `AppSettings.__delitem__` now reports a missing legacy alias using the caller-visible alias in `KeyError.args`, while still deleting canonical storage when present.
- Ukrainian legacy UI/help wording now consistently uses `розділ/розділи` for book chapters and `озвучення` terminology for narration choices.
- Added runtime localization for `FFmpeg не найден.`, the longer FFmpeg installation guidance, FFmpeg timeout errors, and the expired HTTP 404/410 playlist-refresh failure prefix.
- Added domain-based regression coverage in `test_settings_contract.py` and `test_localization.py`; no round-named test module was created.

## Reviewed and intentionally unchanged

- Blocking `requests` connect cancellation cannot close a response object that has not yet been returned; the existing `(20, 120)` timeout remains a compatibility/reliability choice rather than a resource leak.
- Missing/non-increasing middle boundaries of a shared source remain integrity errors by design; guessing a duration can corrupt all following chapter splits.
- Support-bundle absolute-path collapse remains privacy-first; `%USERPROFILE%`/`~` replacement is still useful for embedded non-collapsed fragments.
- `_suppress_source_transfer_ui` is protected by `finally` and was not changed.
- Multi-file `remote_size` remains intentionally unknown rather than issuing an extra network size request for every chapter; disk preflight retains its duration/bitrate fallback.
- The reported duplicate skipped-parts prefix/regex entry is stale in Round 86: only the prefix rule is present.

## Validation baseline

- 945 tests collected.
- 943 runnable tests passed.
- 2 Qt accessibility self-tests remain environment-blocked because PySide6 is unavailable in the validation container.
- Integration suite: 902 collected cases.
