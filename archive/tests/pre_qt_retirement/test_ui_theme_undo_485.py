"""4.8.5 regression coverage: full-window themes, undo, and responsive layout."""
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

from audioknigi import AudioKnigiApp
from audioknigi.help_center import HelpCenter
from audioknigi import ui_kit
from audioknigi.ui_kit import CTkEntry


def _opposite_theme_surfaces(root, *, dark):
    dark_surfaces = {
        "#1e1e1e", "#252525", "#2d2d2d", "#303030", "#333333",
        "#383838", "#444444", "#0a1b31", "#0f4c83", "#123052", "#15365e",
    }
    light_surfaces = {
        "#f5f7fa", "#ffffff", "#f8fafc", "#edf4fb", "#e2ecf7",
        "#eef6ff", "#d9ecff", "#eaf3fb", "#e7f2ff",
    }
    forbidden = light_surfaces if dark else dark_surfaces
    bad = []

    def walk(widget):
        try:
            if isinstance(widget, (tk.Tk, tk.Toplevel, tk.Frame, tk.Label, tk.Text, tk.Canvas, tk.Menu)):
                try:
                    bg = str(widget.cget("bg")).lower()
                    if bg in forbidden:
                        bad.append((widget.winfo_class(), bg, str(widget)))
                except tk.TclError:
                    pass
            for child in widget.winfo_children():
                walk(child)
        except tk.TclError:
            pass

    walk(root)
    return bad


def _visible_overflows(widget):
    failures = []
    try:
        parent_width = widget.winfo_width()
        parent_height = widget.winfo_height()
        children = widget.winfo_children()
    except tk.TclError:
        return failures
    for child in children:
        try:
            if not child.winfo_ismapped():
                continue
            if isinstance(child, tk.Toplevel):
                failures.extend(_visible_overflows(child))
                continue
            x, y = child.winfo_x(), child.winfo_y()
            w, h = child.winfo_width(), child.winfo_height()
            if parent_width > 1 and x + w > parent_width + 3:
                failures.append(("horizontal", str(child)))
            # A scrollable-frame content window is intentionally taller than
            # its viewport and is therefore not a visual clipping failure.
            managed_by_canvas = isinstance(widget, tk.Canvas)
            if not managed_by_canvas and parent_height > 1 and y + h > parent_height + 3:
                failures.append(("vertical", str(child)))
            failures.extend(_visible_overflows(child))
        except tk.TclError:
            pass
    return failures


def _squeezed_text_controls(widget):
    failures = []
    for child in widget.winfo_children():
        try:
            if not child.winfo_ismapped():
                continue
            text = ""
            try:
                text = str(child.cget("text") or "")
            except tk.TclError:
                pass
            if text and isinstance(child, (tk.Label, ttk.Label, ttk.Button, ttk.Checkbutton, ttk.Radiobutton)):
                if child.winfo_width() + 2 < child.winfo_reqwidth() or child.winfo_height() + 2 < child.winfo_reqheight():
                    failures.append((child.winfo_class(), text, child.winfo_width(), child.winfo_reqwidth()))
            failures.extend(_squeezed_text_controls(child))
        except tk.TclError:
            pass
    return failures


def test_ctrl_z_undo_works_with_windows_physical_keycode(monkeypatch):
    root = tk.Tk()
    try:
        entry = CTkEntry(root)
        entry.pack()
        entry.insert(0, "abc")
        entry.icursor("end")
        monkeypatch.setattr(ui_kit.sys, "platform", "win32")

        # Ordinary typing records the state before Tk performs the edit.
        entry._physical_edit_shortcut(SimpleNamespace(state=0, keycode=68, keysym="Cyrillic_ve", char="d"))
        entry.insert("end", "d")
        assert entry.get() == "abcd"

        result = entry._physical_edit_shortcut(SimpleNamespace(state=0x0004, keycode=90, keysym="Cyrillic_ya", char=""))
        assert result == "break"
        assert entry.get() == "abc"

        result = entry._physical_edit_shortcut(SimpleNamespace(state=0x0004, keycode=89, keysym="Cyrillic_en", char=""))
        assert result == "break"
        assert entry.get() == "abcd"
        assert not entry.bind("<Control-KeyPress>")
    finally:
        root.destroy()


def test_help_window_and_all_existing_surfaces_follow_live_theme():
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        for theme, dark in (("dark", True), ("light", False)):
            app.theme_var.set(theme)
            app._apply_theme()
            app.update()
            assert _opposite_theme_surfaces(app, dark=dark) == []

            help_center = HelpCenter(app)
            app.update()
            assert help_center.win.cget("bg").lower() == ("#1e1e1e" if dark else "#f5f7fa")
            assert help_center.text.cget("bg").lower() == ("#252525" if dark else "#ffffff")
            assert _opposite_theme_surfaces(help_center.win, dark=dark) == []
            assert _visible_overflows(help_center.win) == []
            help_center.win.destroy()

        style = ttk.Style(app)
        app.theme_var.set("light")
        app._apply_theme()
        assert style.lookup("AudioKnigi.TEntry", "fieldbackground").lower() == "#ffffff"
        assert style.lookup("Treeview", "fieldbackground").lower() == "#ffffff"
        app.theme_var.set("dark")
        app._apply_theme()
        assert style.lookup("AudioKnigi.TEntry", "fieldbackground").lower() == "#252525"
        assert style.lookup("Treeview", "fieldbackground").lower() == "#252525"
    finally:
        app.destroy()


def test_every_mode_tab_and_scale_has_no_visible_clipping():
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        # Existing 4.8.3 coverage already walks every advanced tab at every
        # scale.  4.8.5 adds the missing simple-dashboard coverage that caught
        # the 175/200% squeezing regression, plus one all-tab smoke pass after
        # the responsive layout change.
        app.theme_var.set("dark")
        app._apply_theme()
        app.ui_mode_var.set("Простой")
        app._apply_ui_mode()
        for scale in ("100", "125", "150", "175", "200"):
            app.scale_var.set(scale)
            app._apply_scale(silent=True)
            app.update_idletasks()
            assert _visible_overflows(app) == [], ("Простой", scale)
            assert _squeezed_text_controls(app) == [], ("Простой", scale)

        app.ui_mode_var.set("Расширенный")
        app._apply_ui_mode()
        app.scale_var.set("125")
        app._apply_scale(silent=True)
        for tab in ("Книга", "Поиск", "Очередь", "История", "Настройки"):
            app.tabview.set(tab)
            app.update_idletasks()
            assert _visible_overflows(app) == [], ("Расширенный", tab)
            assert _squeezed_text_controls(app) == [], ("Расширенный", tab)
    finally:
        app.destroy()

