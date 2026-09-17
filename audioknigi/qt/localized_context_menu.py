from __future__ import annotations

from collections.abc import Callable
import weakref

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QLineEdit, QMenu, QPlainTextEdit, QTextEdit, QWidget

from ..i18n import ui_text


_SUPPORTED_EDITORS = (QLineEdit, QPlainTextEdit, QTextEdit)


def _language(language_getter: Callable[[], str] | None) -> str:
    try:
        value = str(language_getter() if language_getter is not None else "ru").strip().lower()
    except Exception:
        value = "ru"
    return value if value in {"ru", "uk", "de", "en"} else "ru"


def _line_edit_selection_allowed(widget: QLineEdit) -> bool:
    try:
        return widget.echoMode() == QLineEdit.EchoMode.Normal
    except Exception:
        return True


def _has_selection(widget: QWidget) -> bool:
    if isinstance(widget, QLineEdit):
        return bool(widget.hasSelectedText())
    if isinstance(widget, (QPlainTextEdit, QTextEdit)):
        return bool(widget.textCursor().hasSelection())
    return False


def _is_read_only(widget: QWidget) -> bool:
    try:
        return bool(widget.isReadOnly())
    except Exception:
        return False


def _can_undo(widget: QWidget) -> bool:
    try:
        if isinstance(widget, QLineEdit):
            return bool(widget.isUndoAvailable())
        if isinstance(widget, (QPlainTextEdit, QTextEdit)):
            return bool(widget.document().isUndoAvailable())
    except Exception:
        pass
    return False


def _can_redo(widget: QWidget) -> bool:
    try:
        if isinstance(widget, QLineEdit):
            return bool(widget.isRedoAvailable())
        if isinstance(widget, (QPlainTextEdit, QTextEdit)):
            return bool(widget.document().isRedoAvailable())
    except Exception:
        pass
    return False


def _can_paste(widget: QWidget) -> bool:
    if _is_read_only(widget):
        return False
    try:
        mime = QApplication.clipboard().mimeData()
        return bool(mime is not None and mime.hasText())
    except Exception:
        return True


def _delete_selection(widget: QWidget) -> None:
    if _is_read_only(widget) or not _has_selection(widget):
        return
    if isinstance(widget, QLineEdit):
        # Inserting an empty string replaces the selected range without relying
        # on the binding-specific ``del_`` method name.
        widget.insert("")
        return
    if isinstance(widget, (QPlainTextEdit, QTextEdit)):
        cursor = widget.textCursor()
        cursor.insertText("")
        widget.setTextCursor(cursor)


def _global_menu_position(widget: QWidget, pos: QPoint):
    try:
        if pos.x() < 0 or pos.y() < 0:
            return QCursor.pos()
        viewport = widget.viewport() if isinstance(widget, (QPlainTextEdit, QTextEdit)) else widget
        return viewport.mapToGlobal(pos)
    except Exception:
        return QCursor.pos()


def show_localized_text_context_menu(
    widget: QWidget,
    pos: QPoint,
    language_getter: Callable[[], str] | None = None,
) -> None:
    """Show a predictable application-language context menu for text editors.

    Qt's built-in editor menu follows the bundled Qt translation catalogue.  A
    compact PyInstaller build may not include those catalogues, leaving Undo /
    Cut / Copy / Paste in English even while AudioKnigi is Russian or Ukrainian.
    Building the seven standard actions ourselves keeps the menu in the selected
    application language and preserves the editor's native operations.
    """

    if not isinstance(widget, _SUPPORTED_EDITORS):
        return
    language = _language(language_getter)
    menu = QMenu(widget)
    menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

    undo_action = menu.addAction(ui_text(language, "Отменить"))
    redo_action = menu.addAction(ui_text(language, "Повторить"))
    undo_action.setEnabled(not _is_read_only(widget) and _can_undo(widget))
    redo_action.setEnabled(not _is_read_only(widget) and _can_redo(widget))
    undo_action.triggered.connect(widget.undo)
    redo_action.triggered.connect(widget.redo)

    menu.addSeparator()
    selection = _has_selection(widget)
    copy_allowed = selection and (not isinstance(widget, QLineEdit) or _line_edit_selection_allowed(widget))
    cut_action = menu.addAction(ui_text(language, "Вырезать"))
    copy_action = menu.addAction(ui_text(language, "Копировать"))
    paste_action = menu.addAction(ui_text(language, "Вставить"))
    delete_action = menu.addAction(ui_text(language, "Удалить текст"))
    cut_action.setEnabled(not _is_read_only(widget) and copy_allowed)
    copy_action.setEnabled(copy_allowed)
    paste_action.setEnabled(_can_paste(widget))
    delete_action.setEnabled(not _is_read_only(widget) and selection)
    cut_action.triggered.connect(widget.cut)
    copy_action.triggered.connect(widget.copy)
    paste_action.triggered.connect(widget.paste)
    delete_action.triggered.connect(lambda: _delete_selection(widget))

    menu.addSeparator()
    select_all_action = menu.addAction(ui_text(language, "Выделить всё"))
    try:
        select_all_action.setEnabled(bool(widget.text()) if isinstance(widget, QLineEdit) else bool(widget.toPlainText()))
    except Exception:
        select_all_action.setEnabled(True)
    select_all_action.triggered.connect(widget.selectAll)

    menu.exec(_global_menu_position(widget, pos))


def install_localized_text_context_menu(
    widget: QWidget,
    language_getter: Callable[[], str] | None = None,
) -> None:
    if not isinstance(widget, _SUPPORTED_EDITORS):
        return
    if bool(widget.property("audioknigi_localized_context_menu")):
        return
    widget.setProperty("audioknigi_localized_context_menu", True)
    widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    widget_ref = weakref.ref(widget)

    def _show_menu(pos: QPoint) -> None:
        current = widget_ref()
        if current is not None:
            show_localized_text_context_menu(current, pos, language_getter)

    widget.customContextMenuRequested.connect(_show_menu)


__all__ = ["install_localized_text_context_menu", "show_localized_text_context_menu"]
