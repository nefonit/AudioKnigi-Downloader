from __future__ import annotations

import inspect
import tkinter as tk
from types import SimpleNamespace

import pytest

from audioknigi.app import AudioKnigiApp
from audioknigi.core import safe_normalization_mode
from audioknigi.downloader import DownloaderMixin
from audioknigi.library_visuals import LibraryVisualMixin
from audioknigi.ui.settings_tab import SettingsTab
from audioknigi.ui_kit import CTkScrollableFrame, install_destroy_cleanup


def test_normalization_modes_keep_legacy_single_and_reject_unknown():
    assert safe_normalization_mode("off") == "off"
    assert safe_normalization_mode("single") == "single"
    assert safe_normalization_mode("two_pass") == "two_pass"
    assert safe_normalization_mode("BROKEN", "off") == "off"
    assert safe_normalization_mode(None, "single") == "single"


def test_downloader_still_implements_single_pass_normalization():
    host = SimpleNamespace(runtime_normalization_mode="single")
    value = DownloaderMixin._normalization_filter_for_track(host, "unused.mp3", None, None)
    assert value.startswith("loudnorm=")


def test_focus_easy_url_entry_supports_app_alias_and_component_fallback():
    class Entry:
        def __init__(self):
            self.focused = 0
        def focus_set(self):
            self.focused += 1

    direct = Entry()
    host = SimpleNamespace(easy_url_entry=direct)
    assert AudioKnigiApp._focus_easy_url_entry(host) is True
    assert direct.focused == 1

    nested = Entry()
    host = SimpleNamespace(easy_home_view=SimpleNamespace(easy_url_entry=nested))
    assert AudioKnigiApp._focus_easy_url_entry(host) is True
    assert nested.focused == 1


def test_destroy_cleanup_normal_call_and_explicit_owner_are_safe():
    root = tk.Tk()
    root.withdraw()
    try:
        calls = []
        frame = tk.Frame(root)
        assert install_destroy_cleanup(frame, lambda: calls.append("normal")) is True
        frame.destroy()
        assert calls == ["normal"]

        calls2 = []
        frame2 = tk.Frame(root)
        assert install_destroy_cleanup(frame2, lambda: calls2.append("explicit")) is True
        # Non-standard but deliberately supported by the hardened wrapper.
        frame2.destroy(frame2)
        assert calls2 == ["explicit"]
    finally:
        root.destroy()


def test_payload_key_never_collapses_hostile_payload_to_blank_digest():
    class Hostile:
        mode = "RGB"
        size = (1, 1)
        def tobytes(self):
            raise RuntimeError("no bytes")
        def __repr__(self):
            raise RuntimeError("no repr")

    a = LibraryVisualMixin._payload_key("q", "book", Hostile())
    b = LibraryVisualMixin._payload_key("q", "book", Hostile())
    assert a.startswith("q:book:")
    assert a != "q:book:"
    assert b != "q:book:"
    assert a != b


def test_scrollregion_comparison_uses_tcl_list_normalization():
    source = inspect.getsource(CTkScrollableFrame._on_content_configure)
    assert "splitlist" in source
    assert "tuple(int(float(v))" in source


class FakeVar:
    def __init__(self, name):
        self.name = name
        self.added = []
        self.removed = []
    def trace_add(self, mode, callback):
        trace = f"{self.name}-trace-{len(self.added)+1}"
        self.added.append((mode, callback, trace))
        return trace
    def trace_remove(self, mode, trace_id):
        self.removed.append((mode, trace_id))


def _settings_tab_host():
    tab = SettingsTab.__new__(SettingsTab)
    tab.app = SimpleNamespace()
    tab._segment_trace_var = None
    tab._segment_trace_id = None
    tab._output_trace_var = None
    tab._output_trace_id = None
    tab._autosave_trace_bindings = []
    tab._autosave_after_id = None
    return tab


def test_settings_trace_registry_removes_trace_from_original_variable():
    tab = _settings_tab_host()
    first = FakeVar("first")
    second = FakeVar("second")
    cb = lambda *_: None

    first_id = tab._install_trace(first, cb, "_segment_speed_trace_id", "_segment_trace_var", "_segment_trace_id")
    assert first_id
    # Simulate partial legacy metadata loss: the registry still retains the true
    # variable even if the old compatibility app attribute disappears.
    tab.app._segment_speed_trace_id_var = None
    second_id = tab._install_trace(second, cb, "_segment_speed_trace_id", "_segment_trace_var", "_segment_trace_id")
    assert second_id
    assert ("write", first_id) in first.removed


def test_settings_build_no_duplicate_folder_variable_initialization():
    source = inspect.getsource(SettingsTab.build)
    assert source.count('_ensure_string_var("folder_template_var", "{Book_Title}")') == 1


def test_apply_scale_does_not_require_easy_home_component():
    source = inspect.getsource(AudioKnigiApp._apply_scale)
    assert 'getattr(self, "easy_home_view", None)' in source
    assert "if easy_view is not None" in source


def test_accessibility_shutdown_is_already_cancel_safe():
    from audioknigi.accessibility import AccessibilityManager
    source = inspect.getsource(AccessibilityManager.close)
    assert "after_cancel" in source
    assert "self._after_ids.clear()" in source


def test_no_claimed_source_concatenation_or_syntax_truncation():
    import audioknigi.app as app_module
    import audioknigi.search as search_module
    assert hasattr(app_module.AudioKnigiApp, "_focus_easy_url_entry")
    assert hasattr(search_module.SearchMixin, "_parse_search_results")
