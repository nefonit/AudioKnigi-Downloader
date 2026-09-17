import inspect
import json
import threading
import time
from pathlib import Path

import audioknigi.core as core
from audioknigi.brand import DISPLAY_NAME
from audioknigi.accessibility import AccessibilityManager
from audioknigi.dnd import DragDropMixin
from audioknigi.downloader import AdaptiveRangeController, DownloaderMixin
from audioknigi.ui_kit import CTkButton, CTkScrollableFrame
from tkinter import ttk


def test_ctkbutton_is_native_ttk_and_consumes_bootstyle():
    source = inspect.getsource(CTkButton.__init__)
    assert issubclass(CTkButton, ttk.Button)
    assert 'kwargs.pop("bootstyle", None)' in source


def test_dragdrop_docstring_is_real_class_docstring_and_fallbacks_are_safe():
    assert (DragDropMixin.__doc__ or "").startswith("Native Tk drag-and-drop")
    host = DragDropMixin()
    assert host._dnd_easy_mode() is True


def test_load_json_uses_same_lock_as_atomic_writer(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"ok": 1}), encoding="utf-8")
    result = []
    started = threading.Event()

    def reader():
        started.set()
        result.append(core.load_json(path, {}))

    with core._JSON_LOCK:
        thread = threading.Thread(target=reader)
        thread.start()
        assert started.wait(1.0)
        time.sleep(0.05)
        assert not result, "reader must wait while the JSON writer lock is held"
    thread.join(1.0)
    assert result == [{"ok": 1}]


def test_accessibility_ready_announcement_uses_brand_constant():
    source = inspect.getsource(AccessibilityManager._poll_screen_reader)
    assert core.APP_TITLE == DISPLAY_NAME
    assert "DISPLAY_NAME" in source
    assert '"AudioKnigi Downloader готов к работе"' not in source


def test_logical_y_has_root_coordinate_fallback():
    class FakeFrame:
        def winfo_rooty(self):
            return 100

    class FakeWidget:
        def winfo_y(self):
            raise RuntimeError("synthetic hierarchy break")
        def winfo_rooty(self):
            return 175

    value = CTkScrollableFrame._logical_y(FakeFrame(), FakeWidget())
    assert value == 75


def test_adaptive_range_controller_can_recover_workers():
    ctrl = AdaptiveRangeController(8, adaptive=True, min_per_worker=256 * 1024)
    ctrl.last_change -= 5
    for _ in range(6):
        ctrl.observe(8 * 100 * 1024)
    assert ctrl.current_workers() == 4

    ctrl.last_change -= 5
    for _ in range(9):
        ctrl.observe(4 * 512 * 1024)
    assert ctrl.current_workers() == 8


def test_mp3_estimator_has_no_dead_output_mode_variable():
    source = inspect.getsource(DownloaderMixin._estimate_required_space)
    assert 'output_mode = "mp3"' not in source


def test_playlist_json_is_parsed_without_mutating_escaped_slashes():
    source = inspect.getsource(DownloaderMixin._parse_playlist_data)
    assert 'json.loads(playlist_text or "")' in source
    assert 'json.loads((playlist_text or "").replace' not in source
