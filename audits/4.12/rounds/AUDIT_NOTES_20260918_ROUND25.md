# Audit notes — Round 25 (2026-09-18)

Windows user verification of Round 24 found a deterministic Easy-mode freeze after a title search reached 100%. CPU usage stayed low and the application was reported as not responding. The support log showed all three search providers finishing network activity, with no crash traceback.

## Fix

- Search orchestration now reports 99% while returning the final SearchOutcome; 100% is reserved for the GUI slot that has actually received worker completion.
- The SearchWorker logs explicit lifecycle boundaries: run start, service return, finished signal emit and return.
- The GUI completion slot now does only modal teardown and basic control restoration synchronously.
- Search-result model reset, view visibility and accessible focus are deferred to subsequent Qt event-loop turns, after the application-modal progress window has released native modality.
- Removed explicit synchronous `resizeColumnsToContents()` calls on both result tables. Both headers already use `ResizeToContents`, so the calls duplicated full model scans at the worst possible time.
- Added UI lifecycle diagnostics around modal close, model reset, result rendering and focus. If a Windows-specific freeze remains, the next log will identify the exact boundary.

## Verification

- Round 25 focused regressions: **3 passed**.
- Full pytest suite: **405 passed, 0 failed**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (78 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Full parity: **PASS 61/61**.
- Historical regression: **PASS** (`passed=267`, `known_shape_incompatibilities=116`, `resolved=0`).
- `compileall`: **PASS**.
