from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ..brand import DISPLAY_NAME
from ..core import resource_path
from ..i18n import localize_runtime_text, ui_text


class QtTrayController(QObject):
    """Qt-native system tray integration with no legacy GUI dependency."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.icon: QSystemTrayIcon | None = None
        self.menu: QMenu | None = None
        self.show_action: QAction | None = None
        self.hide_action: QAction | None = None
        self.player_action: QAction | None = None
        self.queue_action: QAction | None = None
        self.exit_action: QAction | None = None

    @property
    def available(self) -> bool:
        try:
            return bool(QSystemTrayIcon.isSystemTrayAvailable())
        except Exception:
            return False

    def _l(self, text: str) -> str:
        language = str(getattr(self.window, "language", "ru") or "ru")
        return ui_text(language, text)

    def start(self) -> bool:
        if not self.available:
            return False
        if self.icon is not None:
            return True

        icon = QSystemTrayIcon(self.window)
        app_icon = self.window.windowIcon()
        if app_icon.isNull():
            for name in ("app_icon.png", "app_icon_256.png", "app_icon.ico"):
                path = resource_path("assets", name)
                if path.exists():
                    app_icon = QIcon(str(path))
                    if not app_icon.isNull():
                        break
        icon.setIcon(app_icon)
        icon.setToolTip(DISPLAY_NAME)

        menu = QMenu(self.window)
        self.show_action = QAction(self._l("Показать окно"), menu)
        self.hide_action = QAction(self._l("Скрыть в трей"), menu)
        self.player_action = QAction(self._l("Открыть плеер"), menu)
        self.queue_action = QAction(self._l("Открыть очередь"), menu)
        self.exit_action = QAction(self._l("Выход"), menu)

        self.show_action.triggered.connect(self.window.restore_from_tray)
        self.hide_action.triggered.connect(self.window.hide_to_tray)
        self.player_action.triggered.connect(self.window.show_player_from_tray)
        self.queue_action.triggered.connect(self.window.show_queue_from_tray)
        self.exit_action.triggered.connect(self.window.request_exit)

        menu.addAction(self.show_action)
        menu.addAction(self.hide_action)
        menu.addSeparator()
        menu.addAction(self.player_action)
        menu.addAction(self.queue_action)
        menu.addSeparator()
        menu.addAction(self.exit_action)
        icon.setContextMenu(menu)
        icon.activated.connect(self._activated)

        self.icon = icon
        self.menu = menu
        self.set_window_visible(self.window.isVisible())
        icon.show()
        return True

    def _activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.window.restore_from_tray()

    def set_window_visible(self, visible: bool):
        if self.show_action is not None:
            self.show_action.setEnabled(not bool(visible))
        if self.hide_action is not None:
            self.hide_action.setEnabled(bool(visible))

    def notify(self, message: str, *, title: str = DISPLAY_NAME, timeout_ms: int = 5000) -> bool:
        if self.icon is None or not self.icon.isVisible():
            return False
        try:
            self.icon.showMessage(
                str(title or DISPLAY_NAME),
                localize_runtime_text(str(getattr(self.window, "language", "ru") or "ru"), str(message or "")),
                QSystemTrayIcon.MessageIcon.Information,
                max(1000, int(timeout_ms)),
            )
            return True
        except Exception:
            return False

    def shutdown(self):
        if self.icon is not None:
            try:
                self.icon.hide()
                self.icon.setContextMenu(None)
            except Exception:
                pass
            self.icon.deleteLater()
        if self.menu is not None:
            try:
                self.menu.deleteLater()
            except RuntimeError:
                pass
        self.icon = None
        self.menu = None
        self.show_action = None
        self.hide_action = None
        self.player_action = None
        self.queue_action = None
        self.exit_action = None


__all__ = ["QtTrayController"]
