import tkinter as tk
from pathlib import Path

from audioknigi.ui_kit import ensure_app_string_var


class DummyApp:
    pass


def test_shared_string_var_helper_uses_fallback_for_non_tk_host():
    root = tk.Tk()
    root.withdraw()
    try:
        frame = tk.Frame(root)
        app = DummyApp()
        var = ensure_app_string_var(app, frame, "query_var", "hello")
        assert var.get() == "hello"
        assert app.query_var is var
        assert ensure_app_string_var(app, frame, "query_var", "other") is var
    finally:
        root.destroy()


def test_tabs_delegate_to_shared_helper_and_cleanup_is_present():
    base = Path(__file__).resolve().parents[1]
    settings = (base / "audioknigi/ui/settings_tab.py").read_text(encoding="utf-8")
    queue = (base / "audioknigi/ui/queue_tab.py").read_text(encoding="utf-8")
    search = (base / "audioknigi/ui/search_tab.py").read_text(encoding="utf-8")
    assert "ensure_app_string_var(self.app, self.frame" in settings
    assert "ensure_app_string_var(self.app, self.frame" in queue
    assert "ensure_app_string_var(self.app, self.frame" in search
    assert "install_destroy_cleanup(self.frame, self._on_frame_destroy)" in queue
    assert "install_destroy_cleanup(self.frame, self._on_frame_destroy)" in search
    assert 'bind("<Destroy>"' not in queue
    assert 'bind("<Destroy>"' not in search
    assert 'bind("<ButtonPress-1>", app._queue_drag_press)' in queue
    assert 'bind("<ButtonPress-1>", app._queue_drag_press, add="+")' not in queue


def test_settings_hotkey_wrap_is_dynamic():
    base = Path(__file__).resolve().parents[1]
    settings = (base / "audioknigi/ui/settings_tab.py").read_text(encoding="utf-8")
    assert 'outer.bind("<Configure>", resize_shortcuts, add="+")' in settings
    assert "shortcuts_label.configure(wraplength=max(260, width - 36))" in settings
