# Changelog

## 4.9.4
- `audioknigi.com.ua`: search labels in the form `Author – Title` are now split into separate **Author** and **Title** columns.
- `knigavuhe.org`: current `.bookitem` cards are parsed structurally, so genre text from the cover cannot replace the real book title.
- `knigavuhe.org`: title, author and reader are read directly from the search card; detail-page hydration remains only as a compatibility fallback.
- Knigavuhe pagination (`?page=2`, `?page=3`, ...) is followed automatically up to the application's 100-result limit (currently up to 10 pages at 10 books/page).
- Pagination pages after the first are loaded concurrently and merged in page order with canonical-URL deduplication.
- Reader-only matches are filtered using card metadata, and multiple recording URLs for the same title/author are collapsed into one logical search result; alternative recordings remain available through the book's **Озвучка** selector.

## 4.9.3
- Knigavuhe search now filters out results matched only by narrator/performer.
- Search results show Author and Reader in separate columns.
- Book-page metadata hydration distinguishes title, author and narrator.
- Knigavuhe book pages expose an accessible «Озвучка» selector when alternative recordings are available.
- Rights-restricted recordings are not bypassed; when Knigavuhe exposes other recordings, the app shows those alternatives instead of a dead end.

## 4.9.2

- Исправлено фактическое отображение названий Knigavuhe в поиске: жанры вроде «Биографии», «Для детей» и «Аудиоспектакли» больше не используются как название книги.
- После получения канонических `/book/.../` URL названия подтверждаются по `<title>` соответствующей страницы книги.
- Страницы книг проверяются параллельно (до 6 запросов), порядок результатов сохраняется; сбой одной страницы не ломает общий поиск.
- Добавлен regression-тест для ситуации со скриншота: `/book/leonid-filatov/` должен отображаться как «Леонид Филатов», а не как жанр.

## 4.9.1

- Исправлен парсер результатов поиска `knigavuhe.org`: жанры и служебные ссылки на комментарии больше не попадают в столбцы названия/URL.
- Ссылки результатов Knigavuhe канонизируются до `https://knigavuhe.org/book/<slug>/` без `#comments_block` и tracking-параметров.
- HTML-парсер карточек использует стек ссылок и корректно отделяет название книги от вложенных ссылок жанров, авторов и исполнителей.
- Добавлены regression-тесты для реальной выдачи Knigavuhe; полный набор: 175 passed.

## 4.9.0
- Добавлен второй источник: knigavuhe.org.
- Общий поиск теперь выполняется по audioknigi.com.ua и knigavuhe.org.
- Поддержан разбор BookController JSON: авторы, чтецы, обложка и плейлист.
- Поддержан резервный merged_playlist для повторной загрузки главы при сбое основного URL.
- Ссылки knigavuhe.org работают в главном поле, очереди, буфере обмена и Drag-and-Drop.
- Ограниченные правообладателем страницы не обходятся и показывают понятное сообщение.


## 4.8.22

- Re-verified that the reported source concatenations / `ui_kit.py` truncation are false positives; the shipped Python modules compile normally.
- Kept the official Prismatoid runtime import from `prism` and added a compatibility fallback to `prismatoid` for repackaged/future distributions.
- Made the accessibility fallback tolerant of CTk wrapper class-name suffixes instead of relying on an exact hard-coded class-name set.
- Hardened the process-wide Tk DPI baseline with a physical-DPI fallback and sanity bounds.
- Fixed scale minimum sizing on small/remote displays: even at 200%, the application no longer requests a minimum window larger than the usable screen.
- Made the legacy `normalize_audio_var` a derived mirror of the canonical `normalization_mode_var`, preventing `off` / `single` / `two_pass` state drift.
- Extended unfinished-download source discovery to `_repair_source*` and common audio container suffixes, and cached per-directory final-file checks to avoid repeated `iterdir()` calls.
- Rewrote the tray notification queue trim as explicit slice assignment while preserving list identity.
- Added `tests/test_audit_4822.py`.

## 4.8.21

- Fact-checked the new audit: no source truncation exists, Prismatoid still correctly imports as `prism`, accessibility polling already cancels its Tk timers, and `single` normalization is implemented by the downloader.
- Added `safe_normalization_mode()` and applied it to app startup, settings capture/save, queue snapshots/restores, resume restoration and FFmpeg processing.
- Added a resilient `_focus_easy_url_entry()` onboarding helper and made `EasyHome` expose the same field on both component and app compatibility surfaces.
- Made scale typography refresh explicitly tolerate an unbuilt `EasyHome`.
- Prevented malformed cover payload objects from collapsing to the same blank cache digest.
- Added a Settings trace registry that remembers the real variable/trace owner across rebuilds and partial legacy metadata loss; removed duplicate folder-template variable setup.
- Canonicalized Tk Canvas scrollregion comparisons through `splitlist()`.
- Hardened recursion-safe destroy wrappers for explicit-owner calls without adding `<Destroy>` bindings; retained the old tooltip destroy helper only for compatibility.
- Made player tick rescheduling explicit and no-op-safe for non-Tk mixin test hosts.
- Added `tests/test_audit_4821.py`.

## 4.8.20

- Verified the reported `context_download_part()` / `CTkTabview.add()` truncations are false positives; the shipped sources compile completely.
- Renamed transfer metrics to `speed_bytes_per_sec` to match the downloader's actual byte-rate semantics while preserving MiB/s display.
- Replaced the hard-coded 16 MiB Range threshold with a persistent `segment_threshold_mb` setting and an Advanced Settings selector (4/8/16/32/64 MiB).
- Made queue startup atomic: duplicate Start / Retry calls cannot launch parallel workers; a generation token prevents stale workers from clearing a newer run state.
- Queue status callbacks now target the stable `QueueItem` object rather than a fragile list index, and final completion counts are read under the queue lock.
- Priority toggling now restores a book to its previous queue position when priority is removed.
- The embedded player now updates the file label to `Сейчас играет: ...` when playback starts from the track tree.
- Closing the first-run wizard now means “skip onboarding” and persists `first_run_complete`, so it does not reappear on the next launch.
- Cover-cache hashing now handles objects exposing `tobytes()` and generic payloads instead of silently collapsing to an empty digest.
- `CTkTextbox` copy/cut checks for a real selection before touching `sel.first/sel.last`.
- Replaced tab-level `<Destroy>` event bindings with deterministic `destroy()` lifecycle wrappers. This preserves tooltip/trace cleanup while fixing a reproduced Tk/Python recursion failure during complete widget-tree teardown.
- Added `tests/test_audit_4820.py` and updated lifecycle regressions.

## 4.8.19

- Verified the reported `ActionsMixin`/`app.py`/`SearchMixin` EOF findings are truncated-source false positives; the package compiles successfully.
- Verified `_update_bandwidth_label()`, `AudioKnigiApp.t()`, `_player_position_key()`, `_player_select_current()`, and `_strip_ctk_kwargs()` exist in the composed application.
- Accessibility polling now tracks all Tk `after()` IDs and cancels them during shutdown before the root is destroyed.
- Main, History, and EasyHome now explicitly dispose tooltip resources on container teardown; EasyHome also cancels its pending responsive-layout callback.
- History double-click now requires a concrete row under the pointer and selects that row before opening its folder.
- EasyHome application-owned status variables now use the shared `ensure_app_string_var()` lifecycle helper.
- Settings rebuilds first dispose old traces/autosave timers, secret fields use portable `*` masking, and hotkey wraplength is updated only after meaningful width changes.
- Queue drag clamps above the first row and below the last row instead of dropping the visual target.
- The tray option is visibly disabled when the current platform/backend cannot support tray mode.
- Search relevance now prefers the shorter label when phrase/token relevance is otherwise equal, while parser cleanup removes artificial spaces before punctuation.
- Added `tests/test_audit_4819.py`; 132 pytest tests pass in the main isolated run, the two historically Tcl-pollution-sensitive tests pass separately, and all 27 script-style smoke/audit modules pass in fresh processes.

## 4.8.18

- Verified the reported `ActionsMixin` and `SearchMixin` EOF/SyntaxError findings are truncated-source false positives; both modules compile completely.
- Added `ActionsMixin._tr()` fallback and localized duplicate-book choice hints in RU/UK/DE/EN.
- Added warnings for i18n format-parameter mistakes while preserving non-fatal UI behavior.
- Added deep history validation/sanitization and validate-before-write backup restore semantics.
- Prevented empty history folders from accidentally adopting a `cover.jpg` from the process working directory.
- Queued tray notifications while a native icon generation is starting/restarting.
- Explicitly disposed Settings tooltips at tab teardown and centralized guarded immediate saves for dropdown settings.
- UI scale selection now applies immediately while keeping the Apply button as an explicit fallback.
- Removed the native-Tk width conversion cliff at 15/16 and made Linux edit shortcuts prefer logical keysyms before Cyrillic/physical fallbacks.
- Simplified search tokenization and history-cover cache identity work; moved `LANGUAGES` to a normal module import.
- Added `tests/test_audit_4818.py`; 131/131 collected pytest tests plus 27 script-style smoke modules pass in fresh Tk/Xvfb processes.

## 4.8.17

- Centralized application-owned `StringVar` lifecycle handling in `ui_kit.ensure_app_string_var()` and reused it from Settings, Queue, and Search tabs.
- The shared helper validates stale Tcl variables, prefers the application interpreter, falls back safely in lightweight tests, and never silently returns `None`.
- Removed duplicate per-tab variable bootstrap logic and dead `_existing_*_var` locals.
- Re-verified that Settings hotkey help already resizes on `<Configure>`, Queue/Search already dispose tooltips on `<Destroy>`, and queue row DnD handlers are bound without additive duplication.
- Made simple-mode quality-card descriptions wrap to their live card width, fixing a pre-existing 200% DPI squeeze detected by the full UI regression suite.
- 120 tests pass across fresh Tk/Xvfb groups.

## 4.8.16

- Verified the reported `ActionsMixin`/`ui_kit.py` source truncations are false positives; the shipped files compile completely and `AudioKnigiApp.t()` exists.
- Kept the correct Prismatoid runtime import `from prism import ...`; current upstream packaging builds the Python wheel from `bindings/py/prism/prism`.
- Added an SDL/pygame startup grace window so a transient `get_busy() == False` immediately after play/unpause/seek cannot falsely stop the embedded player.
- Made lazy queue-lock creation race-safe for standalone mixin hosts and gave queue runtime snapshots safe defaults when partial hosts omit runtime attributes.
- Added native support for CustomTkinter-style `(light_color, dark_color)` pairs throughout theme color resolution.
- Preserved an explicit year value of `0` in template substitution instead of treating it as empty.
- Normalized Linux wheel scrolling to one unit per wheel notch, matching Windows behavior.
- Hardened Queue/Search tab StringVar reuse against stale Tcl variables, removed additive duplicate drag bindings, and added explicit tooltip cleanup for tab rebuilds.
- Added explicit `Tooltip.dispose()` without reintroducing per-widget `<Destroy>` callbacks that previously caused Python 3.14/Tk recursion.
- Made the Settings hotkey-help wrap length responsive to the actual scrollable-page width instead of a fixed 980 px.
- Added 4.8.16 regression coverage; all 117 collected tests pass when Tk-heavy groups run in fresh Xvfb/Tcl processes.

## 4.8.15

- Verified `actions.py`, `app.py`, and `ui_kit.py` are complete and compile; the reported EOF/SyntaxError findings were truncated-source false positives.
- Kept the correct Prismatoid runtime import `from prism import ...`; upstream packages the Python binding from `bindings/py/prism/prism`.
- Restored `runtime_output_mode` after isolated context-menu MP3 downloads so M4B/Both settings do not leak across operations.
- Made completion UI tolerant of easy-mode widgets being absent during rebuild/teardown.
- Seeking while paused now reloads at the requested offset and re-pauses the decoder, keeping audio and UI position synchronized.
- M4B/M4A/AAC are opened by the system player instead of being passed to SDL_mixer/pygame.
- Localized the first-run M4B switch for RU/UK/DE/EN.
- Hardened unfinished-download indicator updates against UI teardown.
- Added `CTkOptionMenu.configure(variable=...)`, `CTkSwitch.select/deselect/toggle`, `CTkProgressBar.get`, `CTkTabview.delete`, and `CTkScrollableFrame` geometry-info proxies.
- Expanded ignored CustomTkinter-only compatibility arguments.
- Removed the recurring 500 ms descendant scan from scrollable frames; newly created CTk-compatible children notify their nearest scrollable ancestor instead.
- Smoothed macOS small-delta trackpad scrolling and prevented Command-key shortcuts from polluting the custom Entry undo stack.
- Tooltips now hide on Unmap and refuse to show for unmapped/destroyed owners without reintroducing the old Destroy-recursion bug.
- `set_button_active()` now restores a button's original inactive style instead of always forcing the default style.
- Added 4.8.15 regression coverage; full suite: 104 passed.

## 4.8.14
- Подтверждено, что `AudioKnigiApp.t()` существует, `app.py` и `ui_kit.py` не оборваны, а `apply_tree_zebra()` присутствует; сообщения о соответствующих `SyntaxError`/`AttributeError` не относятся к фактической 4.8.13.
- `_save_settings()` и runtime-снимок параметров устойчивы к пустым, дробным и повреждённым числовым Tk-значениям; `on_bandwidth_slider()` не падает, если `DoubleVar.get()` временно выдаёт `TclError`.
- Исправлена семантика `tk scaling`: пользовательский процент умножается на исходный DPI Tk, а исходный DPI фиксируется один раз на процесс, поэтому повторное создание окна не накапливает масштаб. Заголовок и простой dashboard дополнительно адаптируются на 150–200%.
- `ScreenReaderBridge` синхронизирует `backend/context` через `RLock`; обычные `tk.Entry`, `tk.Scale`, `tk.Checkbutton` и `tk.Radiobutton` теперь отдают значение/состояние, а нативная регистрация Tk 9.1 умеет находить путь внутри wrapper-виджетов.
- Буфер обмена и действия с последней папкой используют безопасные `getattr`; формат номера части устойчив к строковым индексам.
- Resume-манифест принимает `selected_indices=None`; история принимает произвольные `Mapping`; очередь безопасно создаёт запись даже при частично построенном UI.
- Шаблоны понимают строковый индекс трека и не удваивают целевое расширение; `sanitize_log_text()` сохраняет `0` и `False`.
- Мини-плеер не планирует следующий `after()` после уничтожения окна, не перетягивает ползунок во время ручной перемотки и использует позиционные аргументы `pygame.mixer.music.play()` для более широкой совместимости.
- `plyer>=2.1.0` добавлен в зависимости для уведомлений Linux/macOS; threaded pystray отключён на macOS, где Cocoa требует главный поток.
- `CTkTabview.set()` безопасно игнорирует неизвестную вкладку; cleanup `SettingsTab` принимает и Python-widget, и Tcl-path события уничтожения.
- Подтверждено по официальному исходному дереву Prismatoid: Python-модуль называется `prism`, поэтому импорт `from prism import BackendId, Context` оставлен без изменения.
- Добавлен `tests/test_audit_4814.py`; полный набор проходит 89 тестов.

## 4.8.13
- Добавлено отложенное автосохранение текстовых настроек: шаблон папки, шаблон имени трека, URL/API key/Library ID Audiobookshelf сохраняются примерно через 450 мс после окончания ввода.
- `_ensure_string_var()` больше не возвращает `None` при ошибке создания Tk-переменной: используется root-интерпретатор приложения, затем безопасный fallback на frame; при полном сбое выдаётся явная ошибка вместо тихой потери `textvariable`.
- Friendly-переменные `SettingsTab.speed_var` и `output_friendly_var` создаются на Tcl-интерпретаторе корневого приложения, сохраняя локальную область владения вкладки.
- Плашка очереди «Перетащи сюда…» получила явное accessibility-имя/описание и tooltip. Подтверждено тестом, что централизованный `DragDropMixin` регистрирует её через `drop_target_register()` и `<<Drop>>` после построения всех вкладок.
- Двойной щелчок в результатах поиска теперь сначала определяет строку под курсором, делает её активным выделением и только затем открывает книгу; пустая область/заголовок остаются no-op.
- Подтверждено: штатное закрытие и раньше вызывало `_save_settings()`, `use_selected_search_result()` уже был защищён от пустого выделения, а DnD-плашка очереди уже была реальной целью через централизованную регистрацию.
- Добавлен `tests/test_audit_4813.py`; 70 регрессионных тестов проходят в изолированных Tk/Xvfb-группах.

## 4.8.12
- Fixed late accessibility naming so widgets auto-scanned by `_walk()` still update Tk 9.1+ native accessible names when an explicit semantic label is registered later.
- Removed the synchronous tray-thread `join()` from `TrayManager.hide()`; backend retirement and waiting now stay off the Tk UI thread.
- Hardened history insertion to accept both typed `Book` models and mapping/dict records without `AttributeError`.
- Normalized Tk's `widget.configure({...})` dictionary form before filtering legacy CTk aliases in Frame/Label/Button/Entry/Textbox/AccessibleLabel and related controls.
- Added Linux X11/XKB physical keycode handling for Ctrl+A/C/V/X/Y/Z so edit shortcuts continue to work under Cyrillic layouts, with keysym fallback for unusual backends.
- Improved `_parent_bg()` for ttk parents such as `Notebook` by resolving the active ttk style background instead of falling back to a hard-coded surface color.
- Removed the unused `_theme_background(..., fallback_panel=...)` parameter.
- Added audit/regression coverage for the reported 4.8.11 findings.

## 4.8.11
- Усилена потокобезопасность обновления столбцов `Начало / Конец / Длительность`: `_refresh_book_timing_ui()` теперь сам определяет поток и отправляет любые операции `Treeview` в главный Tk-поток через event bus.
- Обработчик автоподстановки ссылки использует безопасный `getattr(..., None)` для `_clipboard_offer_after` поверх существующей ранней инициализации атрибута.
- `continue_unfinished()` больше не предполагает, что все Tk-переменные и вкладки уже созданы: значения восстановления задаются best-effort через безопасный setter, а частично построенный UI не падает с `AttributeError`/`TclError`.
- При восстановлении нескольких книг `resume_selected_indices` явно очищается, чтобы выбранные части предыдущего одиночного восстановления не могли повлиять на последующий ручной анализ.
- Переключение на вкладки при восстановлении использует логический селектор с безопасным fallback, совместимый с будущей локализацией названий вкладок.
- Повторно подтверждено регрессионным тестом: `_main_download_worker()` в 4.8.10 уже имел `except Exception` и `finally`, поэтому при сетевой/дисковой ошибке `busy` гарантированно сбрасывается.
- Повторно подтверждено: `ui_kit.py` полностью компилируется; сообщения об оборванных методах `AccessibleLabel` относятся не к содержимому релизного архива 4.8.10.

## 4.8.10
- Исправлена нативная регистрация Drag-and-Drop для обычного `tk.Tk`: после `TkinterDnD.require()` методы `drop_target_register`, `drop_target_unregister` и `dnd_bind` теперь подключаются из `DnDWrapper` к обычным Tk/ttk-виджетам. Ошибка `'_tkinter.tkapp' object has no attribute 'drop_target_register'` больше не должна возникать при установленном `tkinterdnd2`.
- Если ни одну DnD-цель зарегистрировать не удалось, интерфейс честно помечает Drag-and-Drop недоступным и пишет одну понятную диагностическую строку вместо повторяющихся ошибок по каждому элементу.
- Очередь защищена от рассинхронизированных Treeview iid: перемещение вверх/вниз, приоритет и пауза книги проверяют индекс внутри блокировки перед обращением к `queue_items`.
- `MappingDataclass` получил явный `__slots__ = ()`; `Track`, `Book` и `QueueItem` с `@dataclass(slots=True)` больше не наследуют ненужный `__dict__`.
- Восстановление нескольких незавершённых книг нормализует `selected_indices` в уникальный список целых индексов; некорректные значения из JSON отбрасываются.
- Сравнение директорий незавершённых загрузок на Windows нормализует регистр и разделители, чтобы `C:\...` и `c:\...` не создавали ложные orphan-файлы.
- Fallback `StringVar` вкладки настроек принадлежит главному приложению/Tcl-интерпретатору; существующая переменная дополнительно проверяется вызовом `get()` перед повторным использованием.
- `CTkScrollableFrame` больше не перехватывает колесо мыши у вложенных `Text`, `Treeview`, `Listbox` и `Canvas`; обычные дочерние элементы по-прежнему прокручивают внешнюю страницу.
- `set_appearance_mode()` сразу обновляет внутреннее состояние палитры `_CURRENT_DARK`, поэтому новые окна/подсказки получают правильную тему ещё до следующего полного style-refresh.
- Конвертация исторических pixel-width принимает дробные строки вида `"120.5"` через `int(float(...))`; `CTkOptionMenu` также безопасно обрабатывает такую ширину.
- Горячие клавиши вкладок используют логические ключи `book/search/queue/history/settings`, а не напрямую видимые русские подписи, что готовит переключение вкладок к локализации.
- Быстрый `tray hide() -> show()` больше не теряет запрос показа: повторное создание значка откладывается до полного завершения предыдущего native loop, без запуска двух `pystray.Icon` одновременно.
- Убрано лишнее двойное присваивание подписи файла при восстановлении позиции мини-плеера.
- `PhotoImage` обложек и фирменных изображений теперь создаются с явным `master=self`, что предотвращает привязку к уже уничтоженному Tcl-интерпретатору при пересоздании приложения/тестах.
- Повторно подтверждено: `_clipboard_offer_after`, `_last_clipboard_offer`, `last_completed_folder` и `speed_history` инициализируются до использования; ID3-ошибки уже логируются; `_analysis_worker` использует runtime-снимок каталога/формата вместо чтения Tk variables из worker-потока; `ui_kit.py` не оборван и компилируется полностью.

## 4.8.9
- Исправлен PowerShell WinRT fallback системных уведомлений: `XmlDocument` теперь создаётся с правильным namespace `Windows.Data.Xml.Dom`, а неудачный PowerShell-вызов больше не считается успешным уведомлением.
- Мини-плеер теперь отключает «Пауза» и «Стоп», когда воспроизведение остановлено или естественно завершено; кнопки снова активируются только после запуска аудио.
- `LibraryVisualMixin._payload_key` корректно хэширует как bytes-like данные, так и строки UTF-8.
- Счётчик шагов первого запуска переведён в i18n для RU/UK/DE/EN.
- `MappingDataclass` приведён к `MutableMapping`, соответствуя реализованному `__setitem__`.
- Неизвестные теги пользовательских шаблонов сохраняются как текст; слэши внутри автора/названия очищаются до подстановки и больше не создают неожиданные подпапки.
- Проверка незавершённых загрузок учитывает готовые M4A/M4B/AAC/FLAC/OGG/OPUS/WAV, а восстановление нескольких книг переносит настройки шаблонов в очередь и реально применяет их при обработке.
- История устойчиво обрабатывает нечисловые Treeview iid и некорректное/пустое количество частей.
- `CTkOptionMenu.configure(command=...)` теперь безопасно заменяет callback без `TclError`; `CTkSwitch.configure(variable=...)` обновляет внутреннюю переменную.
- `CTkScrollableFrame` автоматически подключает колесо мыши и фокус к дочерним элементам, добавленным после создания страницы.
- Системный трей не создаёт второй `pystray.Icon`, пока предыдущий экземпляр ещё завершает native loop.
- Вкладка «Поиск» сохраняет ссылку `search_query_entry` и реагирует на двойной щелчок только по ячейкам результатов, не по заголовкам/разделителям.
- Тонкие настройки соединений автоматически сохраняются; выбор friendly-пресета «Максимальная» больше не превращает вручную выбранные 2/4 потока в 8.
- Drag-and-Drop очереди начинается только с ячейки строки, клики по заголовкам больше не считаются перетаскиванием.

## 4.8.8
- Полностью проверен расширенный интерфейс на вкладках «Книга», «Поиск», «Очередь», «История» и «Настройки».
- На вкладке «Поиск» добавлена видимая подпись «Результаты поиска», имена полос прокрутки и подсказки; нижняя кнопка открытия книги теперь всегда резервирует место.
- На вкладке «Книга» кнопка «Проверить файлы» переименована в «Проверить скачанные файлы» и получила точное пояснение: проверяет наличие, целостность и длительность локальных MP3, ничего не скачивает.
- Общая шкала этапов и шкала текущей операции теперь явно различены, имеют accessibility-имена и видимый процент текущей операции.
- Мини-плеер перестроен так, чтобы длинное имя файла не вытесняло транспортные кнопки; «Воспроизвести», «Пауза/Продолжить» и «Стоп» всегда доступны.
- Правая колонка управления на вкладке «Книга» стала независимо прокручиваемой, поэтому при небольшой высоте окна список частей остаётся рабочим, а все элементы управления остаются достижимыми.
- На вкладке «История» добавлены «Создать резервную копию» и «Восстановить копию» рядом с действиями библиотеки; нижняя панель больше не вытесняется таблицей.
- Вкладка «Очередь» получила устойчивую двухрядную панель управления; кнопки больше не сжимаются на 175–200% масштабе.
- Основные элементы расширенного интерфейса получили всплывающие подсказки и accessibility-имена; добавлено имя ползунку ограничения скорости.
- Геометрический аудит 1080×760 в тёмной и светлой теме на 100/125/150/175/200%: 0 выходов за границы и 0 обрезанных текстовых элементов.
- Сохранены исправления Python 3.14 RecursionError из 4.8.7 и временных столбцов из 4.8.6.

## 4.8.7
- Найдена и устранена воспроизводимая причина `RecursionError`: обработчики `<Destroy>` у всплывающих подсказок больше не вызывают Tk-команды во время массового уничтожения дерева интерфейса.
- Исправлена рекурсия Tkinter на Python 3.14.3 при вложенной обработке Configure/Focus/Map событий.
- Убраны `update_idletasks()` из обработчиков масштаба, адаптивной разметки и буфера обмена.
- Адаптивная разметка получила debounce, защиту от повторного входа и гистерезис.
- Усилена защита `<Configure>` у прокручиваемого контейнера.
- Обработчик `RecursionError` больше не открывает вложенный modal messagebox.
- Сохранены исправления столбцов времени из 4.8.6.

## 4.8.6

- Fixed `Начало`, `Конец`, and `Длительность` staying as `—` when a PlayerJS playlist supplies one MP3 per chapter without source `start`/`end` coordinates.
- Playlist timing parser now accepts numeric seconds plus `MM:SS` / `HH:MM:SS` strings from `duration`, `length`, or `time` fields.
- Existing downloaded MP3 files now contribute their measured `actual_duration` to the visible chapter timeline and total book duration without overwriting FFmpeg source-cut coordinates.
- Missing durations for unique remote chapter files are resolved best-effort through `ffprobe`; failures remain non-fatal.
- Timing/status cells refresh while verified chapters become available during a download.
- M4B preview, M4B chapter metadata, sidecars, disk estimates, and the simple completion card now use the best known duration instead of treating unknown playlist duration as zero.
- Added regression coverage for playlist clock parsing, local measured-duration fallback, safe remote probing, live Treeview refresh, and cumulative chapter timing.

## 4.8.5

- Added Ctrl+Z undo and Ctrl+Y / Ctrl+Shift+Z redo to native Entry/Text editing without reintroducing the Python 3.14 recursive Tk event bindings; Windows virtual-key handling keeps these shortcuts working on Russian/Ukrainian layouts.
- Fixed Help and other child windows opening with a platform-white background in dark mode. `CTkToplevel` now applies the active theme before its first paint and follows live theme changes.
- Themed context menus and visual tooltips, and moved the M4B preview to the same themed top-level window class.
- Reworked the simple dashboard for narrow/high-scale layouts: the page is vertically scrollable and automatically stacks the sidebar below the main content at 175–200% or whenever horizontal room is insufficient.
- Re-audited simple + advanced UI at 100/125/150/175/200%: no visible child overflows or squeezed text controls were detected in the automated geometry audit.
- Added regression tests for Help dark/light surfaces, Ctrl+Z/Ctrl+Y, responsive simple-layout clipping, and current ttk field/table colors.

## 4.8.4

- Fixed the Python 3.14/Tkinter `RecursionError` introduced by overlapping clipboard key bindings; text fields now use one non-recursive physical-key handler for Ctrl+A/C/V/X plus the standard Insert shortcuts.
- Added a Windows virtual-key fallback so Ctrl+C/Ctrl+V/Ctrl+X/Ctrl+A keep working with Russian and Ukrainian keyboard layouts without generating replacement Tk events.
- Hardened the Tk callback exception handler so a recursion failure cannot recursively crash the crash-report builder and hide the original error.
- Reworked legacy CustomTkinter pixel-width conversion, including small 24–28 px values that native Tk had interpreted as 24–28 text columns and that squeezed neighbouring controls.
- Removed fixed legacy button widths and let native ttk buttons size to their captions; widened accessibility layouts at 150–200% when screen space permits and made the header mode switcher reserve its width first.
- Refreshed native Tk fonts after UI-scale changes, eliminating stale requested sizes that caused text to be clipped after changing scaling.
- Completed live dark/light theme propagation for native Frame, Label, Entry, Text, Canvas, Treeview, combobox and scrollbar surfaces; changing theme no longer leaves black islands on a light background.
- Added regression checks for clipboard handling, small-width conversion, live theme switching, layout sizing and launch stability.

## 4.8.3

- Restored conventional keyboard editing in every native text field: Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A, Ctrl+Insert and Shift+Insert; added a Windows virtual-key fallback for Russian/Ukrainian keyboard layouts.
- Removed the main URL field's special Ctrl+V interception, so keyboard paste edits the field normally instead of invoking the dedicated “ВСТАВИТЬ” workflow.
- Fixed the native ttk compatibility layer so historical pixel widths are converted correctly for accessible labels; settings labels no longer become hundreds of characters wide and push adjacent controls off-screen.
- Made button widths text-safe so long Russian captions are never truncated by a too-small legacy pixel width.
- Made combobox widths large enough for their longest displayed option.
- Added horizontal and vertical scrollbars to Search, Queue and History tables.
- Split the crowded Queue action strip into two rows so controls remain visible at the minimum supported window width.
- Added regression coverage for clipboard shortcuts, text-safe sizing and the minimum-width interface layout.

## 4.8.2

- Replaced the obsolete DLE-style `index.php?do=search&subaction=search&story=...` request with the website's current `GET /search?text=...` contract.
- Added query-aware filtering so unrelated `/audio-*` links from popular/recommended/sidebar blocks are not returned as search hits.
- Search accepts author surnames and multi-word author/title queries; matching is case-insensitive, `ё/е` tolerant, and word-order tolerant for multi-word queries.
- Added a tolerant HTML parser that reads visible link text, `title`/`aria-label`, and image `alt`, merges duplicate links for the same book, and strips descriptive `Слушать онлайн аудиокниги ...` prefixes.
- Search minimum length is now 3 characters, matching the site's `minlength=3` form.
- Added screen-reader-friendly search guidance and `tests/test_search_accuracy_482.py`.

## 4.8.1

- Verified that the shipped 4.8.0 `app.py` and `easy_home.py` are complete and compile; reported truncations were artifacts of clipped source excerpts.
- Verified `AudioKnigiApp.t()` exists and `on_bandwidth_slider(self, _value=None)` accepts the value passed by native ttk Scale widgets.
- Replaced the leftover CustomTkinter-style focus-border fallback in `EasyHome._keyboardize()` with pure native ttk focus behavior.
- Preserved `placeholder_text` as semantic metadata without ever injecting it into the Entry/StringVar value.
- Added persistent visible “Пример: …” helper text for the book URL and Audiobookshelf server fields; JAWS/NVDA descriptions can announce the same example.
- Restored scrolling for the long Settings page with a passive Canvas viewport while keeping every interactive child a real Tk/ttk control; keyboard focus automatically scrolls the focused setting into view.
- Added `tests/test_audit_481.py` for source completeness, translation helper, slider callback, placeholder semantics, native focus behavior and scroll/focus-follow behavior.

## 4.8.0

- Replaced the runtime CustomTkinter widget layer with native Tk/ttk controls and visual containers; the historical `CTk*` compatibility names now resolve to standard Tk/ttk widgets rather than Canvas-based controls.
- Added `ttkbootstrap>=2.2.0,<3` as the modern theme engine and updated PyInstaller collection accordingly; the app falls back to native `clam` styling if the package cannot be imported.
- Introduced a compact Windows-style palette with WCAG-AA text contrast, Segoe UI typography, larger control padding and visible focus rings.
- Modernized Treeview density and headings, added alternating row backgrounds to book parts, search, queue and library, and retained textual status labels so state is never conveyed by color alone.
- Kept every actionable button text-named; icons remain supplemental rather than icon-only controls.
- Programmatic tab changes now move focus into the first logical native control in the selected tab.
- Native PhotoImage/Pillow rendering now handles brand/cover images without relying on CustomTkinter image objects.
- Added `tests/test_modern_accessible_ui.py` to enforce the no-CustomTkinter runtime, native interactive controls, core contrast ratios, text-named buttons and Treeview density/zebra rules.

## 4.7.10

- Hardened `SettingsTab` against partial initialization: `segment_count_var` and `output_mode_var` are repaired with safe `StringVar` fallbacks when missing.
- `_speed_changed()` now tolerates a missing settings persistence callback instead of raising `AttributeError`.
- Settings traces now have an explicit lifecycle: old traces are removed on rebuild and current traces are detached when the settings frame is destroyed.
- Added regression coverage for complete `app.py`, `AudioKnigiApp.t()`, settings trace cleanup, and partial settings hosts.
- Confirmed that the reported truncated `app.py` and missing `self.t()` were artifacts of incomplete source excerpts, not defects in the shipped 4.7.9 ZIP.

## 4.7.9

- Fixed the auto-download analysis-to-download handoff so the UI remains busy until the queued download or duplicate dialog takes ownership.
- Auto-analysis failures now always release the busy state, even when automatic download was requested.
- Duplicate-book dialog explicitly releases busy state on Open/Cancel and transfers it only when a download worker actually starts.
- `download_selected()` now returns a boolean start result so handoff code can safely resolve failed preflight/no-selection cases.
- Mode-button highlighting now uses an adaptive helper that supports current native `ttk.Button` wrappers and future real CustomTkinter buttons.
- `_book_outputs_complete()` no longer evaluates a Tk `StringVar` from a worker thread through an eager `getattr` default.
- Added `tests/test_audit_479.py` and included it in CI/release workflows.

# Changelog

## 4.9.3
- Knigavuhe search now filters out results matched only by narrator/performer.
- Search results show Author and Reader in separate columns.
- Book-page metadata hydration distinguishes title, author and narrator.
- Knigavuhe book pages expose an accessible «Озвучка» selector when alternative recordings are available.
- Rights-restricted recordings are not bypassed; when Knigavuhe exposes other recordings, the app shows those alternatives instead of a dead end.
## 4.7.8

- Verified the reported `core.py` truncation is not present in the shipped ZIP; the module compiles. Tightened bundled-tool probing from `exists()` to `is_file()` so a same-named directory cannot be treated as FFmpeg/FFprobe.
- Confirmed the 4.7.6+ `CTkButton` compatibility class is intentionally a native `ttk.Button`, so `style=` on the Simple/Advanced buttons is valid.
- Added a future-proof CustomTkinter interactive-class fallback to the accessibility manager while keeping the current universal UI natively ttk.
- Decoupled track Treeview row IDs from `Track.index`; zero-based, sparse or duplicated source indices can no longer select/toggle the wrong list element.
- Player position saving now self-initializes `player_positions` for alternate/minimal host objects instead of assuming the main app constructor already did so.
- Individual queue pause now remembers and restores the prior status, including `Ожидает повтор`.
- Resume manifests safely accept `selected_indices: null` and ignore malformed individual index values.
- History rows without covers omit the Treeview `image` option instead of passing an empty image name.
- `_safe_track_index()` now accepts a direct integer track index.
- Native EasyHome controls receive `accessible_name` before the native-keyboard early return.
- Friendly output settings tolerate partial/minimal app initialization where `output_mode_var` or `_save_settings` is not yet available.
- Added `tests/test_audit_478.py` and wired it into CI/release workflows.

## 4.7.7

- Verified that `app.py` is complete and `AudioKnigiApp.t()` exists; the reported truncation/missing-method issues came from incomplete snippets, not the shipped ZIP.
- Replaced `dataclasses.asdict()` in model serialization with a field-wise safe serializer that never deep-copies Tk/PIL/native image objects from `cover_cache`.
- Explicitly handles empty cover payloads without exception-driven control flow.
- PowerShell toast fallback now constructs `XmlDocument` and `ToastNotification` directly through WinRT type literals. User text remains Base64 data and never executable PowerShell.
- Privacy log sanitizer masks both `C:\Users\Name` and `C:/Users/Name` forms of the home path.
- Interrupted queue restore now uses typed `QueueItem.url` access and synchronizes the legacy normalization BooleanVar.
- Friendly MP3/M4B selector now follows `output_mode_var` changes caused by restore/profile/runtime code.
- Speed label is safe even during partial/minimal UI initialization.
- Language callback accepts either a language code or its display name.
- Accessibility label discovery now recognizes CTkLabel-like visual labels as well as native Tk/ttk labels.
- Added `tests/test_audit_477.py` and wired it into CI/release workflows.

## 4.7.6

- Made accessibility inherent to the single interface: there is no screen-reader-mode setting or alternate UI.
- Interactive controls are always native Tk/ttk widgets even when CustomTkinter is installed; CustomTkinter remains visual-only for cards, covers and layout.
- Replaced clickable-only quality cards with real native radio buttons while preserving the visual card design and mouse-wide click target.
- Added automatic Windows NVDA/JAWS direct-output integration through Prismatoid; it only acquires NVDA/JAWS backends and never falls back to SAPI/TTS.
- Re-detects a reader started/restarted after the app, without restart or user configuration.
- Added semantic focus descriptions, checkbox/radio state, tree-row position, notebook tab selection and restrained live status announcements.
- Progress speech is throttled to 10% milestones to avoid repetitive output.
- Added runtime support for Tk 9.1 `tk accessible` when present while remaining compatible with CPython 3.14's bundled Tk 8.6.
- Added `ACCESSIBILITY.md` and `tests/test_accessibility.py`; CI/release jobs now enforce the universal-accessibility contract.

## 4.7.5

- Normalize missing book titles to `audiobook` before full-MP3/M4B filenames and Mutagen tags.
- Explicitly handle empty tuple cover payloads.
- Publish completed search-result lists on the UI thread instead of incrementally mutating shared state in the worker.
- Explicitly activate Windows Runtime toast types in the PowerShell fallback while keeping user content Base64-transported.
- Track the last valid player position so natural end-of-track clears resume state even when pygame immediately returns `-1`; unexpected early stops preserve resume state.
- Guarantee a non-empty `audiobook` fallback folder for templates.

## 4.7.4

- Made keyboard focus decoration exception-safe for dynamic CustomTkinter cards.
- Kept friendly speed presets synchronized with the advanced segment-count control and made queue/search Tk variables persistent across tab rebuilds.
- Standardized Treeview `show` values and made the track context-menu master explicit.
- Ignored child `<Unmap>` events so tab/layout changes cannot accidentally trigger tray minimization.
- Hardened metadata parsing for `html=None`; retained the verified source-mode resource path and disk helper.
- Normalized Audiobookshelf URLs without a scheme and kept the long 120-second scan timeout.
- Removed PowerShell interpolation of notification text by transporting escaped toast XML as Base64.
- Restricted MappingDataclass mapping keys to declared dataclass fields only.
- Closing the first-run wizard no longer marks setup complete.
- Made player-position lock creation, snapshots and mutations thread-safe while retaining asynchronous disk writes and synchronous shutdown flush.
- Hardened logging home-path masking and corrupted numeric setting recovery.
- Preserved a track title of `0`, hardened folder-template edge cases, fallback widget option translation, Tooltip teardown and late tray-stop behavior.
- Added `tests/test_audit_474.py` and wired it into CI/release workflows.

## 4.7.3

- Removed Book/Track/QueueItem `.get()` and subscript access from the typed runtime path; compatibility mapping access remains only for legacy callers.
- `MappingDataclass` now advertises read-only `Mapping` semantics instead of `MutableMapping`; field deletion raises `TypeError` instead of silently assigning `None`.
- Added regression coverage proving the shipped `dnd.py` is complete/compilable and HTTP session rotation survives `session.close()` failures.
- Fixed empty/directory cover paths so Pillow is never asked to open `Path("")` / a directory.
- Windows PowerShell notification fallback now uses hidden/no-window process flags.
- Increased the default Audiobookshelf library-scan timeout from 20s to 120s.
- Added queue-state `RLock`, typed QueueItem access, per-book runtime snapshots and a structural run snapshot to prevent UI/worker state races.
- Moved periodic player-position JSON writes off the Tk main thread into a single coalescing background writer; shutdown performs a synchronized final flush.
- Fixed template expansion so braces inside real book/author/track data (for example `{Remix}`) are preserved.
- Hardened template input handling for `None`/non-mapping tracks and books, and only treats extensions literally present in the template as format directives.
- Hardened tray icon creation for older Pillow versions and made each tray generation use private start/stop events so a slow old backend cannot poison a later `show()`.
- Improved ttk fallback compatibility: `CTkSwitch.get()`, CTkFrame height preservation, and owner-only tooltip `<Destroy>` handling.
- Added `tests/test_hardening.py` and wired it into CI/release workflows.

## 4.7.2

- Standardized Book/Track use in the application core on typed dataclass attribute access; legacy mapping access remains compatibility-only.
- Fixed disk-space preflight for not-yet-created target folders by checking the nearest existing parent; unknown free space no longer silently bypasses the check.
- Fixed ttk Treeview colors in `system` appearance mode by using CustomTkinter's effective Light/Dark mode.
- Made JSON persistence thread-safe and atomic with a process-wide `RLock` plus `os.replace()`.
- Disabled speed-graph spline smoothing until at least three data points exist.
- Blocked queue deletion/clearing while the queue worker is active and fixed DnD insertion-slot calculations for top-to-bottom moves.
- Kept strict slotted dataclasses intentionally; no undeclared runtime fields are written to Book/Track/QueueItem.
- Moved unfinished-download startup scanning to a daemon worker, validated output paths and bounded directory depth.
- Backup restore now reapplies audio, normalization, templates, bandwidth, integration, UI and language settings to live variables.
- First-run wizard preserves an existing pure `m4b` output mode.
- Cover caches now use stable URL/path keys and prune stale images after queue/history changes.
- Template engine safely handles missing/non-numeric track indices, target extensions and mixed Windows path separators.
- Tooltips now hide on `<Destroy>` to prevent orphan popups.
- Tray startup/shutdown is synchronized to prevent show/hide races and phantom icons.
- Added `tests/test_maintenance.py` and wired it into CI/release smoke tests.

## 4.7.1.3

- Fixed `TclError: image "pyimageN" doesn't exist` when a previous cover preview was cleared.
- CTkLabel image replacement is now image-first and text-second.
- The native Tk image slot is cleared before CTkImage replacement to recover from stale Tcl image handles after DPI/theme redraws.
- Applied the same safe image lifecycle to the completion/result cover card.
- Added a regression test that simulates a stale Tk image handle.

- Range segments now continue automatically when a CDN/proxy returns a capped partial 206 response (for example 3 MiB).
- Interrupted Range responses preserve already-written bytes and retry from the first missing byte.
- Added regression coverage for server-capped Range responses.

## 4.7.1.1

- Fixed delayed UI error callbacks capturing Python exception variables after the `except` block had exited.
- Fixed all five affected callbacks in analysis, download, recheck and Audiobookshelf paths.
- Added an architecture regression guard that rejects unsafe exception-variable capture inside deferred lambda bodies.

## 4.7.1

- Renamed the internal package from `audioknigi_v46` to stable `audioknigi`.
- Moved runtime version to `audioknigi.__version__` / `audioknigi/version.py`.
- Added `pyproject.toml` with dynamic version metadata.
- Standardized documentation as `README.md` and `RELEASE_SETUP.md`.
- Moved smoke/regression scripts to version-neutral `tests/` modules.
- Routed Audiobookshelf HTTP through the shared retry-enabled session.
- Added explicit architecture tests for HTTP timeouts and GUI worker-thread rules.
- Added rotating privacy-sanitized application logs (1 MB × 3 backups).
- Bounded the last crash report and kept it privacy-sanitized.
- Added an explicit `.part` single-stream resume regression test.

## 4.7.0

- First-run wizard, listening-position resume, library covers, duplicate detection, site-structure diagnostics, Help Center, accessibility and RU/UK/DE/EN localization foundation.
