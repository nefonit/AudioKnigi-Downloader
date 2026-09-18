from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout

from .accessibility import configure_accessible


class BlockingOperationDialog(QDialog):
    """Application-modal progress window used by the Easy UI.

    The dialog is shown non-blockingly (``show()`` rather than ``exec()``), so
    worker signals continue to be delivered by the main Qt event loop while the
    main window remains unavailable.  Closing/Escape requests cancellation but
    cannot dismiss the dialog until the owning operation really finishes.
    """

    cancelRequested = Signal()

    def __init__(
        self,
        parent,
        *,
        title: str,
        message: str,
        cancel_text: str,
        cancelling_text: str,
        indeterminate: bool = False,
    ) -> None:
        super().__init__(parent)
        self._allow_close = False
        self._cancel_requested = False
        self._cancelling_text = str(cancelling_text or cancel_text)
        self.setWindowTitle(str(title))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        self.message_label = QLabel(str(message or ""), self)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        self.progress = QProgressBar(self)
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.cancel_button = QPushButton(str(cancel_text), self)
        self.cancel_button.clicked.connect(self._request_cancel)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

        configure_accessible(self, name=str(title), description=str(message or ""), identifier="blocking_operation_dialog")
        configure_accessible(self.progress, name=str(title), description=str(message or ""), identifier="blocking_operation_progress")
        configure_accessible(self.cancel_button, name=str(cancel_text), identifier="blocking_operation_cancel")
        self.set_progress(None if indeterminate else 0, message=message, indeterminate=indeterminate)

    def _request_cancel(self) -> None:
        if self._cancel_requested:
            return
        self._cancel_requested = True
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText(self._cancelling_text)
        self.cancelRequested.emit()

    def set_progress(self, value: int | float | None, *, message: str | None = None, indeterminate: bool = False) -> None:
        if message is not None:
            text = str(message)
            self.message_label.setText(text)
            self.message_label.setAccessibleDescription(text)
            self.progress.setAccessibleDescription(text)
        if indeterminate or value is None:
            self.progress.setRange(0, 0)
            self.progress.setTextVisible(False)
            return
        percent = max(0, min(100, int(round(float(value)))))
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        self.progress.setValue(percent)

    def mark_cancelling(self) -> None:
        self._request_cancel()

    def finish(self) -> None:
        self._allow_close = True
        self.accept()

    def reject(self) -> None:
        if self._allow_close:
            super().reject()
            return
        self._request_cancel()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close:
            event.accept()
            return
        self._request_cancel()
        event.ignore()


__all__ = ["BlockingOperationDialog"]
