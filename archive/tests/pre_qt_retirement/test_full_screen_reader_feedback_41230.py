import os
import tkinter as tk
from tkinter import ttk

import pytest

from audioknigi.accessibility import AccessibilityManager
from audioknigi.ui_kit import CTk, CTkButton, CTkFrame, CTkLabel, CTkOptionMenu, CTkSlider, CTkSwitch


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


def pump(root, ms=100):
    root.after(ms, root.quit)
    root.mainloop()


def test_checkbox_announces_new_state_immediately_after_space():
    root = CTk()
    try:
        var = tk.BooleanVar(root, value=True)
        switch = CTkSwitch(root, text="Воспроизводить звуки событий", variable=var)
        switch.pack()
        manager = AccessibilityManager(root)
        bridge = RecordingBridge()
        manager.bridge = bridge
        manager.register(switch)
        root.update()
        root.focus_force()
        switch.focus_set()
        root.update()
        switch.event_generate("<KeyPress-space>")
        root.update()
        switch.event_generate("<KeyRelease-space>")
        pump(root, 90)
        assert var.get() is False
        assert any("Воспроизводить звуки событий, не отмечен" in msg for msg, _ in bridge.messages)
    finally:
        root.destroy()


def test_combobox_uses_human_label_not_tcl_variable_name():
    root = CTk()
    try:
        row = CTkFrame(root); row.pack()
        CTkLabel(row, text="Язык интерфейса:").pack(side="left")
        var = tk.StringVar(root, value="Русский")
        combo = CTkOptionMenu(row, values=["Русский", "English"], variable=var)
        combo.pack(side="left")
        manager = AccessibilityManager(root)
        root.update()
        desc = manager._describe_widget(combo)
        assert desc.startswith("Язык интерфейса, список")
        assert "Русский" in desc
        assert "PY_VAR" not in desc
    finally:
        root.destroy()


def test_combobox_selection_change_is_spoken():
    root = CTk()
    try:
        row = CTkFrame(root); row.pack()
        CTkLabel(row, text="Язык интерфейса:").pack(side="left")
        var = tk.StringVar(root, value="Русский")
        combo = CTkOptionMenu(row, values=["Русский", "English"], variable=var)
        combo.pack(side="left")
        manager = AccessibilityManager(root)
        bridge = RecordingBridge(); manager.bridge = bridge
        manager.register(combo)
        root.update()
        combo.set("English")
        combo.event_generate("<<ComboboxSelected>>")
        pump(root, 90)
        assert any("Язык интерфейса, выбрано: English" in msg for msg, _ in bridge.messages)
    finally:
        root.destroy()


def test_slider_change_is_spoken_after_keyboard_adjustment():
    root = CTk()
    try:
        value = tk.DoubleVar(root, value=50)
        slider = CTkSlider(root, from_=0, to=100, variable=value, width=300)
        slider.accessible_name = "Громкость звуков программы"
        slider.pack()
        manager = AccessibilityManager(root)
        bridge = RecordingBridge(); manager.bridge = bridge
        manager.register(slider)
        root.update()
        root.focus_force()
        slider.focus_set(); root.update()
        slider.set(60)
        slider.event_generate("<KeyRelease-Right>")
        pump(root, 90)
        assert any("Громкость звуков программы, 60.0" in msg for msg, _ in bridge.messages)
    finally:
        root.destroy()


def test_notebook_focus_description_contains_selected_tab_and_position():
    root = CTk()
    try:
        notebook = ttk.Notebook(root, takefocus=True)
        a = ttk.Frame(notebook); b = ttk.Frame(notebook)
        notebook.add(a, text="Книга"); notebook.add(b, text="Настройки")
        notebook.pack(); notebook.select(b)
        root.update()
        manager = AccessibilityManager(root)
        desc = manager._describe_widget(notebook)
        assert desc.startswith("Навигация по вкладкам, вкладки")
        assert "Настройки, вкладка 2 из 2" in desc
    finally:
        root.destroy()


def test_tab_navigation_skips_disabled_control():
    root = CTk()
    try:
        one = CTkButton(root, text="Первый"); one.pack()
        disabled = CTkButton(root, text="Недоступный", state="disabled"); disabled.pack()
        three = CTkButton(root, text="Третий"); three.pack()
        manager = AccessibilityManager(root)
        manager.bridge = RecordingBridge()
        manager.install()
        root.update()
        root.focus_force()
        one.focus_set(); root.update()
        one.event_generate("<Tab>")
        root.update()
        assert root.focus_get() is three
        assert disabled not in manager._focusable_widgets(root)
    finally:
        root.destroy()



def test_radio_announces_selected_state_after_space():
    root = CTk()
    try:
        var = tk.StringVar(root, value="a")
        radio = ttk.Radiobutton(root, text="Вариант Б", variable=var, value="b", takefocus=True)
        radio.pack()
        manager = AccessibilityManager(root)
        bridge = RecordingBridge(); manager.bridge = bridge
        manager.register(radio)
        root.update(); root.focus_force(); radio.focus_set(); root.update()
        radio.event_generate("<KeyPress-space>"); root.update()
        radio.event_generate("<KeyRelease-space>")
        pump(root, 90)
        assert var.get() == "b"
        assert any("Вариант Б, выбрано" in msg for msg, _ in bridge.messages)
    finally:
        root.destroy()


def test_button_without_status_change_confirms_action():
    root = CTk()
    try:
        hit = {"count": 0}
        button = CTkButton(root, text="Применить", command=lambda: hit.__setitem__("count", hit["count"] + 1))
        button.pack()
        manager = AccessibilityManager(root)
        bridge = RecordingBridge(); manager.bridge = bridge
        manager.register(button)
        root.update(); root.focus_force(); button.focus_set(); root.update()
        button.event_generate("<KeyPress-space>"); root.update()
        button.event_generate("<KeyRelease-space>")
        pump(root, 160)
        assert hit["count"] == 1
        assert any("Применить. Действие выполнено" in msg for msg, _ in bridge.messages)
    finally:
        root.destroy()


def test_readonly_text_stays_focusable_and_reads_lines():
    root = CTk()
    try:
        text = tk.Text(root, takefocus=True)
        text.insert("1.0", "Первая строка\nВторая строка\nТретья строка")
        text.configure(state="disabled")
        text.accessible_name = "Журнал программы"
        text.pack()
        manager = AccessibilityManager(root)
        bridge = RecordingBridge(); manager.bridge = bridge
        manager.register(text)
        root.update(); root.focus_force(); text.focus_set(); root.update()
        assert text in manager._focusable_widgets(root)
        assert "только чтение" in manager._describe_widget(text)
        text.event_generate("<Down>")
        root.update()
        assert any("Строка 2 из 3. Вторая строка" in msg for msg, _ in bridge.messages)
    finally:
        root.destroy()


def test_context_menu_announces_active_item():
    root = CTk()
    try:
        menu = tk.Menu(root, tearoff=False)
        menu.add_command(label="Открыть файл")
        menu.add_command(label="Скачать заново")
        manager = AccessibilityManager(root)
        bridge = RecordingBridge(); manager.bridge = bridge
        manager._bind_menu(menu)
        menu.activate(1)
        menu.event_generate("<<MenuSelect>>")
        root.update()
        assert any("Скачать заново, пункт меню" in msg for msg, _ in bridge.messages)
    finally:
        root.destroy()

def test_every_advanced_tab_focusable_has_human_semantics(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from audioknigi import AudioKnigiApp

    app = AudioKnigiApp()
    try:
        app.update()
        app.set_ui_mode("advanced")
        app.update()
        manager = app.accessibility
        for tab in ("Книга", "Поиск", "Очередь", "История", "Настройки"):
            app.tabview.set(tab)
            app.update()
            descriptions = [manager._describe_widget(w) for w in manager._focusable_widgets(app)]
            assert descriptions, tab
            assert not [d for d in descriptions if "PY_VAR" in d], (tab, descriptions)
            assert not [d for d in descriptions if d.startswith("Элемент")], (tab, descriptions)
    finally:
        app.destroy()
