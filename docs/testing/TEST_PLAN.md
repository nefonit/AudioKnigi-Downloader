**TEST PLAN**

**Project “AudioKnigi Downloader”**

Версія тестової бази: 4.12.42 Round 81

*Статус: Stable baseline / Living test documentation*

Дата: 08.10.2026

Методологічна основа: ISTQB CTFL v4.0.1 та фактична історія тестування проєкту.

# Історія переглядів документа

| **Date**   | **Version** | **Description**                                                                       | **Author / Role**       | **Review**                        | **Approver**  |
|------------|-------------|---------------------------------------------------------------------------------------|-------------------------|-----------------------------------|---------------|
| 08.10.2026 | 1.0         | Створено повний baseline тестової документації на основі історії проєкту до Round 81. | Project QA / Maintainer | Self-review + regression evidence | Project Owner |

# ЗМІСТ (Table of Contents)

1. INTRODUCTION (Вступ)
2. SCOPE (Область застосування)
3. QUALITY OBJECTIVES (Цілі якості)
4. TEST APPROACH (Підхід до тестування)
5. ROLES AND RESPONSIBILITIES (Ролі та відповідальність)
6. ENTRY AND EXIT CRITERIA (Критерії входу та виходу)
7. SUSPENSION CRITERIA AND RESUMPTION REQUIREMENTS
8. TEST STRATEGY (Стратегія тестування)
9. RESOURCE AND ENVIRONMENT NEEDS (Ресурси та середовище)
10. TEST SCHEDULE AND DEVELOPMENT HISTORY (Графік та історія)
11. TEST DELIVERABLES (Тестові артефакти)
12. RISKS AND MITIGATION (Ризики)
13. TEST COMPLETION SUMMARY (Підсумок Round 81)
14. APPROVALS (Затвердження)

# 1 INTRODUCTION (Вступ)

Цей тест-план описує стратегію, обсяг, критерії, середовище, тестові артефакти та підсумкові критерії якості для AudioKnigi Downloader — Windows-орієнтованого доступного PySide6/Qt застосунку для пошуку, аналізу, завантаження, організації та прослуховування аудіокниг.

Документ консолідує не один окремий реліз, а всю накопичену QA-роботу: історію версій від 4.7.x до 4.12.42 Round 81, 80 поточних audit notes, 119 записів changelog, активний набір автоматизованих тестів та ручну регресійну модель. Детальні чек-листи, test suites, test cases, історичні defect reports, traceability і перелік автоматизованих тестів ведуться як супровідна тестова база.

## 1.1 Методологічна база

- Структура документа охоплює основні розділи Test Plan: Introduction, Scope, Quality Objectives, Test Approach, Roles, Entry/Exit Criteria, Suspension/Resumption, Test Strategy, Resources, Schedule, Approvals.
- Чек-лист використовується як стислий список перевірок без детальної процедури; test case — як детальний сценарій з передумовами, кроками та очікуваним результатом; test suite — як логічне групування test cases; bug report — як відтворюваний опис дефекту.
- Підхід узгоджений з ISTQB CTFL: test plan описує test objectives, resources, processes, assumptions/constraints, risks, test approach, entry/exit criteria, metrics, schedule; test completion report містить summary, оцінку якості, відхилення, metrics, невиправлені ризики та lessons learned.

# 2 SCOPE (Область застосування)

## 2.1 Об’єкт тестування

- Qt-only desktop application для Windows із GUI-independent core/services там, де це можливо.
- Три джерела: audioknigi.com.ua, knigavuhe.org, poleknig.com.
- Пошук, аналіз книги, варіанти озвучення, вибір частин, full-MP3, resume, Range download, FFmpeg/FFprobe processing, metadata/covers/sidecars.
- Черга, історія, duplicate preflight, unfinished downloads, backup/restore, CSV export.
- Вбудований Qt Multimedia player, position persistence, chapter navigation.
- RU / UK / DE / EN localization, Help Center, event sounds.
- Keyboard-first accessibility, NVDA/JAWS-oriented behavior, system tray, media keys, clipboard/drag-and-drop.
- Cloudflare DoH / browser fallback / source health та privacy-conscious diagnostic support ZIP.

## 2.2 Функціональний обсяг

| **ID** | **Область** | **Функціональність / якісна характеристика** | **Priority** |
|---|---|---|---|
| REQ-SEARCH-01 | Пошук | Мультиджерельний пошук | High |
| REQ-SEARCH-02 | Пошук | Пошук за назвою та автором | High |
| REQ-SEARCH-03 | Пошук | Пряме відкриття URL | High |
| REQ-SEARCH-04 | Пошук | Сортування та доступність результатів | Medium |
| REQ-ANALYSIS-01 | Аналіз книги | Метадані книги | High |
| REQ-ANALYSIS-02 | Аналіз книги | Варіанти озвучення | High |
| REQ-ANALYSIS-03 | Аналіз книги | Межі та тривалість частин | High |
| REQ-DL-01 | Завантаження | Вибрані частини | Critical |
| REQ-DL-02 | Завантаження | Один MP3 | High |
| REQ-DL-03 | Завантаження | Відновлення завантаження | Critical |
| REQ-DL-04 | Завантаження | Сегментоване Range-завантаження | Critical |
| REQ-DL-05 | Завантаження | Оновлення прострочених URL | Critical |
| REQ-DL-06 | Завантаження | Рішення для недоступної частини | High |
| REQ-MEDIA-01 | Медіа | FFmpeg/FFprobe обробка | Critical |
| REQ-MEDIA-02 | Медіа | Нормалізація гучності | High |
| REQ-MEDIA-03 | Медіа | Теги, обкладинка та sidecar | High |
| REQ-TPL-01 | Шаблони | Імена папок і файлів | High |
| REQ-QUEUE-01 | Черга | Збереження черги | High |
| REQ-QUEUE-02 | Черга | Керування задачами | High |
| REQ-QUEUE-03 | Черга | Режим одного MP3 у черзі | High |
| REQ-LIB-01 | Бібліотека/історія | Duplicate preflight | High |
| REQ-LIB-02 | Бібліотека/історія | Незавершені завантаження | High |
| REQ-LIB-03 | Бібліотека/історія | Backup/restore/CSV | Medium |
| REQ-PLAYER-01 | Плеєр | Відтворення та позиція | High |
| REQ-PLAYER-02 | Плеєр | Навігація і керування | Medium |
| REQ-SET-01 | Налаштування | Схема та міграції | High |
| REQ-LOC-01 | Локалізація | RU/UK/DE/EN | High |
| REQ-A11Y-01 | Доступність | Keyboard-first | Critical |
| REQ-A11Y-02 | Доступність | NVDA/JAWS | Critical |
| REQ-NET-01 | Мережа | Protected sources | High |
| REQ-NET-02 | Мережа | DNS/DoH | High |
| REQ-DIAG-01 | Діагностика | Support bundle | Critical |
| REQ-UI-01 | UI | Simple/Advanced flows | High |
| REQ-UI-02 | UI | Масштабування і DPI | Medium |
| REQ-INT-01 | Інтеграції | Clipboard/Drag&Drop | Medium |
| REQ-WIN-01 | Windows | Tray/media keys/build | High |
| NFR-REL-01 | Надійність | Cancellation/concurrency | Critical |
| NFR-COMP-01 | Сумісність | Runtime/build | High |

## 2.3 Поза поточним обсягом

- Підтримка сторонніх сайтів, яких немає в provider registry.
- Офіційна release-підтримка macOS/Linux; проєкт орієнтований на Windows.
- Тестування коректності контенту сторонніх сайтів як їхньої бізнес-відповідальності.
- Юридична оцінка ліцензування/авторських прав; у QA перевіряється лише наявність release notices/checklists.
- Навантажувальне тестування сторонніх сайтів, яке могло б створювати небажаний трафік.

# 3 QUALITY OBJECTIVES (Цілі якості)

Мета тестування — підтвердити, що ключові користувацькі потоки стабільні, дані не пошкоджуються, помилки відновлюються контрольовано, а застосунок залишається доступним для користувачів клавіатури та скринридерів.

## 3.1 Primary Objectives (Основні цілі)

1. Критичні потоки Search → Analyze → Select → Download/Queue → Playback не мають Blocker/Critical відкритих дефектів.
2. Завантажений файл не вважається успішним без перевірки цілісності/тривалості згідно доступних метаданих.
3. Скасування та shutdown не залишають завислих worker/process/timer callback-ів.
4. Index 0, legacy/string indices, malformed metadata та інші edge cases не повинні призводити до тихих втрат вибору або crash.
5. Privacy diagnostics не повинні розкривати secrets, приватні шляхи, назви книг або медіафайли.
6. Accessibility critical path має бути виконуваним без миші, а NVDA/JAWS повинен отримувати семантичні назви/статуси.

## 3.2 Secondary Objectives (Додаткові цілі)

7. Чотиримовна локалізація без mixed-language runtime strings.
8. Стабільне масштабування/large DPI та коректне розміщення допоміжних UI-елементів.
9. Backward compatibility налаштувань, queue/resume manifests і history data.
10. Відтворювана release-перевірка через автоматизовані quality gates.

# 4 TEST APPROACH (Підхід до тестування)

Використовується risk-based regression approach: критичні сценарії завантаження, цілісності файлів, відновлення, accessibility та privacy виконуються першими. Автоматизовані unit/integration/architecture тести є основною regression safety net; ручні test cases покривають end-to-end, Windows runtime та screen-reader acceptance.

## 4.1 Test Levels / Types

| **Рівень / Type** | **Фокус** |
|---|---|
| Unit | Settings, i18n, templates, provider registry, models, diagnostics helpers. |
| Integration | Search parsers, network, download flow, queue/history/player state, fallback/recovery, localization contracts. |
| Architecture | Project layout, runtime import boundaries, retired legacy isolation. |
| System / Manual | Повний GUI flow, real filesystem/network behavior, Windows integration. |
| Accessibility Acceptance | Keyboard-only, NVDA/JAWS, focus, announcements, context menus. |
| Regression / Quality Gates | Full pytest, compile, JSON strict checks, static audits, historical regression. |

## 4.2 Test Automation

- Активний pytest baseline Round 81: 899 collected tests (27 unit, 856 integration, 16 architecture).
- Остання повна перевірка: 897 passed; 2 Qt accessibility self-tests blocked лише через відсутній PySide6 у середовищі перевірки.
- Окремі quality gates: compileall, strict JSON duplicate-key check, undefined-global, unused-import, exception, Qt-localization audits; release workflow також передбачає full parity, Qt import/runtime boundary та historical regression checks.
- Кожен audit round додає focused regression tests на підтверджені дефекти; хибні/архітектурні findings документуються без зайвих кодових змін.

## 4.3 Test Case Prioritization

- Critical/P1: file integrity, selected parts/index handling, cancellation, accessibility critical path, privacy/secrets, packaged runtime launch.
- High/P2: search/analysis correctness, queue persistence, duplicate protection, localization, source health/recovery.
- Medium/P3: secondary UI behavior, layout/DPI, convenience integrations, non-blocking polish.

# 5 ROLES AND RESPONSIBILITIES (Ролі та відповідальність)

| **Роль** | **Відповідальність** |
|---|---|
| Project Owner / Maintainer | Визначає продуктову поведінку, приймає ризики, затверджує release readiness. |
| QA Engineer | Test planning, чек-листи/test cases, exploratory/regression testing, defect reporting, traceability, test completion summary. |
| Developer / Maintainer | Unit/integration fixes, root-cause analysis, code review, instrumentation, підтримка testability. |
| Automation / CI | Запуск pytest та quality gates, збір release artifacts, фіксація regression failures. |
| Accessibility Reviewer | Keyboard/NVDA/JAWS acceptance на реальному Windows/PySide6 build. |
| External Audit / Review | Надає findings; кожен пункт перевіряється по фактичному коду та тестами перед виправленням. |

# 6 ENTRY AND EXIT CRITERIA (Критерії входу та виходу)

## 6.1 Entry Criteria

1. Визначено конкретний baseline (version/commit/ZIP) та changelog.
2. Проєкт компілюється; залежності для відповідного test level доступні.
3. Для мережевих тестів визначено source/fixture або контрольований mock.
4. Для Windows acceptance доступний реальний PySide6 build, Edge, FFmpeg/ffprobe; для NVDA/JAWS acceptance — відповідний screen reader.
5. Тестові дані не містять приватних credentials або піратського/чутливого контенту.

## 6.2 Exit Criteria

1. 0 відкритих Blocker/Critical defects у critical user flows або явне stakeholder risk acceptance.
2. Усі runnable automated tests проходять; blocked tests мають документовану environment reason і виконуються у належному release environment.
3. Compile/JSON/static quality gates проходять без нових помилок.
4. Critical manual smoke: search, analyze, selected download, full MP3, queue, player, localization, privacy bundle, keyboard flow — Passed.
5. Відомі залишкові ризики/відхилення внесені в Test Completion Summary.

# 7 SUSPENSION CRITERIA AND RESUMPTION REQUIREMENTS

## 7.1 Suspension criteria

- Blocker, що унеможливлює запуск програми або базовий аналіз/завантаження.
- Пошкодження або втрата даних у history/queue/settings/output.
- Неповний/пошкоджений файл помилково маркується як успішний.
- Виявлена privacy leak у support bundle або логах.
- Середовище тестування некоректне: відсутній необхідний runtime, source outage робить результат недостовірним, corrupted fixtures.

## 7.2 Resumption criteria

- Root cause локалізовано та виправлено або ізольовано.
- Додано regression test, що відтворює дефект до fix та проходить після fix.
- Залежне середовище/fixture відновлено.
- Focused regression suite проходить; після цього відновлюється broader regression.

# 8 TEST STRATEGY (Стратегія тестування)

## 8.1 Test Suites

| **ID** | **Suite** | **Level / Type** | **Priority** |
|---|---|---|---|
| TS-01 | Search & Source Discovery | System / Functional | High |
| TS-02 | Book Analysis | System / Integration | High |
| TS-03 | Selected Parts Download | System / Functional | Critical |
| TS-04 | Full MP3 Download | System / Functional | High |
| TS-05 | Network Resume & Segmentation | Integration / Reliability | Critical |
| TS-06 | Expired/Missing Media Recovery | Integration / Recovery | Critical |
| TS-07 | Media Processing | Integration / Functional | Critical |
| TS-08 | Metadata & Templates | System / Functional | High |
| TS-09 | Queue | System / Functional | High |
| TS-10 | History & Library | System / Functional | High |
| TS-11 | Player | System / Functional | High |
| TS-12 | Settings & Migration | Unit / Integration | High |
| TS-13 | Localization | System / Localization | High |
| TS-14 | Accessibility | Acceptance / Accessibility | Critical |
| TS-15 | Network & Source Health | Integration / Reliability | High |
| TS-16 | Diagnostics & Privacy | System / Security/Privacy | Critical |
| TS-17 | UI Modes & DPI | System / UI | High |
| TS-18 | Windows Integration | Acceptance / Compatibility | High |
| TS-19 | Cancellation & Shutdown | Integration / Reliability | Critical |
| TS-20 | Release Quality Gates | Regression / Quality Gate | Critical |

## 8.2 Defect lifecycle

Рекомендований життєвий цикл: New → Confirmed/Open → In Progress → Fixed/Ready for QA → Verified/Closed. Додаткові стани: Reopened, Deferred, Duplicate, Rejected/False Positive. Audit finding не вважається дефектом, доки його не підтверджено по фактичному коду/поведінці.

| **Severity** | **Визначення** |
|---|---|
| Blocker | Застосунок/ключовий flow неможливо використовувати. |
| Critical | Crash, data/file corruption, privacy leak, критичний accessibility blocker. |
| Major | Основна функція працює неправильно, але є workaround/обмежений scope. |
| Minor | Некритичний UI/localization/ergonomics defect. |
| Trivial | Косметичний або документаційний дефект без впливу на flow. |

## 8.3 Traceability / Configuration Management

- Кожна manual test case має Requirement ID та Test Suite ID.
- Checklist містить Requirement ID; test repository агрегує suites, cases та checklist items.
- Автоматизовані тести ідентифікуються повним pytest node id; baseline містить усі 899 node IDs.
- Реліз/аудит версіонується через changelog, Git commit/ZIP, audit notes та test evidence.

# 9 RESOURCE AND ENVIRONMENT NEEDS (Ресурси та середовище)

## 9.1 Testing Tools

- pytest
- Python compileall
- Project quality audit scripts
- Git/GitHub
- Microsoft Edge + Playwright fallback
- FFmpeg / FFprobe
- NVDA / JAWS for manual acceptance
- Structured test documentation

## 9.2 Test Environment

| **Компонент** | **Baseline** |
|---|---|
| Source/runtime | Python 3.11+ |
| Official Windows CI/release | CPython 3.14.7 x64 (project-pinned toolchain) |
| GUI | PySide6 / Qt |
| OS focus | Windows 10/11 |
| Browser fallback | Installed Microsoft Edge |
| Media tools | FFmpeg + FFprobe in PATH or bundled build |
| Sources | audioknigi.com.ua, knigavuhe.org, poleknig.com |
| Languages | RU, UK, DE, EN |
| Accessibility | Keyboard-only + NVDA/JAWS acceptance |

# 10 TEST SCHEDULE AND DEVELOPMENT HISTORY (Графік та історія)

QA виконувався ітеративно: кожна функціональна зміна або зовнішній audit finding проходили перевірку → targeted fix → focused regression → broader/full suite → packaging/integrity check → Git baseline. Історія changelog містить 119 версій/раундів; поточна гілка 4.12.42 містить 80 audit notes.

| **Період** | **Основний QA-фокус** |
|---|---|
| 4.7.x | Базова архітектура пакета, first-run, resume, duplicate detection, accessibility/localization foundation. |
| 4.8.x | Native UI/accessibility/input stability, drag&drop, timing, settings autosave, багато перевірок false-positive audit findings. |
| 4.9.x | Друге джерело Knigavuhe, search relevance, author/title/narrator metadata, narration variants. |
| 4.10.x | Event sounds і language-aware audio cues. |
| 4.11.x | Третє джерело PoleKnig, author catalog search і narration variants. |
| 4.12.0–31 | Universal search/open flow, keyboard/validation UX, downloads/recovery, help, queue/player, accessibility, Windows packaging, Qt migration. |
| 4.12.32–42 | Structured refactor, quality gates, runtime integrity, diagnostics, cancellation, localization, compatibility. |
| Round 61–81 | Систематичний зовнішній audit follow-up: edge cases, privacy, indices, network integrity, fallback, accessibility і regression contracts. |

# 11 TEST DELIVERABLES (Тестові артефакти)

- Цей Test Plan.
- Детальна тестова база: вимоги, тестові набори, чек-лист, тест-кейси, історичні баг-репорти, трасування, автотести, історія QA.
- Automated pytest suite: 899 collected node IDs у 101 test files.
- 80 audit notes у audits/4.12/rounds та 119 changelog entries.
- Runtime/source documentation у README/docs та release quality scripts.

# 12 RISKS AND MITIGATION (Ризики)

| **Risk** | **Impact** | **Mitigation** |
|---|---|---|
| Зовнішні сайти змінюють HTML/API/Cloudflare | High | Fixtures, parser diagnostics, SiteStructureChanged, browser fallback, source-health classification, regression parsers. |
| CDN URL протухає/файл неповний | Critical | Playlist refresh, fallback source, size/duration validation, single/segmented integrity checks. |
| Legacy state/manifest містить malformed data | High | Normalization/safe_int, migrations, fail-closed parsing, compatibility regressions. |
| Concurrency/cancel race | Critical | Cancel events, process ownership, peer abort, lifecycle-safe callbacks, shutdown regressions. |
| Privacy leak у diagnostics | Critical | Redaction, bounded tails, exclusion lists, dedicated privacy regressions. |
| Accessibility regression після UI change | Critical | Stable accessible IDs, keyboard contracts, self-test + real NVDA/JAWS acceptance. |
| PySide6/Windows-only behavior не відтворюється у headless Linux env | Medium | Окремий Windows runtime acceptance gate; blocked tests не трактуються як product failure без environment. |

# 13 TEST COMPLETION SUMMARY (Підсумок Round 81)

| **Metric** | **Result** |
|---|---|
| Baseline | AudioKnigi Downloader 4.12.42 Round 81 |
| Git main commit | f53fc4dba5247561317e12f40ec166db0d3c4d17 |
| Automated tests collected | 899 |
| Passed | 897 |
| Blocked by environment | 2 (Qt accessibility self-tests: PySide6 unavailable in validation environment) |
| Runnable pass rate | 100.00% |
| Overall collected pass share | 99.78% |
| Test files | 101 |
| Active audit notes | 80 |
| Changelog entries | 119 |
| Manual baseline cases | 68 |
| Checklist items | 131 |
| Historical verified defects | 25 |
| Static checks | compileall + strict JSON + undefined_global + unused_import + exception + qt_localization: PASS |

## 13.1 Quality evaluation

За наявними evidence Round 81 може використовуватися як стабільний regression baseline: всі runnable автоматизовані тести пройшли; два tests не виконані лише через відсутність PySide6 у конкретному середовищі перевірки. Остаточний public/release sign-off повинен додатково включати реальний Windows packaged-build smoke та NVDA/JAWS acceptance, тому стабільність не трактується як математична гарантія відсутності дефектів.

## 13.2 Lessons learned

- Кожен зовнішній audit finding необхідно відтворювати по реальному source/archive; значна частина reports була stale або false-positive.
- Edge cases навколо індексу 0, bool як subclass int, string.index, Mapping vs model objects і malformed legacy data потребують явних regression contracts.
- Цілісність файлів важливіша за «успішне завершення» HTTP/FFmpeg процесу: необхідні size/duration/segment checks.
- Accessibility і localization є функціональними вимогами, а не cosmetic post-processing.
- Privacy diagnostics повинні балансувати діагностичну цінність і over-redaction на користь безпеки користувача.

# 14 APPROVALS (Затвердження)

Цей Test Plan встановлює baseline тестової документації для AudioKnigi Downloader 4.12.42 Round 81. Документ є living document та оновлюється при новому релізі/раунді або зміні test strategy.

| **Роль** | **Ім’я** | **Підпис** | **Дата** |
|---|---|---|---|
| Project Owner / Maintainer | | | |
| QA Engineer | | | |
| Accessibility Acceptance Reviewer | | | |
| Release Approver | | | |
