# Archive

This directory contains historical material that is intentionally excluded from the active runtime and active test suite.

- `tests/phase_regressions/` — historical phase/audit regression tests. They are preserved as evidence but may assert obsolete file boundaries from the former monolithic architecture.
- `tests/pre_qt_retirement/` — exact regression suite from the final Tk/Qt coexistence state before Tk retirement.
- `history/` — recovered prior source/release variants and historical artifacts.
- `audits/` — audit reports for retired version branches.
- `tools/phase13/` — one-off migration tooling used to create the original Qt-only Phase 13 tree.

Nothing under `archive/` is imported by the application or collected by the normal `pytest` configuration.
