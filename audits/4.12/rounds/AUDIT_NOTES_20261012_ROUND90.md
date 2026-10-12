# AudioKnigi Downloader 4.12.42 — Round 90 audit follow-up

Date: 2026-10-12

## Implemented and committed
- Crash report functions accept string paths through explicit Path conversion.
- Log sanitizer handles quoted secret values with spaces.
- Partial settings saves preserve existing preferences and do not implicitly complete onboarding.
- Output-directory button callback ignores the Qt checked argument.
- Disk preflight rejects invalid *explicit* selection indices rather than silently underestimating disk space; the download request contract remains strict.
- A missing loudnorm first-pass JSON report falls back to single-pass normalization.
- Runtime status translations include playlist-refresh and loudness-analysis text.
- Preserved the skipped-parts prefix fallback for compatibility; the more specific runtime regex is tried first.
- Added targeted regression tests.

## Reviewed, intentionally unchanged
- DownloadRequest.track_index/validate remain strict: invalid indices must raise ValueError rather than silently select the wrong chapters. Normal analysis generates valid track indices.
- Adaptive segmented-download workers may exit when no jobs remain; this alone is not a lost-work defect. No new jobs are added to that queue.
- Playwright response.body() can delay on streaming responses, but the exception path already provides a requests-based fallback.
- Source health's 404/405 classifications indicate an HTTP-reachable host, not necessarily a functioning provider.
- The QueueItem/QueueTask split is an intentional compatibility boundary pending external-API assessment.

## Still requiring dynamic validation
- support_bundle.py: three targeted path-privacy cases passed against the Round 89 implementation (multiline log continuation, file-path error suffix, and ambiguous directory path). The directory-path ambiguity cannot be reliably resolved without additional delimiters; preserve conservative redaction to avoid leaking names. The same tests are committed for Round 90. Full-suite validation remains outstanding.
- Run the complete pytest suite, Qt accessibility self-test, and NVDA/JAWS manual acceptance on Windows. Passing test counts from Round 89 must not be applied to Round 90.
- Check that strict DownloadRequest.validate behavior, partial settings save semantics, and low-disk-space fallback remain compatible with existing callers.

Status: changes committed; full Round 90 verification not yet completed.

## Validation update (2026-10-12)
- On the Round 89 source archive, 100 focused privacy/settings tests passed (`test_privacy_diagnostics.py` and `test_settings_contract.py`). These are baseline tests, not a confirmation of the subsequent Round 90 code edits.
- Three focused support-bundle path-boundary tests passed in a separate local validation workspace.
- Running the full Round 89 suite in this Linux environment encountered `ModuleNotFoundError: No module named 'PySide6'` in Qt accessibility self-tests. An additional run excluding the accessibility module reached roughly 64% before the execution time limit; no full-suite pass can be claimed.
- The exact current GitHub Round 90 revision was not recreated as a complete runnable local checkout. Full Round 90 regression validation, particularly Qt/NVDA/JAWS on Windows, is still required.

## Consolidated regression check (2026-10-12, Linux)
- The initial archived Round 90 source had 8 failing tests among 905 non-accessibility tests. Root causes: disk preflight silently ignored invalid explicit selections (3 failures), removed translation prefix contrary to compatibility contracts (2), missing localized FFmpeg loudnorm warning (2 static/historical audit failures), and a test filename containing `audit` that broke the test layout rule (1).
- Restored strict invalid selection rejection; retained prefix fallback while preserving regex precedence; added EN/DE/UK translations for the loudnorm fallback warning; renamed the Round 90 test module from `test_round90_audit.py` to `test_round90_regressions.py`.
- Disabled live remote-size probes in two *metadata-only test cases*; no production network behavior was changed. This prevents test hangs when offline or when external sites are slow.
- Re-ran every non-accessibility test in five independent groups, yielding **905 passed, 0 failed**: 75 architecture/unit/quality, 122 core-services/Round90, 156 providers, 282 download/build/localization/media/network, and 270 player/privacy/Qt-contract/queue/search/settings.
- The all-in-one run remains unverified because it stalled on external I/O in this environment. The five groups collectively cover all 905 tests collected with `--ignore=tests/integration/test_accessibility.py`.
- `python tools/qt_localization_audit.py`: OK.
- `PySide6` is not installed in the Linux environment, so Qt accessibility tests and Windows NVDA/JAWS acceptance remain pending. No Windows executable was tested or built here.

## Follow-up review: pasted audit (2026-10-12)
- The current `runtime_exact.json` has no duplicate occurrences of `Аудиоссылка устарела — обновляю плейлист…` or `Проверить системный звук`; its entries were already deduplicated by the earlier Round 90 rewrite. Added a duplicate-key regression test to prevent a recurrence.
- The current `runtime_exact.json` already includes the loudnorm no-statistics warning and its EN/DE/UK translations.
- Confirmed that the disk-space-check failure text in `download/probe.py` was untranslated. Added EN/DE/UK mappings for the multiline warning and the single-line exception used by `book_flow.py` and `download_engine.py`, plus a localization test.
- The raw-string regular expressions in `diagnostics/support_bundle.py` compile on Python 3.13 with SyntaxWarning treated as error. No regex semantics were changed based on the audit's incorrect warning claim.
- `diagnostics/session.py` still uses supported `typing.Mapping`. Changing to `collections.abc.Mapping` would be cosmetic, not a bug fix.
- Other findings (network parked-worker exit, source reuse, FFmpeg fallback, cancellation, and Qt safeguards) describe currently intended behavior and were not modified without a reproducible regression.
- This review does not replace a full Windows Qt/NVDA/JAWS test.
