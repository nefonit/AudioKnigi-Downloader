AudioKnigi Downloader 4.5.0
===============================

Что нового
----------

1. Сохранены и проверены:
   - Auto-Chunker 2/4/8 + автоматическое снижение параллелизма;
   - Playwright cookies/header persistence обратно в requests.Session;
   - Two-pass loudnorm;
   - Smart Format Match;
   - M4B tags + cover через mutagen.mp4;
   - визуальный Drag-and-Drop очереди.

2. Sidecar metadata расширены:
   - metadata.json;
   - book.nfo;
   - book_info.txt;
   - desc.txt;
   - reader.txt;
   - cover.jpg / cover.png.

   metadata.json содержит обычные поля и дополнительные aliases authors,
   narrators, publishedYear и genres для удобной интеграции с медиасерверами.

3. GitHub Actions:
   .github/workflows/ci.yml
     - запускается на push / pull request;
     - Python 3.14;
     - устанавливает зависимости, Chromium и FFmpeg;
     - запускает полный набор smoke tests.

   .github/workflows/release.yml
     - запускается при push тега v*;
     - прогоняет smoke tests;
     - собирает standalone Windows EXE через PyInstaller;
     - упаковывает Chromium fallback, ffmpeg и ffprobe;
     - загружает EXE и ZIP как workflow artifact;
     - создаёт/обновляет GitHub Release.

Локальный запуск
----------------

py -m pip install -r requirements_v4_5_0.txt
py -m playwright install chromium
py audioknigi_gui_v4_5_0.py

Локальная standalone-сборка Windows
----------------------------------

Убедитесь, что ffmpeg и ffprobe доступны через PATH, затем:

build_exe_v4_5_0.bat

Результат:

dist\AudioKnigiDownloader.exe

GitHub Release
--------------

После загрузки проекта в GitHub создайте и отправьте tag, например:

git tag v4.5.0
git push origin v4.5.0

Workflow release.yml автоматически выполнит тесты, соберёт EXE и создаст Release.
