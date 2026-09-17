from __future__ import annotations

"""Complete legacy-to-Qt user-capability inventory.

The current Qt migration rule allows no deferred or intentional
user-facing differences.  A capability can be marked complete only when the
Qt application exposes an equivalent user workflow and persisted-data
contract.  Implementation details (Tk vs Qt, button vs drag-and-drop) may differ
only when *both* interaction methods remain available where legacy exposed both.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FullParityItem:
    key: str
    label: str
    source: str
    qt_surface: str
    complete: bool = True


FULL_PARITY_ITEMS = (
    FullParityItem("first_run", "Мастер первого запуска", "onboarding.py", "qt/onboarding.py"),
    FullParityItem("language", "Язык ru/uk/de/en с сохранением", "app.py/settings_tab.py", "Qt settings + i18n"),
    FullParityItem("easy_mode", "Простой режим", "ui/easy_home.py", "Qt Easy page"),
    FullParityItem("advanced_mode", "Расширенный режим", "app.py/ui/*", "Qt tabs"),
    FullParityItem("universal_input", "Название, автор или ссылка", "actions.py", "Qt Easy/Book routing"),
    FullParityItem("url_drag_drop", "Drag-and-drop ссылок/.url", "dnd.py", "Qt native drop events"),
    FullParityItem("clipboard", "Буфер обмена и предложение ссылки", "actions.py", "Qt clipboard watcher"),
    FullParityItem("search", "Поиск по трём источникам", "search.py", "SearchService + Qt table"),
    FullParityItem("search_actions", "Открыть/копировать/контекстное меню поиска", "ui/search_tab.py", "Qt search table"),
    FullParityItem("search_availability", "Статус доступности результатов", "ui/search_tab.py", "Qt search model"),
    FullParityItem("analysis", "Анализ книги", "actions.py/downloader.py", "BookAnalysisService"),
    FullParityItem("book_metadata", "Название/автор/чтец/жанр/год/описание/длительность", "ui/main_tab.py", "Qt book card"),
    FullParityItem("cover", "Обложка книги", "actions.py/library_visuals.py", "Qt cover label"),
    FullParityItem("narrations", "Несколько озвучек и переход к доступной", "actions.py", "Qt narration combo"),
    FullParityItem("track_columns", "Выбор/№/статус/начало/конец/длительность/источник", "ui/main_tab.py", "Qt track model"),
    FullParityItem("hide_source", "Скрывать технический источник", "settings_tab.py/actions.py", "Qt settings/model column"),
    FullParityItem("track_actions", "Скачать/открыть/удалить и скачать/копировать URL", "actions.py", "Qt context menu"),
    FullParityItem("download_all", "Скачать всю книгу", "actions.py", "Qt Download all"),
    FullParityItem("download_selected", "Скачать отмеченные части", "actions.py", "Qt selected download"),
    FullParityItem("full_mp3", "Одним MP3", "actions.py", "DownloadService full MP3"),
    FullParityItem("duplicate_preflight", "Точный дубликат: открыть/перекачать/отмена", "actions.py", "Qt duplicate preflight"),
    FullParityItem("resume", "resume.json/.part", "storage.py/downloader.py", "Qt recovery + DownloadService"),
    FullParityItem("disk_space", "Проверка свободного места", "downloader.py/actions.py", "DownloadService"),
    FullParityItem("progress", "Этапы и процент", "ui/main_tab.py", "Qt progress widgets"),
    FullParityItem("speed_graph", "Скорость, Range и график", "ui/main_tab.py", "Qt SpeedGraphWidget"),
    FullParityItem("session_log", "Журнал текущей сессии", "ui/main_tab.py", "Qt log viewer"),
    FullParityItem("quality", "Три дружественных пресета качества", "settings_tab.py/easy_home.py", "Qt settings/easy"),
    FullParityItem("download_settings", "Range/скорость/кодирование/нормализация/ID3", "settings_tab.py", "Qt settings"),
    FullParityItem("templates", "Шаблоны папок и MP3", "settings_tab.py", "Qt settings"),
    FullParityItem("audiobookshelf", "Audiobookshelf", "settings_tab.py", "Qt settings/test"),
    FullParityItem("event_sounds", "Голосовые/системные звуки событий", "event_sounds.py", "QtMultimedia event sounds"),
    FullParityItem("event_sound_settings", "Вкл/громкость/предпрослушивание", "settings_tab.py", "Qt settings"),
    FullParityItem("theme", "Light/Dark/System", "actions.py/settings_tab.py", "Qt theme"),
    FullParityItem("scale", "Масштаб интерфейса", "actions.py/settings_tab.py", "Qt application font"),
    FullParityItem("large_mode", "Крупные строки и кнопки", "settings_tab.py", "Qt large mode"),
    FullParityItem("geometry", "Сохранение геометрии окна", "actions.py", "Qt geometry persistence"),
    FullParityItem("queue", "Очередь и сохранение", "queue_manager.py", "QueueStore + Qt"),
    FullParityItem("queue_add", "Добавить текущую/URL/несколько URL DnD", "queue_tab.py/dnd.py", "Qt queue"),
    FullParityItem("queue_pause", "Пауза очереди и конкретной книги", "queue_manager.py", "Qt queue controls"),
    FullParityItem("queue_retry", "Повторить ошибки", "queue_manager.py", "Qt retry"),
    FullParityItem("queue_priority", "Приоритет", "queue_manager.py", "Qt priority"),
    FullParityItem("queue_reorder_buttons", "Вверх/вниз", "queue_manager.py", "Qt queue controls"),
    FullParityItem("queue_reorder_drag", "Drag-and-drop сортировка очереди", "queue_manager.py", "Qt internal drag/drop"),
    FullParityItem("queue_columns", "Обложка/URL/пауза/статус/попытки", "queue_tab.py", "Qt queue table"),
    FullParityItem("history", "История и действия", "storage.py/history_tab.py", "Qt history"),
    FullParityItem("history_cover", "Обложки в истории", "library_visuals.py/history_tab.py", "Qt history icons"),
    FullParityItem("history_export", "Экспорт JSON/CSV", "storage.py", "LibraryService"),
    FullParityItem("backup", "Backup/restore", "storage.py", "LibraryService"),
    FullParityItem("player", "Плеер/пауза/стоп/перемотка/позиции", "player.py", "QtMultimedia"),
    FullParityItem("last_completed", "Открыть/слушать последнюю завершённую", "actions.py/easy_home.py", "Qt completion actions"),
    FullParityItem("tray", "Системный трей", "tray.py", "QSystemTrayIcon"),
    FullParityItem("help", "Контекстная F1 справка", "help_center.py", "Qt HelpCenter"),
    FullParityItem("crash_report", "Копировать обезличенный crash-report", "app.py/help_center.py", "Qt HelpCenter"),
    FullParityItem("screen_reader_test", "Самопроверка доступности", "accessibility.py/actions.py", "Qt accessibility self-test"),
    FullParityItem("hotkeys", "Горячие клавиши и переключение вкладок", "actions.py/help_center.py", "Qt shortcuts/native VK fallback"),
    FullParityItem("dependencies", "Статус FFmpeg/Playwright/ID3/player/cover/tray/DnD", "actions.py/app.py", "Qt diagnostics"),
    FullParityItem("safe_shutdown", "Безопасное закрытие при поиске/анализе/скачивании/очереди", "actions.py/app.py", "Qt closeEvent"),
    FullParityItem("modal_dialogs", "Настоящие блокирующие модальные вопросы", "legacy modal layer/actions.py", "QMessageBox/QDialog application-modal"),
    FullParityItem("context_menus", "Контекстные действия поиска и частей", "search.py/actions.py", "Qt QMenu + Shift+F10"),
    FullParityItem("output_actions", "Выбор/открытие папки и открытие результата", "actions.py/easy_home.py", "Qt folder actions"),
    FullParityItem("completion_notifications", "Статус/звук/tray после завершения", "actions.py/event_sounds.py/tray.py", "Qt status/event sound/tray"),
)


def inventory_parity_complete() -> bool:
    """Return whether every legacy capability has declared Qt source evidence.

    This is an inventory statement, not a runtime/Windows/accessibility acceptance
    result. The strict source audit and frozen self-tests remain separate gates.
    """
    return bool(FULL_PARITY_ITEMS) and all(item.complete for item in FULL_PARITY_ITEMS)


def full_parity_complete(*, runtime_validated: bool = False) -> bool:
    """Compatibility API: a full pass additionally requires runtime validation."""
    return inventory_parity_complete() and bool(runtime_validated)


def parity_keys() -> frozenset[str]:
    return frozenset(item.key for item in FULL_PARITY_ITEMS)


__all__ = ["FullParityItem", "FULL_PARITY_ITEMS", "inventory_parity_complete", "full_parity_complete", "parity_keys"]
