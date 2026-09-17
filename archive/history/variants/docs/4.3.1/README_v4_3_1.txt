AudioKnigi Downloader 4.3.1
===============================

Новое относительно 4.3
----------------------

Drag-and-Drop ссылок через tkinterdnd2 0.6.2+:
- можно перетащить ссылку из браузера в поле/зону на вкладке «Книга»;
- ссылка автоматически вставляется и анализируется;
- несколько ссылок: первая открывается, остальные добавляются в очередь;
- на вкладке «Очередь» можно перетащить сразу несколько ссылок;
- можно перетащить Windows-файл .url;
- можно бросить ссылку на всё окно: активная вкладка определяет действие.

Технически используется поддерживаемая интеграция CustomTkinter:
TkinterDnD.require(existing_customtkinter_root).

Все функции 4.3 сохранены:
- HTTP Range 1/2/4/8 сегментов;
- скорость и ETA;
- общий bandwidth limiter;
- MP3 / M4B / MP3+M4B;
- главы FFMETADATA;
- loudnorm;
- перекодирование 64/96/128 kbps;
- CustomTkinter;
- системный трей;
- поиск;
- dataclass-модели;
- докачка, очередь, пауза, история и резервные копии.

Установка
---------

py -m pip install -r requirements_v4_3_1.txt
py -m playwright install chromium

Запуск
------

py audioknigi_gui_v4_3_1.py

Проверка Drag-and-Drop
----------------------

py dnd_smoketest_v4_3_1.py

PyInstaller
-----------

Для tkinterdnd2 в комплекте есть hook-tkinterdnd2.py.
build_exe_v4_3_1.bat уже запускает PyInstaller с --additional-hooks-dir=.

Дополнительные проверки
------------------------

py selftest_v4_3_1.py
py range_smoketest_v4_3_1.py
py audio_smoketest_v4_3_1.py
py ui_smoketest_v4_3_1.py
