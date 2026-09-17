from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QApplication

from ..models import SearchResult
from ..i18n import localize_runtime_text, ui_text


def _lang() -> str:
    app = QApplication.instance()
    value = str(app.property("audioknigi_language") or "ru") if app is not None else "ru"
    return value if value in ("ru", "uk", "de", "en") else "ru"


class SearchResultsModel(QAbstractTableModel):
    COLUMNS = (
        ("№", "index"),
        ("Название", "title"),
        ("Автор", "author"),
        ("Чтец", "narrator"),
        ("Статус", "availability"),
        ("Озвучки", "variants"),
        ("Источник", "source"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[SearchResult] = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._items)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None
        if role == Qt.ItemDataRole.AccessibleDescriptionRole:
            parts = []
            for column, (column_label, _key) in enumerate(self.COLUMNS):
                cell = self.data(self.index(index.row(), column), Qt.ItemDataRole.DisplayRole)
                parts.append(
                    f"{ui_text(_lang(), column_label)}: {cell or ui_text(_lang(), 'нет данных')}"
                )
            return "; ".join(parts)
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.AccessibleTextRole):
            return None
        item = self._items[index.row()]
        label, key = self.COLUMNS[index.column()]
        if key == "index":
            value = str(index.row() + 1)
        elif key == "variants":
            value = str(max(1, int(getattr(item, "variant_count", 1) or 1)))
        elif key == "availability":
            raw_status = str(getattr(item, "availability", "") or "").strip()
            status_key = raw_status.casefold()
            status_labels = {
                "available": "Доступно",
                "restricted": "Ограничено",
                "unavailable": "Недоступно",
            }
            canonical = status_labels.get(status_key, "Статус не определён" if not raw_status else raw_status)
            value = ui_text(_lang(), canonical) if canonical in status_labels.values() or not raw_status else localize_runtime_text(_lang(), canonical)
        else:
            value = str(getattr(item, key, "") or "")
        if role == Qt.ItemDataRole.AccessibleTextRole:
            return f"{ui_text(_lang(), label)}: {value or ui_text(_lang(), 'нет данных')}"
        return value

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self.COLUMNS):
            return ui_text(_lang(), self.COLUMNS[section][0])
        if orientation == Qt.Orientation.Vertical:
            return str(section + 1)
        return None

    def set_results(self, items: list[SearchResult]):
        self.beginResetModel()
        self._items = list(items or [])
        self.endResetModel()

    def result_at(self, row: int) -> SearchResult | None:
        return self._items[row] if 0 <= row < len(self._items) else None


__all__ = ["SearchResultsModel"]
