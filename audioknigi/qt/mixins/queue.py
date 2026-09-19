from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Slot, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QInputDialog, QMenu, QMessageBox, QPushButton, QStackedWidget, QTableWidgetItem, QVBoxLayout, QWidget
from ...core import valid_site_url
from ...sources import normalize_supported_url
from ...i18n import tr
from ...models import cover_cache_bytes
from ...services.download_request import build_download_request
from ...services.queue_service import QueueTask, next_runnable_index, task_requires_analysis
from ..accessibility import configure_accessible, focus_table_row
from ..menu_utils import transient_menu
from ..workers import QueueTableWidget as _QueueTableWidget



def _same_supported_url(left: str, right: str) -> bool:
    left_value = normalize_supported_url(str(left or ""))
    right_value = normalize_supported_url(str(right or ""))
    return bool(left_value and right_value and left_value == right_value)

class QueueUiMixin:
    """Queue behavior for :class:`AudioKnigiQtWindow`."""

    @staticmethod
    def _queue_parts_count(task) -> int:
        if str(getattr(task, "download_mode", "selected") or "selected") == "full_mp3":
            return 1
        selected = getattr(task.request, "selected_indices", None)
        if selected is None:
            return len(list(getattr(task.request.book, "tracks", None) or []))
        return len(selected)

    def _queue_row_summary(self, row: int) -> str:
        if not (0 <= row < len(self.queue_tasks)):
            return ""
        task = self.queue_tasks[row]
        error = str(task.last_error or self._l("нет"))
        return self._l(
            "Книга: {title}. Статус: {status}. Пауза: {paused}. Приоритет: {priority}. "
            "Попытки: {attempts}. Частей: {parts}. Ошибка: {error}. URL: {url}.",
            title=task.title, status=self._rt(str(task.status)),
            paused=self._l("да") if task.paused else self._l("нет"),
            priority=self._l("да") if task.priority else self._l("нет"),
            attempts=task.attempts, parts=self._queue_parts_count(task), error=error, url=task.url,
        )

    @Slot(int, int, int, int)
    def _queue_current_cell_changed(self, current_row: int, _current_col: int, previous_row: int, _previous_col: int) -> None:
        self._update_queue_action_states()
        # Each current cell already exposes the complete row summary through
        # AccessibleDescriptionRole. Avoid a second explicit announcement of the
        # same text, which causes duplicate speech in NVDA/JAWS.

    def _update_queue_action_states(self) -> None:
        if not hasattr(self, "queue_table"):
            return
        idx = self._selected_queue_index()
        task = self.queue_tasks[idx] if idx is not None else None
        active_download = self._download_thread is not None and self._download_thread.isRunning()
        is_active = bool(task and task.id == self._active_queue_task_id)
        has_selection = task is not None
        completed = bool(task and task.status_code == "completed")
        needs_analysis = bool(task and task_requires_analysis(task))
        self.queue_item_pause_button.setEnabled(has_selection and not is_active and not completed and not needs_analysis and not self._queue_running)
        self.queue_retry_all_button.setEnabled(any(t.status_code == "error" and not task_requires_analysis(t) for t in self.queue_tasks) and not active_download)
        self.queue_resume_button.setEnabled(has_selection and not completed and not needs_analysis and not active_download)
        self.queue_retry_button.setEnabled(has_selection and not is_active and not active_download)
        self.queue_priority_button.setEnabled(has_selection and not is_active and not needs_analysis and not self._queue_running)
        self.queue_up_button.setEnabled(bool(idx is not None and idx > 0 and not self._queue_running))
        self.queue_down_button.setEnabled(bool(idx is not None and idx < len(self.queue_tasks) - 1 and not self._queue_running))
        self.queue_remove_button.setEnabled(has_selection and not is_active)
        self.queue_clear_button.setEnabled(bool(self.queue_tasks) and not self._queue_running and not active_download)
        if task is not None:
            self.queue_priority_button.setAccessibleName(
                self._l("Снять приоритет с выбранной задачи") if task.priority
                else self._l("Назначить приоритет выбранной задаче")
            )
            self.queue_table.setAccessibleDescription(self._queue_row_summary(idx))
        else:
            self.queue_table.setAccessibleDescription(self._l("Выберите задачу стрелками. Каждая строка озвучивает книгу, статус и приоритет."))

    def _build_queue_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        text = QLabel(self._l("Добавляйте книги, меняйте порядок и запускайте последовательную загрузку. Дополнительные действия доступны по правому клику."))
        text.setObjectName("secondaryText")
        text.setWordWrap(True)
        layout.addWidget(text)

        controls = QHBoxLayout()
        self.queue_add_url_button = QPushButton(self._l("+ Добавить URL…"))
        self.queue_add_url_button.setProperty("role", "primary")
        self.queue_start_button = QPushButton(self._l("Запустить очередь"))
        self.queue_start_button.setProperty("role", "primary")
        self.queue_stop_button = QPushButton(self._l("Стоп"))
        self.queue_up_button = QPushButton("▲")
        self.queue_down_button = QPushButton("▼")
        self.queue_remove_button = QPushButton(self._l("Удалить"))
        self.queue_remove_button.setProperty("role", "dangerGhost")
        self.queue_actions_button = QPushButton(self._l("Действия ▾"))

        # Compatibility controls remain available to shortcuts/tests but are no longer
        # part of the crowded toolbar.
        self.queue_pause_button = QPushButton(self._l("Пауза текущей"), page)
        self.queue_item_pause_button = QPushButton(self._l("Пауза книги"), page)
        self.queue_resume_button = QPushButton(self._l("Возобновить"), page)
        self.queue_retry_button = QPushButton(self._l("Повторить задачу"), page)
        self.queue_retry_all_button = QPushButton(self._l("Повторить ошибки"), page)
        self.queue_priority_button = QPushButton(self._l("Приоритет"), page)
        self.queue_clear_button = QPushButton(self._l("Очистить очередь"), page)
        for hidden in (self.queue_pause_button, self.queue_item_pause_button, self.queue_resume_button, self.queue_retry_button, self.queue_retry_all_button, self.queue_priority_button, self.queue_clear_button):
            hidden.setVisible(False)

        for widget, name, ident in (
            (self.queue_add_url_button, "Добавить ссылку в очередь", "queue_add_url"),
            (self.queue_start_button, "Запустить очередь или поставить текущую загрузку на паузу", "queue_start"),
            (self.queue_stop_button, "Остановить очередь", "queue_stop"),
            (self.queue_up_button, "Переместить выбранную задачу выше", "queue_up"),
            (self.queue_down_button, "Переместить выбранную задачу ниже", "queue_down"),
            (self.queue_remove_button, "Удалить выбранную задачу", "queue_remove"),
            (self.queue_actions_button, "Групповые действия с очередью", "queue_actions"),
            (self.queue_pause_button, "Поставить текущую загрузку на паузу", "queue_pause"),
            (self.queue_item_pause_button, "Поставить или снять паузу выбранной книги", "queue_item_pause"),
            (self.queue_resume_button, "Возобновить выбранную задачу", "queue_resume"),
            (self.queue_retry_button, "Повторить выбранную задачу", "queue_retry"),
            (self.queue_retry_all_button, "Повторить все задачи с ошибкой", "queue_retry_all"),
            (self.queue_priority_button, "Переключить приоритет выбранной задачи", "queue_priority"),
            (self.queue_clear_button, "Очистить очередь загрузок", "queue_clear"),
        ):
            configure_accessible(widget, name=name, identifier=ident)

        controls.addWidget(self.queue_add_url_button)
        controls.addSpacing(8)
        controls.addWidget(self.queue_start_button)
        controls.addWidget(self.queue_stop_button)
        controls.addStretch(1)
        controls.addWidget(self.queue_up_button)
        controls.addWidget(self.queue_down_button)
        controls.addWidget(self.queue_remove_button)
        controls.addSpacing(8)
        controls.addWidget(self.queue_actions_button)
        layout.addLayout(controls)

        actions_menu = QMenu(self.queue_actions_button)
        self.queue_retry_all_action = actions_menu.addAction(self._l("Повторить ошибки"))
        self.queue_clear_completed_action = actions_menu.addAction(self._l("Очистить завершённые"))
        actions_menu.addSeparator()
        self.queue_clear_all_action = actions_menu.addAction(self._l("Очистить всю очередь"))
        self.queue_retry_all_action.triggered.connect(self.retry_all_failed)
        self.queue_clear_completed_action.triggered.connect(self.clear_completed_queue)
        self.queue_clear_all_action.triggered.connect(self.clear_queue)
        self.queue_actions_button.setMenu(actions_menu)

        self.queue_table = _QueueTableWidget(0, 10)
        self.queue_table.setHorizontalHeaderLabels([self._l(x) for x in ("Обложка", "№", "Книга", "Статус", "Пауза", "Попытки", "Приоритет", "Частей", "Ошибка", "URL")])
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.queue_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.setShowGrid(False)
        self.queue_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.queue_table.horizontalHeader().setResizeContentsPrecision(60)
        self.queue_table.horizontalHeader().setStretchLastSection(True)
        self.queue_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.queue_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_table.customContextMenuRequested.connect(self._show_queue_context_menu)
        configure_accessible(self.queue_table, name=self._l("Очередь"), identifier="queue_table")
        self.queue_results_stack = QStackedWidget(page)
        self.queue_empty_state = QLabel(self._l("Очередь пуста") + "\n" + self._l("Добавьте книгу по URL, чтобы она появилась в очереди."))
        self.queue_empty_state.setObjectName("emptyState")
        self.queue_empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.queue_empty_state.setWordWrap(True)
        configure_accessible(self.queue_empty_state, name=self._l("Очередь пуста"), identifier="queue_empty_state")
        self.queue_results_stack.addWidget(self.queue_empty_state)
        self.queue_results_stack.addWidget(self.queue_table)
        self.queue_results_stack.setCurrentIndex(0)
        layout.addWidget(self.queue_results_stack, 1)

        self.queue_start_button.clicked.connect(self._queue_primary_action)
        self.queue_pause_button.clicked.connect(self.pause_queue_current)
        self.queue_item_pause_button.clicked.connect(self.toggle_queue_item_pause)
        self.queue_resume_button.clicked.connect(self.resume_queue_selected)
        self.queue_stop_button.clicked.connect(self.stop_queue)
        self.queue_retry_button.clicked.connect(self.retry_queue_selected)
        self.queue_retry_all_button.clicked.connect(self.retry_all_failed)
        self.queue_priority_button.clicked.connect(self.toggle_queue_priority)
        self.queue_up_button.clicked.connect(lambda: self.move_queue_selected(-1))
        self.queue_down_button.clicked.connect(lambda: self.move_queue_selected(1))
        self.queue_remove_button.clicked.connect(self.remove_queue_selected)
        self.queue_add_url_button.clicked.connect(self.queue_add_url)
        self.queue_clear_button.clicked.connect(self.clear_queue)
        self.queue_table.currentCellChanged.connect(self._queue_current_cell_changed)
        self.queue_table.rowsReordered.connect(self._queue_drag_reordered)
        self.queue_table.externalUrlsDropped.connect(self._queue_urls_dropped)
        return page

    @Slot()
    def _queue_primary_action(self):
        active = self._download_thread is not None and self._download_thread.isRunning() and self._active_queue_task_id is not None
        if active:
            self.pause_queue_current()
        else:
            self.start_queue()

    def _show_queue_context_menu(self, pos):
        if pos is None:
            current = self.queue_table.currentIndex()
            pos = self.queue_table.visualRect(current).center() if current.isValid() else self.queue_table.viewport().rect().center()
        row = self.queue_table.rowAt(int(pos.y()))
        if row >= 0:
            self.queue_table.setCurrentCell(row, 2)
            self.queue_table.selectRow(row)
        idx = self._selected_queue_index()
        if idx is None:
            return
        task = self.queue_tasks[idx]
        menu = transient_menu(self.queue_table)
        pause_text = self._l("Возобновить книгу") if task.paused or task.status_code == "paused" else self._l("Пауза книги")
        pause_action = menu.addAction(pause_text)
        priority_action = menu.addAction(self._l("Снять приоритет") if task.priority else self._l("Высокий приоритет"))
        retry_action = menu.addAction(self._l("Повторить задачу"))
        menu.addSeparator()
        up_action = menu.addAction(self._l("Переместить выше"))
        down_action = menu.addAction(self._l("Переместить ниже"))
        menu.addSeparator()
        remove_action = menu.addAction(self._l("Удалить"))
        active = task.id == self._active_queue_task_id
        pause_action.setEnabled(not active and task.status_code != "completed" and not task_requires_analysis(task))
        priority_action.setEnabled(not active and not self._queue_running)
        retry_action.setEnabled(not active)
        up_action.setEnabled(idx > 0 and not self._queue_running)
        down_action.setEnabled(idx < len(self.queue_tasks) - 1 and not self._queue_running)
        remove_action.setEnabled(not active)
        chosen = menu.exec(self.queue_table.viewport().mapToGlobal(pos))
        if chosen is pause_action:
            self.toggle_queue_item_pause()
        elif chosen is priority_action:
            self.toggle_queue_priority()
        elif chosen is retry_action:
            self.retry_queue_selected()
        elif chosen is up_action:
            self.move_queue_selected(-1)
        elif chosen is down_action:
            self.move_queue_selected(1)
        elif chosen is remove_action:
            self.remove_queue_selected()

    @Slot()
    def clear_completed_queue(self):
        if self._queue_running or (self._download_thread is not None and self._download_thread.isRunning()):
            self.set_status("Нельзя изменять очередь во время активного скачивания.", assertive=True)
            return
        before = len(self.queue_tasks)
        self.queue_tasks = [task for task in self.queue_tasks if task.status_code != "completed"]
        removed = before - len(self.queue_tasks)
        if removed:
            self._persist_queue()
            self._refresh_queue()
            self.set_status(f"Удалено завершённых задач: {removed}.", assertive=True)

    def _selected_queue_index(self) -> int | None:
        rows = self.queue_table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        return row if 0 <= row < len(self.queue_tasks) else None

    def _active_queue_task(self) -> QueueTask | None:
        if not self._active_queue_task_id:
            return None
        return next((x for x in self.queue_tasks if x.id == self._active_queue_task_id), None)

    def _persist_queue(self):
        self.queue_store.save(self.queue_tasks)

    def _load_queue(self):
        self.queue_tasks = self.queue_store.load()
        self._refresh_queue()

    def _refresh_queue(self):
        if not hasattr(self, "queue_table"):
            return
        selected_id = None
        selection_model = self.queue_table.selectionModel()
        selected_rows = selection_model.selectedRows() if selection_model is not None else []
        if selected_rows:
            old_row = selected_rows[0].row()
            if 0 <= old_row < len(self.queue_tasks):
                selected_id = self.queue_tasks[old_row].id
        self._refreshing_queue = True
        queue_blocker = QSignalBlocker(self.queue_table)
        self.queue_table.setUpdatesEnabled(False)
        try:
            self.queue_table.setRowCount(len(self.queue_tasks))
            if not self.queue_tasks:
                self.queue_table.clearSelection()
                self.queue_table.setCurrentCell(-1, -1)
            headers = ["Обложка", "№", "Книга", "Статус", "Пауза", "Попытки", "Приоритет", "Частей", "Ошибка", "URL"]
            localized_headers = [self._l(value) for value in headers]
            for row, task in enumerate(self.queue_tasks):
                values = [
                    "", row + 1, task.title, self._rt(str(task.status)),
                    self._l("Да") if task.paused else self._l("Нет"), task.attempts,
                    self._l("Да") if task.priority else self._l("Нет"),
                    self._queue_parts_count(task), task.last_error or self._l("нет"), task.url,
                ]
                row_summary = self._queue_row_summary(row)
                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    accessible_text = f"{localized_headers[col]}: {value or self._l('нет')}"
                    item.setData(Qt.ItemDataRole.AccessibleTextRole, accessible_text)
                    item.setData(Qt.ItemDataRole.AccessibleDescriptionRole, row_summary)
                    self.queue_table.setItem(row, col, item)
                cover = cover_cache_bytes(getattr(task.request.book, "cover_cache", None))
                if cover:
                    pix = QPixmap()
                    if pix.loadFromData(cover):
                        self.queue_table.item(row, 0).setIcon(QIcon(pix))
            self.queue_table.resizeColumnsToContents()
        finally:
            self.queue_table.setUpdatesEnabled(True)
            del queue_blocker
            self._refreshing_queue = False
        restore_id = selected_id or self._active_queue_task_id
        if restore_id:
            restore_row = next((i for i, task in enumerate(self.queue_tasks) if task.id == restore_id), None)
            if restore_row is not None:
                focus_table_row(self.queue_table, restore_row, column=2, focus=False)
        if hasattr(self, "queue_results_stack"):
            self.queue_results_stack.setCurrentIndex(1 if self.queue_tasks else 0)
        active = self._download_thread is not None and self._download_thread.isRunning()
        active_queue_download = bool(active and self._active_queue_task_id is not None)
        self.queue_start_button.setText(self._l("Пауза") if active_queue_download else self._l("Запустить очередь"))
        self.queue_start_button.setAccessibleName(self._l("Поставить текущую книгу на паузу") if active_queue_download else self._l("Запустить очередь загрузок"))
        self.queue_start_button.setEnabled(active_queue_download or (bool(self.queue_tasks) and not active and not self._queue_running))
        self.queue_pause_button.setEnabled(active_queue_download)
        self.queue_stop_button.setEnabled(self._queue_running or self._active_queue_task_id is not None)
        self.queue_retry_all_action.setEnabled(any(t.status_code == "error" and not task_requires_analysis(t) for t in self.queue_tasks) and not active)
        self.queue_clear_completed_action.setEnabled(any(t.status_code == "completed" for t in self.queue_tasks) and not active and not self._queue_running)
        self.queue_clear_all_action.setEnabled(bool(self.queue_tasks) and not active and not self._queue_running)
        self.queue_actions_button.setEnabled(bool(self.queue_tasks) and not active_queue_download)
        self._update_queue_action_states()

    def add_current_to_queue(self):
        self._add_current_to_queue_mode("selected")

    def add_current_full_mp3_to_queue(self):
        self._add_current_to_queue_mode("full_mp3")

    def _add_current_to_queue_mode(self, download_mode: str):
        if self.current_book is None:
            self.set_status("Сначала проанализируйте книгу.", assertive=True)
            return
        if download_mode == "full_mp3":
            if not self._book_supports_full_mp3(self.current_book):
                self.set_status("У книги несколько исходных файлов. Используйте очередь по частям.", assertive=True)
                return
            selected = [int(track.index) for track in self.current_book.tracks]
        else:
            selected = self.track_model.selected_indices()
        try:
            request = build_download_request(self.current_book, self._live_download_settings(), selected)
        except Exception as exc:
            self.set_status(str(exc), assertive=True)
            return
        duplicate = next((x for x in self.queue_tasks if _same_supported_url(x.url, request.book.url) and x.status_code not in {"completed", "cancelled"}), None)
        if duplicate is not None:
            self.set_status("Эта книга уже есть в активной очереди.", assertive=True)
            return
        task = self.queue_store.new_task(request, download_mode=download_mode)
        self.queue_tasks.append(task)
        self._persist_queue()
        self._refresh_queue()
        self.tabs.setCurrentIndex(self.TAB_QUEUE)
        focus_table_row(self.queue_table, len(self.queue_tasks) - 1, column=1, focus=True)
        self.set_status(f"Добавлено в очередь: {task.title}", assertive=True)
        self._play_event_sound("queue_item_added")

    @Slot()
    def queue_add_url(self):
        if self._analysis_thread is not None and self._analysis_thread.isRunning():
            self.set_status("Дождитесь завершения текущего анализа.", assertive=True)
            return
        url, ok = QInputDialog.getText(self, self._l("Добавить URL в очередь"), self._l("Ссылка на книгу:"))
        url = str(url or "").strip()
        if not ok or not url:
            return
        if not valid_site_url(url):
            self._show_message(QMessageBox.Icon.Warning, "Неподдерживаемая ссылка", "Поддерживаются audioknigi.com.ua, knigavuhe.org и poleknig.com.")
            return
        duplicate = next((task for task in self.queue_tasks if _same_supported_url(task.url, url) and task.status_code not in {"completed", "cancelled"}), None)
        if duplicate is not None:
            self.set_status("Эта книга уже есть в активной очереди.", assertive=True)
            return
        self._queue_after_analysis = True
        self._download_after_analysis = False
        self.book_url_edit.setText(url)
        self.set_ui_mode("advanced", persist=False)
        self.tabs.setCurrentIndex(self.TAB_BOOK)
        self.start_analysis()

    @Slot(object)
    def _queue_urls_dropped(self, values):
        urls = []
        for candidate in self._normalize_drop_values(values):
            if valid_site_url(candidate) and candidate not in urls:
                urls.append(candidate)
        if not urls:
            self.set_status("Нет поддерживаемых ссылок для очереди.", assertive=True)
            return
        # Queue URL analysis is sequential to avoid parallel browser workers. The first is started now;
        # the rest are retained and fed one-by-one after analysis.
        self._pending_queue_urls = list(urls)
        self._queue_next_dropped_url()

    def _queue_next_dropped_url(self):
        pending = list(getattr(self, "_pending_queue_urls", []) or [])
        if not pending:
            return
        if self._analysis_thread is not None and self._analysis_thread.isRunning():
            return
        url = pending.pop(0)
        self._pending_queue_urls = pending
        duplicate = next((task for task in self.queue_tasks if _same_supported_url(task.url, url) and task.status_code not in {"completed", "cancelled"}), None)
        if duplicate is not None:
            QTimer.singleShot(0, self._queue_next_dropped_url)
            return
        self._queue_after_analysis = True
        self._download_after_analysis = False
        self.book_url_edit.setText(url)
        self.start_analysis()

    @Slot(int, int)
    def _queue_drag_reordered(self, source_row: int, target_row: int):
        if self._queue_running or self._refreshing_queue:
            return
        if not (0 <= source_row < len(self.queue_tasks) and 0 <= target_row < len(self.queue_tasks)):
            return
        task = self.queue_tasks.pop(source_row)
        self.queue_tasks.insert(target_row, task)
        self._persist_queue()
        self._refresh_queue()
        focus_table_row(self.queue_table, target_row, column=2, focus=True)

    @Slot()
    def toggle_queue_item_pause(self):
        idx = self._selected_queue_index()
        if idx is None:
            return
        task = self.queue_tasks[idx]
        if task.id == self._active_queue_task_id:
            self.pause_queue_current()
            return
        if task.status_code == "completed":
            return
        if task_requires_analysis(task):
            self.set_status("Эту импортированную задачу нужно заново проанализировать и добавить в очередь.", assertive=True)
            return
        task.paused = not task.paused
        if task.paused:
            task.status = "На паузе"
            if task.status_code in {"pending", "retry", "interrupted", "error"}:
                task.status_code = "paused"
        else:
            task.status = "Ожидает"
            task.status_code = "pending"
        self._persist_queue()
        self._refresh_queue()
        focus_table_row(self.queue_table, idx, column=2, focus=True)
        self._play_event_sound("download_paused" if task.paused else "download_resumed")

    @Slot()
    def retry_all_failed(self):
        changed = 0
        for task in self.queue_tasks:
            if task.status_code == "error" and not task_requires_analysis(task):
                task.status = "Ожидает повтор"
                task.status_code = "retry"
                task.last_error = ""
                task.paused = False
                changed += 1
        if changed:
            self._persist_queue()
            self._refresh_queue()
            self.set_status(f"На повтор поставлено задач: {changed}.", assertive=True)

    @Slot()
    def clear_queue(self):
        if self._queue_running or (self._download_thread is not None and self._download_thread.isRunning()):
            self.set_status("Нельзя очищать очередь во время активного скачивания.", assertive=True)
            return
        if not self.queue_tasks:
            return
        answer = self._ask_yes_no(
            "Очистить очередь",
            "Удалить все задачи из очереди? Загруженные аудиофайлы останутся на диске.",
            default_yes=False,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.queue_table.clearSelection()
        self.queue_table.setCurrentCell(-1, -1)
        self.queue_tasks.clear()
        self._persist_queue()
        self._refresh_queue()
        self.set_status("Очередь очищена.", assertive=True)

    @Slot()
    def start_queue(self):
        if self._analysis_thread is not None and self._analysis_thread.isRunning():
            self.set_status("Дождитесь завершения анализа книги.", assertive=True)
            return
        if self._download_thread is not None and self._download_thread.isRunning():
            self.set_status("Сейчас уже выполняется скачивание.", assertive=True)
            return
        self._queue_running = True
        self._queue_stop_requested = False
        self._play_event_sound("queue_started")
        self._queue_pausing = False
        self._start_next_queue_task()

    def _start_next_queue_task(self):
        if not self._queue_running or self._queue_stop_requested:
            return
        idx = next_runnable_index(self.queue_tasks)
        if idx is None:
            self._queue_running = False
            self._active_queue_task_id = None
            self._persist_queue()
            self._refresh_queue()
            unresolved = [
                task for task in self.queue_tasks
                if task.status_code not in {"completed", "cancelled"}
            ]
            if unresolved:
                paused = sum(1 for task in unresolved if task.paused or task.status_code == "paused")
                errors = sum(1 for task in unresolved if task.status_code == "error")
                reanalysis = sum(1 for task in unresolved if task_requires_analysis(task))
                details = []
                if paused:
                    details.append(tr(self.language, "queue_unresolved_paused", count=paused))
                if errors:
                    details.append(tr(self.language, "queue_unresolved_errors", count=errors))
                if reanalysis:
                    details.append(tr(self.language, "queue_unresolved_reanalysis", count=reanalysis))
                detail_text = ", ".join(details) or tr(
                    self.language, "queue_unresolved_actions", count=len(unresolved)
                )
                message = tr(self.language, "queue_stopped_unresolved", details=detail_text)
                self.set_status(message, assertive=True)
                self._play_event_sound("attention")
                self._notify_tray_if_hidden(message)
            else:
                self.set_status("Очередь завершена.", assertive=True)
                self._play_event_sound("queue_complete")
                self._notify_tray_if_hidden(self._l("Очередь завершена."))
            return
        task = self.queue_tasks[idx]
        task.status = "Скачивается"
        task.status_code = "running"
        task.paused = False
        task.attempts += 1
        task.last_error = ""
        self._active_queue_task_id = task.id
        self._persist_queue()
        self._refresh_queue()
        self.queue_table.selectRow(idx)
        self.tabs.setCurrentIndex(self.TAB_QUEUE)
        self._launch_download(
            task.request, self._live_download_settings(), from_queue=True, mode=task.download_mode
        )

    @Slot()
    def pause_queue_current(self):
        task = self._active_queue_task()
        if task is None or self._download_cancel is None:
            self.set_status("В очереди сейчас ничего не скачивается.")
            return
        self._queue_pausing = True
        self._queue_running = False
        task.paused = True
        task.status = "Пауза…"
        self._persist_queue()
        self._refresh_queue()
        self._request_download_cancel()
        self.set_status("Ставлю текущую книгу на паузу…", assertive=True)

    @Slot()
    def resume_queue_selected(self):
        idx = self._selected_queue_index()
        if idx is None:
            self.set_status("Выберите задачу очереди.")
            return
        task = self.queue_tasks[idx]
        if task.status_code == "completed":
            self.set_status("Эта задача уже завершена.")
            return
        if task_requires_analysis(task):
            self.set_status("Эту импортированную задачу нельзя возобновить без повторного анализа книги.", assertive=True)
            return
        task.paused = False
        task.status = "Ожидает"
        task.status_code = "pending"
        task.last_error = ""
        self._persist_queue()
        self._refresh_queue()
        if self._download_thread is None or not self._download_thread.isRunning():
            self.start_queue()

    @Slot()
    def stop_queue(self):
        self._queue_stop_requested = True
        self._queue_running = False
        task = self._active_queue_task()
        if task is not None and self._download_cancel is not None:
            task.status = "Останавливается…"
            self._persist_queue()
            self._refresh_queue()
            self._request_download_cancel()
        else:
            self._active_queue_task_id = None
            self._refresh_queue()
        self.set_status("Очередь остановлена. Незавершённую задачу можно возобновить.", assertive=True)

    @Slot()
    def retry_queue_selected(self):
        idx = self._selected_queue_index()
        if idx is None:
            return
        task = self.queue_tasks[idx]
        if task.id == self._active_queue_task_id:
            return
        if task_requires_analysis(task):
            if self._analysis_thread is not None and self._analysis_thread.isRunning():
                self.set_status("Дождитесь завершения текущего анализа.", assertive=True)
                return
            self._queue_reanalyze_task_id = task.id
            self._queue_after_analysis = False
            self._download_after_analysis = False
            self.book_url_edit.setText(task.url)
            self.tabs.setCurrentIndex(self.TAB_BOOK)
            self.set_status("Повторно анализирую импортированную задачу…", assertive=True)
            self.start_analysis()
            return
        task.status = "Ожидает повтор"
        task.status_code = "retry"
        task.paused = False
        task.last_error = ""
        self._persist_queue()
        self._refresh_queue()
        self.queue_table.selectRow(idx)

    @Slot()
    def toggle_queue_priority(self):
        idx = self._selected_queue_index()
        if idx is None:
            return
        task = self.queue_tasks[idx]
        if task.id == self._active_queue_task_id:
            return
        if task_requires_analysis(task):
            self.set_status("Приоритет недоступен: сначала заново проанализируйте импортированную книгу.", assertive=True)
            return
        task.priority = not task.priority
        self._persist_queue()
        self._refresh_queue()
        self.queue_table.selectRow(idx)

    def move_queue_selected(self, delta: int):
        idx = self._selected_queue_index()
        if idx is None or self._queue_running:
            return
        new_idx = idx + int(delta)
        if not (0 <= new_idx < len(self.queue_tasks)):
            return
        self.queue_tasks[idx], self.queue_tasks[new_idx] = self.queue_tasks[new_idx], self.queue_tasks[idx]
        self._persist_queue()
        self._refresh_queue()
        self.queue_table.selectRow(new_idx)

    @Slot()
    def remove_queue_selected(self):
        idx = self._selected_queue_index()
        if idx is None:
            return
        task = self.queue_tasks[idx]
        if task.id == self._active_queue_task_id:
            self.set_status("Сначала остановите текущую задачу.", assertive=True)
            return
        del self.queue_tasks[idx]
        self._persist_queue()
        self._refresh_queue()
        if self.queue_tasks:
            focus_table_row(self.queue_table, min(idx, len(self.queue_tasks) - 1), column=2, focus=True)
        else:
            self.queue_add_url_button.setFocus(Qt.FocusReason.OtherFocusReason)
        self.set_status("Задача удалена из очереди.")


__all__ = ["QueueUiMixin"]
