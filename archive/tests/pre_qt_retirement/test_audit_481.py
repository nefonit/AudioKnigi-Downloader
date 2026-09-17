"""Regression checks for the 4.8.1 source-fragment audit."""
from __future__ import annotations

import inspect
from pathlib import Path
import tkinter as tk

from audioknigi import AudioKnigiApp
from audioknigi.accessibility import AccessibilityManager
from audioknigi.ui_kit import CTkButton, CTkEntry, CTkScrollableFrame

ROOT = Path(__file__).resolve().parents[1]


def check_sources_complete_and_translation_helper():
    # Compiling/importing the real modules is stronger than inspecting a clipped
    # source excerpt.  The helper is part of the application class contract.
    import audioknigi.app
    import audioknigi.ui.easy_home

    assert callable(getattr(AudioKnigiApp, "t", None))
    app_src = (ROOT / "audioknigi" / "app.py").read_text(encoding="utf-8")
    easy_src = (ROOT / "audioknigi" / "ui" / "easy_home.py").read_text(encoding="utf-8")
    compile(app_src, "app.py", "exec")
    compile(easy_src, "easy_home.py", "exec")


def check_bandwidth_slider_signature():
    signature = inspect.signature(AudioKnigiApp.on_bandwidth_slider)
    # bound call receives the Scale value in the second parameter
    params = list(signature.parameters.values())
    assert len(params) >= 2
    assert params[1].default is None


def check_placeholder_contract_and_accessibility():
    root = tk.Tk()
    root.withdraw()
    try:
        external = tk.StringVar(root, value="")
        entry = CTkEntry(root, textvariable=external, placeholder_text="https://example.test/book")
        entry.pack()
        root.update_idletasks()

        # Placeholder/example metadata must never masquerade as user input.
        assert entry.get() == ""
        assert external.get() == ""
        assert entry.placeholder_text == "https://example.test/book"
        assert "Пример:" in entry.accessible_description

        manager = object.__new__(AccessibilityManager)
        manager.app = root
        manager._registered = set()
        manager._last_status = ""
        manager._last_progress_bucket = -1
        manager._tree_bindings = set()
        manager._notebook_bindings = set()
        manager._tk_accessible_checked = False
        manager._tk_accessible_available = False
        manager.bridge = type("Bridge", (), {"active": False})()
        phrase = manager._describe_widget(entry)
        assert "поле ввода" in phrase
        assert "https://example.test/book" in phrase
        assert "пусто" in phrase
    finally:
        root.destroy()


def check_easy_keyboardize_uses_native_focus():
    src = (ROOT / "audioknigi" / "ui" / "easy_home.py").read_text(encoding="utf-8")
    start = src.index("def _keyboardize")
    end = src.index("def _make_quality_card", start)
    block = src[start:end]
    assert "border_width" not in block
    assert "border_color" not in block
    assert "ttk.Button" in block
    assert "takefocus" in block


def check_visible_examples_exist():
    easy_src = (ROOT / "audioknigi" / "ui" / "easy_home.py").read_text(encoding="utf-8")
    settings_src = (ROOT / "audioknigi" / "ui" / "settings_tab.py").read_text(encoding="utf-8")
    assert 'text="Пример: https://audioknigi.com.ua/audio-..."' in easy_src
    assert 'text=f"Пример: {placeholder}"' in settings_src



def check_scrollable_settings_viewport():
    root = tk.Tk()
    root.geometry("500x260")
    try:
        outer = CTkScrollableFrame(root, fg_color="transparent")
        outer.pack(fill="both", expand=True)
        buttons = []
        for i in range(30):
            button = CTkButton(outer, text=f"Настройка {i + 1}")
            button.pack(fill="x", padx=8, pady=4)
            buttons.append(button)
        root.update()
        root.update_idletasks()
        assert isinstance(outer._scroll_canvas, tk.Canvas)
        assert str(outer._scroll_canvas.cget("takefocus")) in ("0", "")
        assert outer.winfo_reqheight() > outer._scroll_canvas.winfo_height()
        before = outer._scroll_canvas.yview()[0]
        buttons[-1].focus_force()
        root.update()
        root.update_idletasks()
        after = outer._scroll_canvas.yview()[0]
        assert after > before
    finally:
        root.destroy()

def main():
    check_sources_complete_and_translation_helper()
    check_bandwidth_slider_signature()
    check_placeholder_contract_and_accessibility()
    check_easy_keyboardize_uses_native_focus()
    check_visible_examples_exist()
    check_scrollable_settings_viewport()
    print("APP/EASY_HOME COMPLETE: OK")
    print("AudioKnigiApp.t(): OK")
    print("BANDWIDTH SLIDER CALLBACK: OK")
    print("PLACEHOLDER DOES NOT POLLUTE STRINGVAR: OK")
    print("VISIBLE + SCREEN-READER EXAMPLES: OK")
    print("NATIVE TTK FOCUS CONTRACT: OK")
    print("SCROLLABLE SETTINGS + FOCUS FOLLOW: OK")
    print("AUDIT 4.8.1: OK")


if __name__ == "__main__":
    main()
