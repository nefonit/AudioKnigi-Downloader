# Test Suites / распределение по функциональным пакетам

| Suite | Coverage | Evidence | Acceptance |
|---|---|---|---|
| S-01 Source analysis | SRC, search, variant selection | `tests/integration/test_providers.py`, `test_search.py` | URL, chapters, variants |
| S-02 Download & Network | DL, NET, REL | `test_download_flow.py`, `test_network.py` | byte-perfect transfer, cancel/resume |
| S-03 Media | AUD | `test_media_processing.py` | duration, playable MP3, loudnorm, tags |
| S-04 Queue/History | Q, H | `test_queue_history.py` | persistence, status transitions |
| S-05 Playback | P | `test_player.py` | resume, seek, play/pause |
| S-06 Settings & localization | CFG, I18N | `test_settings_contract.py`, `test_localization.py` | migration, translated states |
| S-07 Accessibility | AX, UI | `test_accessibility.py`, `test_qt_ui.py` | Windows NVDA/JAWS independent manual P1 |
| S-08 Privacy & diagnostics | SEC | `test_privacy_diagnostics.py` | token/path redaction, support bundle |
| S-09 Build/Release | BLD | `test_build_release.py`, `test_quality_gates.py` | Windows exact EXE smoke |

## Entry/Exit of suites

Automated suites require exact SHA, reproducible dependencies and captured logs. Manual suites require real device/software versions, dated evidence and clear Pass/Fail/Blocked. A suite is not passed merely because related code was audited. Before release, P1 manual acceptance must have written results.