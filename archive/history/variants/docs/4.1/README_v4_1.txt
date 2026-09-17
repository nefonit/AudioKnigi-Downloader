AudioKnigi Downloader 4.1

Основные архитектурные изменения:

1. Requests-first
   Страница книги и .pl.txt сначала загружаются через requests.Session.
   Chromium больше не запускается при обычном успешном анализе.

2. Playwright fallback
   Playwright запускается только если обычный HTTP не смог получить
   плейлист или сайт показал защитную страницу.

3. Retry
   requests.Session использует HTTPAdapter + urllib3 Retry:
   429, 500, 502, 503, 504, connect/read errors.

4. ThreadPoolExecutor
   Параллельно выполняются независимые задачи:
   - получение размера источника и обложки;
   - загрузка нескольких независимых исходных MP3;
   - запись ID3-тегов в разные части.

5. Без time.sleep
   В рабочем коде больше нет time.sleep().
   Отмена использует threading.Event.

6. FFmpeg
   shell=False, аргументы передаются списком.
   Ожидание выполняется через communicate(timeout=...).
   Сохраняется возможность немедленной отмены.

Запуск:

py -m pip install -r requirements_v4_1.txt
py -m playwright install chromium
py audioknigi_gui_v4_1.py

Playwright Chromium можно оставить установленным: в 4.1 он используется только
как резервный способ анализа.
