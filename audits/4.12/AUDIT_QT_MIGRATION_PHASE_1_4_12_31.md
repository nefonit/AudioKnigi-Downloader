# Audit — Qt migration Phase 1 (4.12.31)

Дата: 2026-09-06

## Проверено

- Стабильный `audioknigi_gui.py` сохранён без замены Qt-кодом.
- Новый Qt entrypoint отделён: `audioknigi_qt.py`.
- Новый UI слой `audioknigi/qt/` не импортирует `tkinter`, `ttkbootstrap` или `ui_kit`.
- Новый search service `audioknigi/services/search_service.py` также GUI-independent.
- Поиск выполняется вне Qt GUI thread через `QThread`.
- Таблица результатов использует стандартный `QTableView`/`QAbstractTableModel`.
- Accessibility строится на стандартных Qt properties и `QAccessibleAnnouncementEvent`; нет `focus_force`, `grab_set` или собственного глобального Tab traversal в Qt-слое.
- Модальные информационные/вопросительные окна используют `QMessageBox`.
- Settings/history совместимы с текущими JSON-файлами приложения.
- PySide6 зафиксирован как `>=6.8,<7`, потому что Phase 1 использует native accessibility announcement API Qt 6.8+.

## Автоматические проверки

Добавлен `tests/test_qt_migration_phase1_41231.py`:

- проверяет параллельное существование Tk и Qt entrypoints;
- запрещает Tk imports в новом Qt/service слое;
- проверяет PySide6 dependency;
- проверяет применение native accessibility API;
- проверяет `QTableView` + `QThread` архитектуру;
- повторяет ключевую regression-проверку фильтрации поиска AudioKnigi.

## Известные риски

- PySide6 отсутствовал в среде аудита, поэтому фактический NVDA/JAWS Windows runtime smoke-test должен быть выполнен на целевой Windows-машине после `pip install -r requirements-qt.txt`.
- Search service временно дублирует часть чистой parsing-логики legacy `SearchMixin`; после достижения parity legacy Tk search следует переключить на общий service и удалить дубликат.
- Queue/downloader/player пока остаются Tk-coupled и не должны импортироваться из Qt UI.

## Вердикт

Phase 1 пригодна как безопасная основа миграции: Qt интерфейс уже запускается отдельным entrypoint и содержит полезный рабочий вертикальный срез (поиск → выбор URL + история/settings), при этом стабильная Tk версия остаётся доступна.

## Результаты проверки в среде миграции

- `tests/test_qt_migration_phase1_41231.py`: **6 passed**.
- `tests/test_architecture.py + test_search_accuracy_482.py + test_search_variants_495.py + test_modal_ownership_41231.py`: **10 passed, 1 skipped**.
- `tests/test_theme_contrast_system_41231.py` через `xvfb-run`: **6 passed**.
- `test_repository_catalog_41231.py + test_qt_migration_phase1_41231.py`: **9 passed**.
- Полный `pytest` через виртуальный дисплей прошёл без видимых ошибок примерно до 55% и был остановлен внешним лимитом времени среды, а не тестовым падением.
- `py_compile` для всех новых Qt/service модулей: OK.
- `pyproject.toml` разбирается `tomllib`; Qt dependency объявлена как optional extra, поэтому стабильный Tk `requirements.txt` не утяжелён PySide6.

Runtime запуск Qt в этой Linux-среде не выполнялся: PySide6 не установлен, а `pip` не имеет сетевого доступа. API, использованные для accessibility (`accessibleName`, `accessibleDescription`, `accessibleIdentifier`, `QAccessibleAnnouncementEvent`), сверены с актуальной официальной документацией Qt for Python.
