# AudioKnigi Downloader — Test Documentation

Official living test documentation for **AudioKnigi Downloader 4.12.42 Round 81**.

Git baseline: `f53fc4dba5247561317e12f40ec166db0d3c4d17`

## Documents

- [TEST_PLAN.md](TEST_PLAN.md) — complete project test plan: scope, quality objectives, approach, roles, entry/exit criteria, suspension/resumption criteria, strategy, environment, development history, risks, completion summary, and approvals.
- [TEST_DOCUMENTATION.md](TEST_DOCUMENTATION.md) — inventory and maintenance rules for the detailed requirements, suites, checklist, test cases, defect history, traceability, automated tests, and QA history.
- [TEST_CONSOLIDATION_STAGE1_REPORT.md](TEST_CONSOLIDATION_STAGE1_REPORT.md) — Stage 1 report for the domain-based integration-test consolidation.
- The executable regression evidence remains in the repository's `tests/` tree, quality-audit scripts, changelog, and `audits/4.12/rounds/`.

## Current regression baseline

- Automated tests collected: **899**
- Passed: **897**
- Environment-blocked: **2** Qt accessibility self-tests because PySide6 was unavailable in the validation environment
- Runnable pass rate: **100%**
- Test modules: **23** total (**15 integration + 6 unit + 2 architecture**)
- Integration structure: **93 historical files → 15 domain modules**, with all **856 integration cases preserved**
- Manual baseline test cases: **68**
- Checklist items: **131**
- Historical verified defects documented: **25**
- Active audit notes: **80**
- Changelog / QA history entries: **119**

Test structure baseline: **Test Consolidation Stage 1 (08.10.2026)**. Historical round-oriented test origins remain traceable through `tests/integration/README.md`, `consolidation_manifest.json`, audits, and Git history.

The documentation is maintained as a living baseline and is updated whenever a release, audit round, or test-structure change affects requirements, risks, regression coverage, traceability, or release-readiness evidence.
