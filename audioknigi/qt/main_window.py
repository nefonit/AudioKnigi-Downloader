from __future__ import annotations
import threading
import weakref
from PySide6.QtCore import QThread, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton, QStackedWidget, QStatusBar, QTabWidget, QTableView, QVBoxLayout, QWidget
from ..brand import BRAND_NAME, DISPLAY_NAME, PRODUCT_NAME
from ..metadata import APP_VERSION
from ..core import DEFAULT_OUTPUT, valid_site_url
from ..sources import normalize_supported_url
from ..models import Book, SearchResult
from ..config.settings import load_app_settings, save_app_settings
from ..i18n import LANGUAGES, localize_runtime_text, tr, ui_text
from ..logging_utils import app_logger
from ..services.queue_service import QueueStore, QueueTask
from .accessibility import AccessibleAnnouncer, configure_accessible, ensure_accessibility_tree
from .event_sounds import QtEventSoundManager
from .onboarding import QtFirstRunWizard
from .operation_dialog import BlockingOperationDialog
from .worker_ui_relay import WorkerUiRelay
from .search_model import SearchResultsModel
from .search_progress import CircularSearchProgress
from .track_model import TrackTableModel
from .player_mixin import PlayerUiMixin
from .player_controller import QtPlayerController
from .settings_sync import SettingsSyncMixin
from .main_window_pages import MainWindowPagesMixin
from .mixins import (
    AccessibilityUiMixin, AnalysisDownloadUiMixin, ClipboardUiMixin, HistoryUiMixin,
    LifecycleUiMixin, QueueUiMixin, SearchUiMixin, SettingsUiMixin,
)
from .tray_controller import QtTrayController
from .media_keys import WindowsMediaKeyFilter
from .workers import AnalysisWorker as _AnalysisWorker, AudiobookshelfWorker as _AudiobookshelfWorker, DownloadWorker as _DownloadWorker, MissingMediaDecision as _MissingMediaDecision, SearchWorker as _SearchWorker
class AudioKnigiQtWindow(
    MainWindowPagesMixin, SettingsSyncMixin, PlayerUiMixin, AccessibilityUiMixin,
    ClipboardUiMixin, AnalysisDownloadUiMixin, SearchUiMixin, QueueUiMixin, HistoryUiMixin,
    SettingsUiMixin, LifecycleUiMixin, QMainWindow,
):
    TAB_BOOK = 0
    TAB_SEARCH = 1
    TAB_QUEUE = 2
    TAB_HISTORY = 3
    TAB_SETTINGS = 4
    TAB_PLAYER = 5
    def __init__(self):
        super().__init__()
        self.settings = load_app_settings()
        self.language = str(self.settings.get("language", "ru") or "ru")
        if self.language not in LANGUAGES:
            self.language = "ru"
        app = QApplication.instance()
        if app is not None:
            app.setProperty("audioknigi_language", self.language)
        self.last_completed_folder = ""
        self.last_completed_book: Book | None = None
        self._session_log_lines: list[str] = []
        self._refreshing_queue = False
        self._syncing_output_dirs = False
        self._syncing_quality = False
        self._book_url_is_stale = False
        self._search_thread: QThread | None = None
        self._search_worker: _SearchWorker | None = None
        self._search_cancel: threading.Event | None = None
        self._abs_thread: QThread | None = None
        self._abs_worker: _AudiobookshelfWorker | None = None
        self._history_rows: list[dict] = []
        self._unfinished_records = []
        self._resume_selected_indices: set[int] | None = None
        self._last_clipboard_prompt = ""
        self._suppress_clipboard_prompt_text = ""
        self._clipboard_prompt_scheduled = False
        self._queue_after_analysis = False
        self._queue_reanalyze_task_id: str | None = None
        self._download_after_analysis = False
        self._history_redownload_confirmed = False
        self._full_mp3_after_analysis = False
        self._known_narration_variants = None
        self._pending_narration_switch = False
        self._suppress_next_book_found_sound = False
        self._analysis_thread: QThread | None = None
        self._analysis_worker: _AnalysisWorker | None = None
        self._analysis_cancel: threading.Event | None = None
        self._download_thread: QThread | None = None
        self._download_worker: _DownloadWorker | None = None
        self._download_cancel: threading.Event | None = None
        self._active_download_mode = "selected"
        self.queue_store = QueueStore()
        self.queue_tasks: list[QueueTask] = []
        self._queue_running = False
        self._queue_stop_requested = False
        self._queue_pausing = False
        self._active_queue_task_id: str | None = None
        self.current_book: Book | None = None
        self._pending_search_result: SearchResult | None = None
        self.search_model = SearchResultsModel(self)
        self.player_controller: QtPlayerController | None = None
        self._player_seek_active = False
        self._active_missing_prompt: _MissingMediaDecision | None = None
        self._active_missing_box: QMessageBox | None = None
        self._operation_dialog: BlockingOperationDialog | None = None
        self._operation_dialog_kind = ""
        self._operation_ui_blocked = False
        self._worker_ui_relay = WorkerUiRelay(self)
        self._exit_requested = False
        self._exit_deadline: float | None = None
        self._exit_poll_scheduled = False
        self._restore_was_maximized = False
        self._tray_notice_shown = False
        self.tray_controller = QtTrayController(self)
        self.event_sound_manager = QtEventSoundManager(
            self,
            enabled=bool(self.settings.get("event_sounds_enabled", True)),
            volume=max(0.0, min(1.0, float(self.settings.get("event_sound_volume", 100.0) or 100.0) / 100.0)),
            language=self.language,
        )
        self.setAcceptDrops(True)
        self.setWindowTitle(f"{DISPLAY_NAME} {APP_VERSION}")
        self.resize(1240, 820)
        self.setMinimumSize(900, 620)
        configure_accessible(
            self,
            name=DISPLAY_NAME,
            description=tr(self.language, "main_window_description"),
            identifier="main_window",
        )
        self._build_ui()
        self._install_localized_text_context_menus()
        self._restore_window_geometry()
        self._init_player()
        self._media_key_filter = WindowsMediaKeyFilter(self)
        if app is not None:
            app.installNativeEventFilter(self._media_key_filter)
        ensure_accessibility_tree(self)
        self._install_shortcuts()
        self._load_queue()
        self._load_history()
        self._refresh_unfinished()
        self._apply_saved_theme()
        app = QApplication.instance()
        if app is not None:
            app.applicationStateChanged.connect(self._application_state_changed)
            clipboard = QApplication.clipboard()
            clipboard.dataChanged.connect(self._clipboard_data_changed)
            QTimer.singleShot(300, self._schedule_clipboard_prompt_check)
        tray_started = self.tray_controller.start()
        self.tray_controller.set_window_visible(True)
        ready_text = self._rt("Приложение готово.")
        tray_text = self._rt(" Системный трей активен." if tray_started else " Системный трей недоступен.")
        self.set_status(ready_text + tray_text)
        self._play_event_sound("app_ready", force=True)
    def _build_ui(self):
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(14, 14, 14, 10)
        layout.setSpacing(10)
        header = QWidget(central)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel(f"{BRAND_NAME} {PRODUCT_NAME}")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.subtitle_label = QLabel(ui_text(self.language, "Аудиокниги без лишних шагов"))
        self.subtitle_label.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.subtitle_label)
        layout.addWidget(header)
        mode_row = QHBoxLayout()
        self.easy_mode_button = QPushButton(tr(self.language, "simple"))
        self.advanced_mode_button = QPushButton(tr(self.language, "advanced"))
        for mode_button in (self.easy_mode_button, self.advanced_mode_button):
            mode_button.setCheckable(True)
            mode_button.setProperty("role", "segment")
        configure_accessible(self.easy_mode_button, name=tr(self.language, "simple"), identifier="ui_mode_easy")
        configure_accessible(self.advanced_mode_button, name=tr(self.language, "advanced"), identifier="ui_mode_advanced")
        self.easy_mode_button.clicked.connect(lambda: self.set_ui_mode("easy"))
        self.advanced_mode_button.clicked.connect(lambda: self.set_ui_mode("advanced"))
        mode_row.addWidget(self.easy_mode_button)
        mode_row.addWidget(self.advanced_mode_button)
        mode_row.addStretch(1)
        layout.addLayout(mode_row)

        self.tabs = QTabWidget(central)
        configure_accessible(
            self.tabs,
            name=ui_text(self.language, "Разделы программы"),
            description=ui_text(self.language, "Книга, поиск, очередь, история, настройки и плеер"),
            identifier="main_tabs",
        )
        self.tabs.addTab(self._build_book_tab(), ui_text(self.language, "Книга"))
        self.tabs.addTab(self._build_search_tab(), ui_text(self.language, "Поиск"))
        self.tabs.addTab(self._build_queue_tab(), tr(self.language, "queue"))
        self.tabs.addTab(self._build_history_tab(), tr(self.language, "history"))
        self.tabs.addTab(self._build_settings_tab(), tr(self.language, "settings"))
        self.tabs.addTab(self._build_player_tab(), ui_text(self.language, "Плеер"))

        self.mode_stack = QStackedWidget(central)
        configure_accessible(self.mode_stack, name=ui_text(self.language, "Режим интерфейса"), identifier="ui_mode_stack")
        self.easy_page = self._build_easy_page()
        self.mode_stack.addWidget(self.easy_page)
        self.mode_stack.addWidget(self.tabs)
        layout.addWidget(self.mode_stack, 1)

        self.setCentralWidget(central)
        self.status = QStatusBar(self)
        configure_accessible(self.status, name=ui_text(self.language, "Строка состояния"), identifier="status_bar")
        self.setStatusBar(self.status)
        self._accessibility_announcer = AccessibleAnnouncer(self.status, parent=self)
        self._wire_live_accessibility_feedback()
        self._wire_output_dir_sync()
        self._build_menu()
        self.set_ui_mode(str(self.settings.get("ui_mode", "easy") or "easy"), persist=False)
        self._apply_large_mode()
        self._apply_source_visibility()

    def _build_easy_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(24, 18, 24, 18)
        outer.setSpacing(12)
        outer.addStretch(1)

        center_row = QHBoxLayout()
        center_row.addStretch(1)
        card = QWidget(page)
        card.setObjectName("easyCard")
        card.setMinimumWidth(660)
        card.setMaximumWidth(900)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(12)

        title = QLabel(tr(self.language, "download_one_click"))
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        hint = QLabel(self._l("Вставьте ссылку на книгу или введите название/автора для поиска."))
        hint.setObjectName("secondaryText")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.easy_input = QLineEdit()
        self.easy_input.setPlaceholderText(self._l("Название, автор или https://…"))
        self.easy_input.setMinimumHeight(40)
        configure_accessible(self.easy_input, name=self._l("Название, автор или ссылка"), identifier="easy_universal_input")
        self.easy_input.returnPressed.connect(self.easy_universal_action)
        self.easy_input.textChanged.connect(self._update_easy_action_text)
        row = QHBoxLayout()
        row.addWidget(self.easy_input, 1)
        self.easy_paste_button = QPushButton(self._l("Вставить"))
        self.easy_action_button = QPushButton(self._l("Искать"))
        self.easy_action_button.setProperty("role", "primary")
        configure_accessible(self.easy_paste_button, name=self._l("Вставить из буфера обмена"), identifier="easy_paste")
        configure_accessible(self.easy_action_button, name=self._l("Найти книгу или открыть ссылку"), identifier="easy_action")
        self.easy_paste_button.clicked.connect(self.easy_paste)
        self.easy_action_button.clicked.connect(self.easy_universal_action)
        row.addWidget(self.easy_paste_button)
        row.addWidget(self.easy_action_button)
        layout.addLayout(row)

        self.easy_search_progress_row = QWidget(card)
        easy_progress_layout = QHBoxLayout(self.easy_search_progress_row)
        easy_progress_layout.setContentsMargins(0, 2, 0, 2)
        easy_progress_layout.addStretch(1)
        self.easy_search_progress = CircularSearchProgress(self.easy_search_progress_row)
        self.easy_search_progress.setObjectName("easySearchProgress")
        configure_accessible(
            self.easy_search_progress,
            name=self._l("Ход поиска"),
            description=self._l("Поиск не запущен"),
            identifier="easy_search_progress",
        )
        self.easy_search_progress_label = QLabel(self._l("Поиск выполняется…"))
        self.easy_search_progress_label.setObjectName("secondaryText")
        self.easy_search_progress_label.setWordWrap(True)
        easy_progress_layout.addWidget(self.easy_search_progress)
        easy_progress_layout.addSpacing(8)
        easy_progress_layout.addWidget(self.easy_search_progress_label)
        self.easy_cancel_search_button = QPushButton(self._l("Отменить поиск"), self.easy_search_progress_row)
        configure_accessible(self.easy_cancel_search_button, name=self._l("Отменить поиск"), identifier="easy_cancel_search")
        self.easy_cancel_search_button.clicked.connect(self.cancel_search)
        easy_progress_layout.addWidget(self.easy_cancel_search_button)
        easy_progress_layout.addStretch(1)
        self.easy_search_progress_row.setVisible(False)
        layout.addWidget(self.easy_search_progress_row)

        settings_row = QHBoxLayout()
        self.easy_quality_combo = QComboBox()
        for text, value in (("Стандартное", "standard"), ("Для телефона", "phone"), ("Выравнять громкость", "normalize")):
            self.easy_quality_combo.addItem(self._l(text), value)
        self._set_combo_data(self.easy_quality_combo, self.settings.get("quality_preset", "standard"))
        configure_accessible(self.easy_quality_combo, name=self._l("Качество"), identifier="easy_quality")
        self.easy_output_edit = QLineEdit(str(self.settings.get("output_dir", DEFAULT_OUTPUT) or DEFAULT_OUTPUT))
        configure_accessible(self.easy_output_edit, name=self._l("Папка для аудиокниг"), identifier="easy_output_dir")
        easy_folder = QPushButton(self._l("Папка…"))
        configure_accessible(easy_folder, name=self._l("Выбрать папку для аудиокниг"), identifier="easy_choose_folder")
        easy_folder.clicked.connect(lambda: self._choose_output_dir(target=self.easy_output_edit))
        settings_row.addWidget(QLabel(self._l("Качество:")))
        settings_row.addWidget(self.easy_quality_combo)
        settings_row.addSpacing(8)
        settings_row.addWidget(QLabel(self._l("Папка:")))
        settings_row.addWidget(self.easy_output_edit, 1)
        settings_row.addWidget(easy_folder)
        layout.addLayout(settings_row)

        self.easy_download_button = QPushButton(self._l("СКАЧАТЬ КНИГУ"))
        self.easy_download_button.setProperty("role", "primary")
        self.easy_download_button.setMinimumHeight(46)
        configure_accessible(self.easy_download_button, name=self._l("Скачать всю выбранную книгу"), identifier="easy_download")
        self.easy_download_button.clicked.connect(self.start_download_all)
        self.easy_download_button.setEnabled(False)
        layout.addWidget(self.easy_download_button)

        self.easy_search_table = QTableView()
        self.easy_search_table.setModel(self.search_model)
        self.easy_search_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.easy_search_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.easy_search_table.setAlternatingRowColors(True)
        self.easy_search_table.verticalHeader().setVisible(False)
        # Easy mode must fit every search column without horizontal scrolling.
        # Human-readable metadata shares the remaining width while compact
        # service columns keep only the space their contents actually need.
        easy_header = self.easy_search_table.horizontalHeader()
        easy_header.setMinimumSectionSize(28)
        easy_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for column, (_label, key) in enumerate(SearchResultsModel.COLUMNS):
            if key in {"index", "availability", "variants", "source"}:
                easy_header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        easy_header.setResizeContentsPrecision(20)
        easy_header.setStretchLastSection(False)
        self.easy_search_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.easy_search_table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.easy_search_table.setWordWrap(False)
        self.easy_search_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.easy_search_table.customContextMenuRequested.connect(lambda pos: self._show_search_context_menu(self.easy_search_table, pos))
        configure_accessible(self.easy_search_table, name=self._l("Результаты поиска в простом режиме"), identifier="easy_search_results")
        self.easy_search_table.doubleClicked.connect(lambda _index: self.use_selected_result())
        self.easy_search_table.setVisible(False)
        layout.addWidget(self.easy_search_table, 1)

        easy_search_actions = QHBoxLayout()
        self.easy_use_result_button = QPushButton(self._l("Выбрать и проанализировать"))
        self.easy_copy_url_button = QPushButton(self._l("Копировать ссылку"))
        configure_accessible(self.easy_use_result_button, name=self._l("Выбрать и проанализировать"), identifier="easy_use_result")
        configure_accessible(self.easy_copy_url_button, name=self._l("Копировать ссылку выбранной книги"), identifier="easy_copy_url")
        self.easy_use_result_button.clicked.connect(self.use_selected_result)
        self.easy_copy_url_button.clicked.connect(self.copy_selected_url)
        self.easy_use_result_button.setEnabled(False)
        self.easy_copy_url_button.setEnabled(False)
        easy_selection_model = self.easy_search_table.selectionModel()
        if easy_selection_model is not None:
            easy_selection_model.selectionChanged.connect(lambda _selected, _deselected: self._update_search_action_states())
        self.easy_use_result_button.setVisible(False)
        self.easy_copy_url_button.setVisible(False)
        easy_search_actions.addWidget(self.easy_use_result_button)
        easy_search_actions.addWidget(self.easy_copy_url_button)
        easy_search_actions.addStretch(1)
        layout.addLayout(easy_search_actions)

        self.easy_empty_hint = QLabel(self._l("Вставьте ссылку или найдите книгу — здесь появятся обложка и сведения о ней."))
        self.easy_empty_hint.setObjectName("emptyState")
        self.easy_empty_hint.setWordWrap(True)
        self.easy_empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        configure_accessible(self.easy_empty_hint, name=self._l("Вставьте ссылку или найдите книгу — здесь появятся обложка и сведения о ней."), identifier="easy_empty_state")
        layout.addWidget(self.easy_empty_hint)

        self.easy_book_card = QWidget()
        self.easy_book_card.setObjectName("bookCard")
        easy_book_layout = QHBoxLayout(self.easy_book_card)
        easy_book_layout.setContentsMargins(14, 14, 14, 14)
        self.easy_cover_label = QLabel(self._l("Нет обложки"))
        self.easy_cover_label.setObjectName("coverPlaceholder")
        self.easy_cover_label.setFixedSize(160, 160)
        self.easy_cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.easy_cover_label.setScaledContents(True)
        configure_accessible(self.easy_cover_label, name=self._l("Обложка выбранной книги"), identifier="easy_book_cover")
        self.easy_summary = QLabel(self._l("Введите название, автора или ссылку."))
        self.easy_summary.setWordWrap(True)
        self.easy_summary.setObjectName("bookMetadata")
        configure_accessible(self.easy_summary, name=self._l("Сведения о выбранной книге"), identifier="easy_book_summary")
        easy_book_layout.addWidget(self.easy_cover_label)
        easy_book_layout.addWidget(self.easy_summary, 1)
        self.easy_book_card.setVisible(False)
        layout.addWidget(self.easy_book_card)

        # Secondary actions are grouped into one menu instead of three unrelated
        # buttons across the bottom edge of the card.
        easy_download_row = QHBoxLayout()
        self.easy_open_listen_button = QPushButton(self._l("Открыть / слушать ▾"))
        configure_accessible(self.easy_open_listen_button, name=self._l("Открыть / слушать ▾"), identifier="easy_open_listen")
        easy_open_menu = QMenu(self.easy_open_listen_button)
        self.easy_open_last_action = easy_open_menu.addAction(self._l("Открыть папку"))
        self.easy_listen_last_action = easy_open_menu.addAction(self._l("Слушать"))
        self.easy_open_last_action.setObjectName("easy_open_last_folder_action")
        self.easy_listen_last_action.setObjectName("easy_listen_last_action")
        self.easy_open_last_action.triggered.connect(self.open_last_completed_folder)
        self.easy_listen_last_action.triggered.connect(self.listen_last_completed_book)
        self.easy_open_listen_button.setMenu(easy_open_menu)
        self.easy_open_listen_button.setEnabled(False)
        # Compatibility aliases keep the download completion paths simple while
        # referring to the single visible grouped control.
        self.easy_open_folder_button = self.easy_open_listen_button
        self.easy_listen_button = self.easy_open_listen_button

        self.easy_another_button = QPushButton(self._l("Скачать следующую книгу"))
        configure_accessible(self.easy_another_button, name=self._l("Найти другую книгу"), identifier="easy_another_book")
        self.easy_another_button.clicked.connect(self.easy_add_another_book)
        easy_download_row.addWidget(self.easy_open_listen_button)
        easy_download_row.addWidget(self.easy_another_button)
        easy_download_row.addStretch(1)
        layout.addLayout(easy_download_row)

        center_row.addWidget(card)
        center_row.addStretch(1)
        outer.addLayout(center_row)
        outer.addStretch(1)
        return page

    def _update_easy_action_text(self, text: str = "") -> None:
        if not hasattr(self, "easy_action_button"):
            return
        value = str(text if text is not None else self.easy_input.text()).strip()
        is_url = value.lower().startswith(("http://", "https://"))
        self.easy_action_button.setText(self._l("Открыть" if is_url else "Искать"))
        self.easy_action_button.setAccessibleName(
            self._l("Найти книгу или открыть ссылку")
        )
        current = getattr(self, "current_book", None)
        if current is not None and hasattr(self, "easy_download_button"):
            current_url = normalize_supported_url(str(getattr(current, "url", "") or ""))
            incoming_url = normalize_supported_url(value) if is_url and valid_site_url(value) else ""
            easy_stale = bool(is_url and not (incoming_url and current_url and incoming_url == current_url))
            self._easy_input_is_stale = easy_stale
            self.easy_download_button.setEnabled(
                bool(getattr(current, "tracks", None))
                and not easy_stale
                and not bool(getattr(self, "_book_url_is_stale", False))
            )


    def _set_operation_ui_blocked(self, blocked: bool) -> None:
        blocked = bool(blocked)
        if self._operation_ui_blocked == blocked:
            return
        self._operation_ui_blocked = blocked
        central = self.centralWidget()
        if central is not None:
            central.setEnabled(not blocked)
        menu = self.menuBar()
        if menu is not None:
            menu.setEnabled(not blocked)

    def _show_blocking_operation(
        self,
        kind: str,
        *,
        title: str,
        message: str,
        cancel_callback,
        progress: int | float | None = None,
        indeterminate: bool = False,
    ) -> None:
        """Show one modeless progress window while manually blocking Easy UI."""
        if self.current_ui_mode() != "easy":
            return
        self._finish_blocking_operation()
        dialog = BlockingOperationDialog(
            self,
            title=title,
            message=message,
            cancel_text=self._l("Отменить"),
            cancelling_text=self._l("Отмена…"),
            indeterminate=indeterminate,
        )
        dialog.cancelRequested.connect(cancel_callback)
        self._operation_dialog = dialog
        self._operation_dialog_kind = str(kind or "")
        dialog.set_progress(progress, message=message, indeterminate=indeterminate)
        self._set_operation_ui_blocked(True)
        app_logger.info("OPERATION UI | event=show | kind=%s | native_modal=0", self._operation_dialog_kind)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _update_blocking_operation(
        self,
        kind: str,
        *,
        progress: int | float | None = None,
        message: str | None = None,
        indeterminate: bool = False,
    ) -> None:
        dialog = self._operation_dialog
        if dialog is None or self._operation_dialog_kind != str(kind or ""):
            return
        try:
            dialog.set_progress(progress, message=message, indeterminate=indeterminate)
        except RuntimeError:
            self._operation_dialog = None
            self._operation_dialog_kind = ""

    def _finish_blocking_operation(self, kind: str | None = None) -> None:
        dialog = self._operation_dialog
        if dialog is None:
            self._operation_dialog_kind = ""
            self._set_operation_ui_blocked(False)
            return
        if kind is not None and self._operation_dialog_kind != str(kind):
            return
        finished_kind = self._operation_dialog_kind
        self._operation_dialog = None
        self._operation_dialog_kind = ""
        app_logger.info("OPERATION UI | event=finish_begin | kind=%s", finished_kind)
        try:
            dialog.finish()
        except RuntimeError:
            pass
        self._set_operation_ui_blocked(False)
        try:
            dialog.deleteLater()
        except RuntimeError:
            pass
        app_logger.info("OPERATION UI | event=finish_end | kind=%s", finished_kind)

    def _l(self, text: str, **kwargs) -> str:
        return ui_text(self.language, text, **kwargs)

    def _rt(self, text: str) -> str:
        return localize_runtime_text(self.language, text)

    def set_ui_mode(self, mode: str, *, persist: bool = True) -> None:
        mode = "easy" if str(mode).lower() == "easy" else "advanced"
        self.mode_stack.setCurrentIndex(0 if mode == "easy" else 1)
        self.easy_mode_button.setChecked(mode == "easy")
        self.advanced_mode_button.setChecked(mode == "advanced")
        if hasattr(self, "view_easy_action"):
            self.view_easy_action.setChecked(mode == "easy")
        if hasattr(self, "view_advanced_action"):
            self.view_advanced_action.setChecked(mode == "advanced")
        if persist:
            self.settings["ui_mode"] = mode
            save_app_settings(self.settings)
        target = self.easy_input if mode == "easy" else self.book_url_edit
        target_ref = weakref.ref(target)

        def focus_target_if_alive() -> None:
            widget = target_ref()
            if widget is None:
                return
            try:
                widget.setFocus(Qt.FocusReason.OtherFocusReason)
            except RuntimeError:
                # The queued callback can outlive the QWidget during offscreen
                # self-tests/window teardown. A deleted Shiboken wrapper is not
                # an application error and must not escape through the Qt event loop.
                return

        QTimer.singleShot(0, focus_target_if_alive)

    def current_ui_mode(self) -> str:
        return "easy" if self.mode_stack.currentIndex() == 0 else "advanced"

    def easy_paste(self):
        self.easy_input.setText(QApplication.clipboard().text().strip())
        self._play_event_sound("link_pasted")
        self.easy_universal_action()

    def easy_universal_action(self):
        text = self.easy_input.text().strip()
        if not text:
            self._show_message(QMessageBox.Icon.Information, tr(self.language, "input_required_title"), tr(self.language, "input_required_text"))
            self.easy_input.setFocus(Qt.FocusReason.OtherFocusReason)
            return
        if valid_site_url(text):
            self.book_url_edit.setText(text)
            self.easy_search_table.setVisible(False)
            self.easy_use_result_button.setVisible(False)
            self.easy_copy_url_button.setVisible(False)
            self.start_analysis()
            return
        if text.lower().startswith(("http://", "https://")):
            self._show_message(QMessageBox.Icon.Warning, self._l("Неподдерживаемая ссылка"), self._l("Поддерживаются audioknigi.com.ua, knigavuhe.org и poleknig.com."))
            return
        self.search_edit.setText(text)
        self.start_search()

    def easy_add_another_book(self):
        self.current_book = None
        self.track_model.set_book(Book(url="", title="", tracks=[]))
        self.easy_summary.setText(self._l("Введите название, автора или ссылку."))
        self.easy_cover_label.setPixmap(QPixmap())
        self.easy_cover_label.setText(self._l("Нет обложки"))
        self.easy_book_card.setVisible(False)
        self.easy_empty_hint.setVisible(True)
        self.easy_input.clear()
        self.book_url_edit.clear()
        self.easy_search_table.setVisible(False)
        self.easy_use_result_button.setVisible(False)
        self.easy_copy_url_button.setVisible(False)
        self.easy_download_button.setEnabled(False)
        self.easy_input.setFocus(Qt.FocusReason.OtherFocusReason)


    def _play_event_sound(self, event: str, *, force: bool = False):
        manager = getattr(self, "event_sound_manager", None)
        if manager is not None:
            manager.play(event, force=force)

    def _append_log(self, message: str):
        raw = str(message or "").strip()
        if not raw:
            return
        text = self._rt(raw)
        self._session_log_lines.append(text)
        if len(self._session_log_lines) > 1000:
            del self._session_log_lines[:-1000]
        if hasattr(self, "session_log"):
            self.session_log.appendPlainText(text)

    def _apply_large_mode(self):
        large = bool(self.settings.get("large_mode", False))
        height = 36 if large else 24
        for table in self.findChildren(QTableView):
            try:
                table.verticalHeader().setDefaultSectionSize(height)
            except Exception:
                pass
        if hasattr(self, "large_mode_check"):
            self.large_mode_check.setChecked(large)

    def _apply_source_visibility(self):
        hide = bool(self.settings.get("hide_source", False))
        if hasattr(self, "track_table"):
            self.track_table.setColumnHidden(TrackTableModel.SOURCE_COLUMN, hide)
        if hasattr(self, "hide_source_check"):
            self.hide_source_check.setChecked(hide)

    def maybe_show_first_run_wizard(self):
        if bool(self.settings.get("first_run_complete", False)):
            return
        wizard = QtFirstRunWizard(self, settings=self.settings)
        if wizard.exec():
            self.settings = wizard.result_settings()
            self.language = str(self.settings.get("language", "ru") or "ru")
            save_app_settings(self.settings)
            self._apply_settings_to_qt_controls()
            self.set_ui_mode(str(self.settings.get("ui_mode", "easy") or "easy"), persist=False)
            start = str(self.settings.get("first_run_start", "search") or "search")
            if start == "link":
                self.book_url_edit.setFocus(Qt.FocusReason.OtherFocusReason)
            else:
                self.easy_input.setFocus(Qt.FocusReason.OtherFocusReason)

    def change_language(self):
        code = str(self.language_combo.currentData() or "ru") if hasattr(self, "language_combo") else self.language
        if code not in LANGUAGES:
            code = "ru"
        changed = code != self.language
        self.language = code
        self.settings["language"] = code
        app = QApplication.instance()
        if app is not None:
            app.setProperty("audioknigi_language", code)
        save_app_settings(self.settings)
        self.event_sound_manager.configure(language=code)
        if changed:
            self._show_message(
                QMessageBox.Icon.Information,
                tr(code, "language"),
                self._l("Язык сохранён. Изменения интерфейса полностью применятся после перезапуска программы."),
            )


    def set_status(self, text: str, *, assertive: bool = False):
        message = self._rt(str(text or ""))
        self.status.showMessage(message)
        announcer = getattr(self, "_accessibility_announcer", None)
        if announcer is not None:
            announcer.speak(message, assertive=assertive)


__all__ = ["AudioKnigiQtWindow"]
