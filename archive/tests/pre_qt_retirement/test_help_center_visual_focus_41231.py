import tkinter as tk

from audioknigi.accessibility import AccessibilityManager
from audioknigi.help_center import HelpCenter
from audioknigi.ui_kit import CTk, CTkButton, CTkEntry, CTkToplevel, set_appearance_mode


class RecordingBridge:
    def __init__(self):
        self.active = True
        self.backend_name = "NVDA"
        self.messages = []

    def announce(self, text, *, interrupt=False):
        self.messages.append((str(text), bool(interrupt)))
        return True

    def refresh(self):
        return True

    def diagnostic_summary(self):
        return "backend=NVDA | active=True | processes=NVDA"

    def close(self):
        return None


def pump(root, ms=180):
    root.after(ms, root.quit)
    root.mainloop()


def make_help_app():
    app = CTk()
    app.geometry("1000x760")
    app.language = "ru"
    app.brand_window_icon = None
    app.brand_icon_small = None
    app.copy_last_crash_report = lambda: None
    translations = {
        "help_window_title": "Справка",
        "help_label": "СПРАВКА",
        "help_center": "Справочный центр",
        "help_text_accessible": "Текст справки",
        "copy_error_report": "Копировать отчёт",
        "help_shortcuts_hint": "Клавиатурные подсказки",
        "app_tagline": "",
        "help_choose_topic": "Выберите тему",
        "help_short_intro": "Введение",
    }
    app.t = lambda key, **kwargs: translations.get(key, key)
    manager = AccessibilityManager(app)
    manager.bridge = RecordingBridge()
    app.accessibility = manager
    manager.install()
    return app, manager


def test_visual_focus_ring_is_larger_than_focused_button_and_moves_to_entry():
    root = CTk()
    try:
        root.geometry("700x300")
        button = CTkButton(root, text="Первая кнопка")
        button.pack(padx=50, pady=35)
        entry = CTkEntry(root)
        entry.pack(padx=50, pady=35)
        manager = AccessibilityManager(root)
        manager.bridge = RecordingBridge()
        manager.install()
        root.update(); root.focus_force(); button.focus_set(); root.update()

        ring = manager._visual_focus_ring
        assert manager._visual_focus_widget is button
        assert ring is not None and ring.winfo_ismapped()
        assert ring.winfo_width() >= button.winfo_width() + 3
        assert ring.winfo_height() >= button.winfo_height() + 3

        entry.focus_set(); root.update()
        assert manager._visual_focus_widget is entry
        assert manager._visual_focus_ring is not None
        assert manager._visual_focus_ring.winfo_ismapped()
    finally:
        root.destroy()


def test_readonly_text_uses_theme_aware_three_pixel_focus_highlight():
    try:
        for mode, expected in (("light", "#005a9e"), ("dark", "#ffd400")):
            set_appearance_mode(mode)
            root = CTk()
            try:
                text = tk.Text(root, takefocus=True, highlightthickness=1)
                text.insert("1.0", "Справка")
                text.configure(state="disabled")
                text.pack()
                manager = AccessibilityManager(root)
                manager.bridge = RecordingBridge()
                manager.install()
                root.update(); root.focus_force(); text.focus_set(); root.update()
                assert manager._visual_focus_widget is text
                assert int(text.cget("highlightthickness")) == 3
                assert str(text.cget("highlightcolor")).lower() == expected
            finally:
                root.destroy()
    finally:
        set_appearance_mode("system")


def test_help_topic_enter_moves_focus_to_document_and_reads_first_paragraph():
    app, manager = make_help_app()
    help_center = None
    try:
        help_center = HelpCenter(app, "settings")
        help_center.win.update()
        help_center.win.focus_force()
        topic_button = help_center.topic_buttons["settings"]
        topic_button.focus_set(); help_center.win.update()
        topic_button.invoke()
        pump(help_center.win, 220)

        assert help_center.win.focus_get() is help_center.text
        assert help_center.text.accessible_read_mode == "paragraph"
        spoken = [m for m, _ in manager.bridge.messages]
        assert any("Текст справки" in m and "только чтение" in m.lower() for m in spoken)
        assert any("Абзац 1 из" in m and "Основные" in m for m in spoken)

        help_center.text.event_generate("<Down>")
        help_center.win.update()
        assert any("Абзац 2 из" in m for m, _ in manager.bridge.messages)
    finally:
        if help_center is not None:
            try: help_center.win.destroy()
            except Exception: pass
        app.destroy()


def test_shift_tab_from_help_document_returns_to_current_topic_button():
    app, manager = make_help_app()
    help_center = None
    try:
        help_center = HelpCenter(app, "accessibility")
        help_center.win.update(); help_center.win.focus_force()
        help_center.show("accessibility", focus_text=True)
        pump(help_center.win, 80)
        assert help_center.win.focus_get() is help_center.text
        help_center.text.event_generate("<Shift-Tab>")
        help_center.win.update()
        assert help_center.win.focus_get() is help_center.topic_buttons["accessibility"]
    finally:
        if help_center is not None:
            try: help_center.win.destroy()
            except Exception: pass
        app.destroy()


def test_tab_navigation_does_not_escape_active_toplevel():
    root = CTk()
    top = None
    try:
        main_button = CTkButton(root, text="Главное окно")
        main_button.pack()
        top = CTkToplevel(root)
        one = CTkButton(top, text="Диалог один"); one.pack()
        two = CTkButton(top, text="Диалог два"); two.pack()
        manager = AccessibilityManager(root)
        manager.bridge = RecordingBridge()
        manager.install(); manager.refresh(top)
        root.update(); top.update(); top.focus_force(); one.focus_set(); top.update()
        one.event_generate("<Tab>")
        top.update()
        assert top.focus_get() is two
        assert root.focus_get() is two
        assert main_button not in manager._focusable_widgets(manager._focus_scope(one))
    finally:
        if top is not None:
            try: top.destroy()
            except Exception: pass
        root.destroy()

def test_real_advanced_tabs_visual_focus_covers_every_focusable(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from audioknigi import AudioKnigiApp

    app = AudioKnigiApp()
    try:
        # Keep this audit visual/focus-only; no real screen reader is needed.
        app.accessibility.bridge = type(
            "SilentBridge",
            (),
            {"active": False, "close": lambda self: None},
        )()
        app.update()
        app.set_ui_mode("advanced")
        app.update()
        manager = app.accessibility
        checked = 0
        for tab in ("Книга", "Поиск", "Очередь", "История", "Настройки"):
            app.tabview.set(tab)
            app.update()
            for widget in manager._focusable_widgets(app):
                widget.focus_set()
                app.update()
                if app.focus_get() is not widget:
                    continue
                checked += 1
                assert manager._visual_focus_widget is widget, (tab, widget)
                if isinstance(widget, tk.Text):
                    assert int(widget.cget("highlightthickness")) >= 3, (tab, widget)
                else:
                    ring = manager._visual_focus_ring
                    assert ring is not None and ring.winfo_ismapped(), (tab, widget)
        assert checked >= 50
    finally:
        app.destroy()

def test_default_readonly_text_description_matches_five_unit_page_step():
    root = CTk()
    try:
        text = tk.Text(root, takefocus=True)
        text.insert("1.0", "\n".join(f"Строка {i}" for i in range(1, 12)))
        text.configure(state="disabled")
        text.pack()
        manager = AccessibilityManager(root)
        manager.bridge = RecordingBridge()
        manager.install(); manager.refresh(root)
        root.update()

        assert "по пять строк" in text.accessible_description
        assert "по десять строк" not in text.accessible_description

        root.focus_force(); text.focus_set(); root.update()
        manager.read_readonly_text(text, 0)
        text.event_generate("<Next>")
        root.update()
        assert getattr(text, "_accessible_read_line", None) == 5
    finally:
        root.destroy()

