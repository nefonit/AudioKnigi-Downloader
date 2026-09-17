from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QWidget


def transient_menu(parent: QWidget) -> QMenu:
    """Create a one-shot context menu that releases its Qt children on close."""
    menu = QMenu(parent)
    menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
    return menu


__all__ = ["transient_menu"]
