# Documentation catalog

Current documentation is organized by purpose. Historical migration documents are retained, but they are not current runtime instructions.

## Current architecture and development

- [`architecture/PROJECT_STRUCTURE.md`](architecture/PROJECT_STRUCTURE.md) — canonical repository/package structure and placement rules.
- [`development/SETTINGS_SCHEMA.md`](development/SETTINGS_SCHEMA.md) — settings schema, defaults and migrations.
- [`development/LOCALIZATION.md`](development/LOCALIZATION.md) — stable localization IDs and external catalogs.
- [`user/DIAGNOSTICS.md`](user/DIAGNOSTICS.md) — privacy-conscious diagnostic support bundle.
- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) — compatibility link to the canonical structure document.

## Runtime domains

- `accessibility/` — NVDA/JAWS, keyboard operation, accessibility contracts and Help Center.
- `audio/` — event sounds and audio UX.
- `build/` — Windows/PyInstaller/FFmpeg build documentation.
- `features/` — feature-specific release notes.
- `network/` — DNS/network transport.
- `reliability/` — logging, shutdown and runtime hardening.
- `sources/` — provider/source-specific notes.
- `ui/` — UI, scale, theme and interaction documentation.

## Historical documentation

- `migration/` — the recorded Tk → Qt migration phases. References to retired launchers/modules are historical by design.
- `history/` — historical release markers retained for traceability.
- `../archive/` — historical tests, source variants, retired-branch audits and one-off migration tooling.

## Audit evidence

Current branch audit/review evidence is cataloged in [`../audits/INDEX.md`](../audits/INDEX.md). New audit reports belong in `audits/<current-branch>/`, not in the repository root.
