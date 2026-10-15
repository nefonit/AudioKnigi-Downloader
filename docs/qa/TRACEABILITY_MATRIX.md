# Requirements Traceability Matrix (RTM)

AudioKnigi Downloader 4.12.42 | QA Baseline v1.0 | 2026-10-15

Матрица показывает наличие проектного тест-кейса и возможный тестовый модуль, но **не доказывает фактическое исполнение** конкретного ручного кейса и не устанавливает 1:1 связь с pytest node-id.

| Requirement | Area | Manual test cases | Unit/Integration module | Evidence state |
| --- | --- | --- | --- | --- |
| RQ-SRC-01 | Источники и анализ | TC-SRC-001, TC-SRC-002, TC-SRC-003, TC-SRC-004, TC-SRC-005, TC-SRC-006 | test_providers.py; test_search.py | Частичное (на уровне модулей) |
| RQ-DL-01 | Загрузка глав | TC-DL-001, TC-DL-002, TC-DL-003, TC-DL-004, TC-DL-005, TC-DL-006, TC-DL-007, TC-DL-008, TC-DL-009, TC-DL-010 | test_download_flow.py; test_network.py | Частичное (на уровне модулей) |
| RQ-NET-01 | Сеть и отмена | TC-NET-001, TC-NET-002, TC-NET-003, TC-NET-004, TC-NET-005 | test_network.py; test_download_flow.py | Частичное (на уровне модулей) |
| RQ-AUD-01 | Аудио/FFmpeg | TC-AUD-001, TC-AUD-002, TC-AUD-003, TC-AUD-004, TC-AUD-005, TC-AUD-006, TC-AUD-007 | test_media_processing.py | Частичное (на уровне модулей) |
| RQ-Q-01 | Очередь | TC-Q-001, TC-Q-002, TC-Q-003, TC-Q-004, TC-Q-005, TC-Q-006, TC-Q-007 | test_queue_history.py | Частичное (на уровне модулей) |
| RQ-H-01 | История/резервные копии | TC-H-001, TC-H-002, TC-H-003, TC-H-004 | test_queue_history.py | Частичное (на уровне модулей) |
| RQ-P-01 | Плеер | TC-P-001, TC-P-002, TC-P-003, TC-P-004, TC-P-005, TC-P-006 | test_player.py | Частичное (на уровне модулей) |
| RQ-CFG-01 | Настройки | TC-CFG-001, TC-CFG-002, TC-CFG-003, TC-CFG-004, TC-CFG-005, TC-CFG-006 | test_settings_contract.py | Частичное (на уровне модулей) |
| RQ-I18N-01 | Локализация | TC-I18N-001, TC-I18N-002, TC-I18N-003, TC-I18N-004, TC-I18N-005 | test_localization.py | Частичное (на уровне модулей) |
| RQ-AX-01 | Доступность | TC-AX-001, TC-AX-002, TC-AX-003, TC-AX-004, TC-AX-005, TC-AX-006, TC-AX-007 | test_accessibility.py; test_qt_ui.py | Частичное (на уровне модулей) |
| RQ-UI-01 | Интерфейс | TC-UI-001, TC-UI-002, TC-UI-003, TC-UI-004 | test_qt_ui.py | Частичное (на уровне модулей) |
| RQ-SEC-01 | Приватность/диагностика | TC-SEC-001, TC-SEC-002, TC-SEC-003, TC-SEC-004 | test_privacy_diagnostics.py | Частичное (на уровне модулей) |
| RQ-REL-01 | Устойчивость/файлы | TC-REL-001, TC-REL-002, TC-REL-003, TC-REL-004 | test_core_services.py; test_queue_history.py | Частичное (на уровне модулей) |
| RQ-BLD-01 | Сборка и установка | TC-BLD-001, TC-BLD-002, TC-BLD-003, TC-BLD-004 | test_build_release.py; test_quality_gates.py | Частичное (на уровне модулей) |