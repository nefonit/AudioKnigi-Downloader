# AudioKnigi Downloader — Test Consolidation Stage 1

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
