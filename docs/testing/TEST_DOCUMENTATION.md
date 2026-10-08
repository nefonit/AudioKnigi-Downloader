# Detailed Test Documentation Baseline

Baseline: **AudioKnigi Downloader 4.12.42 Round 81**  
Git baseline: `f53fc4dba5247561317e12f40ec166db0d3c4d17`

This document describes the structured test repository maintained together with the Test Plan. The detailed working copy is organized into the following logical sections.

## Requirements

**38 requirements** cover search, analysis, downloads, media processing, templates, queue, history/library, player, settings, localization, accessibility, network/source health, diagnostics/privacy, UI, Windows integration, reliability, and runtime compatibility.

Each requirement has a stable requirement ID such as `REQ-SEARCH-01`, `REQ-DL-04`, `REQ-A11Y-01`, or `NFR-REL-01`.

## Test Suites

**20 test suites** group manual and automated coverage by risk and subsystem:

1. Search & Source Discovery
2. Book Analysis
3. Selected Parts Download
4. Full MP3 Download
5. Network Resume & Segmentation
6. Expired/Missing Media Recovery
7. Media Processing
8. Metadata & Templates
9. Queue
10. History & Library
11. Player
12. Settings & Migration
13. Localization
14. Accessibility
15. Network & Source Health
16. Diagnostics & Privacy
17. UI Modes & DPI
18. Windows Integration
19. Cancellation & Shutdown
20. Release Quality Gates

## Manual Checklist

The regression checklist contains **131 items**. It is intentionally concise: each item identifies the verification target without repeating a full low-level procedure. Critical download integrity, recovery, cancellation, accessibility, and privacy checks have the highest priority.

## Manual Test Cases

The baseline contains **68 detailed test cases**. Each test case is linked to a Requirement ID and Test Suite ID and includes the scenario, preconditions, steps, expected result, priority, and current baseline status.

The manual cases complement automated coverage with end-to-end Windows behavior, keyboard-only flows, screen-reader acceptance, packaged-runtime checks, and real integration scenarios that are not reliable in a headless environment.

## Historical Defect Reports

The documentation contains **25 verified historical defect reports** selected from the development/audit history. Each report records the affected component, reproduction conditions or steps, actual result, expected result, severity, priority, and resolved status.

Audit findings are not automatically treated as defects: each finding must first be reproduced against the actual source/archive. Stale, architectural, intentional-design, and false-positive findings are documented without unnecessary code changes.

## Traceability

Traceability connects:

`Requirement → Test Suite → Checklist/Test Case → Automated regression evidence → defect/audit history`

Automated tests use their complete pytest node IDs as stable evidence. Release/audit baselines are tied to Git commits, ZIP hashes where applicable, changelog entries, and audit notes.

## Automated Test Baseline

Round 81 regression evidence:

- **899** collected automated tests
- **897** passed
- **2** environment-blocked Qt accessibility self-tests because PySide6 was unavailable in the validation environment
- **100%** pass rate for runnable automated tests
- **101** test files

Additional quality gates include Python compilation, strict JSON duplicate-key validation, undefined-global checks, unused-import checks, exception audits, Qt localization audits, and historical regression contracts.

## QA / Development History

The baseline records **119 development/QA history entries** covering the evolution from 4.7.x through 4.12.42 Round 81.

Major phases include:

- 4.7.x — package architecture, first-run, resume, duplicate detection, accessibility/localization foundation
- 4.8.x — native UI/accessibility/input stability, drag-and-drop, timing, settings persistence
- 4.9.x — Knigavuhe integration, relevance, author/title/narrator metadata, narration variants
- 4.10.x — event sounds and language-aware audio cues
- 4.11.x — PoleKnig integration, author catalog search, narration variants
- 4.12.0–31 — universal search/open flow, validation UX, recovery, help, queue/player, Windows packaging, Qt migration
- 4.12.32–42 — structured refactoring, quality gates, runtime integrity, diagnostics, cancellation, localization, compatibility
- Rounds 61–81 — systematic external-audit follow-up for edge cases, privacy, indices, network integrity, fallback behavior, accessibility, and regression contracts

## Maintenance Rules

1. Every confirmed defect should receive a focused regression test where practical.
2. Every external audit finding must be checked against the real source before code changes are made.
3. Changes to requirements, risks, or user-visible behavior must update the relevant test documentation.
4. Release readiness requires all runnable automated tests and static quality gates to pass.
5. The two environment-blocked Qt accessibility self-tests must be executed in a suitable PySide6/Windows validation environment before final packaged-release sign-off.
6. Accessibility and localization are functional requirements, not cosmetic post-processing.
7. File integrity and privacy guarantees take precedence over optimistic success reporting or diagnostic convenience.
