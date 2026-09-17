# Qt migration Phase 11 — live NVDA acceptance hardening

Phase 11 is driven by the first real Windows NVDA acceptance run. Automated frozen gates passed; manual failures identified six concrete accessibility surfaces: ComboBox, queue, history, settings, player, and modal dialogs.

The implementation keeps the native Qt accessibility model and does not add FocusIn hooks or event filters. It adds signal-only QAccessible announcements where NVDA did not reliably expose transient values, row summaries for QTableWidget navigation, explicit seconds/percent semantics for the player, and application-modal message boxes with a safe Escape action.

The acceptance runner is now incremental for the same EXE hash. A rerun preserves already-passed checks and asks only failed/skipped/unanswered checks unless `--retest-all` is supplied. `run_qt_acceptance.bat` forwards command-line arguments, so `run_qt_acceptance.bat --reader nvda` and `run_qt_acceptance.bat --reader jaws` are supported.

Any rebuilt EXE has a new SHA-256 and therefore starts a fresh manual acceptance report.
