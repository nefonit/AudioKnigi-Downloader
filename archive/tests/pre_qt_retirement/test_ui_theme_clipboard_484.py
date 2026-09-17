"""4.8.4 regression coverage for Python 3.14 editing, sizing and live themes."""
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

from audioknigi import AudioKnigiApp
from audioknigi import ui_kit
from audioknigi.ui_kit import CTkEntry, CTkLabel, _pixel_width_to_chars


def test_small_legacy_pixel_widths_do_not_become_character_counts():
    assert _pixel_width_to_chars(24) <= 4
    assert _pixel_width_to_chars(28) <= 4
    assert _pixel_width_to_chars(1) == 1

    root = tk.Tk()
    try:
        dot = CTkLabel(root, text="●", width=24)
        count = CTkLabel(root, text="0", width=28)
        assert int(dot.cget("width")) <= 4
        assert int(count.cget("width")) <= 4
    finally:
        root.destroy()


def test_single_physical_shortcut_handler_supports_windows_layout_keycodes(monkeypatch):
    root = tk.Tk()
    try:
        entry = CTkEntry(root)
        entry.pack()
        entry.insert(0, "abc")
        entry.icursor("end")
        root.clipboard_clear()
        root.clipboard_append("XYZ")
        monkeypatch.setattr(ui_kit.sys, "platform", "win32")

        result = entry._physical_edit_shortcut(SimpleNamespace(state=0x0004, keycode=86, keysym="Cyrillic_em"))
        assert result == "break"
        assert entry.get() == "abcXYZ"

        entry.selection_range(0, 3)
        result = entry._physical_edit_shortcut(SimpleNamespace(state=0x0004, keycode=67, keysym="Cyrillic_es"))
        assert result == "break"
        assert root.clipboard_get() == "abc"

        assert not entry.bind("<Control-KeyPress>")
    finally:
        root.destroy()


def test_live_light_theme_repaints_native_widgets_and_returns_to_dark():
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        app.geometry("1080x760")
        app.theme_var.set("light")
        app._apply_theme()
        app.update_idletasks()

        dark_backgrounds = {
            "#1e1e1e", "#252525", "#2d2d2d", "#303030", "#333333",
            "#383838", "#444444", "#0a1b31", "#0f4c83", "#123052",
        }
        leftovers = []

        def walk(widget):
            if isinstance(widget, (tk.Frame, tk.Label, tk.Text, tk.Canvas)):
                try:
                    bg = str(widget.cget("bg")).lower()
                    if bg in dark_backgrounds:
                        leftovers.append((widget.winfo_class(), bg))
                except tk.TclError:
                    pass
            for child in widget.winfo_children():
                walk(child)

        walk(app)
        assert leftovers == []
        assert app.root_content.cget("bg").lower() == "#f5f7fa"
        assert ttk.Style(app).lookup("AudioKnigi.TEntry", "fieldbackground").lower() == "#ffffff"
        assert app.speed_canvas.cget("bg").lower() == "#f5f7fa"

        app.theme_var.set("dark")
        app._apply_theme()
        app.update_idletasks()
        assert app.root_content.cget("bg").lower() == "#1e1e1e"
        assert app.speed_canvas.cget("bg").lower() == "#1e1e1e"
    finally:
        app.destroy()


def test_default_125_percent_easy_layout_keeps_real_text_controls_visible():
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        app.geometry("1080x760")
        app.ui_mode_var.set("Простой")
        app._apply_ui_mode()
        app.scale_var.set("125")
        app._apply_scale(silent=True)
        app.update_idletasks()

        # The quality choices were previously squeezed by decorative 24/28px
        # elements that native Tk interpreted as character widths.  Compare the
        # actual caption pixels rather than ttk's requested width (which also
        # includes theme padding and the radio indicator).
        import tkinter.font as tkfont
        style = ttk.Style(app)
        radio_font = tkfont.Font(root=app, font=style.lookup("AudioKnigi.TRadiobutton", "font"))
        for radio in app.easy_home_view.quality_indicators.values():
            assert radio.winfo_width() >= radio_font.measure(radio.cget("text")) + 18

        # Status text must retain real space next to the dot and optional icon.
        status_labels = [
            child for child in app.easy_status_dot.master.winfo_children()
            if isinstance(child, ttk.Label)
        ]
        assert status_labels
        assert max(label.winfo_width() for label in status_labels) >= 150
    finally:
        app.destroy()
