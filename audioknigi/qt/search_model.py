from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QApplication

from ..models import SearchResult
from ..i18n import ui_text
from ..services.search_service import search_result_sort_key


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
        ("Озвучки", "variants"),
        ("Источник", "source"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[SearchResult] = []
        self._query = ""

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

    def set_results(self, items: list[SearchResult], *, query: str = ""):
        self.beginResetModel()
        self._items = list(items or [])
        self._query = str(query or "").strip()
        self.endResetModel()

    def sort_by(self, field: str) -> None:
        field = str(field or "").strip().casefold()
        if field not in {"title", "author", "narrator"}:
            return
        self.beginResetModel()
        self._items.sort(key=lambda item: search_result_sort_key(item, field, query=self._query))
        self.endResetModel()

    def row_for_url(self, url: str) -> int:
        wanted = str(url or "").strip()
        for row, item in enumerate(self._items):
            if str(getattr(item, "url", "") or "").strip() == wanted:
                return row
        return -1

    def result_at(self, row: int) -> SearchResult | None:
        return self._items[row] if 0 <= row < len(self._items) else None


__all__ = ["SearchResultsModel"]
