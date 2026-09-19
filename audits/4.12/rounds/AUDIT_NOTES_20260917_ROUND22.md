# Audit notes — Round 22 (2026-09-17)

This round was applied on top of Round 21. Every supplied finding was checked against the current implementation before changing runtime behavior.

## Confirmed and fixed

- `poleknig.py`: Playwright cookie restoration is fault-isolated per cookie. One malformed/stale cookie can no longer abort the entire browser fallback.
- `poleknig.py`: the `page.on("request", ...)` callback no longer raises `Cancelled`; cancellation remains enforced in the synchronous controlling flow while the event callback returns immediately.
- `network_dns.py`: CONNECT now uses the normal half-close-preserving relay instead of terminating as soon as the upstream write side reaches EOF. A runtime socket-pair regression verifies that client-to-upstream bytes still pass after upstream half-close. Plain HTTP keeps the bounded `return_when_right_closes=True` behavior.
- `download_engine.py`: duplicate-output deletion now obtains track indices through `DownloadRequest.track_index()`, matching the rest of the engine and supporting Mapping-like track records.
- `core.py`: `safe_name()` now replaces ASCII control characters `0x00–0x1F` in addition to the normal Windows-forbidden filename characters.
- `poleknig.py`: H1/title extraction uses punctuation-preserving cleanup so meaningful leading/trailing dashes are not silently removed from book titles. Generic UI/metadata label cleanup remains unchanged.
- `download/book_flow.py`: source-cleanup telemetry now calls `unlink_with_retry(..., missing_ok=False)`, so already-missing sources are caught by `FileNotFoundError` and are not counted as removed.
- `download/network.py`: removed the redundant successful-206 `response.raise_for_status()` no-op while preserving explicit error handling for non-206 statuses.
- `services/book_analysis_service.py`: Playwright cookies are restored individually so a bad cookie cannot abort analysis.
- `services/book_analysis_service.py`: removed the unreachable `playlist_response is None` branch after `session.get(...).raise_for_status()`.

## Reviewed but intentionally not changed

- `config/settings.py`: the legacy `auto_chunk_min_kbps` value can initially be a string, but the existing later `safe_int()` normalization converts it before runtime use; no defect remains.
- `providers/audioknigi_search.py`: cancellation during parallel hydration already cancels queued futures and does not duplicate hydrated records; no leak/reordering defect was reproduced.
- Localization catalog duplication between `legacy_literals.json` and `runtime_exact.json` is intentional because UI and runtime-event localization use separate paths.
- `Повторить` -> `Redo` remains the edit-menu translation; queue retry uses the distinct `Повторить задачу` key.
- Queue restoration of `running` to `interrupted` remains intentional and resumable through the queue's runnable-status contract.
- `event_sounds.py` already stops players, disconnects callbacks and guards deleted Qt objects with `RuntimeError`; no additional lifetime fix was necessary.
- `media_keys.py` already treats `RegisterHotKey` conflicts as non-fatal and falls back to `WM_APPCOMMAND`; this is the desired Windows behavior.
- `player_controller.py` keeps the 4-second save timer because `save_position()` exits before disk I/O when no resumable media is active; changing timer lifetime would add state complexity without a demonstrated defect.
- The project support baseline remains Python 3.11+ even though several individual language features would also work on Python 3.10; Windows CI continues to verify Python 3.11 and 3.14.7.

## Regression coverage

New `tests/integration/test_report_followup_round22_20260917.py` covers:

1. Windows control-character filename sanitization;
2. Mapping-aware duplicate-output track selection;
3. preservation of meaningful PoleKnig title punctuation;
4. per-cookie Playwright restore and non-throwing request callback contracts;
5. accurate source-cleanup telemetry contract;
6. runtime CONNECT half-close full-duplex behavior;
7. CONNECT-vs-plain-HTTP relay call contracts;
8. removal of the unreachable/redundant HTTP checks while retaining the existing settings migration normalization.

Three active historical source-shape regressions were updated because they explicitly required the old unsafe CONNECT/cleanup form. One archived phase-14 source-shape test was added to the historical incompatibility allowlist because it requires the now-removed `playlist_response = None`/guard shape.

## Verification

- Round 22 focused regressions: **8 passed**.
- Full pytest suite: **387 passed, 0 failed**.
- Historical regression: **PASS** (`passed=267`, `known_shape_incompatibilities=116`, `resolved=0`).
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (77 modules).
- Unused-import audit: **OK** (32 implementation modules).
- Qt localization: **OK** (`ru`, `uk`, `de`, `en`; help/onboarding/accessibility catalogs complete).
- Full parity: **PASS 61/61**.
- Qt import boundary: **OK** (73 project modules, no legacy frontend path).
- `compileall`: **PASS**.

The Windows frozen EXE is not claimed as validated from this Linux environment. Windows source/Qt CI on Python 3.11 and 3.14.7 is run in GitHub before merge; the frozen executable still requires the separate release-build workflow.
