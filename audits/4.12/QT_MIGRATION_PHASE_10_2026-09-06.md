# Audit — Qt Migration Phase 10

Date: 2026-09-06

## Scope

Release-candidate hardening after Phase 9 critical functional parity. The goal was to make the final Windows/NVDA/JAWS gate deterministic, reproducible and tied to one exact frozen binary without changing the stable Tk frontend.

## Findings and changes

1. Added `audioknigi/qt/acceptance_contract.py` with one machine-readable promotion contract: three automated gates, NVDA + JAWS, and fourteen required manual checks per reader.
2. Added SHA-256 binding so acceptance for one EXE can never be reused for a rebuilt binary.
3. Extended `build_qt_ci.ps1` to generate `dist/qt_release_candidate.json` after all frozen build gates pass.
4. Added `tools/qt_windows_acceptance.py` and `run_qt_acceptance.bat` for incremental Windows manual acceptance.
5. Added `check_qt_acceptance.bat` for status-only validation of the exact current candidate.
6. Added passive `QApplication.focusChanged` tracing in `audioknigi/qt/accessibility_trace.py`.
7. Focus tracing records only static IDs/classes/window/state and deliberately excludes editor contents, URLs, titles and accessible names.
8. Added trace summary diagnostics for focus loss, hidden/disabled destinations and repeated A/B oscillation patterns.
9. `run_qt.bat` now forwards optional diagnostic command-line arguments while normal launch behavior is unchanged.
10. The migration stage is now `phase-10`; Qt remains a release candidate until actual Windows NVDA and JAWS evidence passes.

## Regression result

- Full active repository suite: **591/591 passed**.
- Qt Phase 1–10 focused suite: **79/79 passed**.
- Phase 10 focused suite: **11/11 passed**.
- Static Qt import graph: **33 project modules, 0 legacy frontend paths**.
- `compileall`: pass.

## Stable Tk branch

Fourteen key legacy files/build manifests were compared byte-for-byte with the Phase 9 archive: **14/14 unchanged**.

## Conclusion

Phase 10 provides a complete, hash-bound Windows acceptance pipeline. It intentionally does **not** claim real NVDA/JAWS success in the Linux development environment and does not promote Qt automatically. Default-launcher promotion is now an evidence-based decision rather than a code-completeness assumption.
