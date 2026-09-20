from __future__ import annotations

from time import monotonic
import threading
import weakref

from PySide6.QtCore import QItemSelectionModel, QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QAccessible
try:  # Defensive fallback for environments below the declared PySide6>=6.8 runtime.
    from PySide6.QtGui import QAccessibleAnnouncementEvent
except ImportError:  # pragma: no cover - supported builds provide this class
    QAccessibleAnnouncementEvent = None
from ..i18n import localize_runtime_text, ui_text

from PySide6.QtWidgets import (
    QAbstractButton, QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QFocusFrame, QLineEdit, QListWidget, QPlainTextEdit, QPushButton, QSlider, QTableView, QTextEdit, QWidget,
)


_ACCESSIBLE_HINTS = {
    "ru": {
        "button": "Нажмите Enter или пробел, чтобы выполнить действие.",
        "edit": "Введите текст. Tab переходит к следующему элементу.",
        "combo": "Alt+стрелка вниз открывает список; стрелки меняют значение.",
        "check": "Пробел включает или выключает параметр.",
        "slider": "Стрелки меняют значение; Page Up и Page Down меняют его крупным шагом.",
        "table": "Стрелки перемещают по строкам; Shift+F10 открывает контекстные действия, если они доступны.",
        "list": "Стрелки перемещают по списку; Enter активирует выбранный пункт.",
        "spin": "Стрелки вверх и вниз меняют значение.",
        "widget": "Tab переходит к следующему элементу интерфейса.",
    },
    "uk": {
        "button": "Натисніть Enter або пробіл, щоб виконати дію.",
        "edit": "Введіть текст. Tab переходить до наступного елемента.",
        "combo": "Alt+стрілка вниз відкриває список; стрілки змінюють значення.",
        "check": "Пробіл вмикає або вимикає параметр.",
        "slider": "Стрілки змінюють значення; Page Up і Page Down змінюють його великим кроком.",
        "table": "Стрілки переміщують рядками; Shift+F10 відкриває контекстні дії, якщо вони доступні.",
        "list": "Стрілки переміщують списком; Enter активує вибраний пункт.",
        "spin": "Стрілки вгору й вниз змінюють значення.",
        "widget": "Tab переходить до наступного елемента інтерфейсу.",
    },
    "de": {
        "button": "Enter oder Leertaste führt die Aktion aus.",
        "edit": "Text eingeben. Tab wechselt zum nächsten Element.",
        "combo": "Alt+Pfeil nach unten öffnet die Liste; Pfeiltasten ändern den Wert.",
        "check": "Leertaste schaltet die Option ein oder aus.",
        "slider": "Pfeiltasten ändern den Wert; Bild auf/ab ändert ihn in größeren Schritten.",
        "table": "Pfeiltasten bewegen durch die Zeilen; Umschalt+F10 öffnet verfügbare Kontextaktionen.",
        "list": "Pfeiltasten bewegen durch die Liste; Enter aktiviert den ausgewählten Eintrag.",
        "spin": "Pfeil nach oben/unten ändert den Wert.",
        "widget": "Tab wechselt zum nächsten Oberflächenelement.",
    },
    "en": {
        "button": "Press Enter or Space to perform this action.",
        "edit": "Enter text. Tab moves to the next control.",
        "combo": "Alt+Down opens the list; arrow keys change the value.",
        "check": "Press Space to toggle this option.",
        "slider": "Arrow keys change the value; Page Up and Page Down use larger steps.",
        "table": "Arrow keys move through rows; Shift+F10 opens context actions when available.",
        "list": "Arrow keys move through the list; Enter activates the selected item.",
        "spin": "Up and Down arrows change the value.",
        "widget": "Tab moves to the next interface control.",
    },
}


def _current_ui_language() -> str:
    app = QApplication.instance()
    if app is not None:
        try:
            value = str(app.property("audioknigi_language") or "").strip().lower()
            if value in _ACCESSIBLE_HINTS:
                return value
        except Exception:
            pass
    return "ru"


_GENERIC_NAMES = {
    "ru": {"button": "Кнопка", "edit": "Поле ввода", "combo": "Список выбора", "check": "Флажок", "slider": "Ползунок", "table": "Таблица", "list": "Список", "spin": "Числовое поле", "widget": "Элемент управления"},
    "uk": {"button": "Кнопка", "edit": "Поле введення", "combo": "Список вибору", "check": "Прапорець", "slider": "Повзунок", "table": "Таблиця", "list": "Список", "spin": "Числове поле", "widget": "Елемент керування"},
    "de": {"button": "Schaltfläche", "edit": "Eingabefeld", "combo": "Auswahlliste", "check": "Kontrollkästchen", "slider": "Schieberegler", "table": "Tabelle", "list": "Liste", "spin": "Zahlenfeld", "widget": "Bedienelement"},
    "en": {"button": "Button", "edit": "Text field", "combo": "Selection list", "check": "Checkbox", "slider": "Slider", "table": "Table", "list": "List", "spin": "Number field", "widget": "Control"},
}


def _widget_kind(widget: QWidget) -> str:
    if isinstance(widget, QPushButton): return "button"
    if isinstance(widget, QLineEdit): return "edit"
    if isinstance(widget, QComboBox): return "combo"
    if isinstance(widget, QCheckBox): return "check"
    if isinstance(widget, QSlider): return "slider"
    if isinstance(widget, QTableView): return "table"
    if isinstance(widget, QListWidget): return "list"
    if isinstance(widget, QAbstractSpinBox): return "spin"
    return "widget"


def _fallback_accessible_name(widget: QWidget, identifier: str | None) -> str:
    language = _current_ui_language()
    # Prefer visible localized text for buttons/checkboxes.
    getter = getattr(widget, "text", None)
    if callable(getter):
        try:
            visible = str(getter() or "").replace("&", "").strip()
            if visible:
                return visible
        except Exception:
            pass
    base = _GENERIC_NAMES[language][_widget_kind(widget)]
    return f"{base} ({identifier})" if identifier else base


def _default_accessible_description(widget: QWidget) -> str:
    hints = _ACCESSIBLE_HINTS[_current_ui_language()]
    if isinstance(widget, QPushButton):
        return hints["button"]
    if isinstance(widget, QLineEdit):
        return hints["edit"]
    if isinstance(widget, QComboBox):
        return hints["combo"]
    if isinstance(widget, QCheckBox):
        return hints["check"]
    if isinstance(widget, QSlider):
        return hints["slider"]
    if isinstance(widget, QTableView):
        return hints["table"]
    if isinstance(widget, QListWidget):
        return hints["list"]
    if isinstance(widget, QAbstractSpinBox):
        return hints["spin"]
    return hints["widget"]


def configure_accessible(
    widget: QWidget,
    *,
    name: str | None = None,
    description: str | None = None,
    identifier: str | None = None,
) -> QWidget:
    """Apply Qt-native accessibility metadata without custom focus hooks."""
    if identifier:
        widget.setObjectName(identifier)
        setter = getattr(widget, "setAccessibleIdentifier", None)
        if callable(setter):
            setter(identifier)
    if name:
        language = _current_ui_language()
        # Preserve explicit dynamic content (book/chapter/person names) even when
        # it contains Cyrillic under an English/German UI. Static app strings are
        # covered by the localization audit; replacing unknown content with a
        # generic “Button”/“Control” destroys useful information for screen readers.
        widget.setAccessibleName(ui_text(language, str(name)))
    elif identifier and not str(widget.accessibleName() or "").strip():
        # Derive a useful name from native widget text when a caller only supplied
        # a stable identifier. This is safer than leaving a newly added control
        # silent to NVDA/JAWS.
        getter = getattr(widget, "text", None)
        if callable(getter):
            try:
                derived = str(getter() or "").strip()
                if derived:
                    widget.setAccessibleName(derived.replace("&", ""))
            except Exception:
                pass
    if description:
        widget.setAccessibleDescription(localize_runtime_text(_current_ui_language(), str(description)))
    elif identifier and not str(widget.accessibleDescription() or "").strip():
        widget.setAccessibleDescription(_default_accessible_description(widget))
    return widget




class KeyboardFocusFrameManager(QObject):
    """Show one external Qt focus frame around the currently focused control.

    Unlike changing the widget's own border, QFocusFrame is an overlay managed
    by Qt around the target geometry.  This keeps text/input padding stable and
    makes keyboard focus especially clear on Windows 10 system themes.
    """

    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self._app = app
        self._frame: QFocusFrame | None = None
        self._frame_window = None
        app.focusChanged.connect(self._focus_changed)
        self._focus_changed(None, app.focusWidget())

    @staticmethod
    def _outer_control(widget: QWidget | None) -> QWidget | None:
        current = widget
        while current is not None:
            parent = current.parentWidget()
            if isinstance(parent, (QComboBox, QAbstractSpinBox)):
                current = parent
                continue
            break
        return current

    def _hide_frame(self) -> None:
        frame = self._frame
        if frame is None:
            return
        try:
            frame.hide()
        except RuntimeError:
            # The parent top-level window may already have destroyed the C++
            # QFocusFrame. Never touch the stale wrapper a second time.
            self._frame = None
            self._frame_window = None

    def _discard_frame(self) -> None:
        frame = self._frame
        self._frame = None
        self._frame_window = None
        if frame is None:
            return
        try:
            frame.hide()
        except RuntimeError:
            return
        try:
            frame.setWidget(None)
        except RuntimeError:
            return
        try:
            frame.deleteLater()
        except RuntimeError:
            pass

    @Slot(object, object)
    def _focus_changed(self, _old, now) -> None:
        target = self._outer_control(now if isinstance(now, QWidget) else None)
        if target is None:
            self._hide_frame()
            return
        try:
            if target.focusPolicy() == Qt.FocusPolicy.NoFocus or not target.isVisible():
                self._hide_frame()
                return
            window = target.window()
            if window is None:
                self._hide_frame()
                return
            if self._frame is None or self._frame_window is not window:
                self._discard_frame()
                frame = QFocusFrame(window)
                frame.setObjectName("keyboardFocusFrame")
                frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                self._frame = frame
                self._frame_window = window
            if self._frame is None:
                return
            self._frame.setWidget(target)
            self._frame.show()
            self._frame.raise_()
        except RuntimeError:
            # Focus changes can race with deferred dialog/menu destruction.
            # Clear the wrapper without invoking methods on a deleted C++ object.
            self._frame = None
            self._frame_window = None


def install_keyboard_focus_frame(app: QApplication, parent=None) -> KeyboardFocusFrameManager:
    return KeyboardFocusFrameManager(app, parent)


def ensure_accessibility_tree(root: QWidget) -> QWidget:
    """Fill missing screen-reader metadata on every app-level focusable control.

    Explicit ``configure_accessible`` calls remain the preferred source of names.
    This final sweep is a release-safety net: a newly added button/edit/list cannot
    become silent to NVDA/JAWS merely because a developer forgot metadata.
    """
    interactive_types = (
        QAbstractButton, QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSlider,
        QTableView, QListWidget, QAbstractSpinBox,
    )
    for widget in [root, *root.findChildren(QWidget)]:
        if not isinstance(widget, interactive_types):
            continue
        try:
            if widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
                continue
            identifier = str(widget.objectName() or "").strip() or None
            if not str(widget.accessibleName() or "").strip():
                widget.setAccessibleName(_fallback_accessible_name(widget, identifier))
            if not str(widget.accessibleDescription() or "").strip():
                widget.setAccessibleDescription(_default_accessible_description(widget))
        except RuntimeError:
            # A deferred teardown may delete a wrapped C++ object between discovery
            # and inspection. Accessibility hardening must never block shutdown.
            continue
    return root


_DIRECT_ANNOUNCE_LOCK = threading.Lock()
_DIRECT_ANNOUNCE_LAST_TEXT = ""
_DIRECT_ANNOUNCE_LAST_AT = 0.0
_DEFAULT_ANNOUNCER_REF = None


def announce(widget: QWidget, message: str, *, assertive: bool = False) -> None:
    """Request a native Qt accessibility announcement without stealing focus."""
    text = str(message or "").strip()
    if not text or QAccessibleAnnouncementEvent is None:
        return
    try:
        if widget.thread() != QThread.currentThread():
            ref = _DEFAULT_ANNOUNCER_REF
            announcer = ref() if callable(ref) else None
            if announcer is not None and callable(getattr(announcer, "speak", None)):
                announcer.speak(text, assertive=assertive)
            return
    except RuntimeError:
        return
    global _DIRECT_ANNOUNCE_LAST_TEXT, _DIRECT_ANNOUNCE_LAST_AT
    now = monotonic()
    if not assertive:
        with _DIRECT_ANNOUNCE_LOCK:
            # Guard the low-level API too: callers that bypass AccessibleAnnouncer
            # cannot flood Windows UIA/NVDA with dozens of events per second.
            if now - _DIRECT_ANNOUNCE_LAST_AT < 0.06:
                return
            if text == _DIRECT_ANNOUNCE_LAST_TEXT and now - _DIRECT_ANNOUNCE_LAST_AT < 0.8:
                return
            _DIRECT_ANNOUNCE_LAST_TEXT = text
            _DIRECT_ANNOUNCE_LAST_AT = now
    try:
        event = QAccessibleAnnouncementEvent(widget, text)
        if assertive:
            politeness_enum = getattr(QAccessible, "AnnouncementPoliteness", None)
            assertive_value = getattr(politeness_enum, "Assertive", None) if politeness_enum is not None else None
            if assertive_value is not None:
                try:
                    event.setPoliteness(assertive_value)
                except (AttributeError, TypeError):
                    # Announcement events are best-effort feedback. Older/minor
                    # bindings should still receive the polite announcement.
                    pass
        QAccessible.updateAccessibility(event)
    except Exception:
        # Accessibility feedback must never break the main UI flow.
        pass


class AccessibleAnnouncer(QObject):
    """Rate-limit native announcements without starving continuous progress updates."""

    _queued_speak = Signal(str, bool)

    def __init__(self, widget: QWidget, *, polite_delay_ms: int = 180, parent: QObject | None = None):
        super().__init__(parent or widget)
        global _DEFAULT_ANNOUNCER_REF
        self.widget = widget
        _DEFAULT_ANNOUNCER_REF = weakref.ref(self)
        self.polite_delay_ms = max(0, int(polite_delay_ms))
        self._pending = ""
        self._latest_pending = ""
        self._last_spoken = ""
        self._last_spoken_at = 0.0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._flush)
        self._queued_speak.connect(self._enqueue, Qt.ConnectionType.QueuedConnection)

    def speak(self, message: str, *, assertive: bool = False) -> None:
        text = str(message or "").strip()
        if not text:
            return
        # QTimer belongs to the GUI thread. Marshal calls from workers instead of
        # starting/stopping it from an arbitrary Python/Qt thread.
        if QThread.currentThread() != self.thread():
            self._queued_speak.emit(text, bool(assertive))
            return
        self._enqueue(text, bool(assertive))

    @Slot(str, bool)
    def _enqueue(self, text: str, assertive: bool = False) -> None:
        now = monotonic()
        if text == self._last_spoken and now - self._last_spoken_at < 0.8:
            return
        if assertive:
            self._timer.stop()
            self._pending = ""
            self._latest_pending = ""
            self._deliver(text, assertive=True)
            return
        # Preserve the first operation status while coalescing later progress
        # updates. This avoids both starvation (timer restart loops) and losing
        # a quick "started" message when a second status arrives <180 ms later.
        if not self._pending:
            self._pending = text
            if not self._timer.isActive():
                self._timer.start(self.polite_delay_ms)
        else:
            self._latest_pending = text

    def _flush(self) -> None:
        text = self._pending
        self._pending = ""
        if text:
            self._deliver(text, assertive=False)
        latest = self._latest_pending
        self._latest_pending = ""
        if latest and latest != text:
            self._pending = latest
            self._timer.start(self.polite_delay_ms)

    def _deliver(self, text: str, *, assertive: bool) -> None:
        self._last_spoken = text
        self._last_spoken_at = monotonic()
        announce(self.widget, text, assertive=assertive)


def focus_table_row(
    view: QAbstractItemView,
    row: int = 0,
    *,
    column: int = 0,
    focus: bool = True,
    reason: Qt.FocusReason = Qt.FocusReason.OtherFocusReason,
) -> bool:
    """Give a table a real current cell/row before moving keyboard focus to it.

    Screen readers can otherwise announce only "table" after a model reset because
    the view has focus but no current accessible cell.
    """
    model = view.model()
    if model is None or row < 0 or row >= model.rowCount():
        return False
    column = max(0, min(int(column), max(0, model.columnCount() - 1)))
    index = model.index(int(row), column)
    if not index.isValid():
        return False
    view.setCurrentIndex(index)
    selection = view.selectionModel()
    if selection is not None:
        flags = QItemSelectionModel.SelectionFlag.ClearAndSelect
        if view.selectionBehavior() == QAbstractItemView.SelectionBehavior.SelectRows:
            flags |= QItemSelectionModel.SelectionFlag.Rows
        selection.select(index, flags)
    try:
        view.scrollTo(index, QAbstractItemView.ScrollHint.EnsureVisible)
    except Exception:
        pass
    if focus:
        view.setFocus(reason)
    return True


__all__ = ["configure_accessible", "ensure_accessibility_tree", "announce", "AccessibleAnnouncer", "focus_table_row"]
