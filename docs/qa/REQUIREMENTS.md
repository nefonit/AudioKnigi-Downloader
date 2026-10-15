# Реестр требований (производные от фактических функций)

AudioKnigi Downloader 4.12.42 | QA Baseline v1.0 | 2026-10-15

**Базовая ревизия исходников:** `157e16a23f9b88a7dbebc6c6c0f0d694df2bd0c0` (GitHub `main`, 15.10.2026).  
**Источник фактов:** исходный ZIP Round 90, `README.md`, `CHANGELOG.md`, `docs/`, `tests/`, `audits/4.12/rounds/` и `archive/history/`.  
**Правило доказательности:** отмечать PASS только при наличии конкретного протокола исполнения. Ретроспективный тест-кейс = спецификация проверки, а не свидетельство, что она была выполнена.

**Важно:** это baseline наблюдаемых функций, составленный ретроспективно; пока владелец продукта не утвердил его как спецификацию.

| ID | Область | Проверяемое требование | Приоритет | Основание в коде | Доменные автотесты |
| --- | --- | --- | --- | --- | --- |
| RQ-SRC-01 | Источники и анализ | Поиск, выбор провайдера, метаданные, варианты озвучки | P1 | audioknigi/providers/; audioknigi/services/book_analysis_service.py | test_providers.py; test_search.py |
| RQ-DL-01 | Загрузка глав | Выбор частей, скачивание, полная книга, возобновление | P1 | audioknigi/download/; audioknigi/download_engine.py | test_download_flow.py; test_network.py |
| RQ-NET-01 | Сеть и отмена | Range/HTTP, DNS, Cloudflare, пауза/отмена | P1 | audioknigi/download/network.py; audioknigi/network_dns.py | test_network.py; test_download_flow.py |
| RQ-AUD-01 | Аудио/FFmpeg | MP3, сегментация, нормализация, битрейт, теги | P2 | audioknigi/download/media.py | test_media_processing.py |
| RQ-Q-01 | Очередь | Постановка, сохранение, повтор, отмена, восстановление | P1 | audioknigi/services/queue_service.py | test_queue_history.py |
| RQ-H-01 | История/резервные копии | История, экспорт CSV, дубликаты, резервные копии | P2 | audioknigi/services/library_service.py | test_queue_history.py |
| RQ-P-01 | Плеер | Воспроизведение, позиция, скорость, громкость, медиа-клавиши | P1 | audioknigi/qt/player_controller.py | test_player.py |
| RQ-CFG-01 | Настройки | Миграция, запись, первый запуск, темы и масштаб | P2 | audioknigi/config/settings.py | test_settings_contract.py |
| RQ-I18N-01 | Локализация | RU/UK/DE/EN, динамический текст, справка | P2 | audioknigi/i18n.py; audioknigi/locales/ | test_localization.py |
| RQ-AX-01 | Доступность | NVDA/JAWS, клавиатура, фокус, объявления, F1 | P1 | audioknigi/qt/accessibility.py | test_accessibility.py; test_qt_ui.py |
| RQ-UI-01 | Интерфейс | Простой/расширенный режим, поиск, таблица глав | P2 | audioknigi/qt/main_window.py | test_qt_ui.py |
| RQ-SEC-01 | Приватность/диагностика | Редакция логов, диагностика, crash/support ZIP | P1 | audioknigi/diagnostics/; audioknigi/logging_utils.py | test_privacy_diagnostics.py |
| RQ-REL-01 | Устойчивость/файлы | Аварийное закрытие, диск, повреждённый JSON | P1 | audioknigi/services/; audioknigi/download/ | test_core_services.py; test_queue_history.py |
| RQ-BLD-01 | Сборка и установка | Windows EXE, упакованные файлы, обновление | P2 | build_qt_exe.bat; .github/workflows/ | test_build_release.py; test_quality_gates.py |