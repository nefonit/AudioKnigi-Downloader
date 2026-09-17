AudioKnigi Downloader 4.2
=============================

ГЛАВНОЕ В 4.2

1. Модульная архитектура
   - audioknigi_v42/downloader.py
   - audioknigi_v42/player.py
   - audioknigi_v42/storage.py
   - audioknigi_v42/queue_manager.py
   - audioknigi_v42/event_bus.py
   - audioknigi_v42/ui/main_tab.py
   - audioknigi_v42/ui/queue_tab.py
   - audioknigi_v42/ui/history_tab.py
   - audioknigi_v42/ui/settings_tab.py

   Главный класс AudioKnigiApp теперь только координирует модули.

2. Thread-safe UI
   Фоновые потоки не вызывают Tkinter через after(0) напрямую.
   UI-команды передаются через queue.Queue и обрабатываются главным потоком.

3. Windows-safe имена
   Удаляются завершающие точки/пробелы.
   Обрабатываются зарезервированные имена CON, PRN, AUX, NUL, COM1..COM9, LPT1..LPT9.

4. FFprobe / Mutagen cache
   Длительность кешируется по:
   полный путь + размер + время изменения файла.
   Повторная проверка неизменившихся MP3 не запускает ffprobe заново.

5. Параллельная обработка
   - несколько независимых исходных файлов могут скачиваться параллельно;
   - нарезка параллелится максимум в 3 потока только между разными исходниками;
   - части одного большого исходного MP3 режутся последовательно;
   - ID3-теги для независимых файлов записываются параллельно.

6. Requests Session / User-Agent
   Используется Session + Retry.
   HTTP-профиль выбирается для сессии и периодически обновляется.
   Playwright остаётся fallback-методом.

7. Обложки
   Превью масштабируется через ImageOps.contain(..., (150, 150)).

8. Скорость и ETA
   Во время скачивания статус показывает:
   скачано / всего • MB/s • ETA.

9. Пауза очереди
   Кнопка ПАУЗА не обрывает текущую книгу.
   Текущая книга завершается, после чего обработка следующей ждёт команды ПРОДОЛЖИТЬ.

10. Уведомления
    При завершении длинной очереди, если окно свернуто/неактивно,
    программа пытается показать системное уведомление.
    Сначала используется plyer, если он уже установлен.
    На Windows есть встроенный PowerShell fallback, поэтому plyer не обязателен.

11. Отмена
    threading.Event используется вместо time.sleep.
    FFmpeg запускается с shell=False и контролируется через communicate(timeout=...),
    чтобы сохранить быструю отмену.

ЗАПУСК

1. Распаковать ZIP полностью.
2. Открыть PowerShell в папке AudioKnigi_Downloader_v4_2.
3. Выполнить:

   py -m pip install -r requirements_v4_2.txt
   py -m playwright install chromium

4. Запуск:

   py audioknigi_gui_v4_2.py

ПРИМЕЧАНИЕ

Поскольку версия 4.2 модульная, нельзя вынимать только файл
audioknigi_gui_v4_2.py из папки. Рядом должна оставаться папка audioknigi_v42.

СБОРКА EXE

Запустить:
build_exe_v4_2.bat

FFmpeg и FFprobe должны оставаться доступными через PATH.
