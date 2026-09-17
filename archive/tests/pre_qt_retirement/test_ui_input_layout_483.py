"""4.8.3 keyboard editing and layout regression tests."""
import tkinter as tk
from tkinter import ttk

from audioknigi import AudioKnigiApp
from audioknigi.ui_kit import AccessibleLabel, CTkButton, CTkEntry, CTkOptionMenu


def test_entry_edit_shortcuts_and_text_safe_widths():
    root = tk.Tk()
    try:
        entry = CTkEntry(root)
        entry.pack()
        root.update()

        entry.insert(0, "abc def")
        entry.selection_range(0, 3)
        entry._copy_selection()
        assert root.clipboard_get() == "abc"

        entry.selection_clear()
        root.clipboard_clear()
        root.clipboard_append("XYZ")
        root.update()
        entry.icursor("end")
        entry.focus_force()
        entry.event_generate("<Control-v>", when="tail")
        root.update()
        assert entry.get() == "abc defXYZ"

        entry.selection_range(0, 3)
        entry.event_generate("<Control-x>", when="tail")
        root.update()
        assert entry.get() == " defXYZ"

        entry.event_generate("<Control-a>", when="tail")
        root.update()
        assert entry.selection_present()

        button = CTkButton(root, text="АНАЛИЗИРОВАТЬ", width=110)
        button.pack()
        root.update_idletasks()
        # 4.8.4 lets ttk auto-size buttons from the active font instead of
        # freezing legacy CustomTkinter pixel widths into character cells.
        assert button.cget("width") in ("", 0, "0")
        assert button.winfo_width() >= button.winfo_reqwidth()

        label = AccessibleLabel(root, text="Порог медленного соединения:", width=220)
        # 220 historical pixels must not become 220 ttk character cells.
        assert len("Порог медленного соединения:") <= int(label.cget("width")) < 60

        combo = CTkOptionMenu(root, values=["Коротко", "Очень длинное значение"], width=100)
        assert int(combo.cget("width")) >= len("Очень длинное значение") + 2
    finally:
        root.destroy()


def _visible_horizontal_overflows(widget):
    failures = []
    for child in widget.winfo_children():
        try:
            if not child.winfo_ismapped():
                continue
            parent_width = widget.winfo_width()
            if parent_width > 1 and child.winfo_x() + child.winfo_width() > parent_width + 3:
                failures.append(child)
            failures.extend(_visible_horizontal_overflows(child))
        except tk.TclError:
            pass
    return failures


def test_minimum_window_has_no_clipped_native_controls():
    app = AudioKnigiApp()
    try:
        app.geometry("1080x760")
        app.ui_mode_var.set("Расширенный")
        app._apply_ui_mode()
        app.update()

        for scale in ("100", "125", "150", "175", "200"):
            app.scale_var.set(scale)
            app._apply_scale(silent=True)
            app.update()
            for name in ("Книга", "Поиск", "Очередь", "История", "Настройки"):
                app.tabview.set(name)
                app.update()
                assert not _visible_horizontal_overflows(app), (
                    f"horizontal overflow on tab {name} at {scale}%"
                )

        # Explicit pixel widths on AccessibleLabel must now be converted.
        label_widths = []
        def collect(widget):
            for child in widget.winfo_children():
                if isinstance(child, ttk.Label):
                    try:
                        label_widths.append(int(child.cget("width") or 0))
                    except Exception:
                        pass
                collect(child)
        collect(app)
        assert max(label_widths or [0]) < 80

        # The three wide data views now expose scrollbars for narrow windows.
        for tree in (app.search_tree, app.queue_tree, app.history_tree):
            assert tree.cget("xscrollcommand")
            assert tree.cget("yscrollcommand")
    finally:
        app.destroy()
