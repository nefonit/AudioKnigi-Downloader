# Qt Migration Phase 13 — Full parity and legacy retirement

## Release rule

Phase 13 removes the legacy Tk runtime only after two independent gates:

1. the old and new code coexist and the complete repository regression passes;
2. the Qt-only copy is built, the legacy files are physically removed, and the strict parity audit passes again with `--require-legacy-retired`.

## Full capability inventory

`audioknigi/qt/full_parity.py` contains 61 user-facing capabilities. `tools/full_parity_audit.py` binds every item to concrete Qt/backend source evidence. No item is deferred or marked as an intentional difference.

The inventory covers first-run setup, ru/uk/de/en language selection, Simple and Advanced modes, universal input, clipboard and drag/drop, search across all sources, availability and context actions, analysis/metadata/covers/narrations, all track columns/actions, selected/all/full-MP3 downloads, exact duplicate handling, resume, disk checks, progress/speed graph/session log, quality/advanced downloader settings/templates/Audiobookshelf, event sounds, themes/scale/large mode/geometry, complete queue operations including item pause and drag reorder, history/covers/export/backup, player, last-completed actions, tray, help/crash/accessibility diagnostics/hotkeys/dependencies, safe shutdown/modal behavior/context menus/output actions and completion notifications.

## Verification before retirement

- strict parity: **61/61 PASS**;
- complete pre-retirement pytest suite: **613/613 PASS** (split into non-overlapping groups because of execution time limits);
- migration Phase 1–13 suite: **101/101 PASS** before final support-module retirement hardening;
- Qt runtime import graph does not cross into legacy UI.

The exact pre-retirement tests are preserved under `archive/tests/pre_qt_retirement/`.

## What was removed from the Qt-only tree

The retired runtime includes `audioknigi_gui.py`, the old Tk app/actions/accessibility/DnD/help/onboarding/player/queue/search/storage/tray/ui/ui_kit/event-sound layers, and unreachable legacy support modules (`event_bus`, `library_visuals`, `notifications`, `ui_state`, `visuals`). Obsolete Tk build hooks, legacy build scripts and promotion/rollback launcher files are also removed.

Common backend code that Qt really imports (for example `downloader.py`, `download_engine.py`, source parsers, models and services) remains. Removal is therefore based on the actual Qt import graph, not filename guesses.

## Qt-only package contract

- `run.bat` has no legacy fallback;
- PySide6 is a normal project dependency;
- `requirements.txt` and `requirements-qt.txt` contain only the Qt/common runtime dependencies;
- GitHub CI/release workflows are Qt-only;
- `build_qt_ci.ps1` still performs import-boundary, frozen-module, runtime, accessibility and Playwright/Edge self-tests;
- NVDA and JAWS acceptance remains required for the exact Windows EXE hash before release sign-off.

## Verification after retirement

- `tools/full_parity_audit.py --require-legacy-retired`: **61/61 PASS; legacy paths 0**;
- `tools/qt_import_audit.py`: **39 project modules reachable; 0 legacy frontend paths**;
- active Qt-only release tests: **5/5 PASS**;
- `compileall`: **PASS**.
