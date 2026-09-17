# Consolidated maintenance audit — 4.12.31

**Дата фиксации:** 2026-09-05  
**Базовая версия приложения:** 4.12.31  
**Назначение:** зафиксировать пост-релизные исправления и проверки, выполненные после первоначального архива 4.12.31.

## 1. Контекстная справка F1

**Проблема:** на вкладке «Книга» F1 открывал тему `download`, хотя в Help Center существует отдельная тема `book`.  
**Исправление:** сопоставление изменено на `"book": "book"`.  
**Основной файл:** `audioknigi/app.py`.  
**Регрессия:** покрыта тестами Help Center 4.12.31.

## 2. Page Up / Page Down в read-only Text

**Проблема:** доступное описание сообщало «по десять строк», тогда как фактическое перемещение выполнялось по пять.  
**Исправление:** описание синхронизировано с реальным шагом в пять строк.  
**Основной файл:** `audioknigi/accessibility.py`.  
**Регрессия:** добавлена проверка соответствия текста подсказки реальному поведению.

## 3. Event Bus и Python 3.14

**Проблема:** `return` внутри `finally` в `audioknigi/event_bus.py` вызывал `SyntaxWarning: 'return' in a 'finally' block` и мог подавлять исключение.  
**Исправление:** логика `finally` перестроена без `return`, при сохранении прежней семантики остановки/reschedule.  
**Основной файл:** `audioknigi/event_bus.py`.  
**Регрессия:** `tests/test_event_bus_build_hardening_41231.py` и существующие Event Bus тесты.

## 4. BAT-файлы сборки и UTF-8 BOM

**Проблема:** CMD видел BOM как часть первой команды и выводил `я╗┐@echo off`.  
**Исправление:** `build_exe.bat` и `build_exe_fixed.bat` сохранены без UTF-8 BOM.  
**Результат:** `@echo off` интерпретируется корректно, лишний вывод команд в консоль устранён.

## 5. Полный аудит тем оформления

Проверены четыре фактических состояния:

- Dark;
- Light;
- System-Dark;
- System-Light.

### Исправлено

- семантические цвета текста/outline отделены от цветов заливки кнопок;
- контраст `primary`, `info`, `success`, `warning`, `danger` приведён к доступным значениям;
- `normal`, `hover`, `pressed`, `disabled` получили визуально различимые состояния;
- скрытые карточки Simple UI больше не остаются тёмными в Light/System-Light;
- системная тема отслеживает изменение светлой/тёмной темы Windows во время работы;
- устранена утечка глобального состояния при разрешении пар `(light, dark)`;
- фокус-кольцо использует жёлтый цвет в тёмной теме и тёмно-синий в светлой, чтобы сохранять контраст.

**Основные файлы:** `audioknigi/ui_kit.py`, `audioknigi/ui/easy_home.py` и связанные UI-модули.  
**Аудит:** `audits/4.12/THEME_AUDIT_4_12_31.md`.  
**Регрессия:** `tests/test_theme_contrast_system_41231.py` и связанные UI/accessibility-тесты.

### Измеренная проверка

Для каждого из четырёх вариантов темы проверялся фактический UI:

- по 211 элементов интерфейса;
- по 60 кнопок с состояниями normal/hover/pressed/disabled;
- обычный текст не имеет найденных состояний с контрастом ниже 4.5:1;
- hover/pressed визуально отличаются от normal.

## 6. Настоящая модальность диалогов

**Проблема:** часть окон вопроса/ошибки могла потерять визуальное владение, уйти за главное окно или позволить пользователю взаимодействовать с главным интерфейсом.  
**Исправление:** все нативные Tk `messagebox` получили явный `parent`; собственные диалоги используют общий механизм `transient + grab` и усиленное владение окном на Windows.

### Инвентаризация

В текущем коде обнаружено **71** вызов `messagebox`, и **0** из них остаются без `parent`.

Распределение:

- `audioknigi/actions.py` — 30;
- `audioknigi/app.py` — 7;
- `audioknigi/downloader.py` — 2;
- `audioknigi/player.py` — 5;
- `audioknigi/queue_manager.py` — 13;
- `audioknigi/search.py` — 1;
- `audioknigi/storage.py` — 12;
- `audioknigi/ui/easy_home.py` — 1.

Собственные вопросные/обязательные окна также переведены на общий modal helper.  
**Регрессия:** `tests/test_modal_ownership_41231.py`.

## 7. Проверка после функциональных исправлений

После исправления тем и модальности полный набор проекта был разбит на части из-за лимита времени среды. Все части завершились успешно. Итоговая зафиксированная проверка: **442/442 теста прошли**.

## 8. Каталогизация репозитория

В рамках последующей уборки:

- все Markdown-аудиты перенесены из корня в `audits/<версия>/`;
- техническая документация перенесена в `docs/<категория>/`;
- в корне оставлены только основные пользовательские/релизные документы и рабочие файлы запуска/сборки;
- добавлены `audits/INDEX.md` и `docs/INDEX.md`;
- ссылки на перемещённые документы обновлены;
- regression-тест архитектуры обновлён на новое расположение release-документации.

## 9. Статус

Состояние после перечисленных исправлений считается базовой обслуженной сборкой 4.12.31. Новые изменения должны сопровождаться отдельным аудитом в `audits/4.12/` либо в каталоге следующей версии.

## 10. Финальная проверка каталогизированного архива

После реорганизации документации добавлены три regression-теста структуры/release-фильтра. Итоговый полный набор: **445/445 тестов прошли**.

Дополнительно:

- `docs/build/` подтверждённо включается в source release;
- корневые generated `build/` и `dist/` по-прежнему исключаются;
- `__pycache__`, `.pytest_cache`, `.pyc`, `.pyo`, virtualenv не попадают в release ZIP;
- локальные Markdown-ссылки проверены: **0** битых ссылок;
- audit Markdown вне `audits/`: **0**.


## Deep concurrency and lifecycle hardening

A later full-project audit found and fixed cross-module operation races, stale search/cover publication, worker/model publication ordering, blocking player FFprobe, cooperative media-process cancellation, shutdown/network lifecycle, history synchronization, strict persistence, fail-safe logging startup, file-dialog ownership and periodic accessibility polling on the Tk thread. The complete implementation and regression evidence are recorded in [`AUDIT_DEEP_HARDENING_4_12_31.md`](AUDIT_DEEP_HARDENING_4_12_31.md). The active suite reached **459/459 passed** after these fixes.
## Screen-reader editor, layout-independent hotkeys and search focus

The final 4.12.31 accessibility follow-up added Windows `tk-uia` UI Automation exposure for the universal book/title/author editor, a Prism-backed `Insert+Up` fallback, physical-VK handling for global `Ctrl+L/D/F/Q/H`, and an explicit NVDA/JAWS announcement after focus moves to search results. Windows PyInstaller builds also collect and frozen-self-test `tk_uia`. Full details are recorded in [`AUDIT_SCREENREADER_EDITOR_HOTKEYS_SEARCH_FOCUS_4_12_31.md`](AUDIT_SCREENREADER_EDITOR_HOTKEYS_SEARCH_FOCUS_4_12_31.md). The active suite reached **470/470 passed** after this follow-up.

## Final accessibility + Cloudflare DNS follow-up

The final follow-up extended the Simple editor accessibility contract to Advanced editable fields, added direct log diagnostics for UIA/Insert+Up/VK hotkeys/search focus, and introduced strict Cloudflare 1.1.1.1 DNS-over-HTTPS routing for public Python hostnames. Playwright/Chromium and remote FFprobe are routed through the application-owned Cloudflare-resolving localhost proxy. Tk root recreation also resets inherited process scaling before child widgets are built. See [`AUDIT_ACCESSIBILITY_CLOUDFLARE_DNS_4_12_31.md`](AUDIT_ACCESSIBILITY_CLOUDFLARE_DNS_4_12_31.md). The active suite reached **485/485 passed**.

