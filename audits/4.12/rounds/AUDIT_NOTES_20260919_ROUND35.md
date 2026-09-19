# Round 35 — repository housekeeping (2026-09-19)

This round contains no runtime feature change. It aligns the repository and source-release layout with the canonical project structure.

## Changes

- Moved all root-level `AUDIT_NOTES_*.md` files into `audits/4.12/rounds/`.
- Added `audits/4.12/rounds/INDEX.md` as the chronological round catalog.
- Added a repository `.gitignore` for Python/test caches, historical-regression temporary worktrees, build output, local runtime state, logs and IDE/OS noise.
- Removed leftover `.historical-regression-*` directories from the source-release workspace.
- Added `tools/package_source_release.py`, which creates a clean source ZIP and excludes generated/runtime artifacts even if they physically exist in the worktree.
- Updated architecture/docs/audit indexes to document the canonical placement.
- Added architecture tests that reject root audit notes and generated historical-regression worktrees.

## Root contract

The repository root is reserved for launch/build entrypoints, dependency/package metadata and project-wide documents. Runtime code belongs under `audioknigi/`, active tests under `tests/`, active tooling under `tools/`, documentation under `docs/`, current audit evidence under `audits/`, and retired material under `archive/`.

## Verification

- Architecture/layout tests: **16 passed**.
- Current pytest suite excluding the nested historical wrapper: **484 passed, 0 failed**.
- Historical wrapper test: **1 passed**.
- Effective current pytest contract: **485 passed, 0 failed**.
- Historical regression audit: **PASS** (`passed=264`, `known_shape_incompatibilities=119`, `resolved=0`).
- Full parity: **PASS 61/61**.
- Qt localization audit: **OK** (`ru`, `uk`, `de`, `en`).
- Qt import audit: **OK**.
- Exception audit: **PASS** (`reviewed_broad_exception_passes=107`).
- Undefined-global audit: **OK** (79 modules).
- Unused-import audit: **OK** (32 implementation modules).
- `compileall`: **PASS**.
