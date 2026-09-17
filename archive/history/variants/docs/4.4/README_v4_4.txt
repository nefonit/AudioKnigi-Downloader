AudioKnigi Downloader 4.4
=========================

Версия 4.4 развивает 4.3.1 и сохраняет предыдущие функции:
requests-first / Playwright fallback, Retry, докачку .part, Range,
M4B, MP3, очередь, историю, Drag-and-Drop, поиск, мини-плеер,
CustomTkinter, системный трей, резервные копии и проверку MP3.

НОВОЕ В 4.4
------------

1. Auto-Chunker
   - auto: <50 МБ -> 2 Range-потока
   - 50-200 МБ -> 4
   - >200 МБ -> 8
   - большие файлы делятся на большее количество Range-задач;
   - при низкой скорости на один поток активный параллелизм может
     автоматически уменьшаться (только в auto и без ручного лимита скорости).

2. Token Bucket Bandwidth Limiter
   Общий лимит скорости для всех HTTP-потоков и Range-сегментов.
   Короткое окно burst делает нагрузку на сеть более плавной.

3. Smart Cookie / Session Persistence
   Если requests получает защитную страницу и срабатывает Playwright fallback,
   cookies Chromium сохраняются в:
     %APPDATA%\AudioKnigiDownloader\session_cookies.json
   Следующие requests.Session автоматически используют эти cookies.

4. Smart Format Match
   FFprobe определяет codec/bitrate/sample rate/channels исходника.
   Если выбран более тяжелый MP3-профиль, чем уже имеет источник,
   и нормализация выключена, программа использует -c copy.
   При перекодировании битрейт/каналы не повышаются выше источника.

5. Two-pass loudnorm
   Нормализация:
   - off
   - single
   - two_pass
   two_pass сначала измеряет loudness JSON-статистику FFmpeg, затем
   выполняет второй проход с measured_I/LRA/TP/threshold/offset.

6. M4B metadata
   После FFmpeg Mutagen MP4 записывает в M4B:
   - title / album
   - author
   - year
   - genre
   - description
   - narrator (freeform NARRATOR)
   - source URL
   - cover (covr)
   Главы FFMETADATA сохраняются.

7. Параллельная нарезка одного источника
   Опциональный режим 2 FFmpeg-процессов для одного исходного MP3.
   Рекомендуется только для SSD. По умолчанию выключен.

8. Sidecar metadata
   После успешной книги рядом сохраняются:
   - book_info.txt
   - metadata.json
   - cover.jpg / cover.png (если обложка доступна)
   Включаются автор, диктор, жанр, год, описание, источник и главы.

9. Audiobookshelf
   Настройки:
   - Server URL
   - API key
   - Library ID
   После успешной загрузки программа может выполнить:
     POST /api/libraries/<ID>/scan
   Через Authorization: Bearer <API key>.
   Ошибка интеграции не делает уже скачанную книгу ошибочной.

10. Template Engine
   Можно включить пользовательские шаблоны.
   Папка по умолчанию:
     {Book_Title}
   Пример:
     {Author}/{Book_Title} ({Year})
   MP3 по умолчанию:
     {Track_Number}.mp3
   Пример:
     {Track_Number} - {Track_Title}.mp3
   Поддерживаются:
     {Output_Dir} {Author} {Book_Title} {Year} {Genre}
     {Narrator} {Track_Number} {Track_Title}

11. График скорости
   На вкладке Книга показываются текущая скорость, активные Range-потоки
   и мини-график последних измерений.

12. Интерактивная очередь
   До запуска очередь можно:
   - перетаскивать внутри списка мышью;
   - двигать стрелками вверх/вниз;
   - ставить книгу в приоритет;
   - ставить отдельную книгу на паузу.
   Общая ПАУЗА очереди по-прежнему завершает текущую книгу и ждёт перед следующей.

13. Предпросмотр M4B
   Кнопка "Предпросмотр M4B" показывает будущие главы, названия,
   точные start/end и общую длительность до скачивания/сборки.

УСТАНОВКА
---------

1. Распаковать ZIP полностью.
2. Открыть PowerShell в папке версии 4.4.
3. Выполнить:

   py -m pip install -r requirements_v4_4.txt
   py -m playwright install chromium

4. Проверить:

   ffmpeg -version
   ffprobe -version

5. Запустить:

   py audioknigi_gui_v4_4.py

ТЕСТЫ
-----

py selftest_v4_4.py
py range_smoketest_v4_4.py
py network_integration_smoketest_v4_4.py
py dnd_smoketest_v4_4.py
py ui_smoketest_v4_4.py
py queue_ui_smoketest_v4_4.py
py audio_smoketest_v4_4.py
py advanced_smoketest_v4_4.py

Некоторые UI/audio tests требуют графического окружения; на обычном Windows
они запускаются напрямую.

EXE
---

build_exe_v4_4.bat

FFmpeg/FFprobe остаются внешними программами и должны быть в PATH.
