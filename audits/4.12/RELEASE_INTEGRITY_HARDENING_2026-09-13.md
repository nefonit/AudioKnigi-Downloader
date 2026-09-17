# AudioKnigi Downloader 4.12.36 — release integrity hardening

## Scope

This pass reviewed the 2026-09-12 follow-up audit against the actual 4.12.35 source tree. It focused on Windows release tooling, quality-gate portability, legacy queue recovery, accessibility wording, localization terminology, and post-refactor cleanup.

## Confirmed fixes

- `tools/qt_windows_acceptance.py` now imports `APP_VERSION` from `audioknigi.metadata` and waits after a forced `kill()` before recording the exit code.
- `tools/historical_regression_audit.py` normalizes both Windows and POSIX path separators.
- `tools/qt_localization_audit.py` accepts `ast.Assign` and `ast.AnnAssign` constants.
- `tools/undefined_global_audit.py` recognizes package `__path__`.
- `tools/exception_audit.py` now fails on stale allowlist entries; the two retired `source_analysis.py` entries were removed and the allowlist is sorted.
- `audioknigi/services/queue_service.py` parses malformed legacy selected-index payloads defensively; the string `all` maps to whole-book selection.
- `MissingSelectedTracksError` identifies the count omitted after the first 12 track indices.
- The main window uses a dedicated stable localized accessibility description.
- Ukrainian Undo/Appearance and German Help/Download terminology were made distinct/consistent.
- Remaining compact semicolon forms and spacing artifacts called out by the audit were cleaned.

## Reviewed but intentionally retained

- `core.APP_VERSION` remains as a documented public compatibility export because external acceptance/build tooling and older integrations can import it. New code uses `audioknigi.metadata.APP_VERSION`.
- The historical string `Phase 39 is Qt-only` remains in the entry-point documentation as a compatibility/history marker; the adjacent sentence no longer hard-codes an obsolete patch release.
- Hidden compatibility buttons on the Book page remain intentional accessibility/parity contract objects; they are not user-visible duplicate actions.

## Validation target

The release candidate is expected to pass the active pytest suite, full parity 61/61, localization, Qt import boundary, exception, unused-import, undefined-global, historical-regression and compileall gates. Final archive validation is recorded after packaging.

## Working-tree validation

- pytest: 121/121 passed
- Full Parity: 61/61
- Localization Audit: OK (ru/uk/de/en)
- Qt Import Audit: OK (72 modules)
- Exception Audit: PASS (113 reviewed bare-exception passes)
- Unused Import Audit: OK (31 implementation modules)
- Undefined Global Audit: OK (76 modules)
- Historical Regression: PASS (273 passed; 108 known shape incompatibilities; 0 unexpected regressions)
- compileall: OK
