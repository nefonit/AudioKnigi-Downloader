AudioKnigi Downloader 4.4.1
===============================

Версия 4.4.1 усиливает шесть функций сетевого/аудио ядра 4.4.

1. ВИЗУАЛЬНЫЙ DRAG-AND-DROP ОЧЕРЕДИ
-----------------------------------
- Книгу можно тянуть мышью по очереди.
- Во время движения подсвечивается/выбирается будущая позиция.
- Под списком показывается текст: куда именно будет перемещена книга.
- После отпускания отображается новая позиция.
- Кнопки Вверх/Вниз, Приоритет и Пауза книги сохранены.

2. AUTO-CHUNKER
---------------
Автоматический режим выбирает стартовое число Range-потоков:
- меньше 50 MB -> 2
- 50-300 MB -> 4
- больше 300 MB -> 8

Если средняя скорость одного активного сегмента несколько замеров подряд
ниже порога, Auto-Chunker уменьшает параллелизм 8 -> 4 -> 2.
Порог можно выбрать в настройках: 128 / 256 / 512 / 1024 KB/s.
Если пользователь включил общий Bandwidth Limiter, адаптивное снижение
не вмешивается, чтобы не принять искусственный лимит за плохую сеть.

3. SESSION PERSISTENCE
----------------------
После успешного Playwright fallback сохраняются:
- cookies (включая cf_clearance-подобные cookie, если сайт их выдал);
- User-Agent браузера;
- Accept-Language;
- безопасные sec-ch-ua заголовки, если они были доступны.

Новые requests.Session автоматически подхватывают этот профиль.
Истёкшие cookies при загрузке профиля пропускаются.

4. TWO-PASS LOUDNORM
---------------------
Режим two_pass:
- проход 1: FFmpeg loudnorm измеряет input_i/input_lra/input_tp/input_thresh/offset;
- проход 2: измеренные значения передаются обратно loudnorm.
Работает и для отдельных MP3, и для итогового M4B.

5. SMART FORMAT MATCH
---------------------
Перед обработкой FFprobe получает codec/bitrate/sample-rate/channels.
Если выбран более тяжёлый MP3-профиль, чем уже имеет MP3-источник,
и нормализация выключена, применяется copy вместо бессмысленного
перекодирования вверх. При необходимости перекодирования выходной bitrate
и число каналов не повышаются выше исходника.

6. M4B TAGS + COVER
-------------------
После FFmpeg финальный M4B обрабатывается через mutagen.mp4:
- title / album
- author / album artist
- year
- genre
- description
- source URL
- narrator
- cover (covr)
- media kind = audiobook
- encoded-by

После save файл перечитывается: title и обложка проверяются повторно.
Главы по-прежнему создаются FFmpeg/FFMETADATA.

ЗАПУСК
------
py -m pip install -r requirements_v4_4_1.txt
py -m playwright install chromium
py audioknigi_gui_v4_4_1.py

ТЕСТЫ
-----
py selftest_v4_4_1.py
py network_integration_smoketest_v4_4_1.py
py range_smoketest_v4_4_1.py
py dnd_smoketest_v4_4_1.py
py queue_ui_smoketest_v4_4_1.py
py audio_smoketest_v4_4_1.py
py advanced_smoketest_v4_4_1.py
py ui_smoketest_v4_4_1.py

СБОРКА EXE
----------
build_exe_v4_4_1.bat

FFmpeg и FFprobe должны быть доступны через PATH.
Playwright/Chromium используется только как fallback.
