# Audit — Qt migration Phase 12 — 2026-09-06

## Goal

Prevent an unaccepted or rebuilt Qt EXE from silently becoming the application's default frontend while still allowing explicit promotion and instant rollback.

## Implemented controls

- Separate acceptance and promotion contracts.
- Promotion marker bound to app version, migration stage and exact EXE SHA-256.
- `run.bat` revalidates promotion on every start and fails closed to legacy.
- Rebuilt Qt binaries automatically lose eligibility because SHA-256 changes.
- Explicit `promote_qt_launcher.bat`, `check_default_launcher.bat`, and `rollback_to_legacy.bat`.
- Rollback deletes only the promotion marker.
- Stable Tk entrypoint/build remains present and is not modified by the promotion mechanism.
- Promotion contract uses no PySide6 or Tk imports.

## Repository hygiene

The two Phase 11 Qt build audit documents that had landed directly under `audits/` were moved to `audits/4.12/` to comply with the existing audit catalog rule.

## Safety property

A stale/missing acceptance report, missing promotion marker, failed NVDA/JAWS check, changed migration stage, changed app version, missing EXE, or changed EXE bytes all resolve to the legacy launcher.
## Verification

- Phase 12 targeted tests: **7/7 passed**.
- Qt migration Phase 1–12 tests: **92/92 passed**.
- Qt migration + repository catalog focused set: **95/95 passed**.
- Complete active repository suite, run in non-overlapping Xvfb groups: **604/604 passed**.
- Static Qt runtime import audit: **33 project modules, 0 legacy frontend paths**.
- `compileall` for application/tools entrypoints: **OK**.
- Stable legacy protection versus the uploaded Phase 11 base: **14/14 key files byte-for-byte unchanged**.

