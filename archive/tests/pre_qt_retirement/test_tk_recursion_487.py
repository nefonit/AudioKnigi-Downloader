import inspect
import tkinter as tk

from audioknigi import actions as actions_module
from audioknigi import app as app_module
from audioknigi.ui.easy_home import EasyHome
from audioknigi.ui_kit import CTkScrollableFrame, Tooltip


def test_no_nested_event_pump_in_geometry_callbacks():
    scale_source = inspect.getsource(actions_module.ActionsMixin._apply_scale)
    responsive_source = inspect.getsource(EasyHome.refresh_responsive_layout)
    configure_source = inspect.getsource(EasyHome._on_dashboard_configure)
    scale_code = "\n".join(line for line in scale_source.splitlines() if not line.lstrip().startswith("#"))
    responsive_code = "\n".join(line for line in responsive_source.splitlines() if not line.lstrip().startswith("#"))
    assert "update_idletasks(" not in scale_code
    assert ".update(" not in scale_code
    assert "update_idletasks(" not in responsive_code
    assert ".update(" not in responsive_code
    configure_code = "\n".join(line for line in configure_source.splitlines() if not line.lstrip().startswith("#"))
    assert "after_idle(" not in configure_code
    assert ".after(" in configure_code


def test_recursion_handler_does_not_open_nested_messagebox():
    source = inspect.getsource(app_module.AudioKnigiApp._tk_exception_handler)
    recursion_branch = source.split("if is_recursion:", 1)[1].split("return", 1)[0]
    code_only = "\n".join(line for line in recursion_branch.splitlines() if not line.lstrip().startswith("#"))
    assert "messagebox." not in code_only


def test_scrollable_configure_handlers_are_reentrant_safe():
    content = inspect.getsource(CTkScrollableFrame._on_content_configure)
    canvas = inspect.getsource(CTkScrollableFrame._on_canvas_configure)
    assert "_content_configuring" in content
    assert "_canvas_configuring" in canvas


def test_responsive_layout_stress_without_update_reentry():
    root = tk.Tk()
    root.withdraw()
    try:
        class AppStub:
            def __init__(self):
                self.scale_var = tk.StringVar(master=root, value="125")
        obj = EasyHome.__new__(EasyHome)
        obj.app = AppStub()
        obj.dashboard = tk.Frame(root)
        obj.main_panel = tk.Frame(obj.dashboard)
        obj.sidebar_panel = tk.Frame(obj.dashboard)
        obj.main_panel.grid(row=0, column=0)
        obj.sidebar_panel.grid(row=0, column=1)
        obj._layout_stacked = None
        obj._layout_after = None
        obj._layout_in_progress = False
        for width in [980, 1005, 995, 1010, 970, 1100, 990] * 30:
            obj._apply_responsive_layout(width)
        assert obj._layout_in_progress is False
    finally:
        root.destroy()


def test_tooltip_does_not_bind_destroy_callback():
    source = inspect.getsource(Tooltip.__init__)
    code_only = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
    assert 'bind("<Destroy>"' not in code_only


def test_full_app_can_be_destroyed_without_callback_recursion(tmp_path, monkeypatch):
    # This reproduces the failure that occurred in 4.8.5/4.8.6: destroying the
    # complete widget tree while every tooltip owned a <Destroy> callback could
    # overflow tkinter._substitute before mainloop returned.
    import audioknigi.app as app_mod
    import audioknigi.core as core_mod

    app_dir = tmp_path / "state"
    app_dir.mkdir()
    settings = app_dir / "settings.json"
    settings.write_text('{"first_run_complete": true, "clipboard_auto": false, "scale": 125}', encoding="utf-8")
    monkeypatch.setattr(app_mod, "SETTINGS_FILE", settings)
    monkeypatch.setattr(app_mod, "HISTORY_FILE", app_dir / "history.json")
    monkeypatch.setattr(app_mod, "PLAYER_POSITIONS_FILE", app_dir / "positions.json")
    monkeypatch.setattr(app_mod, "SESSION_STATE_FILE", app_dir / "session.json")
    monkeypatch.setattr(app_mod, "CRASH_REPORT_FILE", app_dir / "crash.txt")

    app = app_mod.AudioKnigiApp()
    # Avoid first-run/background post-startup work influencing this teardown test.
    try:
        app.after(80, app.destroy)
        app.mainloop()
    finally:
        try:
            app.event_bus.close()
        except Exception:
            pass
    # Returning from mainloop without RecursionError is the regression check.
    assert True


def test_focusin_storm_is_coalesced_without_recursion():
    from tkinter import ttk
    from audioknigi.accessibility import AccessibilityManager

    root = tk.Tk()
    button = ttk.Button(root, text="Focus storm")
    button.pack()
    root.update()
    manager = AccessibilityManager(root)
    try:
        manager._install_global_focus_probe()
        for _ in range(1500):
            button.event_generate("<FocusIn>")
        # The FocusIn callbacks only replace the pending widget; all 1500
        # events must share a single zero-delay processor.
        assert manager._pending_focus_widget is button
        assert manager._focus_probe_after_id is not None
        root.update()
        assert manager._focus_probe_after_id is None
        assert manager._focus_probe_active is False
    finally:
        try:
            manager.close()
        except Exception:
            pass
        root.destroy()


def test_focus_accessibility_paths_never_pump_nested_tk_events():
    from audioknigi.accessibility import AccessibilityManager
    from audioknigi.search import SearchMixin

    for method in (AccessibilityManager._show_visual_focus, AccessibilityManager.focus_initial_control, SearchMixin._focus_search_results_for_keyboard):
        source = inspect.getsource(method)
        code_only = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
        assert "update_idletasks(" not in code_only
        assert ".update(" not in code_only


def test_scrollable_focus_autoreveal_is_zero_delay_and_coalesced():
    source = inspect.getsource(CTkScrollableFrame._on_descendant_focus)
    code_only = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
    assert "_focus_scroll_after_id" in source
    assert "_pending_focus_scroll_widget" in source
    assert "after_idle(" not in code_only
    assert ".after(0," in code_only
