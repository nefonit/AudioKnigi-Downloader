# Round 23 — analysis-time process-exit hardening (2026-09-18)

Observed symptom: the application could disappear about five seconds after book/URL analysis began, with no Python traceback. The runtime log ended while `analysis-duration_*` workers were still probing PoleKnig media.

Changes:

- `request_exit()` no longer sets `_exit_requested` or cancels workers before `closeEvent()` runs. This restores the intended confirmation dialog for an active search, analysis, or download.
- Removed the GUI lifecycle `os._exit(0)` emergency path. If a worker remains blocked after the five-second grace period plus the bounded final wait, the close request is aborted, the window is restored, and the application remains alive.
- Added lifecycle diagnostics for `request_exit`, `close_event`, `deferred_exit_begin`, and `deferred_exit_timeout`.
- Added Ukrainian, German, and English runtime translations for the new close-timeout status.
- Removed the now-stale exception-audit allowlist entry for the deleted hard-exit cleanup block.
- Added regression tests in `tests/integration/test_report_followup_round23_20260918.py`.

The five-second grace timer remains only as a bounded *close attempt* timeout; it can no longer kill the process.
