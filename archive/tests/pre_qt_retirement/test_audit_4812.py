from __future__ import annotations

import inspect
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import audioknigi.accessibility as accessibility_module
import audioknigi.storage as storage_module
import audioknigi.tray as tray_module
import audioknigi.ui_kit as ui_kit
from audioknigi.accessibility import AccessibilityManager
from audioknigi.storage import StorageMixin


ROOT = Path(__file__).resolve().parents[1]


def test_reported_truncations_are_not_present():
    actions = (ROOT / "audioknigi" / "actions.py").read_text(encoding="utf-8")
    ui_kit_source = (ROOT / "audioknigi" / "ui_kit.py").read_text(encoding="utf-8")
    compile(actions, "actions.py", "exec")
    compile(ui_kit_source, "ui_kit.py", "exec")
    assert "finally:" in actions and ("self.set_busy(False)" in actions or "self._finish_operation(operation_id)" in actions)
    assert "class AccessibleLabel" in ui_kit_source


def test_late_accessibility_name_refreshes_native_registration():
    class FakeWidget:
        def __str__(self):
            return ".fake"
        def bind(self, *_args, **_kwargs):
            return None

    manager = object.__new__(AccessibilityManager)
    manager._registered = {".fake"}
    calls = []
    manager._register_with_tk_accessible = lambda widget, name=None: calls.append((widget, name))
    widget = FakeWidget()

    manager.register(widget, name="Кастомное имя")

    assert widget.accessible_name == "Кастомное имя"
    assert calls == [(widget, "Кастомное имя")]


def test_add_history_accepts_mapping_book(monkeypatch, tmp_path):
    class Host(StorageMixin):
        pass

    host = Host()
    host.history = []
    host.ui = lambda cb: None
    monkeypatch.setattr(storage_module, "save_json", lambda *_args, **_kwargs: None)

    book = {
        "title": "Dictionary Book",
        "author": "Author",
        "narrator": "Narrator",
        "genre": "Genre",
        "year": "2026",
        "description": "Description",
        "cover_url": "https://example.invalid/cover.jpg",
        "url": "https://audioknigi.com.ua/dict-book",
    }
    host._add_history(book, tmp_path, None)

    assert host.history[0]["title"] == "Dictionary Book"
    assert host.history[0]["parts"] == 0
    assert host.history[0]["url"].endswith("dict-book")


def test_tray_hide_does_not_join_worker_on_calling_thread(monkeypatch):
    class FakeIcon:
        def stop(self):
            return None

    class ExistingThread:
        def __init__(self):
            self.join_calls = 0
        def is_alive(self):
            return True
        def join(self, timeout=None):
            self.join_calls += 1
            time.sleep(0.2)

    spawned = []
    class DeferredThread:
        def __init__(self, target=None, *args, **kwargs):
            self.target = target
            spawned.append(self)
        def start(self):
            # Intentionally do not execute the retirement helper here. The test
            # verifies that hide() itself never waits for the native worker.
            return None

    worker = ExistingThread()
    manager = tray_module.TrayManager(SimpleNamespace())
    manager.icon = FakeIcon()
    manager._thread = worker
    manager._started_event = None
    manager._stop_event = None
    monkeypatch.setattr(tray_module.threading, "Thread", DeferredThread)

    started = time.monotonic()
    manager.hide()
    elapsed = time.monotonic() - started

    assert worker.join_calls == 0
    assert elapsed < 0.1
    assert manager.icon is None
    assert manager._retiring_thread is worker
    assert spawned


def test_configure_dict_form_filters_ctk_aliases():
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        widgets = [
            ui_kit.CTkFrame(root),
            ui_kit.CTkLabel(root, text="label"),
            ui_kit.CTkButton(root, text="button"),
            ui_kit.CTkEntry(root),
            ui_kit.CTkTextbox(root),
            ui_kit.AccessibleLabel(root, text="status"),
        ]
        for widget in widgets:
            # These are CustomTkinter compatibility aliases and must be consumed
            # by the wrapper instead of leaking into native Tk/ttk configure().
            widget.configure({"fg_color": "#333333", "text_color": "#E6E6E6"})
    finally:
        root.destroy()


def test_linux_cyrillic_physical_shortcuts_use_x11_keycodes(monkeypatch):
    import tkinter as tk

    monkeypatch.setattr(ui_kit.sys, "platform", "linux")
    root = tk.Tk()
    root.withdraw()
    try:
        entry = ui_kit.CTkEntry(root)
        entry.insert(0, "abc")
        entry.selection_range(0, "end")
        result = entry._physical_edit_shortcut(
            SimpleNamespace(state=0x0004, keycode=54, keysym="Cyrillic_es", char="")
        )
        assert result == "break"
        assert root.clipboard_get() == "abc"

        root.clipboard_clear(); root.clipboard_append("XYZ")
        entry.selection_range(0, "end")
        result = entry._physical_edit_shortcut(
            SimpleNamespace(state=0x0004, keycode=55, keysym="Cyrillic_em", char="")
        )
        assert result == "break"
        assert entry.get() == "XYZ"

        text = ui_kit.CTkTextbox(root)
        text.insert("1.0", "text")
        text.tag_add("sel", "1.0", "end-1c")
        result = text._physical_text_shortcut(
            SimpleNamespace(state=0x0004, keycode=54, keysym="Cyrillic_es", char="")
        )
        assert result == "break"
        assert root.clipboard_get() == "text"
    finally:
        root.destroy()


def test_parent_bg_resolves_ttk_notebook_style_background():
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.withdraw()
    try:
        style = ttk.Style(root)
        style.configure("Audit4812.TNotebook", background="#123456")
        notebook = ttk.Notebook(root, style="Audit4812.TNotebook")
        assert ui_kit._parent_bg(notebook, "#ABCDEF") == "#123456"
    finally:
        root.destroy()


def test_theme_background_no_dead_fallback_parameter():
    assert "fallback_panel" not in inspect.signature(ui_kit._theme_background).parameters
