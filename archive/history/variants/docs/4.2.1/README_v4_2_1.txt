AudioKnigi Downloader 4.2.1
===============================

Исправление относительно 4.2
----------------------------

Исправлена ошибка запуска:

AttributeError: 'MainTab' object has no attribute 'tk'

Причина:
контекстное меню создавалось как tk.Menu(self), но MainTab является
обычным Python-классом, а не Tkinter-виджетом.

Исправление:
tk.Menu(app, tearoff=False)

Дополнительно версия 4.2.1 прошла реальный smoke-test создания полного
Tkinter-интерфейса, а не только проверку синтаксиса.

Запуск
------

py audioknigi_gui_v4_2_1.py

Проверка импортов / safe_name:

py selftest_v4_2.py

Быстрый UI smoke-test:

py ui_smoketest_v4_2_1.py

Если smoke-test выводит:

UI SMOKETEST: OK

значит основной интерфейс успешно создаётся.

Все функции 4.2 сохранены:
- модульная архитектура;
- queue.Queue между worker-потоками и Tkinter;
- requests-first / Playwright fallback;
- Retry;
- кеш FFprobe/Mutagen;
- проверка MP3;
- докачка;
- очередь и пауза;
- скорость/ETA;
- мини-плеер;
- история;
- резервные копии;
- темы и доступность.
