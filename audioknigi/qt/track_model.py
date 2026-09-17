from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QApplication

from ..core import display_track_timeline, effective_track_duration, fmt_time, safe_int
from ..models import (
    Book,
    Track,
    TRACK_STATUS_DAMAGED,
    TRACK_STATUS_MISSING,
    TRACK_STATUS_PRESENT,
    TRACK_STATUS_READY,
    normalize_track_status,
)
from ..i18n import localize_runtime_text, tr, ui_text


def _lang() -> str:
    app = QApplication.instance()
    value = str(app.property("audioknigi_language") or "ru") if app is not None else "ru"
    return value if value in ("ru", "uk", "de", "en") else "ru"


class TrackTableModel(QAbstractTableModel):
    """Complete legacy track-table information with a native Qt check column."""

    HEADERS = ("Скачать", "№", "Статус", "Начало", "Конец", "Длительность", "Название", "Источник")
    SOURCE_COLUMN = 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self._book: Book | None = None
        self._tracks: list[Track] = []
        self._timeline_rows: list[tuple[float | None, float | None, float | None]] = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._tracks)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self.HEADERS):
            return ui_text(_lang(), self.HEADERS[section])
        if orientation == Qt.Orientation.Vertical:
            return str(section + 1)
        return None

    @staticmethod
    def _time(value):
        return fmt_time(value) if value is not None else "—"

    @staticmethod
    def _safe_track_index(track: Track, row: int | None = None) -> int:
        fallback = max(0, int(row) + 1) if row is not None else 1
        value = safe_int(getattr(track, "index", fallback), fallback)
        return value if value >= 0 else fallback

    def _display_value(self, track: Track, column: int, row: int | None = None):
        if column == 1:
            return self._safe_track_index(track, row)
        if column == 2:
            status = normalize_track_status(getattr(track, "local_status", ""))
            key = {
                TRACK_STATUS_MISSING: "track_status_missing",
                TRACK_STATUS_PRESENT: "track_status_present",
                TRACK_STATUS_READY: "track_status_ready",
                TRACK_STATUS_DAMAGED: "track_status_damaged",
            }.get(status)
            return tr(_lang(), key) if key else localize_runtime_text(_lang(), str(getattr(track, "local_status", "") or ""))
        if column in (3, 4, 5):
            timeline = None
            if row is not None and 0 <= row < len(self._timeline_rows):
                timeline = self._timeline_rows[row]
            if timeline is None:
                duration = effective_track_duration(track)
                timeline = (getattr(track, "start", None), getattr(track, "end", None), duration)
            start, end, duration = timeline
            if column == 3:
                return self._time(start)
            if column == 4:
                return self._time(end)
            return self._time(duration)
        if column == 6:
            safe_index = self._safe_track_index(track, row)
            return str(track.title or ui_text(_lang(), "Часть {index}", index=f"{safe_index:02d}"))
        if column == 7:
            return str(track.file or "")
        return ""

    def _accessible_row_summary(self, row: int, track: Track) -> str:
        selected = ui_text(_lang(), "Скачать: выбрано") if bool(track.selected) else ui_text(_lang(), "Скачать: не выбрано")
        parts = [selected]
        # Column 7 is the raw source URL. It is intentionally omitted from the
        # row summary so NVDA/JAWS do not read long technical addresses.
        for column in range(1, min(self.columnCount(), 7)):
            value = self._display_value(track, column, row)
            parts.append(f"{ui_text(_lang(), self.HEADERS[column])}: {value or ui_text(_lang(), 'нет данных')}")
        return "; ".join(parts)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._tracks):
            return None
        track = self._tracks[index.row()]
        column = index.column()
        if column == 0 and role == Qt.ItemDataRole.CheckStateRole:
            return Qt.CheckState.Checked if bool(track.selected) else Qt.CheckState.Unchecked
        if role == Qt.ItemDataRole.AccessibleTextRole:
            if column == 0:
                return ui_text(_lang(), "Скачать: выбрано") if bool(track.selected) else ui_text(_lang(), "Скачать: не выбрано")
            value = self._display_value(track, column, index.row())
            return f"{ui_text(_lang(), self.HEADERS[column])}: {value or ui_text(_lang(), 'нет данных')}"
        if role == Qt.ItemDataRole.AccessibleDescriptionRole:
            return self._accessible_row_summary(index.row(), track)
        if role == Qt.ItemDataRole.DisplayRole:
            return "" if column == 0 else self._display_value(track, column, index.row())
        if role == Qt.ItemDataRole.ToolTipRole and column in (6, 7):
            return str(track.file or "")
        if role == Qt.ItemDataRole.TextAlignmentRole and column in (0, 1, 2, 3, 4, 5):
            return Qt.AlignmentFlag.AlignCenter
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 0:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not (index.isValid() and index.column() == 0 and 0 <= index.row() < len(self._tracks)):
            return False
        if role not in (Qt.ItemDataRole.CheckStateRole, Qt.ItemDataRole.EditRole):
            return False

        if isinstance(value, Qt.CheckState):
            selected = value == Qt.CheckState.Checked
        elif isinstance(value, bool):
            selected = value
        else:
            try:
                numeric = int(value)
            except (TypeError, ValueError):
                return False
            if numeric not in (Qt.CheckState.Unchecked.value, Qt.CheckState.Checked.value):
                return False
            selected = numeric == Qt.CheckState.Checked.value

        self._tracks[index.row()].selected = bool(selected)
        left = self.index(index.row(), 0)
        right = self.index(index.row(), max(0, self.columnCount() - 1))
        self.dataChanged.emit(
            left, right,
            [Qt.ItemDataRole.CheckStateRole, Qt.ItemDataRole.AccessibleTextRole, Qt.ItemDataRole.AccessibleDescriptionRole],
        )
        return True

    def set_book(self, book: Book | None):
        self.beginResetModel()
        self._book = book
        self._tracks = list(getattr(book, "tracks", []) or []) if book is not None else []
        self._timeline_rows = display_track_timeline(self._tracks)
        self.endResetModel()

    def book(self) -> Book | None:
        return self._book

    def track_at(self, row: int) -> Track | None:
        return self._tracks[row] if 0 <= row < len(self._tracks) else None

    def selected_indices(self) -> list[int]:
        return [int(track.index) for track in self._tracks if bool(track.selected)]

    def selected_count(self) -> int:
        return sum(1 for track in self._tracks if bool(track.selected))

    def set_all_selected(self, selected: bool):
        if not self._tracks:
            return
        for track in self._tracks:
            track.selected = bool(selected)
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(len(self._tracks) - 1, max(0, self.columnCount() - 1)),
            [Qt.ItemDataRole.CheckStateRole, Qt.ItemDataRole.AccessibleTextRole, Qt.ItemDataRole.AccessibleDescriptionRole],
        )


__all__ = ["TrackTableModel"]
