from __future__ import annotations

from PySide6.QtCore import QEvent, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPalette, QPen
from PySide6.QtWidgets import QWidget


class CircularSearchProgress(QWidget):
    """Compact circular progress indicator for multi-provider search.

    The numeric value reflects completed search stages/providers.  A small rotating
    activity arc continues moving while a slow provider is still working, so the
    interface never looks frozen even when the percentage is temporarily unchanged.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0
        self._angle = 0
        self._active = False
        self._sync_size_to_font()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._animate)

    def _sync_size_to_font(self) -> None:
        metrics = QFontMetrics(self.font())
        side = max(76, metrics.horizontalAdvance("100%") + 36, metrics.height() + 40)
        self.setFixedSize(side, side)

    def changeEvent(self, event) -> None:
        if event.type() == QEvent.Type.FontChange:
            self._sync_size_to_font()
        super().changeEvent(event)

    def progress(self) -> int:
        return self._progress

    def setProgress(self, value: int) -> None:
        self._progress = max(0, min(100, int(value)))
        self.update()

    def start(self, value: int = 5) -> None:
        self._active = True
        self.setProgress(value)
        self.show()
        if not self._timer.isActive():
            self._timer.start()

    def stop(self, value: int = 100) -> None:
        self.setProgress(value)
        self._active = False
        self._timer.stop()
        self.update()

    def reset(self) -> None:
        self._active = False
        self._timer.stop()
        self._angle = 0
        self.setProgress(0)
        self.hide()

    def _animate(self) -> None:
        if not self.isVisible():
            self._timer.stop()
            return
        self._angle = (self._angle + 14) % 360
        self.update()

    def hideEvent(self, event) -> None:
        # A hidden progress widget must not keep its 80 ms animation timer alive.
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._active and self._progress < 100 and not self._timer.isActive():
            self._timer.start()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        side = min(self.width(), self.height())
        scale = max(1.0, side / 76.0)
        margin = 7.0 * scale
        rect = QRectF(
            (self.width() - side) / 2.0 + margin,
            (self.height() - side) / 2.0 + margin,
            side - margin * 2.0,
            side - margin * 2.0,
        )

        background = self.palette().color(QPalette.ColorRole.Mid)
        background.setAlpha(110)
        painter.setPen(QPen(background, 6.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 0, 360 * 16)

        accent = QColor("#0a6ed1")
        painter.setPen(QPen(accent, 6.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        span = int(-360.0 * (self._progress / 100.0) * 16.0)
        painter.drawArc(rect, 90 * 16, span)

        if self._active and self._progress < 100:
            activity = QColor("#63b3ff")
            activity.setAlpha(230)
            painter.setPen(QPen(activity, 3.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(rect.adjusted(3.5 * scale, 3.5 * scale, -3.5 * scale, -3.5 * scale), int((90 - self._angle) * 16), -42 * 16)

        painter.setPen(self.palette().color(QPalette.ColorRole.Text))
        font = painter.font()
        font.setBold(True)
        font.setPointSizeF(max(8.0, font.pointSizeF()))
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._progress}%")


__all__ = ["CircularSearchProgress"]
