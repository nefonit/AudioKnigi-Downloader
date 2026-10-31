# Documentation catalog

Current documentation is organized by purpose. Historical migration documents are retained, but they are not current runtime instructions.

## Current architecture and development

- [`architecture/PROJECT_STRUCTURE.md`](architecture/PROJECT_STRUCTURE.md) — canonical repository/package structure and placement rules.
- [`architecture/ROOT_MODULES_V22.md`](architecture/ROOT_MODULES_V22.md) — current implementation owners and compatibility aliases.
- [`architecture/HELP_CENTER_V26.md`](architecture/HELP_CENTER_V26.md) — Help Center content/UI split and accessibility invariants.
- [`architecture/HELP_CENTER_V27.md`](architecture/HELP_CENTER_V27.md) — Help Center formatter, topic-selection logic and event-handler contracts.
- [`architecture/TRANSFER_POLICY_V28.md`](architecture/TRANSFER_POLICY_V28.md) — HTTP throughput policy extraction with resume compatibility.
- [`architecture/HTTP_RESUME_V29.md`](architecture/HTTP_RESUME_V29.md) — safe HTTP 206/416 resume validation and connection-loss regressions.
- [`architecture/RANGE_RETRY_V30.md`](architecture/RANGE_RETRY_V30.md) — bounded Retry-After and network-error recovery for Range segments.
- [`architecture/RANGE_INTEGRITY_V31.md`](architecture/RANGE_INTEGRITY_V31.md) — validate declared HTTP 206 segment body sizes and rollback malformed responses.
- [`architecture/SEGMENT_CHECKSUMS_V32.md`](architecture/SEGMENT_CHECKSUMS_V32.md) — persistent segment SHA-256 checkpoints and verification during assembly.
- [`architecture/STATE_RECOVERY_V33.md`](architecture/STATE_RECOVERY_V33.md) — crash-safe queue and history snapshots, state restoration and UI continuity.
- [`architecture/QUEUE_RECONCILIATION_V34.md`](architecture/QUEUE_RECONCILIATION_V34.md) — worker-side recovery of fully completed downloads after an abrupt application exit.
- [`architecture/SHUTDOWN_SAFETY_V35.md`](architecture/SHUTDOWN_SAFETY_V35.md) — bounded exit protection for Audiobookshelf checks and final state flush.
- [`development/RELEASE_PREFLIGHT_V36.md`](development/RELEASE_PREFLIGHT_V36.md) — source archive privacy, dependency parity, release candidate SHA-256 and outstanding manual gates.
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

- [`qa/README.md`](qa/README.md) — test strategy, test plan, detailed test cases, checklists, requirements traceability, historical verification/defect evidence, risks and release readiness.
- [`qa/UPGRADE_ACCEPTANCE_V37.md`](qa/UPGRADE_ACCEPTANCE_V37.md) — controlled Windows old-to-new EXE rehearsal with isolated profile, privacy-conscious before/after checks and separate NVDA/JAWS sign-off. The QA pack is retrospective and does not represent Windows NVDA/JAWS release acceptance.

## Audit evidence

Current branch audit/review evidence is cataloged in [`../audits/INDEX.md`](../audits/INDEX.md). Incremental 4.12 round notes are indexed in [`../audits/4.12/rounds/INDEX.md`](../audits/4.12/rounds/INDEX.md). New audit reports belong under `audits/<current-branch>/`, never in the repository root.
