# Test Execution History — ретроспектива, а не новый прогон

AudioKnigi Downloader 4.12.42 | QA Baseline v1.0 | 2026-10-15

**Внимание:** тестовый статус определяется конкретным commit/build/средой. Результаты прежних rounds не суммируются и не доказывают готовность текущего EXE. Ни один из новых ручных кейсов автоматически не становится Passed.

| Date | Baseline | Объявленный результат | Первичный источник | Ограничение |
| --- | --- | --- | --- | --- |
| 2026-09-05 | Архивация ранних релизов / 4.12.31 | 107 архивов; 456 уникальных прошлых вариантов; 445/445 исторически задокументированных текущих тестов | archive/history/RECOVERY_AUDIT.md | Испытания относятся к ревизии даты аудита, не к Round 90 |
| 2026-09-17 | Round 20 | 370 passed в историческом отчёте | audits/4.12/rounds/AUDIT_NOTES_20260917_ROUND20.md | Не переносить в статистику текущего SHA |
| 2026-09-23 | Round 48 | 604/604 исторически сообщалось | audits/4.12/rounds/AUDIT_NOTES_20260923_ROUND48.md | Сведения в аудите/истории переписки, не новый прогон |
| 2026-09-28 | Round 58 | 14 focused/settings PASS локально; прочие CI итоги в первичном audit не указаны | audits/4.12/rounds/AUDIT_NOTES_20260928_ROUND58.md | Не приравнивать к полному CI; журнал Round 58 содержит только локальные фокусные результаты |
| 2026-10-11 | Round 89 | 955 runnable passed; 2 блокированы PySide6; 957 collected | audits/4.12/rounds/AUDIT_NOTES_20261011_ROUND89.md | Результат прежней ревизии |
| 2026-10-12 | Round 90 / расширенная проверка | 905 passed (пять независимых групп) без Qt accessibility | audits/4.12/rounds/AUDIT_NOTES_20261012_ROUND90.md | В том же файле есть более ранние ограниченные прогоны |
| 2026-10-15 | Round 90 / предыдущая ревизия | 967 passed (811 + 156), исключён Qt accessibility | audits/4.12/rounds/REPORT_20261015_172446_VERIFICATION.md | Тесты выполнены до данной ретроспективной документации, без нового Windows EXE прогона |

## Состояние QA baseline

- Текущий SHA документирования: `157e16a23f9b88a7dbebc6c6c0f0d694df2bd0c0`.
- Архивная история: Round 2–90, дополнительно исторические 3.x–4.9 и версии Qt/пред-Qt из архивных индексов.
- Автоматизация текущего релиза: по последнему аудиту 967 Pass, но **повторный независимый официальный релизный прогон не выполнен при создании этих документов**.
- Ручные кейсы: Not Run / Not Evidenced.
- Windows EXE runtime, NVDA, JAWS: Not Evidenced.

## Шаблон новой записи прогона

`Run ID | Дата UTC | Коммит | Build SHA256 | Windows/Python/Qt | Команда | Collected | Pass | Fail | Skip | Blocked | Logs URL | Исполнитель | Подпись`.

## 2026-10-30 — Round 90 external report verification (new execution)

- Baseline: `main`, source snapshot before October 30 fixes, then corrected working copy.
- Evidence: `audits/4.12/rounds/REPORT_20261030_193239_VERIFICATION.md`.
- Execution: 811 unit/core/integration passed, 3 deselected; 156 provider tests passed. 967 passed total; excludes Windows/PySide6 accessibility and live-source acceptance.
- Confirmed/covered: synchronous EndOfMedia state race, inconsistent numeric track-title padding, and missing dynamic ID3 translation.
- Manual test cases are **Not Run**; this evidence does not authorize production release.
