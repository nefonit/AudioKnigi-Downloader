# 4.12.35 — Recovery, diagnostics and localization hardening

Date: 2026-09-12

## Confirmed fixes

- Whole-book `resume.json` manifests with `selected_indices: null` or legacy `[]` are discoverable and resume as whole-book downloads.
- `UnfinishedDownload.selected_indices` now explicitly permits `None`.
- Knigavuhe title hydration propagates `Cancelled` from worker futures.
- `BookAnalysisService._analyze_audioknigi_playwright()` raises a clear runtime dependency error instead of relying on `assert`.
- Support-bundle home redaction is filesystem-root safe and uses `%USERPROFILE%` on Windows and `~` on Unix-like systems.
- `ui_text()` skips `.format()` when no interpolation values were supplied.
- The backup-created runtime regex accepts both LF and CRLF.
- Exact/literal translation overlaps are checked for consistency; legacy literal catalogs are kept sorted.
- Qt self-test DeferredDelete flushing uses the binding-safe keyword form.
- README quality-gate commands use portable forward-slash paths.
- PyInstaller/bootloader attribution and a release-licensing checklist were added; no application license is selected automatically.
- PEP-8-compressed hot paths in `download/network.py` and `poleknig.py` were expanded for maintainability.
- The unused-import quality gate now covers 31 implementation modules instead of only the split download/mixin subset.

## Audit items already fixed before this round

- self-test failures already printed full tracebacks to stderr;
- accessibility teardown already continued after `window.close()` failures;
- `selected_indices=None` was already fixed in request validation, queue serialization and active download UI paths;
- dependency metadata fallback in frozen diagnostics was already present;
- strict duplicate-JSON-key detection was already part of the localization audit.

## Audit items intentionally not changed

- Python 3.14.7, PySide6 6.11.2, Playwright 1.62.0, Pillow 12.3.0 and PyInstaller 6.22.2 are released packages in the current 2026 environment; the report's "nonexistent/future" premise is stale.
- Chrome 153 is a released stable desktop Chrome major in September 2026; the User-Agent was not rolled back to 2025-era majors.
- `qt_runtime_audit.py` remains package-level because it is a runtime boundary assertion imported by both source and frozen self-tests; README documents this placement.
- Historical CHANGELOG entries preserve their original language by design; current release entries are maintained in English.
- Literal/runtime translation duplication remains a compatibility boundary, but the audit now fails if overlapping translations diverge.

## Verification

- active pytest: 109 passed;
- Full Parity: 61/61;
- localization audit: OK (ru/uk/de/en);
- Qt import audit: OK (72 project modules);
- exception audit: PASS (113 reviewed cases);
- unused-import audit: OK (31 implementation modules);
- undefined-global audit: OK (76 modules);
- historical regression gate: 273 passed, 108 known incompatibilities, 0 unexpected regressions;
- compileall: PASS.
