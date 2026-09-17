from __future__ import annotations

from collections import deque
import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from ..i18n import ui_text


def _language() -> str:
    app = QApplication.instance()
    value = str(app.property("audioknigi_language") or "ru") if app is not None else "ru"
    return value if value in ("ru", "uk", "de", "en") else "ru"


class SpeedGraphWidget(QWidget):
    """Small accessible transfer-speed history graph; values are MiB/s."""

    def __init__(self, parent=None, *, capacity: int = 90):
        super().__init__(parent)
        self._values = deque(maxlen=max(10, int(capacity)))
        self.setFixedHeight(40)
        self._expanded_height = 72
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName(ui_text(_language(), "График скорости загрузки"))
        self.setAccessibleDescription(ui_text(_language(), "История скорости скачивания во времени"))
        self.setObjectName("speed_graph")

    def set_transfer_active(self, active: bool):
        self.setFixedHeight(self._expanded_height if active else 40)
        self.updateGeometry()

    def add_speed(self, mib_per_second: float):
        try:
            value = float(mib_per_second or 0.0)
        except (TypeError, ValueError):
            value = 0.0
        if not math.isfinite(value):
            value = 0.0
        self._values.append(max(0.0, value))
        if value > 0.0 and self.height() != self._expanded_height:
            self.set_transfer_active(True)
        peak = max(self._values, default=0.0)
        self.setAccessibleDescription(ui_text(_language(), "График скорости. Максимум {peak:.2f} мегабайт в секунду", peak=peak))
        self.update()

    def clear(self):
        self._values.clear()
        self.set_transfer_active(False)
        self.update()

    def values(self) -> tuple[float, ...]:
        return tuple(self._values)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        palette = self.palette()
        painter.fillRect(self.rect(), palette.base())
        if self.width() <= 2 or self.height() <= 2:
            return
        values = [value for value in self._values if math.isfinite(value) and value >= 0.0]
        if len(values) < 2:
            # The current speed is already presented by the dedicated accessible
            # label above the graph. Keep the graph visually quiet until history
            # exists instead of duplicating "Скорость: —".
            return
        actual_peak = max(values, default=0.0)
        scale_peak = max(actual_peak, 0.1)
        w = max(1, self.width() - 12)
        h = max(1, self.height() - 14)
        points = []
        for i, value in enumerate(values):
            x = 6 + (w * i / max(1, len(values) - 1))
            y = 7 + h - (value / scale_peak) * h
            points.append((x, y))
        pen = QPen(palette.highlight().color())
        pen.setWidth(2)
        painter.setPen(pen)
        for left, right in zip(points, points[1:]):
            painter.drawLine(int(left[0]), int(left[1]), int(right[0]), int(right[1]))
        painter.setPen(palette.text().color())
        painter.drawText(7, 13, ui_text(_language(), "max {peak:.1f} МБ/с", peak=actual_peak))


__all__ = ["SpeedGraphWidget"]
