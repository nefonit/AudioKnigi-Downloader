# Qt / PySide6 migration — Phase 2

Дата: 2026-09-06  
Основа: Qt Migration Phase 1 + стабильная Tk 4.12.31

## Цель Phase 2

Перенести анализ книги и выбор частей, не импортируя старый `DownloaderMixin` в Qt. Это принципиально: новый GUI не должен зависеть от `tkinter`, `StringVar`, `Treeview`, `grab_set` или `ui_kit` даже временно.

## Реализовано

1. Новый GUI-independent `audioknigi/services/book_analysis_service.py`.
2. Поддержаны те же три источника:
   - audioknigi.com.ua;
   - knigavuhe.org;
   - poleknig.com.
3. Для audioknigi.com.ua сохранён быстрый requests-анализ и Playwright fallback.
4. Анализ запускается из Qt через отдельный `QThread`.
5. Добавлена отмена через обычный `threading.Event`, не связанный с GUI toolkit.
6. Progress/status сообщения идут callback -> Qt Signal -> status bar / accessibility announcement.
7. Добавлен `TrackTableModel` (`QAbstractTableModel`) и `QTableView` с нативными checkbox-состояниями частей.
8. Добавлены «Выбрать все» и «Снять все».
9. После анализа показываются название, автор, чтец, жанр, год и число частей.
10. Добавлен GUI-neutral `DownloadRequest` — контракт для Phase 3. Он фиксирует выбранные индексы, output dir, naming/audio/normalization/template параметры и валидирует запрос до запуска загрузчика.
11. Стабильный Tk GUI и существующий `DownloaderMixin` в Phase 2 не изменялись.

## Почему скачивание ещё не подключено кнопкой

Существующий downloader содержит не только HTTP download, но и resume/range, ffmpeg, split по таймкодам, ID3/cover, duplicate preflight, disk-space checks, fallback источников, восстановление URL и очередь. Подключение его к Qt через фиктивный Tk-объект вернуло бы именно тот слой совместимости, от которого выполняется миграция.

Поэтому Phase 2 заканчивается на проверенном `DownloadRequest`; Phase 3 переносит движок за этот контракт и только после этого включает кнопку «Скачать выбранные».

## Accessibility

Используются стандартные Qt элементы:

- `QLineEdit` для URL;
- `QPushButton` для анализа/отмены/выбора;
- `QTableView` + check state для дорожек;
- `QProgressBar` для состояния операции;
- существующие `accessibleName`, `accessibleDescription`, `accessibleIdentifier` и `QAccessibleAnnouncementEvent`.

Ни analysis service, ни download contract не импортируют Qt/Tk — accessibility остаётся задачей GUI-слоя, а не backend.

## Phase 3

1. Выделить downloader engine из Tk `DownloaderMixin`.
2. На вход принимать `DownloadRequest`.
3. На выход отдавать progress/status callbacks и cancellation event.
4. Перенести resume/range + ffmpeg/split/ID3 без функциональных потерь.
5. Включить кнопку «Скачать выбранные» в Qt.
6. Затем перенести очередь поверх того же engine.
