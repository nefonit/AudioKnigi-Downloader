# AudioKnigi Downloader project structure

The repository is organized by runtime responsibility rather than migration phase. New production code belongs in a focused package; historical phase material belongs under `archive/`.

## Root

Only launchers, packaging/build metadata, release requirements, and project-wide documents live at the root:

- `audioknigi_qt.py` — Python Qt entry point.
- `run.bat`, `run_qt.bat` — Windows launchers.
- `build_qt_exe.bat`, `build_qt_ci.ps1` — Windows build entry points.
- `pyproject.toml`, `requirements*.txt` — package and dependency metadata.
- `README.md`, `CHANGELOG.md`, `THIRD_PARTY_NOTICES.md` — primary project documentation.
- `.gitignore` — generated/cache/build/runtime-state exclusions.

Do not add feature modules, audit reports, temporary scripts, or historical snapshots to the root.

## Runtime package: `audioknigi/`

- `config/` — versioned settings schema, defaults, validation, and migrations.
- `diagnostics/` — privacy-conscious support-bundle creation.
- `download/` — focused download core:
  - `probe.py` — media probing and validation;
  - `source_analysis.py` — source/page analysis and recovery;
  - `network.py` — HTTP, resume, segmented/range downloading and bandwidth control;
  - `media.py` — FFmpeg conversion, splitting, normalization, tagging and covers;
  - `book_flow.py` — book-level orchestration;
  - `common.py`, `errors.py` — shared helpers/contracts.
- `downloader.py` — compatibility facade composing the focused download mixins.
- `download_engine.py` — GUI-neutral request orchestration, duplicate preflight, resume manifests and full-MP3 coordination.
- `providers/` — common `SourceProvider` interface, provider adapters, registry, and provider-specific low-level search adapters.
- `services/` — GUI-independent application use cases (analysis, search orchestration, requests, queue, library, player positions). `search_service` consumes the provider registry; provider search implementations must not import `services.search_service`, which avoids the previous search-cycle workaround. Audioknigi book fetching still delegates lazily to the headless analysis service, whose implementation does not import the provider registry.
- `qt/` — PySide6 interface. `qt/mixins/` groups main-window behavior by responsibility; `main_window.py` composes the application window and common state.
- `locales/` — external JSON localization catalogs packaged with the Python distribution.
- `i18n.py` — compact localization loader plus compatibility bridge for older Russian literal keys.
- `qt_runtime_audit.py` — package-level runtime-boundary assertion used by both source and frozen Qt self-tests; it stays in the package root because it validates the package boundary rather than rendering UI.
- source parsers such as `knigavuhe.py`, `poleknig.py`, plus shared core/network/model modules remain at package root when they are domain modules rather than UI layers.

## Tests

Active tests live only under `tests/` and are grouped by behavior:

- `tests/unit/` — isolated component tests.
- `tests/integration/` — service and quality-gate integration tests.
- `tests/architecture/` — repository boundaries and structure contracts.
- `tests/fixtures/providers/` — sanitized source fixtures used by parser/provider tests.

`pyproject.toml` points pytest only at `tests/`. Historical phase/audit regression tests are preserved under `archive/tests/` and are not collected during normal CI.

## Tooling

`tools/` contains active release/quality gates only:

- functional parity gate;
- Qt import-boundary audit;
- localization audit;
- reviewed bare-exception audit;
- unused-import audit for the refactored downloader/Qt-mixin layers;
- undefined-global audit for split-module imports/constants that `compileall` cannot detect;
- historical-regression compatibility gate;
- clean source-release ZIP packager;
- frozen-module and Windows accessibility acceptance checks.

One-off migration tools belong under `archive/tools/`.

## Documentation and audit evidence

- `docs/architecture/` — current architecture.
- `docs/development/` — developer contracts such as settings/localization.
- `docs/user/` — user-facing operational documentation.
- `docs/accessibility/`, `network/`, `reliability/`, `sources/`, etc. — domain documentation.
- `docs/migration/`, `docs/history/` — historical migration records, not current runtime instructions.
- `audits/4.12/` — current branch audit/review evidence.
- `audits/4.12/rounds/` — incremental Round 2+ audit/fix notes; these never live at repository root.
- `archive/audits/` — audits from retired branches.
- `archive/history/` — historical source/release snapshots.

## Placement rules

1. Runtime code goes into the smallest existing responsibility package; create a new package only for a genuinely new subsystem.
2. Active tests are named by behavior/domain, not by audit or phase number.
3. Current audit evidence goes in `audits/<branch>/`; historical evidence is moved to `archive/audits/`.
4. Historical source snapshots and migration-only tooling never live in the runtime package or repository root.
5. Generated caches/build output (`__pycache__`, `.pytest_cache`, `.historical-regression-*`, `build`, `dist`, `*.pyc`) are never part of source releases.
6. Root-level `AUDIT_NOTES_*.md` files are forbidden; current round notes belong in `audits/4.12/rounds/`.
