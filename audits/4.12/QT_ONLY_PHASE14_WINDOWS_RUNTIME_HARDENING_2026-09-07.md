# Audit — Qt-only Phase 14 Windows runtime hardening

Date: 2026-09-07
Stage: `phase-14`

## Trigger

A real Windows/PySide6 launch failed in `AudioKnigiQtWindow._apply_large_mode()` because `QObject.findChildren()` was called with `(QTableView, QTableWidget)` as a tuple. PySide6 accepts one type per call, not a tuple.

## Resolution

The startup crash was fixed and the accompanying runtime-audit findings were reviewed one by one. Confirmed bugs were fixed; defensive findings were hardened without reintroducing any legacy Tk runtime.

Notable distinctions:

- `QApplication.setStyle(str)` is documented by current PySide6 as a valid overload, so it was not itself proven to be the observed crash. Phase 14 nevertheless uses `QStyleFactory.create()` to avoid binding-overload differences.
- `QAccessible.AnnouncementPoliteness` is available in the project's supported Qt/PySide6 6.8+ range. A fallback was still added so accessibility feedback cannot crash on a binding mismatch.
- The Playwright local-variable report was defensive: an exception before assignment would propagate before the final parse call in the existing function. Variables are now initialized and guarded explicitly anyway.

## Gates

- Strict parity: 61/61 PASS.
- Qt import boundary: 39 project modules, 0 legacy frontend paths.
- `compileall`: PASS.
- Phase 14 + Qt-only source tests: PASS.
- Live Windows rerun required after extracting the Phase 14 archive.
