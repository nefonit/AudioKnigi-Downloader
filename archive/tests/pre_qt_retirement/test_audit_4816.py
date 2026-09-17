from __future__ import annotations

import inspect
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import audioknigi.player as player_module
import audioknigi.ui_kit as ui_kit_module
from audioknigi.actions import ActionsMixin
from audioknigi.app import AudioKnigiApp
from audioknigi.player import PlayerMixin
from audioknigi.queue_manager import QueueMixin
from audioknigi.templates import template_values
from audioknigi.ui_kit import CTkScrollableFrame, Tooltip


class Var:
    def __init__(self, value=None): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


class Button:
    def __init__(self): self.options = {}
    def configure(self, **kwargs): self.options.update(kwargs)


def test_reported_source_truncation_and_missing_t_are_false_positives():
    source = Path("audioknigi/actions.py").read_text(encoding="utf-8")
    compile(source, "actions.py", "exec")
    assert "tags.add(TIT2(encoding=3, text=book_title))" in source
    assert callable(AudioKnigiApp.t)


def test_prismatoid_distribution_runtime_import_remains_prism():
    source = Path("audioknigi/accessibility.py").read_text(encoding="utf-8")
    assert "from prism import BackendId, Context" in source


def test_player_startup_grace_does_not_false_stop(monkeypatch):
    class Music:
        @staticmethod
        def get_pos(): return -1
        @staticmethod
        def get_busy(): return False
    class Mixer:
        music = Music()
        @staticmethod
        def get_init(): return True
    monkeypatch.setattr(player_module, "pygame", SimpleNamespace(mixer=Mixer()))

    class Host(PlayerMixin):
        def __init__(self):
            self.player_playing = True
            self.player_paused = False
            self.player_duration = 120.0
            self.player_base_position = 0.0
            self._player_started_at = time.monotonic()
            self._player_last_absolute = 0.0
            self.player_position_var = Var(0.0)
            self.player_file = Path("chapter.mp3")
            self.player_pause_btn = Button()
            self.player_stop_btn = Button()
            self.scheduled = 0
        def winfo_exists(self): return True
        def after(self, *_args): self.scheduled += 1
        def _save_current_player_position(self, *args, **kwargs): pass
        def _update_player_time_text(self, _position): pass

    host = Host()
    host._player_tick()
    assert host.player_playing is True
    assert host.scheduled == 1


def test_queue_lazy_lock_creation_is_singleton_under_contention():
    class Host(QueueMixin): pass
    host = Host()
    ids = []
    gate = threading.Barrier(16)
    def worker():
        gate.wait()
        ids.append(id(host._queue_state_lock()))
    threads = [threading.Thread(target=worker) for _ in range(16)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert len(set(ids)) == 1


def test_queue_snapshot_apply_has_safe_defaults_on_partial_host():
    host = QueueMixin()
    host._apply_queue_runtime_snapshot({
        "naming_mode": "",
        "output_mode": None,
        "audio_preset": "",
        "normalization_mode": None,
    })
    assert host.runtime_naming_mode == "number"
    assert host.runtime_output_mode == "mp3"
    assert host.runtime_audio_preset == "copy"
    assert host.runtime_normalization_mode == "off"


def test_queue_worker_status_methods_are_thread_marshalled_by_actions_mixin():
    for method_name in ("set_status", "set_stage", "set_progress"):
        source = inspect.getsource(getattr(ActionsMixin, method_name))
        assert "self.ui(" in source


def test_theme_color_pairs_resolve_by_active_theme(monkeypatch):
    monkeypatch.setattr(ui_kit_module, "_CURRENT_DARK", False)
    pair = ("#F5F7FA", "#1E1E1E")
    assert ui_kit_module._theme_background(pair) == "#F5F7FA"
    monkeypatch.setattr(ui_kit_module, "_CURRENT_DARK", True)
    assert ui_kit_module._theme_background(pair) == "#1E1E1E"


def test_template_year_zero_is_preserved():
    assert template_values({"title": "Book", "year": 0})["Year"] == "0"


def test_linux_wheel_matches_single_windows_notch(monkeypatch):
    calls = []
    host = object.__new__(CTkScrollableFrame)
    host._mac_scroll_remainder = 0.0
    host._scroll_canvas = SimpleNamespace(yview_scroll=lambda steps, unit: calls.append((steps, unit)))
    monkeypatch.setattr(ui_kit_module.sys, "platform", "linux")
    assert host._on_mousewheel(SimpleNamespace(num=4, delta=0)) == "break"
    assert host._on_mousewheel(SimpleNamespace(num=5, delta=0)) == "break"
    assert calls == [(-1, "units"), (1, "units")]


def test_textbox_notifies_scrollable_ancestor_in_source():
    source = inspect.getsource(ui_kit_module.CTkTextbox.__init__)
    assert "_notify_scrollable_ancestor(self)" in source


def test_queue_and_search_tabs_use_live_string_var_helpers_and_dispose_tooltips():
    queue_source = Path("audioknigi/ui/queue_tab.py").read_text(encoding="utf-8")
    search_source = Path("audioknigi/ui/search_tab.py").read_text(encoding="utf-8")
    assert 'self._ensure_string_var("queue_url_var"' in queue_source
    assert 'self._ensure_string_var("search_query_var"' in search_source
    assert "tooltip.dispose()" in queue_source
    assert "tooltip.dispose()" in search_source
    assert 'bind("<ButtonPress-1>", app._queue_drag_press)' in queue_source
    assert 'bind("<ButtonPress-1>", app._queue_drag_press, add="+")' not in queue_source


def test_settings_shortcut_help_wraps_responsively():
    source = Path("audioknigi/ui/settings_tab.py").read_text(encoding="utf-8")
    assert "wraplength=980" not in source
    assert "shortcuts_label.configure(wraplength=max(260, width - 36))" in source


def test_tooltip_explicit_dispose_releases_bindings():
    import tkinter as tk
    root = tk.Tk(); root.withdraw()
    try:
        label = tk.Label(root, text="x")
        label.pack()
        tip = Tooltip(label, "help")
        assert tip._bindings
        tip.dispose()
        assert tip._bindings == []
    finally:
        root.destroy()
