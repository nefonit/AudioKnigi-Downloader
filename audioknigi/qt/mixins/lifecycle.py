from __future__ import annotations

import os
import sys
import time

from PySide6.QtCore import QByteArray, QEvent, Slot, Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QMessageBox
from ...core import SETTINGS_FILE, save_json
from ...logging_utils import app_logger
from ..accessibility import focus_table_row

_EXIT_GRACE_SECONDS = 5.0
_EXIT_FINAL_WAIT_MS = 750
_EXIT_POLL_MS = 150

class LifecycleUiMixin:
    """Lifecycle behavior for :class:`AudioKnigiQtWindow`."""

    def _restore_window_geometry(self):
        encoded = str(self.settings.get("geometry", "") or "").strip()
        if not encoded:
            return
        try:
            data = QByteArray.fromBase64(encoded.encode("ascii"))
            if not data.isEmpty():
                self.restoreGeometry(data)
        except Exception:
            pass

    def _save_window_geometry(self):
        try:
            self.settings["geometry"] = bytes(self.saveGeometry().toBase64()).decode("ascii")
        except Exception:
            pass

    def _persist_exit_state_best_effort(self) -> None:
        """Persist small user state before normal or emergency process exit."""
        self._save_window_geometry()
        try:
            self.settings.update(self._settings_from_ui())
        except Exception:
            pass
        try:
            save_json(SETTINGS_FILE, self.settings)
        except Exception:
            app_logger.debug("Could not persist settings during exit", exc_info=True)
        controller = getattr(self, "player_controller", None)
        if controller is not None:
            try:
                controller.save_position(force=True)
            except Exception:
                app_logger.debug("Could not persist player position during exit", exc_info=True)

    def _tray_available(self) -> bool:
        return bool(self.tray_controller is not None and self.tray_controller.available)

    def _long_operation_active(self) -> bool:
        downloading = self._download_thread is not None and self._download_thread.isRunning()
        return bool(downloading or self._queue_running or self._active_queue_task_id is not None)

    def _should_auto_tray(self) -> bool:
        check = getattr(self, "minimize_to_tray_check", None)
        return bool(check is not None and check.isChecked() and self._tray_available() and self._long_operation_active())

    @Slot()
    def hide_to_tray(self):
        if not self._tray_available():
            self.set_status("Системный трей недоступен в этой среде.", assertive=True)
            return False
        if not self.isMinimized():
            self._restore_was_maximized = self.isMaximized()
        self.hide()
        self.tray_controller.set_window_visible(False)
        if not self._tray_notice_shown:
            self.tray_controller.notify("Программа продолжает работать в системном трее.")
            self._tray_notice_shown = True
        return True

    @Slot()
    def restore_from_tray(self):
        if self._restore_was_maximized:
            self.showMaximized()
        else:
            self.showNormal()
        self.raise_()
        self.activateWindow()
        self.tray_controller.set_window_visible(True)
        self.set_status("Окно восстановлено из системного трея.")

    @Slot()
    def show_player_from_tray(self):
        self.restore_from_tray()
        self.tabs.setCurrentIndex(self.TAB_PLAYER)
        self.player_play_button.setFocus(Qt.FocusReason.OtherFocusReason)

    @Slot()
    def show_queue_from_tray(self):
        self.restore_from_tray()
        self.tabs.setCurrentIndex(self.TAB_QUEUE)
        if self.queue_tasks:
            row = self._selected_queue_index()
            focus_table_row(self.queue_table, 0 if row is None else row, column=1, focus=True)
        else:
            self.queue_table.setFocus(Qt.FocusReason.OtherFocusReason)

    @Slot()
    def request_exit(self):
        self._exit_requested = True
        self._cancel_all_workers_for_exit()
        if not self.isVisible():
            self.restore_from_tray()
        self.close()

    def _notify_tray_if_hidden(self, message: str):
        if not self.isVisible() and self._tray_available():
            self.tray_controller.notify(message)

    def _hide_if_still_minimized(self):
        if self.isMinimized() and self._should_auto_tray():
            self.hide_to_tray()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized() and self._should_auto_tray():
            try:
                old_state = event.oldState()
                self._restore_was_maximized = bool(old_state & Qt.WindowState.WindowMaximized)
            except Exception:
                pass
            QTimer.singleShot(0, self._hide_if_still_minimized)
        super().changeEvent(event)

    def _cancel_all_workers_for_exit(self):
        if self._active_queue_task_id is not None:
            self._queue_stop_requested = True
            self._queue_running = False
        self._request_download_cancel()
        if self._analysis_cancel is not None:
            self._analysis_cancel.set()
        if self._search_cancel is not None:
            self._search_cancel.set()
        if self._abs_thread is not None and self._thread_is_running(self._abs_thread):
            try:
                self._abs_thread.requestInterruption()
            except RuntimeError:
                pass

    @staticmethod
    def _thread_is_running(thread) -> bool:
        if thread is None:
            return False
        try:
            return bool(thread.isRunning())
        except RuntimeError:
            return False

    def _running_exit_threads(self):
        return tuple(
            thread
            for thread in (self._download_thread, self._analysis_thread, self._search_thread, self._abs_thread)
            if self._thread_is_running(thread)
        )

    def _force_stop_workers_for_exit(self, threads) -> bool:
        """Final cooperative wait before the process-level emergency exit.

        QThread.terminate() can kill Python/PySide while the GIL or a native
        mutex is held.  Request interruption once more and wait briefly; if a
        blocked worker still cannot exit, closeEvent uses os._exit(0) rather
        than corrupting the live interpreter heap.
        """
        for thread in tuple(threads):
            try:
                thread.requestInterruption()
            except RuntimeError:
                pass
        for thread in tuple(threads):
            try:
                thread.wait(_EXIT_FINAL_WAIT_MS)
            except RuntimeError:
                pass
        return bool(self._running_exit_threads())

    def _schedule_exit_poll(self) -> None:
        if self._exit_poll_scheduled:
            return
        self._exit_poll_scheduled = True
        QTimer.singleShot(_EXIT_POLL_MS, self._poll_deferred_exit)

    def _poll_deferred_exit(self) -> None:
        self._exit_poll_scheduled = False
        if self._exit_requested:
            self.close()

    def _begin_deferred_exit(self):
        self._exit_requested = True
        self._exit_deadline = time.monotonic() + _EXIT_GRACE_SECONDS
        self._cancel_all_workers_for_exit()
        self.hide()
        try:
            self.tray_controller.shutdown()
        except Exception:
            app_logger.debug("Could not shut down tray during deferred exit", exc_info=True)
        self._schedule_exit_poll()

    def closeEvent(self, event: QCloseEvent):
        if self._exit_requested:
            # A previous close request already asked active workers to stop.
            # Poll only for a bounded grace period; a permanently blocked worker
            # must not leave an invisible process alive forever.
            running_threads = self._running_exit_threads()
            if running_threads:
                deadline = self._exit_deadline
                if deadline is None:
                    deadline = time.monotonic() + _EXIT_GRACE_SECONDS
                    self._exit_deadline = deadline
                if time.monotonic() < deadline:
                    event.ignore()
                    self.hide()
                    self._schedule_exit_poll()
                    return
                still_running = self._force_stop_workers_for_exit(running_threads)
                if still_running:
                    self._persist_exit_state_best_effort()
                    # Last-resort hard exit: QThread termination itself can fail
                    # when the OS blocks inside an uninterruptible I/O call.
                    # The user already explicitly chose to cancel work and exit.
                    try:
                        sys.stderr.write(
                            "AudioKnigi: background worker did not stop after exit timeout; forcing process exit.\n"
                        )
                        sys.stderr.flush()
                    except Exception:
                        pass
                    os._exit(0)
        if self._thread_is_running(self._download_thread):
            answer = self._ask_yes_no(
                "Скачивание выполняется",
                "Скачивание ещё выполняется. Отменить его и закрыть программу после остановки?",
                default_yes=False,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._begin_deferred_exit()
            else:
                self._exit_requested = False
                self._exit_deadline = None
            event.ignore()
            return
        if self._thread_is_running(self._analysis_thread):
            answer = self._ask_yes_no(
                "Анализ выполняется",
                "Анализ книги ещё выполняется. Отменить его и закрыть программу после завершения?",
                default_yes=False,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._begin_deferred_exit()
            else:
                self._exit_requested = False
                self._exit_deadline = None
            event.ignore()
            return
        if self._thread_is_running(self._search_thread):
            answer = self._ask_yes_no(
                "Поиск выполняется",
                "Поиск ещё выполняется. Отменить его и закрыть программу после остановки?",
                default_yes=False,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._begin_deferred_exit()
            else:
                self._exit_requested = False
                self._exit_deadline = None
            event.ignore()
            return
        self._persist_exit_state_best_effort()
        app = QApplication.instance()
        media_filter = getattr(self, "_media_key_filter", None)
        if media_filter is not None:
            try:
                media_filter.shutdown()
            except Exception:
                pass
            if app is not None:
                try:
                    app.removeNativeEventFilter(media_filter)
                except Exception:
                    pass
        if self.player_controller is not None:
            self.player_controller.shutdown()
        if self.event_sound_manager is not None:
            self.event_sound_manager.shutdown()
        if self.tray_controller is not None:
            self.tray_controller.shutdown()
        event.accept()


__all__ = ["LifecycleUiMixin"]
