# Audit catalog

Current-branch audit evidence lives under `audits/4.12/`. Reports for retired version branches were moved to `archive/audits/` so the active audit tree does not mix current and historical branches.

The active test suites live in `tests/`. Historical phase/audit regression tests are preserved under `archive/tests/`; `tools/historical_regression_audit.py` executes them as a compatibility safety net while explicitly allowing source-shape assertions tied to the retired monolithic architecture.

## Current branch

- `4.12/` — current 4.12.31 audit, migration, accessibility and hardening evidence.
- `4.12/STRUCTURAL_REFACTOR_2026-09-12.md` — current architecture/catalog refactor and disposition of the nine improvement goals.

## Archive

- `archive/audits/4.7/`
- `archive/audits/4.8/`
- `archive/audits/4.9/`
- `archive/tests/phase_regressions/`
- `archive/tests/pre_qt_retirement/`

Historical reports may intentionally mention retired launchers, Tk modules, old migration phases, or previous folder paths. They are evidence, not current operating instructions.
