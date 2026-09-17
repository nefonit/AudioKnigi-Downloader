# Audit 4.8.14

## Подтверждённые исправления

- Безопасный разбор числовых настроек и runtime-параметров.
- DPI-aware `tk scaling` с неизменяемой process-baseline и адаптивным заголовком/hero-текстом на больших масштабах.
- Потокобезопасный `ScreenReaderBridge`; поддержка значений/состояний классических `tk.*` контролов и wrapper-путей для Tk Accessibility API.
- Безопасные clipboard/completion helpers, очередь при частично построенном UI, resume `selected_indices=None`, история для generic `Mapping`.
- Строковые индексы и защита от двойного расширения в шаблонах.
- Логи сохраняют `0`/`False`.
- Плеер безопасно завершает таймер после уничтожения окна, не борется с ручной перемоткой и использует совместимый вызов pygame.
- `plyer` объявлен как зависимость; pystray не запускает Cocoa loop в worker-thread на macOS.
- Неизвестное имя вкладки — безопасный no-op; cleanup SettingsTab работает как с widget-объектом, так и с Tcl-путём.

## Ложноположительные замечания, проверенные по 4.8.13

- `AudioKnigiApp.t()` присутствует.
- `app.py` не оборван и полностью компилируется.
- `ui_kit.py` не оборван и полностью компилируется.
- `_last_clipboard_offer`, `last_completed_folder`, `_clipboard_offer_after` и `speed_history` инициализируются до использования.
- `apply_tree_zebra()` присутствует.
- `runtime_normalize_audio` содержит завершённое сравнение с `"off"`.
- Prismatoid устанавливает Python binding под import-name `prism`; менять импорт на `prismatoid` не нужно.

## Проверки

- `python -m compileall -q .`
- полный `pytest` под Xvfb: **89 passed**, одно старое `PytestCollectionWarning` для `TestDownloader.__init__`.
- `--version` и `--ci-selftest`.
- GUI smoke-test без traceback.
