# Реестр дефектов: историческая выборка с доказательствами

AudioKnigi Downloader 4.12.42 | QA Baseline v1.0 | 2026-10-15

Это **индекс исторически задокументированных исправлений**, а не утверждение, что дефекты воспроизведены в текущем EXE или официально закрыты по приёмке. Полные аудиты каждого Round находятся в `HISTORY_EVIDENCE.csv`.

| ID | Краткое описание | Round | Серьёзность | Статус | Источник |
| --- | --- | --- | --- | --- | --- |
| HDEF-001 | 125% UI scale on fresh settings mapping | R02 | Major | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20260915_ROUND2.md |
| HDEF-002 | Nonfinite loudnorm fallback | R02 | Major | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20260915_ROUND2.md |
| HDEF-003 | UTF-8 search decoding and resuming queue | R20 | Major | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20260917_ROUND20.md |
| HDEF-004 | Advanced book tab geometry after analysis | R48 | Major | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20260923_ROUND48.md |
| HDEF-005 | DNS Auto fallback after Cloudflare failure | R58 | Critical | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20260928_ROUND58.md |
| HDEF-006 | User profile absolute paths leak in support bundles | R63 | Critical | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20260929_ROUND63.md |
| HDEF-007 | Missing-media refresh 404/410 contract | R69 | Major | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20260930_ROUND69.md |
| HDEF-008 | Primitive indices and Mapping track selection | R79 | Major | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20261005_ROUND79.md |
| HDEF-009 | Incomplete HTTP response falsely considered complete | R81 | Critical | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20261006_ROUND81.md |
| HDEF-010 | Runtime progress/error localization gaps | R89 | Minor | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20261011_ROUND89.md |
| HDEF-011 | String paths in crash-report helpers | R90 | Major | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20261012_ROUND90.md |
| HDEF-012 | Quoted secrets with spaces in log sanitizer | R90 | Critical | Historical fix documented; release re-test not evidenced | audits/4.12/rounds/AUDIT_NOTES_20261012_ROUND90.md |