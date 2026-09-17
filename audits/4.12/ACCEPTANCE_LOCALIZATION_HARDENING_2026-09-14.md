# 4.12.38 — Acceptance & localization hardening

Date: 2026-09-14

## Confirmed fixes

- Kept the accessibility self-test failure handler on the safe `details` payload and added a regression preventing a return to an uninitialized `report` variable.
- Made Windows acceptance report reads UTF-8-BOM tolerant (`utf-8-sig`).
- Added `WindowsError` to the platform-neutral undefined-global audit special names so a Windows-only compatibility alias does not become a POSIX false positive.
- Added four Ukrainian legacy UI literals already present in `runtime_exact.json`:
  - `Ничего не найдено.`
  - `Сначала выберите книгу в результатах поиска.`
  - `Сначала выберите часть книги.`
  - `Сначала проанализируйте книгу.`
- Refreshed the release-baseline verification date to 2026-09-14.
- Clarified the entry-point module docstring: Qt-only is the active runtime; Phase 39 is retained only as historical compatibility context.
- Updated `QT_RUNTIME_STAGE` to `qt-only-4.12.38`.

## Reviewed but not changed

- The reported `UnboundLocalError` in `_qt_accessibility_selftest()` was not present in the 4.12.37 base archive: the exception path already passed `details` to `_write_report()`.
- `requests==2.32.5` is a published PyPI release, and CPython 3.14.7 is an official Python release; those pins are therefore not downgraded.
- The Russian-only `CYRILLIC` regular expression in the localization audit is intentional for detecting Russian source literals, not a general Unicode/Cyrillic detector.
- Mutagen remains an explicit runtime dependency and is discoverable by the PyInstaller build from the pinned release requirements.

## Validation

- Active pytest suite: 140 passed.
- Full parity: 61/61.
- Localization audit: OK (ru/uk/de/en).
- Qt import audit: OK (72 modules, no legacy frontend path).
- Exception audit: PASS (113 reviewed broad silent handlers).
- Unused-import audit: OK (31 implementation modules).
- Undefined-global audit: OK (76 modules).
- Historical regression audit: PASS (273 passed, 108 known shape incompatibilities, no new regressions).
