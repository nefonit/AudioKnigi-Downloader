"""4.12.31 theme hardening: contrast, state feedback and live System theme."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from audioknigi import AudioKnigiApp, ui_kit


def _lum(root, color):
    r, g, b = root.winfo_rgb(str(color))
    channels = [value / 65535 for value in (r, g, b)]
    channels = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(root, a, b):
    high, low = sorted((_lum(root, a), _lum(root, b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _style_pair(style, name, state=()):
    return (
        style.lookup(name, "foreground", state),
        style.lookup(name, "background", state),
    )


def test_semantic_buttons_are_readable_and_have_distinct_hover_pressed_states():
    root = tk.Tk()
    root.withdraw()
    try:
        style = ttk.Style(root)
        names = (
            "Primary", "Success", "Info", "Warning", "Danger",
            "PrimaryOutline", "SecondaryOutline", "SuccessOutline",
            "InfoOutline", "WarningOutline", "DangerOutline",
        )
        for dark in (True, False):
            ui_kit.configure_accessible_styles(root, dark=dark)
            for key in names:
                name = f"AudioKnigi.{key}.TButton"
                normal = _style_pair(style, name)
                active = _style_pair(style, name, ("active",))
                pressed = _style_pair(style, name, ("pressed",))
                disabled = _style_pair(style, name, ("disabled",))
                for state_name, (fg, bg) in (
                    ("normal", normal), ("active", active),
                    ("pressed", pressed), ("disabled", disabled),
                ):
                    assert _contrast(root, fg, bg) >= 4.5, (dark, key, state_name, fg, bg)
                assert active[1].lower() != normal[1].lower(), (dark, key, "hover has no visual change")
                assert pressed[1].lower() != active[1].lower(), (dark, key, "pressed has no visual change")
    finally:
        root.destroy()


def test_control_borders_and_focus_colors_meet_non_text_contrast():
    root = tk.Tk()
    root.withdraw()
    try:
        for dark in (True, False):
            ui_kit.configure_accessible_styles(root, dark=dark)
            colors = dict(ui_kit._RUNTIME_COLORS)
            assert _contrast(root, colors["border"], colors["panel"]) >= 3.0
            assert _contrast(root, colors["accent"], colors["panel"]) >= 3.0
            focus = "#FFD400" if dark else "#005A9E"
            assert _contrast(root, focus, colors["panel"]) >= 3.0
            assert _contrast(root, focus, colors["bg"]) >= 3.0
    finally:
        root.destroy()


def test_hidden_easy_cards_have_theme_specific_surfaces_and_readable_labels():
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        expected = {
            "dark": {"confirm": "#2f353b", "action": "#3a3030"},
            "light": {"confirm": "#f1f7fd", "action": "#fff3f1"},
        }
        for mode in ("dark", "light"):
            app.theme_var.set(mode)
            app._apply_theme()
            app.update_idletasks()
            assert app.easy_confirm_frame.cget("bg").lower() == expected[mode]["confirm"]
            assert app.easy_action_frame.cget("bg").lower() == expected[mode]["action"]

            # The visible static heading on the confirmation card exercises the
            # custom Tk-label foreground resolver; dynamic labels use the same path.
            heading = next(
                child for child in app.easy_confirm_frame.winfo_children()
                if isinstance(child, tk.Label) and "Проверьте" in str(child.cget("text") or "")
            )
            assert _contrast(app, heading.cget("fg"), heading.cget("bg")) >= 4.5
    finally:
        app.destroy()


def test_system_theme_repaints_when_windows_appearance_changes(monkeypatch):
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        monkeypatch.setattr(ui_kit, "_system_appearance", lambda: "Light")
        app.theme_var.set("system")
        app._apply_theme()
        app.update_idletasks()
        assert app._system_theme_effective == "light"
        assert ui_kit._RUNTIME_COLORS["bg"].lower() == "#f5f7fa"

        monkeypatch.setattr(ui_kit, "_system_appearance", lambda: "Dark")
        app._poll_system_theme()
        app.update_idletasks()
        assert app._system_theme_effective == "dark"
        assert ui_kit._RUNTIME_COLORS["bg"].lower() == "#1e1e1e"
        assert app.easy_confirm_frame.cget("bg").lower() == "#2f353b"
    finally:
        app._cancel_system_theme_watch()
        app.destroy()


def test_external_keyboard_focus_ring_is_theme_aware(monkeypatch):
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    app.geometry("1100x800+0+0")
    try:
        app.deiconify()
        app.ui_mode_var.set("Простой")
        app._apply_ui_mode()
        app.update()
        for mode, expected in (("light", "#005a9e"), ("dark", "#ffd400")):
            app.theme_var.set(mode)
            app._apply_theme()
            app.update()
            app.accessibility._hide_visual_focus()
            app.accessibility._show_visual_focus(app.easy_download_btn)
            ring = app.accessibility._visual_focus_ring
            assert ring is not None
            assert ring.cget("bg").lower() == expected
    finally:
        app.destroy()


def _widget_text(widget):
    text = ""
    try:
        text = str(widget.cget("text") or "")
    except Exception:
        pass
    if not text:
        try:
            variable = widget.cget("textvariable")
            if variable:
                text = str(widget.getvar(variable) or "")
        except Exception:
            pass
    return " ".join(text.split())


def _normal_widget_colors(root, widget):
    if isinstance(widget, ttk.Widget):
        style = ttk.Style(root)
        try:
            name = str(widget.cget("style") or widget.winfo_class())
        except Exception:
            name = widget.winfo_class()
        fg = style.lookup(name, "foreground")
        if isinstance(widget, (ttk.Entry, ttk.Combobox)):
            bg = style.lookup(name, "fieldbackground") or style.lookup(name, "background")
        else:
            bg = style.lookup(name, "background")
        return fg, bg
    fg = bg = ""
    for option in ("fg", "foreground"):
        try:
            fg = str(widget.cget(option) or "")
            if fg:
                break
        except Exception:
            pass
    for option in ("bg", "background"):
        try:
            bg = str(widget.cget(option) or "")
            if bg:
                break
        except Exception:
            pass
    return fg, bg


def _walk(widget):
    yield widget
    try:
        children = widget.winfo_children()
    except Exception:
        children = ()
    for child in children:
        yield from _walk(child)


def _assert_text_contrast(root):
    text_types = (
        tk.Label, tk.Text, tk.Entry, tk.Button,
        ttk.Label, ttk.Button, ttk.Entry, ttk.Combobox,
        ttk.Radiobutton, ttk.Checkbutton,
    )
    failures = []
    for widget in _walk(root):
        if not isinstance(widget, text_types):
            continue
        text = _widget_text(widget)
        if not text and not isinstance(widget, (tk.Text, tk.Entry, ttk.Entry, ttk.Combobox)):
            continue
        fg, bg = _normal_widget_colors(root, widget)
        if not fg or not bg:
            continue
        try:
            ratio = _contrast(root, fg, bg)
        except tk.TclError:
            continue
        if ratio < 4.5:
            failures.append((str(widget), widget.winfo_class(), text[:80], fg, bg, round(ratio, 2)))
    assert not failures, failures[:20]


def test_all_main_ui_text_across_direct_and_system_themes_meets_aa(monkeypatch):
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        cases = (
            ("dark", None),
            ("light", None),
            ("system", "Light"),
            ("system", "Dark"),
        )
        for mode, system_value in cases:
            if system_value is not None:
                monkeypatch.setattr(ui_kit, "_system_appearance", lambda value=system_value: value)
            app.theme_var.set(mode)
            app._apply_theme()
            app.update_idletasks()
            _assert_text_contrast(app)

            app.ui_mode_var.set("Расширенный")
            app._apply_ui_mode()
            for tab in ("Книга", "Поиск", "Очередь", "История", "Настройки"):
                app.tabview.set(tab)
                app.update_idletasks()
                _assert_text_contrast(app)
    finally:
        app._cancel_system_theme_watch()
        app.destroy()
