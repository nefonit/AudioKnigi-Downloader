from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "testing"

report = """# AudioKnigi Downloader — Test Consolidation Stage 1

Baseline: 4.12.42 Round 81 runtime/code.
Scope: test-suite organization only; application runtime code is unchanged.

## Before

- 93 files in `tests/integration/`
- 856 collected integration cases
- 899 collected tests in the whole project
- historical filenames dominated by `test_*round*.py` / `test_report_followup_*.py`

## After

- 15 domain-oriented integration modules
- 856 collected integration cases (unchanged)
- 899 collected tests in the whole project (unchanged)
- 23 test modules total: 15 integration + 6 unit + 2 architecture

Domain modules:

- `test_quality_gates.py`
- `test_privacy_diagnostics.py`
- `test_build_release.py`
- `test_localization.py`
- `test_accessibility.py`
- `test_player.py`
- `test_settings_contract.py`
- `test_queue_history.py`
- `test_providers.py`
- `test_search.py`
- `test_network.py`
- `test_media_processing.py`
- `test_download_flow.py`
- `test_qt_ui.py`
- `test_core_services.py`

`tests/integration/README.md` contains the complete historical-file → domain mapping. `consolidation_manifest.json` provides the machine-readable mapping and per-domain counts.

## Validation

- pytest collection: 899 / 899 preserved
- runnable tests: 897 passed
- 2 known Qt accessibility self-tests remain environment-blocked only because PySide6 is unavailable in the validation environment
- FULL PARITY: PASS 61/61
- Qt import audit: PASS
- Qt localization audit: PASS
- exception audit: PASS
- unused-import audit: PASS
- undefined-global audit: PASS
- historical-regression audit: PASS (252 passed; 131 known shape incompatibilities)
- Python compileall: PASS

## Safety

No application runtime file was changed by the consolidation. The operation only reorganizes `tests/integration/` and updates test documentation/traceability.
"""
(DOCS / "TEST_CONSOLIDATION_STAGE1_REPORT.md").write_text(report, encoding="utf-8")

readme_path = DOCS / "README.md"
readme = readme_path.read_text(encoding="utf-8")
readme = readme.replace(
    "- [TEST_DOCUMENTATION.md](TEST_DOCUMENTATION.md) — inventory and maintenance rules for the detailed requirements, suites, checklist, test cases, defect history, traceability, automated tests, and QA history.\n",
    "- [TEST_DOCUMENTATION.md](TEST_DOCUMENTATION.md) — inventory and maintenance rules for the detailed requirements, suites, checklist, test cases, defect history, traceability, automated tests, and QA history.\n"
    "- [TEST_CONSOLIDATION_STAGE1_REPORT.md](TEST_CONSOLIDATION_STAGE1_REPORT.md) — Stage 1 report for the domain-based integration-test consolidation.\n",
)
readme = readme.replace(
    "- Runnable pass rate: **100%**\n",
    "- Runnable pass rate: **100%**\n"
    "- Test modules: **23** total (**15 integration + 6 unit + 2 architecture**)\n"
    "- Integration structure: **93 historical files → 15 domain modules**, with all **856 integration cases preserved**\n",
)
readme = readme.replace(
    "The documentation is maintained as a living baseline and is updated whenever a release or audit round changes requirements, risks, regression coverage, traceability, or release-readiness evidence.",
    "Test structure baseline: **Test Consolidation Stage 1 (08.10.2026)**. Historical round-oriented test origins remain traceable through `tests/integration/README.md`, `consolidation_manifest.json`, audits, and Git history.\n\n"
    "The documentation is maintained as a living baseline and is updated whenever a release, audit round, or test-structure change affects requirements, risks, regression coverage, traceability, or release-readiness evidence.",
)
readme_path.write_text(readme, encoding="utf-8")

plan_path = DOCS / "TEST_PLAN.md"
plan = plan_path.read_text(encoding="utf-8")
plan = plan.replace(
    "- Активний pytest baseline Round 81: 899 collected tests (27 unit, 856 integration, 16 architecture).",
    "- Активний pytest baseline Round 81: 899 collected tests (27 unit, 856 integration, 16 architecture) у 23 test modules: 15 integration + 6 unit + 2 architecture.",
)
plan = plan.replace(
    "- Автоматизовані тести ідентифікуються повним pytest node id; baseline містить усі 899 node IDs.",
    "- Автоматизовані тести ідентифікуються повним pytest node id; baseline містить усі 899 node IDs. Після Test Consolidation Stage 1 актуальні node IDs використовують доменні integration-модулі, а історичне походження збережено у `tests/integration/README.md` та `consolidation_manifest.json`.",
)
plan = plan.replace(
    "- Automated pytest suite: 899 collected node IDs у 101 test files.",
    "- Automated pytest suite: 899 collected node IDs у 23 test modules (15 integration + 6 unit + 2 architecture).\n"
    "- Test Consolidation Stage 1 traceability: 93 історичних integration-файли консолідовано у 15 доменних модулів без втрати 856 integration cases; mapping збережено у `tests/integration/README.md` та `consolidation_manifest.json`.",
)
plan = plan.replace(
    "| Test files | 101 |",
    "| Test modules | 23 (15 integration + 6 unit + 2 architecture) |",
)
plan_path.write_text(plan, encoding="utf-8")

detail_path = DOCS / "TEST_DOCUMENTATION.md"
detail = detail_path.read_text(encoding="utf-8")
detail = detail.replace(
    "Automated tests use their complete pytest node IDs as stable evidence. Release/audit baselines are tied to Git commits, ZIP hashes where applicable, changelog entries, and audit notes.",
    "Current automated tests use their complete pytest node IDs as executable evidence. Test Consolidation Stage 1 changed integration module paths, so historical node-path provenance is retained through `tests/integration/README.md` and `consolidation_manifest.json`. Release/audit baselines remain tied to Git commits, ZIP hashes where applicable, changelog entries, and audit notes.",
)
detail = detail.replace(
    "- **101** test files",
    "- **23** test modules: **15 integration + 6 unit + 2 architecture**",
)
marker = "## Maintenance Rules\n"
section = """## Test Suite Structure Consolidation

Test Consolidation Stage 1 reorganized the integration suite from **93 historical integration test files** into **15 behavior-domain modules** while preserving all **856 integration cases** and all **899 collected tests** across the project.

The consolidation is organizational only: application runtime code is unchanged. Human-readable provenance is stored in `tests/integration/README.md`; machine-readable provenance and per-domain counts are stored in `tests/integration/consolidation_manifest.json`.

New integration regression tests should be added to the relevant domain module rather than creating a new `round`/follow-up module. Round history belongs in `audits/4.12/rounds/`, changelog entries where appropriate, and Git history.

"""
if section not in detail:
    detail = detail.replace(marker, section + marker)
detail = detail.replace(
    "7. File integrity and privacy guarantees take precedence over optimistic success reporting or diagnostic convenience.",
    "7. File integrity and privacy guarantees take precedence over optimistic success reporting or diagnostic convenience.\n"
    "8. New integration regressions should be placed in the appropriate domain module; do not create new `test_*round*.py` or `test_report_followup_*.py` files.",
)
detail_path.write_text(detail, encoding="utf-8")
