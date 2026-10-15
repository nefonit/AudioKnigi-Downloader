# Release readiness / Go–No-Go — Round 90

AudioKnigi Downloader 4.12.42 | QA Baseline v1.0 | 2026-10-15

| Критерий | Текущее свидетельство | Статус | Следующее действие |
|---|---|---|---|
| Актуальный код и история | GitHub SHA `157e16a23f9b88a7dbebc6c6c0f0d694df2bd0c0`; архивы и аудит | Evidence | Заморозить релизный SHA |
| Регрессионный Python | Исторический отчёт 967 PASS по группам | Historical Pass | Запустить весь suite на exact релизном SHA и сохранить junit/логи |
| Windows PySide6 E2E | Нет подтверждённого теста exact сборки | Blocked | Выполнить smoke + реальные скачивания |
| NVDA keyboard и speech | Нет подписанного протокола | Blocked | Выполнить P1 с NVDA |
| JAWS keyboard и speech | Нет подписанного протокола | Blocked | Выполнить P1 с JAWS |
| Network/resume/FFmpeg failure E2E | Есть unit/integration и архивные аудиты, не релизный сетевой E2E | Partial | Выполнить тестовый HTTP stub и реальный источник |
| Privacy diagnostic ZIP на Windows | Были регрессионные тесты, релизный ZIP не проверен вручную | Partial | Проверить токены и пути в support ZIP |
| Windows EXE build и установка | Есть CI/scripts, точный артефакт не проверен | Blocked | Проверить SHA-256, Defender, AV, первый запуск |
| Открытые Blocker/Critical | Нет отдельного подтверждённого triage реестра open issues | Unknown | Провести triage и согласовать остаточные риски |
| Product Owner sign-off | Нет | Pending | Решение после всех P1 |

**Итоговое решение: No-Go / Pending Acceptance**, пока не получены перечисленные доказательства. Это не отменяет успешных автоматических проверок и не означает, что каждый путь нестабилен.