# AudioKnigi Downloader 4.12.31 — Screen-reader all-elements & Tk recursion hardening

## Основание проверки

Реальная Windows-проверка с JAWS/NVDA показала три проблемы:

1. стандартная команда `Insert+Up` могла быть полностью перехвачена скринридером до Tk, поэтому приложение не видело жест и пользователь слышал не введённое значение;
2. список вариантов озвучки не объяснял явно, как открыть/закрыть его и как перемещаться по вариантам;
3. после серии событий фокуса в Help Center был зарегистрирован `RecursionError` внутри `tkinter._substitute`, а попытка обычного форматирования traceback могла повторно переполнить стек.

Лог одновременно подтвердил, что `tk-uia` был включён, поле ввода содержало корректное значение, а выбор narrator-вариантов доходил до accessibility-слоя. Следовательно, требовалось усилить обработку жеста, состояния Combobox и reentrancy focus callbacks, а не менять модель данных редактора.

## Исправления

### 1. Physical Insert+Up observer на Windows

Добавлен `WindowsInsertUpObserver` на базе `WH_KEYBOARD_LL`.

- отслеживает физический `Insert`/Numpad Insert + `Up`/Numpad Up;
- не блокирует и не подменяет команду NVDA/JAWS — всегда передаёт событие дальше через `CallNextHookEx`;
- после стандартной команды скринридера с небольшой задержкой озвучивает через Prism фактическое значение сфокусированного `Entry`, `Combobox` или `Text`;
- работает независимо от раскладки клавиатуры;
- корректно снимает hook при закрытии accessibility manager;
- пишет диагностические события `SCREEN READER GESTURE` и `ACCESSIBILITY KEYBOARD HOOK`.

### 2. Подсказки для всех фокусируемых элементов

`AccessibilityManager._interaction_hint()` теперь автоматически формирует клавиатурную инструкцию по роли элемента:

- Entry — ввод текста и `Insert+Up`;
- Combobox — открыть `Alt+Down`, `F4`, `Enter` или `Space`, выбрать стрелками, подтвердить `Enter`, закрыть `Escape`;
- Button — `Enter`/`Space`;
- Checkbutton / Radiobutton — `Space`;
- Scale — стрелки + `Home`/`End`;
- Treeview — стрелки и `Shift+F10` при наличии контекстных действий;
- Notebook — `Ctrl+Tab` / `Ctrl+Shift+Tab`;
- Text — инструкции чтения или редактирования.

Подсказка автоматически входит в `_describe_widget()`, поэтому распространяется и на динамически добавленные стандартные ttk/Tk controls.

### 3. Narration Combobox

В обоих режимах интерфейса список озвучек теперь явно объясняет управление.

Закрытое состояние сообщает текущее значение и способы открытия. Открытое состояние сообщает количество вариантов и клавиши навигации. При перемещении стрелками приложение дополнительно озвучивает текущий вариант и его позицию в списке. После закрытия произносится выбранный вариант и инструкция повторного открытия.

Keyboard support дополнен `Enter`, `KP Enter`, `Space`, `F4`, `Alt+Down`, `Escape`, `Up/Down` и numpad arrows.

### 4. Защита от reentrant FocusIn

Повторный Windows crash показал, что одного boolean reentrancy guard недостаточно: сам `FocusIn`-callback вызывал `update_idletasks()`, а значит мог запустить вложенный Tk event loop, пока `tkinter._substitute` ещё находился в стеке.

Теперь глобальный focus probe работает как coalescing queue:

- `FocusIn` только сохраняет последний widget в `_pending_focus_widget`;
- одновременно существует не более одного `_focus_probe_after_id`;
- visual focus, auto-registration и диагностическое описание выполняются только на следующем `after(0)` turn;
- новые `FocusIn`, пришедшие во время обработки, не обрабатываются рекурсивно, а планируют следующий turn;
- `_focus_probe_suspended` позволяет аварийному handler полностью остановить focus work без Tcl/Tk-вызовов.

Из `_show_visual_focus()` и `focus_initial_control()` удалён `update_idletasks()`. Рамка фокуса использует фактическую уже размещённую геометрию widget, поэтому не создаёт layout overflow при масштабировании.

`CTkScrollableFrame` также coalesces повторные `FocusIn`: вложенные scrollable ancestors больше не создают по `after_idle()` на каждое событие, а держат один `after(0)` для последнего target.

### 5. Безопасный RecursionError handler

`AudioKnigiApp._tk_exception_handler()` обрабатывает `RecursionError` до обычного `log_exception()` и `build_report()`.

Повторный crash показал, что даже `after_idle()` в аварийной ветке небезопасен: стек уже исчерпан, и любой новый Tcl/Tk-вызов может снова войти в `_report_exception`. Поэтому emergency branch теперь делает **ноль Tcl/Tk-вызовов**. Он только:

- сохраняет короткий `last_crash_report` в Python-памяти;
- ставит `_focus_probe_suspended=True`;
- очищает Python-ссылку на pending focus widget;
- пишет короткую запись logger без форматирования полного traceback.

В этой ветке нет `after`, `after_idle`, `messagebox`, `focus_get`, `update`, `update_idletasks` или UI status update.

## Runtime-инвентаризация всех элементов

Проверен фактический интерфейс через Tk/Xvfb:

| Область | Фокусируемых элементов | Без имени/роли/нужной подсказки |
| --- | ---: | ---: |
| Простой режим | 15 | 0 |
| Расширенный — Книга | 15 | 0 |
| Расширенный — Поиск | 7 | 0 |
| Расширенный — Очередь | 15 | 0 |
| Расширенный — История | 12 | 0 |
| Расширенный — Настройки | 35 | 0 |
| Help Center | 18 | 0 |
| **Всего по снимкам** | **117** | **0** |

Информационные labels не получают управляющую подсказку, поскольку они не являются пользовательским действием; их текст/роль остаются доступными скринридеру.

## Focus stress tests

Повторно переключались темы справки и фокус `topic button -> help text -> topic button` большим числом циклов. Дополнительно новый regression генерирует **1 500 последовательных `FocusIn`** для одного control до обработки event queue. Все события coalesce в один deferred processor; `RecursionError` не воспроизводится.

Отдельные source-level проверки запрещают nested `update()` / `update_idletasks()` в accessibility visual-focus, initial-focus и search-result focus paths и требуют coalesced zero-delay auto-reveal для `CTkScrollableFrame`.

## Regression coverage

Добавлен `tests/test_screenreader_all_elements_recursion_41231.py`.

Он проверяет:

- Windows Insert+Up delivery текущего значения;
- Combobox open/close/navigation callbacks и keyboard contract;
- автоматические usage hints стандартных control roles;
- explicit narrator instructions в Easy/Advanced UI;
- RecursionError emergency handler без полного traceback formatter;
- deferred/coalesced global FocusIn processing;
- 1,500-event FocusIn storm without recursion;
- отсутствие nested Tk event pumps в focus paths;
- coalesced scrollable auto-reveal;
- runtime audit Easy + всех Advanced tabs + Help Center;
- многократное переключение Help Center focus без рекурсии.

После окончательного follow-up полный активный набор: **512/512 passed**.

## Windows manual verification

Автотесты не могут полностью эмулировать внутренние команды реального NVDA/JAWS. После сборки EXE необходимо проверить на Windows:

1. ввести текст в редактор и нажать `Insert+Up`;
2. убедиться, что после стандартной команды скринридера произносится фактическое содержимое поля;
3. перейти на список вариантов озвучки и услышать текущее значение + инструкцию открытия;
4. открыть список `Alt+Down`/`F4`/`Enter`/`Space`;
5. перемещаться `Up/Down` и слышать варианты;
6. подтвердить `Enter`, закрыть `Escape`;
7. интенсивно перемещаться по Help Center и убедиться в отсутствии падения.
