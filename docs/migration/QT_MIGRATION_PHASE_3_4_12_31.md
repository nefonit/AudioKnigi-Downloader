# Qt / PySide6 migration — Phase 3

Дата: 2026-09-06  
Основа: Qt Migration Phase 2 + стабильная Tk 4.12.31

## Цель Phase 3

Подключить к Qt **реальное скачивание выбранных частей** без фиктивных Tk-виджетов, `StringVar`, `Treeview`, `grab_set` или импорта `ui_kit` в общий download engine. При этом стабильная Tk-версия должна сохранить прежнее поведение.

## Архитектурное изменение

До Phase 3 `audioknigi/downloader.py` содержал две прямые Tk-зависимости:

1. `messagebox` для disk-space warning;
2. собственный Tk `Toplevel` для решения по HTTP 404/410 (остановить или пропустить недоступную часть).

Обе UI-ответственности вынесены из downloader core:

- `DownloaderMixin` теперь не импортирует `tkinter`, `ttk`, `messagebox` или `ui_kit`;
- Tk-реализация этих двух hooks находится в `ActionsMixin` и сохраняет прежнюю modal ownership через `activate_modal_window`;
- GUI-neutral fallback в downloader core никогда самовольно не пропускает отсутствующую часть: без интерактивного frontend решение по умолчанию — `stop`.

Это позволяет импортировать и использовать mature downloader core из Qt без загрузки Tk runtime.

## Новый `audioknigi/download_engine.py`

`DownloadService` — переходный GUI-neutral façade над проверенным `DownloaderMixin`.

На вход получает:

- `DownloadRequest`;
- settings snapshot;
- `threading.Event` для cancellation;
- набор callbacks.

На выход возвращает `DownloadResult` с:

- итоговой папкой;
- выбранными индексами;
- реально пропущенными недоступными индексами.

Callbacks покрывают:

- status;
- stage;
- progress;
- aggregate transfer speed / Range workers;
- log;
- missing-media decision;
- history-changed event.

`download_engine.py` не импортирует Tk или Qt. Он является bridge-слоем на время миграции; после полного разделения downloader core его можно будет упростить или перенести в `services/` без изменения Qt API.

## Что теперь реально работает в Qt

1. Анализ книги.
2. Выбор отдельных частей в `QTableView`.
3. `Скачать выбранные`.
4. Фоновая загрузка через отдельный `QThread`.
5. Безопасная отмена через `threading.Event` плюс interruption активных HTTP responses / subprocesses.
6. Progress bar 0–100.
7. Отображение текущего этапа 1–5.
8. Скорость в MiB/s и число активных Range workers.
9. Resume manifest и `.part`-докачка через общий downloader core.
10. Single/Range/segmented HTTP download.
11. FFmpeg split/transcode/copy path.
12. Normalization presets из существующих settings.
13. ID3 и cover path согласно существующим settings.
14. Sidecar metadata/NFO.
15. Source cleanup согласно `delete_source`.
16. Audiobookshelf scan согласно существующим settings.
17. History persistence и мгновенное обновление вкладки Qt History.
18. HTTP 404/410 refresh flow и доступный Qt `QMessageBox` для решения «пропустить / остановить».
19. Закрытие окна во время скачивания предлагает отменить операцию и закрывается только после worker completion.

## Accessibility

Download UI использует только стандартные Qt Widgets:

- `QPushButton` — старт/отмена;
- `QProgressBar` — прогресс;
- `QLabel` — этап и скорость;
- `QMessageBox` — missing-media decision;
- `QTableView` — список частей.

Для новых элементов заданы `accessibleName` / `accessibleDescription` / `accessibleIdentifier` через общий Qt accessibility helper. Нет `focus_force`, Tk `grab_set` или ручного Prism announcement слоя внутри backend.

## Проверки

Phase 3 добавляет `tests/test_qt_migration_phase3_41231.py`.

Проверяется:

- отсутствие Tk/UI imports в `downloader.py`;
- сохранение Tk modal hooks в `actions.py`;
- import `audioknigi.download_engine` без появления `tkinter` в `sys.modules`;
- cancellation до старта;
- GUI-neutral missing-media callback;
- статическая Qt wiring-проверка worker/start/cancel/dialog;
- **реальный local integration smoke**: FFmpeg генерирует два MP3, локальный HTTP server отдаёт их DownloadService, после чего проверяются оба итоговых MP3, удаление `resume.json`, history и финальные progress/stage callbacks.

Итоговый полный активный test suite был прогнан частями из-за общего лимита одного запуска: **531 passed**.

Дополнительно downloader-focused набор: **242 passed**.

## Что сознательно ещё не перенесено

- очередь;
- восстановление очереди как Qt workflow;
- плеер;
- system tray;
- onboarding/help center;
- drag-and-drop;
- полный Qt settings parity для всех advanced options;
- реальный Windows NVDA/JAWS smoke на собранном Qt EXE.

При этом advanced download settings уже читаются из прежнего `settings.json`, поэтому поведение download engine сохраняет существующие параметры даже до переноса всех соответствующих Qt controls.

## Phase 4

Следующий вертикальный срез — **Queue** поверх `DownloadService`:

1. GUI-neutral queue controller;
2. `QAbstractTableModel` для QueueItem;
3. start/pause/resume/cancel;
4. retry/transient error policy;
5. priority/reorder;
6. восстановление `resume.json`;
7. затем плеер и tray.
