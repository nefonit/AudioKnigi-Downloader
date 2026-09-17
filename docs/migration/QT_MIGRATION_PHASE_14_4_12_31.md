# Qt Migration Phase 14 — Windows runtime hardening

Phase 14 is a Qt-only maintenance phase driven by a real Windows/PySide6 source-run crash and a follow-up runtime audit.

## Confirmed crash

`QObject.findChildren((QTableView, QTableWidget))` is invalid in PySide6. The large-mode pass now uses `findChildren(QTableView)`, which also covers `QTableWidget` because it subclasses `QTableView`.

## Additional hardening

- Theme application creates concrete styles with `QStyleFactory.create()`.
- Accessibility announcements retain Qt 6.8+ assertive priority when available and gracefully fall back to polite delivery if a binding lacks the enum/overload.
- Missing-media cancellation resolves the worker decision and closes any active application-modal message box.
- Queue clearing removes stale selection/current-cell state before clearing tasks.
- Keyboard changes to the player seek slider update the time label and seek immediately; mouse dragging still commits on release.
- Player Stop stores the resume point in controller state and reapplies it immediately before the next Play, avoiding an asynchronous `stop()`/`setPosition()` race.
- Dynamic missing-media accessibility IDs have an explicit contract separate from the always-present main-window controls.
- Duplicate settings writes were removed.
- Playwright analysis locals are initialized defensively and the browser context is explicitly closed.
- Track checkbox model accepts valid check-state values from both `CheckStateRole` and defensive `EditRole` delegates.

## Verification

- Strict full parity: 61/61 PASS.
- Legacy runtime: absent.
- Qt import audit: 39 project modules reachable, 0 legacy frontend paths.
- Active source tests include a Phase 14 regression specifically preventing the `findChildren(tuple)` startup crash.
- Live PySide6/NVDA/JAWS execution remains a Windows-side check; use `py audioknigi_qt.py --qt-accessibility-selftest` before the normal interactive launch.
