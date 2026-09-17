# Qt / PySide6 migration — Phase 1

Дата: 2026-09-06  
Исходная стабильная ветка: 4.12.31 Tk/ttkbootstrap  
Новый интерфейс: PySide6 / Qt Widgets

## Цель

Начать миграцию интерфейса без риска потерять работающую Tk-версию. Стабильный вход `audioknigi_gui.py` не изменён. Новый вход `audioknigi_qt.py` запускает отдельный Qt Widgets интерфейс и использует тот же каталог настроек/истории.

## Что уже перенесено

1. `QApplication` + `QMainWindow` и стандартная вкладочная навигация `QTabWidget`.
2. Стандартные Qt Widgets вместо собственных Tk wrappers для нового интерфейса.
3. Qt-native accessibility metadata:
   - `accessibleName`;
   - `accessibleDescription`;
   - `accessibleIdentifier` / `objectName`;
   - `QAccessibleAnnouncementEvent` без перевода фокуса.
4. Реальный поиск сразу по трём источникам:
   - audioknigi.com.ua;
   - knigavuhe.org;
   - poleknig.com.
5. Поиск вынесен в GUI-independent `audioknigi/services/search_service.py` и выполняется в отдельном `QThread`.
6. Результаты поиска показываются через `QTableView` + `QAbstractTableModel`.
7. Выбранный результат можно перенести во вкладку «Книга» и скопировать его URL.
8. История читается из прежнего `history.json` и отображается в Qt.
9. Базовые настройки (папка, тема, масштаб) читаются/сохраняются в прежний `settings.json` с сохранением неизвестных старых полей.
10. Модальные сообщения используют `QMessageBox`, а не Tk `grab_set`/`focus_force`.
11. Добавлены отдельные `run_qt.bat` и `build_qt_exe.bat`.

## Почему пока два GUI

Полная замена Tk одним коммитом слишком рискованна: загрузчик, очередь, плеер и часть storage-кода ещё обращаются к Tk-переменным и виджетам. Поэтому миграция идёт вертикальными срезами. Старый GUI остаётся контрольной реализацией до достижения функционального паритета.

## Текущие ограничения Qt Phase 1

Пока не перенесены:

- анализ страницы книги и выбор дорожек;
- запуск/отмена загрузки;
- очередь и восстановление очереди;
- плеер;
- tray;
- onboarding/help center;
- drag-and-drop;
- полная локализация всех Qt-строк;
- окончательное удаление Prism/tk-uia/Tk accessibility слоя.

Кнопки «Анализировать» и «Скачать» в Qt намеренно отключены до переноса соответствующих backend-контроллеров. Это лучше, чем подключать Tk mixin к Qt через фиктивные `StringVar` и снова создавать слой совместимости.

## Следующий этап

Phase 2 должен отделить анализ/загрузчик от Tk UI:

1. создать GUI-independent controller для анализа `Book`;
2. перенести выбор дорожек в `QTableView`/model;
3. добавить progress/state signals;
4. подключить отмену операции;
5. только после этого включить Qt-кнопки «Анализировать» и «Скачать»;
6. покрыть NVDA/JAWS реальными Windows smoke-тестами.

## Запуск

После установки зависимостей:

```bat
python -m pip install -r requirements-qt.txt
run_qt.bat
```

Или:

```bat
python audioknigi_qt.py
```

Проверка импорта Qt:

```bat
python audioknigi_qt.py --qt-selftest
```

## Сборка EXE

```bat
build_qt_exe.bat
```

На Phase 1 это отдельная preview-сборка `AudioKnigiDownloader_Qt`; стабильная Tk-сборка остаётся прежней.
