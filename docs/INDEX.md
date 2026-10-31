# Documentation catalog

Current documentation is organized by purpose. Historical migration documents are retained, but they are not current runtime instructions.

## Current architecture and development

- [`architecture/PROJECT_STRUCTURE.md`](architecture/PROJECT_STRUCTURE.md) — canonical repository/package structure and placement rules.
- [`architecture/ROOT_MODULES_V22.md`](architecture/ROOT_MODULES_V22.md) — current implementation owners and compatibility aliases.
- [`architecture/CONCURRENCY_V25.md`](architecture/CONCURRENCY_V25.md) — shared asynchronous task cancellation and compatibility guarantees.
- [`development/SETTINGS_SCHEMA.md`](development/SETTINGS_SCHEMA.md) — settings schema, defaults and migrations.
- [`development/LOCALIZATION.md`](development/LOCALIZATION.md) — stable localization IDs and external catalogs.
- [`user/DIAGNOSTICS.md`](user/DIAGNOSTICS.md) — privacy-conscious diagnostic support bundle.
- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) — compatibility link to the canonical structure document.

## Runtime domains

- `accessibility/` — NVDA/JAWS, keyboard operation, accessibility contracts and Help Center.
- `audio/` — event sounds and audio UX.
- [Windows build instructions](../README.md#windows-build) — PyInstaller/FFmpeg build guidance; build scripts live at the repository root and under `tools/`.
- `features/` — feature-specific release notes.
- `network/` — DNS/network transport.
- `reliability/` — logging, shutdown and runtime hardening.
- `sources/` — provider/source-specific notes.
- `ui/` — UI, scale, theme and interaction documentation.

## Historical documentation

- `migration/` — the recorded Tk → Qt migration phases. References to retired launchers/modules are historical by design.
- `history/` — historical release markers retained for traceability.
- `../archive/` — historical tests, source variants, retired-branch audits and one-off migration tooling.

## QA and release testing

- [`qa/README.md`](qa/README.md) — test strategy, test plan, detailed test cases, checklists, requirements traceability, historical verification/defect evidence, risks and release readiness. The QA pack is retrospective and does not represent Windows NVDA/JAWS release acceptance.

## Audit evidence

Current branch audit/review evidence is cataloged in [`../audits/INDEX.md`](../audits/INDEX.md). Incremental 4.12 round notes are indexed in [`../audits/4.12/rounds/INDEX.md`](../audits/4.12/rounds/INDEX.md). New audit reports belong under `audits/<current-branch>/`, never in the repository root.
