from __future__ import annotations

import threading

from PySide6.QtCore import QThread, Slot, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMenu, QPushButton, QStackedWidget, QTableView, QToolButton, QVBoxLayout, QWidget
from ...models import SearchResult
from ...services.search_service import SearchOutcome
from ..accessibility import configure_accessible, focus_table_row
from ..search_model import SearchResultsModel
from ..search_progress import CircularSearchProgress
from ..menu_utils import transient_menu
from ..workers import SearchWorker as _SearchWorker

class SearchUiMixin:
    """Search behavior for :class:`AudioKnigiQtWindow`."""

    def _build_search_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        row = QHBoxLayout()
        label = QLabel(self._l("Название или автор:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self._l("Минимум 3 символа"))
        configure_accessible(
            self.search_edit,
            name="Поисковый запрос",
            description="Введите название аудиокниги или автора, минимум три символа",
            identifier="search_query",
        )
        label.setBuddy(self.search_edit)
        self.search_button = QPushButton(self._l("Искать"))
        configure_accessible(
            self.search_button,
            name="Искать аудиокниги",
            description="Поиск одновременно на трёх поддерживаемых сайтах",
            identifier="search_button",
        )
        self.search_edit.returnPressed.connect(self.start_search)
        self.search_button.clicked.connect(self.start_search)
        self.search_filter_button = QToolButton(page)
        self.search_filter_button.setText(self._l("Фильтры ▾"))
        self.search_filter_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.search_filter_menu = QMenu(self.search_filter_button)
        self._search_source_actions = {}
        for source_name in ("audioknigi.com.ua", "knigavuhe.org", "poleknig.com"):
            action = self.search_filter_menu.addAction(source_name)
            action.setCheckable(True)
            action.setChecked(True)
            self._search_source_actions[source_name] = action
        self.search_filter_menu.addSeparator()
        self.search_only_available_action = self.search_filter_menu.addAction(self._l("Только доступные"))
        self.search_only_available_action.setCheckable(True)
        self.search_filter_button.setMenu(self.search_filter_menu)
        configure_accessible(
            self.search_filter_button,
            name=self._l("Фильтры поиска"),
            description=self._l("Выберите сайты поиска и при необходимости показывайте только доступные книги"),
            identifier="search_filters",
        )
        row.addWidget(label)
        row.addWidget(self.search_edit, 1)
        row.addWidget(self.search_filter_button)
        row.addWidget(self.search_button)
        layout.addLayout(row)

        self.search_progress_row = QWidget(page)
        search_progress_layout = QHBoxLayout(self.search_progress_row)
        search_progress_layout.setContentsMargins(0, 2, 0, 4)
        search_progress_layout.addStretch(1)
        self.search_progress = CircularSearchProgress(self.search_progress_row)
        self.search_progress.setObjectName("searchProgress")
        configure_accessible(
            self.search_progress,
            name=self._l("Ход поиска"),
            description=self._l("Поиск не запущен"),
            identifier="search_progress",
        )
        self.search_progress_label = QLabel(self._l("Поиск выполняется…"))
        self.search_progress_label.setObjectName("secondaryText")
        self.search_progress_label.setWordWrap(True)
        search_progress_layout.addWidget(self.search_progress)
        search_progress_layout.addSpacing(8)
        search_progress_layout.addWidget(self.search_progress_label)
        self.cancel_search_button = QPushButton(self._l("Отменить поиск"), self.search_progress_row)
        configure_accessible(self.cancel_search_button, name=self._l("Отменить поиск"), identifier="cancel_search")
        self.cancel_search_button.clicked.connect(self.cancel_search)
        search_progress_layout.addWidget(self.cancel_search_button)
        search_progress_layout.addStretch(1)
        self.search_progress_row.setVisible(False)
        layout.addWidget(self.search_progress_row)

        if not hasattr(self, "search_model"):
            self.search_model = SearchResultsModel(self)
        self.search_table = QTableView()
        self.search_table.setModel(self.search_model)
        self.search_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.search_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.search_table.setAlternatingRowColors(True)
        self.search_table.setSortingEnabled(False)
        self.search_table.verticalHeader().setVisible(False)
        self.search_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.search_table.horizontalHeader().setResizeContentsPrecision(60)
        self.search_table.horizontalHeader().setStretchLastSection(True)
        configure_accessible(
            self.search_table,
            name="Результаты поиска",
            description="Таблица с названием, автором, чтецом, количеством озвучек и источником",
            identifier="search_results",
        )
        self.search_table.doubleClicked.connect(lambda _index: self.use_selected_result())
        self.search_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_table.customContextMenuRequested.connect(lambda pos: self._show_search_context_menu(self.search_table, pos))
        self.search_results_stack = QStackedWidget(page)
        self.search_empty_state = QLabel(self._l("Результаты поиска появятся здесь") + "\n" + self._l("Введите минимум 3 символа для поиска"))
        self.search_empty_state.setObjectName("emptyState")
        self.search_empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_empty_state.setWordWrap(True)
        configure_accessible(self.search_empty_state, name=self._l("Результаты поиска появятся здесь"), identifier="search_empty_state")
        self.search_results_stack.addWidget(self.search_empty_state)
        self.search_results_stack.addWidget(self.search_table)
        self.search_results_stack.setCurrentIndex(0)
        layout.addWidget(self.search_results_stack, 1)

        actions = QHBoxLayout()
        self.use_result_button = QPushButton(self._l("Выбрать и проанализировать"))
        self.copy_result_button = QPushButton(self._l("Копировать ссылку"))
        configure_accessible(self.use_result_button, name=self._l("Выбрать и проанализировать"), identifier="use_search_result")
        configure_accessible(self.copy_result_button, name="Копировать ссылку выбранной книги", identifier="copy_search_url")
        self.use_result_button.clicked.connect(self.use_selected_result)
        self.copy_result_button.clicked.connect(self.copy_selected_url)
        self.use_result_button.setEnabled(False)
        self.copy_result_button.setEnabled(False)
        selection_model = self.search_table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(lambda _selected, _deselected: self._update_search_action_states())
        actions.addWidget(self.use_result_button)
        actions.addWidget(self.copy_result_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return page

    def _focus_search(self):
        self.tabs.setCurrentIndex(self.TAB_SEARCH)
        self.search_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search_edit.selectAll()

    def _set_search_progress(self, percent: int, message: str, *, visible: bool = True) -> None:
        value = max(0, min(100, int(percent)))
        localized_message = self._rt(str(message or "")) or self._l("Поиск выполняется…")
        description = self._l("Поиск выполняется: {percent}%", percent=value)
        if localized_message:
            description = f"{description}. {localized_message}"
        for row_name, progress_name, label_name in (
            ("search_progress_row", "search_progress", "search_progress_label"),
            ("easy_search_progress_row", "easy_search_progress", "easy_search_progress_label"),
        ):
            row = getattr(self, row_name, None)
            progress = getattr(self, progress_name, None)
            label = getattr(self, label_name, None)
            if row is None or progress is None or label is None:
                continue
            row.setVisible(bool(visible))
            if visible:
                if not progress.isVisible():
                    progress.start(value)
                else:
                    progress.setProgress(value)
                label.setText(localized_message)
                progress.setAccessibleDescription(description)
                label.setAccessibleDescription(description)
            else:
                progress.reset()

    @Slot()
    def cancel_search(self) -> None:
        cancel_event = getattr(self, "_search_cancel", None)
        if cancel_event is None:
            return
        cancel_event.set()
        if hasattr(self, "cancel_search_button"):
            self.cancel_search_button.setEnabled(False)
        if hasattr(self, "easy_cancel_search_button"):
            self.easy_cancel_search_button.setEnabled(False)
        self.set_status(self._l("Запрошена отмена поиска…"), assertive=True)

    @Slot(int, str)
    def _search_progress_changed(self, percent: int, message: str) -> None:
        self._set_search_progress(percent, message, visible=True)
        self._update_blocking_operation(
            "search",
            progress=percent,
            message=self._rt(str(message or "")) or self._l("Поиск выполняется…"),
        )

    def _hide_search_progress_if_idle(self) -> None:
        thread = self._search_thread
        if thread is not None and thread.isRunning():
            return
        self._set_search_progress(0, "", visible=False)

    @Slot()
    def start_search(self):
        query = self.search_edit.text().strip()
        if len(query) < 3:
            self.set_status("Введите минимум 3 символа для поиска.", assertive=True)
            self.search_edit.setFocus(Qt.FocusReason.OtherFocusReason)
            return
        if self._search_thread is not None and self._search_thread.isRunning():
            self.set_status("Предыдущий поиск ещё выполняется.")
            return

        sources = [name for name, action in getattr(self, "_search_source_actions", {}).items() if action.isChecked()]
        if not sources:
            self.set_status(self._l("Выберите хотя бы один сайт для поиска."), assertive=True)
            return

        self.search_model.set_results([])
        if hasattr(self, "search_results_stack"):
            self.search_results_stack.setCurrentIndex(0)
        self._update_search_action_states()
        self.search_button.setEnabled(False)
        self.search_edit.setReadOnly(True)
        if hasattr(self, "cancel_search_button"):
            self.cancel_search_button.setEnabled(True)
        if hasattr(self, "easy_cancel_search_button"):
            self.easy_cancel_search_button.setEnabled(True)
        if hasattr(self, "easy_action_button"):
            self.easy_action_button.setEnabled(False)
            self.easy_input.setReadOnly(True)
        self._set_search_progress(5, "Поиск запущен", visible=True)
        self.set_status(f"Ищу: {query}")
        self._show_blocking_operation(
            "search",
            title=self._l("Поиск"),
            message=self._l("Поиск выполняется…"),
            cancel_callback=self.cancel_search,
            progress=5,
        )

        cancel_event = threading.Event()
        thread = QThread(self)
        worker = _SearchWorker(
            query, cancel_event, sources=sources,
            only_available=bool(getattr(self, "search_only_available_action", None) and self.search_only_available_action.isChecked()),
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._search_progress_changed)
        worker.finished.connect(self._search_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._clear_search_thread)
        thread.finished.connect(thread.deleteLater)
        self._search_cancel = cancel_event
        self._search_thread = thread
        self._search_worker = worker
        thread.start()

    @Slot(object)
    def _search_finished(self, outcome: SearchOutcome):
        self._set_search_progress(100, "Поиск завершён", visible=True)
        self._update_blocking_operation(
            "search", progress=100, message=self._rt("Поиск завершён")
        )
        self._finish_blocking_operation("search")
        QTimer.singleShot(650, self._hide_search_progress_if_idle)
        self.search_model.set_results(outcome.results)
        self.search_button.setEnabled(True)
        self.search_edit.setReadOnly(False)
        if hasattr(self, "cancel_search_button"):
            self.cancel_search_button.setEnabled(False)
        if hasattr(self, "easy_cancel_search_button"):
            self.easy_cancel_search_button.setEnabled(False)
        if outcome.results:
            if hasattr(self, "search_results_stack"):
                self.search_results_stack.setCurrentIndex(1)
            if outcome.source_count:
                message = self._rt(f"Найдено {len(outcome.results)} книг, источников: {outcome.source_count}.")
            else:
                message = self._rt(f"Найдено {len(outcome.results)} книг.")
            if outcome.errors:
                message += " " + self._rt("Часть источников недоступна.")
            self.set_status(message)
            self.search_table.resizeColumnsToContents()
            self.easy_search_table.resizeColumnsToContents()
            self.easy_search_table.setVisible(self.current_ui_mode() == "easy")
            self.easy_use_result_button.setVisible(self.current_ui_mode() == "easy")
            self.easy_copy_url_button.setVisible(self.current_ui_mode() == "easy")
            if self.current_ui_mode() == "easy":
                focus_table_row(self.easy_search_table, 0, column=1, focus=True)
            else:
                focus_table_row(self.search_table, 0, column=1, focus=True)
            self._update_search_action_states()
            self._play_event_sound("search_complete")
        elif outcome.errors:
            if hasattr(self, "search_results_stack"):
                self.search_results_stack.setCurrentIndex(0)
            self.set_status("Поиск не выполнен: " + "; ".join(outcome.errors), assertive=True)
            if self.current_ui_mode() == "easy":
                self.easy_input.setFocus(Qt.FocusReason.OtherFocusReason)
            else:
                self.search_edit.setFocus(Qt.FocusReason.OtherFocusReason)
            self._play_event_sound("error")
        else:
            if hasattr(self, "search_results_stack"):
                self.search_results_stack.setCurrentIndex(0)
            self.set_status("Ничего не найдено.")
            if self.current_ui_mode() == "easy":
                self.easy_input.setFocus(Qt.FocusReason.OtherFocusReason)
            else:
                self.search_edit.setFocus(Qt.FocusReason.OtherFocusReason)
            self._play_event_sound("book_not_found")

    @Slot()
    def _clear_search_thread(self):
        self._search_thread = None
        self._search_worker = None
        self._search_cancel = None
        self._finish_blocking_operation("search")
        if self._exit_requested:
            return
        self.search_button.setEnabled(True)
        self.search_edit.setReadOnly(False)
        if hasattr(self, "easy_action_button"):
            self.easy_action_button.setEnabled(True)
            self.easy_input.setReadOnly(False)
            self._update_easy_action_text(self.easy_input.text())

    def _update_search_action_states(self) -> None:
        search_selected = self._selected_search_result(self.search_table) is not None if hasattr(self, "search_table") else False
        easy_selected = self._selected_search_result(self.easy_search_table) is not None if hasattr(self, "easy_search_table") else False
        if hasattr(self, "use_result_button"):
            self.use_result_button.setEnabled(search_selected)
        if hasattr(self, "copy_result_button"):
            self.copy_result_button.setEnabled(search_selected)
        if hasattr(self, "easy_use_result_button"):
            self.easy_use_result_button.setEnabled(easy_selected)
        if hasattr(self, "easy_copy_url_button"):
            self.easy_copy_url_button.setEnabled(easy_selected)

    def _show_search_context_menu(self, table, pos):
        if pos is not None and (index := table.indexAt(pos)).isValid():
            table.setCurrentIndex(index)
            table.selectRow(index.row())
        result = self._selected_search_result(table)
        if result is None:
            return
        menu = transient_menu(table)
        use = menu.addAction(self._l("Выбрать и проанализировать"))
        copy = menu.addAction(self._l("Копировать ссылку"))
        open_web = menu.addAction(self._l("Открыть страницу в браузере"))
        if pos is None:
            current = table.currentIndex()
            rect = table.visualRect(current) if current.isValid() else table.rect()
            global_pos = table.viewport().mapToGlobal(rect.center())
        else:
            global_pos = table.viewport().mapToGlobal(pos)
        action = menu.exec(global_pos)
        if action is use:
            self.use_selected_result()
        elif action is copy:
            self.copy_selected_url()
        elif action is open_web:
            QDesktopServices.openUrl(QUrl(result.url))

    def _selected_search_result(self, table=None) -> SearchResult | None:
        if table is None:
            table = self.easy_search_table if self.current_ui_mode() == "easy" and self.easy_search_table.isVisible() else self.search_table
        model = table.selectionModel()
        selection = model.selectedRows() if model is not None else []
        if not selection:
            return None
        return self.search_model.result_at(selection[0].row())

    @Slot()
    def use_selected_result(self):
        result = self._selected_search_result()
        if result is None:
            self.set_status("Сначала выберите книгу в результатах поиска.")
            self.search_table.setFocus(Qt.FocusReason.OtherFocusReason)
            return
        self._pending_search_result = result
        self.book_url_edit.setText(result.url)
        if self.current_ui_mode() == "easy":
            self.easy_input.setText(result.url)
            self.easy_search_table.setVisible(False)
            self.easy_use_result_button.setVisible(False)
            self.easy_copy_url_button.setVisible(False)
            self.easy_summary.setText(self._l("Выбрана: {title}. Анализирую…", title=result.title))
        else:
            self.tabs.setCurrentIndex(self.TAB_BOOK)
            self.book_url_edit.setFocus(Qt.FocusReason.OtherFocusReason)
        self.set_status(f"Выбрана книга: {result.title}")
        # Choosing a search result means the user has already identified the
        # book.  Analyze it immediately in both UI modes so the next deliberate
        # action is simply Download.
        QTimer.singleShot(0, self.start_analysis)

    @Slot()
    def copy_selected_url(self):
        result = self._selected_search_result()
        if result is None:
            self.set_status("Сначала выберите книгу в результатах поиска.")
            return
        self._set_clipboard_text(result.url)
        self.set_status("Ссылка скопирована в буфер обмена.")


__all__ = ["SearchUiMixin"]
