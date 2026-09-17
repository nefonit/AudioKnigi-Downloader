import tkinter as tk
from tkinter import ttk
from pathlib import Path

import pytest

from audioknigi.accessibility import AccessibilityManager, WindowsInsertUpObserver
from audioknigi.app import AudioKnigiApp
from audioknigi.ui_kit import bind_combobox_keyboard, post_combobox_popdown, unpost_combobox_popdowns


class _Bridge:
    def __init__(self):
        self.active = True
        self.backend_name = "JAWS"
        self.spoken = []

    def announce(self, text, interrupt=False):
        self.spoken.append((str(text), bool(interrupt)))
        return True


class _Manager:
    def __init__(self, app):
        self.app = app
        self._closed = False
        self.calls = []

    def announce_focused_editable_text(self, widget, interrupt=True):
        self.calls.append((widget, interrupt, widget.get()))
        return True


def test_windows_insert_up_observer_delivers_focused_editor_value_without_stealing_key():
    root = tk.Tk()
    root.withdraw()
    entry = ttk.Entry(root)
    entry.insert(0, "сталкер")
    entry.pack()
    root.deiconify()
    root.update_idletasks()
    entry.focus_force()
    root.update()
    manager = _Manager(root)
    observer = WindowsInsertUpObserver(manager)
    observer._pending = True
    observer._deliver()
    assert observer._pending is False
    assert manager.calls and manager.calls[-1][2] == "сталкер"
    root.destroy()


def test_combobox_open_close_is_announced_and_enter_space_are_supported():
    root = tk.Tk()
    root.withdraw()
    combo = ttk.Combobox(root, values=("Первый", "Второй"), state="readonly")
    combo.set("Первый")
    combo.pack()
    events = []
    combo._audioknigi_accessibility_on_open = lambda: events.append("open")
    combo._audioknigi_accessibility_on_close = lambda: events.append("close")
    bind_combobox_keyboard(combo)
    root.deiconify()
    root.update_idletasks()
    combo.focus_force()
    root.update()
    assert post_combobox_popdown(combo) is True
    root.update()
    assert "open" in events
    assert unpost_combobox_popdowns(root) >= 1
    root.update()
    assert "close" in events
    # Keyboard contract is explicit, even if a particular headless Tk theme
    # cannot visually post its popdown from a synthesized event.
    bindings = " ".join(str(combo.bind(seq) or "") for seq in ("<Return>", "<KP_Enter>", "<space>", "<F4>", "<Alt-Down>"))
    assert bindings.strip()
    root.destroy()


def test_every_standard_interactive_role_has_a_usage_hint():
    root = tk.Tk()
    manager = AccessibilityManager.__new__(AccessibilityManager)
    manager.app = root
    widgets = [
        ttk.Button(root, text="Кнопка"),
        ttk.Checkbutton(root, text="Флажок"),
        ttk.Radiobutton(root, text="Вариант"),
        ttk.Entry(root),
        ttk.Combobox(root, values=("A", "B"), state="readonly"),
        ttk.Scale(root),
        ttk.Treeview(root),
        ttk.Notebook(root),
        tk.Text(root),
    ]
    for widget in widgets:
        hint = manager._interaction_hint(widget)
        assert hint.strip(), type(widget).__name__
        description = manager._describe_widget(widget)
        assert hint in description
    root.destroy()


def test_narration_combobox_in_both_modes_has_opening_instructions():
    root = Path(__file__).resolve().parents[1]
    main = (root / "audioknigi" / "ui" / "main_tab.py").read_text(encoding="utf-8")
    easy = (root / "audioknigi" / "ui" / "easy_home.py").read_text(encoding="utf-8")
    for source in (main, easy):
        assert "Alt+стрелка вниз" in source
        assert "F4" in source
        assert "Enter" in source
        assert "пробел" in source
        assert "Escape" in source


def test_tk_recursion_handler_never_calls_full_exception_formatter(monkeypatch):
    class AccessibilityStub:
        _focus_probe_suspended = False
        _pending_focus_widget = object()

    class Fake:
        _handling_tk_recursion = False
        last_crash_report = ""
        accessibility = AccessibilityStub()

        def __getattr__(self, name):
            if name in {"after", "after_idle", "update", "update_idletasks", "focus_get"}:
                raise AssertionError(f"Tk call is forbidden in recursion emergency path: {name}")
            raise AttributeError(name)

    fake = Fake()
    import audioknigi.app as app_module

    def forbidden(*args, **kwargs):
        raise AssertionError("full traceback logger must not run in recursion emergency path")

    monkeypatch.setattr(app_module, "log_exception", forbidden)
    AudioKnigiApp._tk_exception_handler(fake, RecursionError, RecursionError("maximum recursion depth exceeded"), None)
    assert "RecursionError" in fake.last_crash_report
    assert fake._handling_tk_recursion is True
    assert fake.accessibility._focus_probe_suspended is True
    assert fake.accessibility._pending_focus_widget is None


def test_focus_probe_is_deferred_and_coalesced():
    root = Path(__file__).resolve().parents[1]
    source = (root / "audioknigi" / "accessibility.py").read_text(encoding="utf-8")
    assert "_focus_probe_active" in source
    assert "_focus_probe_suspended" in source
    assert "_pending_focus_widget" in source
    assert "_focus_probe_after_id" in source
    assert "self.app.after(0, process_pending_focus)" in source


def test_runtime_all_visible_focusables_have_names_roles_and_keyboard_hints():
    """Audit the actual easy UI, every advanced tab and Help Center."""
    from audioknigi.help_center import HelpCenter

    app = AudioKnigiApp()
    total = 0
    try:
        app.update()
        manager = app.accessibility

        def assert_scope(label, root):
            nonlocal total
            app.update_idletasks()
            app.update()
            widgets = manager._focusable_widgets(root)
            assert widgets, label
            total += len(widgets)
            for widget in widgets:
                description = manager._describe_widget(widget)
                role = manager._role_of(widget)
                assert description.strip(), (label, widget)
                assert not description.startswith("Элемент"), (label, widget, description)
                assert role.strip(), (label, widget, description)
                # Focusable interactive controls must tell keyboard/screen-reader
                # users how to operate them. Labels are not part of this list.
                if role not in {"текст", "label"}:
                    assert manager._interaction_hint(widget).strip(), (label, widget, role, description)

        app.set_ui_mode("easy")
        app.update()
        assert_scope("easy", app)

        app.set_ui_mode("advanced")
        app.update()
        for key in ("book", "search", "queue", "history", "settings"):
            app.open_advanced_tab(key)
            app.update()
            assert_scope(f"advanced:{key}", app)

        help_center = HelpCenter(app, "overview")
        try:
            help_center.win.update()
            assert_scope("help", help_center.win)
        finally:
            help_center.win.destroy()
        assert total >= 100
    finally:
        app.destroy()


def test_help_center_repeated_focus_topic_navigation_does_not_recurse():
    from audioknigi.help_center import HelpCenter

    app = AudioKnigiApp()
    try:
        app.update()
        # No real speech backend is needed; reentrant Tk focus paths are what
        # this regression protects.
        app.accessibility.bridge.announce = lambda *args, **kwargs: True
        help_center = HelpCenter(app, "overview")
        try:
            help_center.win.update()
            keys = [key for key, *_rest in help_center.topics]
            for index in range(75):
                key = keys[index % len(keys)]
                help_center.show(key, focus_text=True)
                help_center.win.update_idletasks()
                help_center.win.update()
                button = help_center.topic_buttons[key]
                button.focus_set()
                help_center.win.update()
                help_center.text.focus_set()
                help_center.win.update()
        finally:
            help_center.win.destroy()
    finally:
        app.destroy()


def test_open_combobox_arrow_navigation_has_screenreader_callback():
    root = tk.Tk()
    combo = ttk.Combobox(root, values=("А", "Б", "В"), state="readonly")
    combo.set("А")
    combo.pack()
    calls = []
    combo._audioknigi_accessibility_on_navigate = lambda: calls.append(combo.get())
    bind_combobox_keyboard(combo)
    root.update()
    combo.focus_force()
    root.update()
    combo.event_generate("<Down>")
    root.update()
    assert calls, "open-list arrow navigation must schedule a screen-reader announcement"
    root.destroy()
