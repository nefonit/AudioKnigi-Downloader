# Audit — Qt Migration Phase 8

Date: 2026-09-06

## Scope

Accessibility hardening of the PySide6 interface and creation of a frozen Windows accessibility acceptance gate.

## Implemented

- Added debounced native `QAccessibleAnnouncementEvent` delivery for polite status messages; assertive errors remain immediate.
- Added `focus_table_row()` so a focused table has a valid current accessible child.
- Added `AccessibleTextRole` data to search/track models and header/value semantics to queue/history cells.
- Added table-local keyboard actions: Space toggles the current track; Enter/Return activates a search result.
- Added F1 accessibility/hotkey help.
- Changed Qt player seek UI from milliseconds to seconds (5 s arrow step, 30 s page step) while preserving millisecond QMediaPlayer boundary.
- Added dynamic Play/Pause accessible name.
- Added explicit accessible button semantics plus a safe Escape/Stop path to the missing-media modal.
- Added `audioknigi/qt/accessibility_audit.py` with required IDs/name/focusability checks.
- Added `--qt-accessibility-selftest` and frozen report `qt_accessibility_frozen_selftest.txt`.
- Added the frozen accessibility self-test to `build_qt_ci.ps1`.
- Added the manual NVDA/JAWS acceptance matrix in `docs/migration/QT_MIGRATION_PHASE_8_4_12_31.md`.

## Anti-regression principle

Phase 8 does **not** reintroduce the old custom FocusIn/screen-reader bridge architecture into the Qt branch. The new accessibility layer contains no FocusIn handler/event filter and no Tk/Prism/NVDA/JAWS-specific runtime dependency.

## Automated verification

- Full active repository suite: **571/571 passed** in non-overlapping Xvfb groups.
- Qt migration Phase 1–8: **59/59 passed**.
- Phase 6–8 focused accessibility/build checks: **27/27 passed**.
- `compileall`: pass.

## Remaining external acceptance

This environment is Linux and does not contain PySide6, NVDA or JAWS. The Windows one-file build must still execute:

- `--qt-runtime-selftest`;
- `--qt-accessibility-selftest`;
- `--playwright-edge-selftest`;
- the manual NVDA checklist;
- the manual JAWS checklist.

A default-launcher switch is not approved until those checks are completed.
