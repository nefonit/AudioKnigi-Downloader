# Audit notes — Round 21 (2026-09-17)

This round was applied to the verified Round 20 tree. Every supplied finding was checked against the current implementation and executable regression behavior before changing code.

## Confirmed and fixed

- `download_engine.py`: redownload cleanup now uses `unlink_with_retry()` for both full-MP3 targets and individual track outputs, tolerating short Windows Defender/indexer sharing locks.
- `core.py`: `save_json()` keeps its atomic temporary-file replace but now retries transient `PermissionError` / WinError 5/32 before reporting persistence failure. The helper remains in `core.py` to avoid reintroducing a package-import cycle through `audioknigi.download`.
- `knigavuhe.py`: the direct-script MP3 fallback now exposes one current `NarrationVariant`, matching the normal parser's UI/service contract.
- `poleknig.py`: alternative-recording author validation now accepts conservative full-name/initial/surname variants while still rejecting unrelated authors; exact matches remain the fast path.
- `download/network.py`: temporary `.part`, `.assembling`, `.segments.json` and `.segNNN` cleanup paths consistently use `unlink_with_retry()` instead of direct `Path.unlink()` calls.
- `diagnostics/support_bundle.py`: an explicitly directory-shaped destination ending in `/` or `\\` is created when missing and receives the timestamped support ZIP inside it.
- `services/player_position_store.py`: empty media paths no longer normalize to the process working directory; reads return 0 and update/clear reject the empty key without persisting bogus state.
- Updated the active Round 18 source-shape regression to require retry-safe Range cleanup, and removed two stale broad-exception allowlist entries made obsolete by the narrower `OSError` cleanup handlers.

## Reviewed but intentionally not changed

- `templates.py` does **not** produce `00.mp3` for `track=None` in the reported path. `safe_name("")` currently yields `audiobook`, so the executable result is `audiobook.mp3`. No speculative naming change was made.
- The plain-HTTP POST/PUT proxy-body observation is a future architecture concern. Current protected-site browser traffic uses HTTPS `CONNECT`; no current reproducible truncation was established, so the relay protocol was not widened in this maintenance round.
- Adaptive Range parked workers already test `jobs.empty()` before parking, so they do not livelock after work is exhausted.
- `_shared_source_timeline_issue()` supplies `expected_end` and `actual_duration` for both current error reasons; the reported logging `KeyError` is not present.
- The trailing `return False` in `unlink_with_retry()` is stylistically unreachable under the current raise-or-success contract, but it does not create a runtime defect.
- A non-existing support-bundle path *without* a trailing separator remains intentionally ambiguous and is kept as the existing archive-basename contract (for example `bundle_1.0` -> `bundle_1.0.zip`). Only an explicit directory-shaped path is newly treated as a missing directory.
- Queue `selected_indices=None` versus `[]` semantics remain unchanged: `None` means all tracks; an explicit empty list must remain empty so validation cannot silently download an entire book.
- Existing ffprobe cancellation, backup rollback, CSV injection protection, accessibility IDs/announcements, media-key HWND handling, player resume protection, queue scheduling and deferred shutdown safeguards were verified and required no Round 21 code change.

## Regression coverage

New `tests/integration/test_report_followup_round21_20260917.py` covers:

1. transient Windows-style `save_json()` replace retries;
2. retry-safe duplicate-output deletion;
3. Knigavuhe fallback current narration variant;
4. PoleKnig author matching with initials vs unrelated authors;
5. retry-safe network temporary-file cleanup contract;
6. explicit missing support-bundle directory handling;
7. empty player-position path rejection;
8. unchanged queue empty-selection and bounded proxy-drain contracts;
9. Windows CI pytest availability plus Python 3.14 synthetic-global handling.

## Verification

- Round 21 focused regressions: **9 passed**.
- Full pytest suite: **379 passed, 0 failed**.
- Historical regression: **PASS** (`passed=268`, `known_shape_incompatibilities=115`, `resolved=0`).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (77 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Qt localization: **OK** (`ru`, `uk`, `de`, `en`; help/onboarding/accessibility catalogs complete).
- Full parity: **PASS 61/61**.
- Qt import boundary: **OK** (73 project modules, no legacy frontend path).
- `compileall`: **PASS**.
- Windows CI follow-up: installs `pytest` before historical/full pytest gates and recognizes Python 3.14 synthetic `__conditional_annotations__` in the undefined-global audit.

The Windows frozen EXE is not claimed as validated from this Linux environment; GitHub Actions/Windows build results remain the authoritative frozen-runtime evidence.
