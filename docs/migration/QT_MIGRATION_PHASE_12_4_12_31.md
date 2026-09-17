# Qt migration Phase 12 — acceptance-gated default launcher promotion

Phase 12 adds the final safety boundary between a release-candidate Qt build and the application's default launcher.

Qt acceptance and Qt promotion are intentionally separate operations. A successful NVDA+JAWS acceptance report does **not** silently change the default frontend. The exact accepted EXE must be explicitly promoted with `promote_qt_launcher.bat`.

`run.bat` fails closed. It selects the Qt EXE only when all of the following still match at launch time:

1. the Qt EXE exists;
2. the hash-bound Windows acceptance report exists;
3. all automated gates are PASS;
4. every required NVDA check is PASS;
5. every required JAWS check is PASS;
6. an explicit promotion marker exists;
7. the marker's app version, migration stage and SHA-256 match the exact current Qt EXE.

If any condition is stale or missing, `run.bat` launches the stable legacy Tk executable/source instead. Rebuilding the Qt EXE therefore automatically revokes default-launch eligibility until the new hash is accepted and explicitly promoted.

Rollback is immediate and non-destructive: `rollback_to_legacy.bat` removes only `dist/qt_launcher_promotion.json`. It does not delete the Qt EXE, acceptance reports, settings, history, queue state, player positions or downloads.

Helper commands:

- `promote_qt_launcher.bat` — explicit promotion after complete acceptance;
- `check_default_launcher.bat` — shows which frontend is eligible;
- `rollback_to_legacy.bat` — removes promotion;
- `run.bat` — safe default selector;
- `run_qt.bat` — remains an explicit direct Qt source launcher for testing.

Phase 12 does not claim that NVDA/JAWS acceptance has passed in this Linux environment. It only makes successful Windows acceptance enforceable by the launcher.
## Verification

- Phase 12 targeted tests: **7/7 passed**.
- Qt migration Phase 1–12 tests: **92/92 passed**.
- Qt migration + repository catalog focused set: **95/95 passed**.
- Complete active repository suite, run in non-overlapping Xvfb groups: **604/604 passed**.
- Static Qt runtime import audit: **33 project modules, 0 legacy frontend paths**.
- `compileall` for application/tools entrypoints: **OK**.
- Stable legacy protection versus the uploaded Phase 11 base: **14/14 key files byte-for-byte unchanged**.

