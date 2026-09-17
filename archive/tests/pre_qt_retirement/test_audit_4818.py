from __future__ import annotations

import inspect
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

import audioknigi.storage as storage_module
import audioknigi.tray as tray_module
import audioknigi.ui_kit as ui_kit
from audioknigi.actions import ActionsMixin
from audioknigi.app import AudioKnigiApp
from audioknigi.i18n import STRINGS, tr
from audioknigi.player import PlayerMixin
from audioknigi.storage import StorageMixin
from audioknigi.ui.settings_tab import SettingsTab


def test_reported_source_truncations_are_false_positives():
    for filename in ("audioknigi/actions.py", "audioknigi/search.py"):
        source = Path(filename).read_text(encoding="utf-8")
        compile(source, filename, "exec")
    assert "tags.add(TIT2(encoding=3, text=book_title))" in Path("audioknigi/actions.py").read_text(encoding="utf-8")


def test_actions_dependencies_are_supplied_and_translation_has_fallback():
    assert callable(AudioKnigiApp.t)
    assert callable(PlayerMixin._player_position_key)
    assert callable(PlayerMixin._player_select_current)

    class Host(ActionsMixin):
        language = "en"

    assert Host()._tr("duplicate_title") == STRINGS["en"]["duplicate_title"]


def test_duplicate_dialog_choice_hint_is_localized_for_every_language():
    for language in ("ru", "uk", "de", "en"):
        assert STRINGS[language]["duplicate_choices"].strip()
    source = inspect.getsource(ActionsMixin._offer_duplicate_book)
    assert 'self._tr("duplicate_choices")' in source
    assert "Да — открыть папку" not in source


def test_i18n_bad_format_is_logged_instead_of_silent(monkeypatch):
    import audioknigi.i18n as i18n_module
    warnings = []
    monkeypatch.setattr(i18n_module._logger, "warning", lambda *args, **kwargs: warnings.append(args))
    value = tr("en", "resume")
    assert "{time}" in value
    assert warnings
    assert "i18n formatting failed" in warnings[0][0]


def test_history_payload_sanitizer_rejects_non_mapping_records():
    with pytest.raises(ValueError):
        StorageMixin._sanitize_history_records([{"title": "ok"}, "broken"], strict=True)
    result = StorageMixin._sanitize_history_records(["broken", {"title": "ok", "parts": "3"}])
    assert len(result) == 1
    assert result[0]["title"] == "ok"
    assert result[0]["parts"] == 3


def test_history_refresh_cannot_crash_on_primitive_record():
    class Tree:
        def __init__(self): self.rows = []
        def get_children(self): return ()
        def delete(self, _row): pass
        def tag_configure(self, *_args, **_kwargs): pass
        def insert(self, *args, **kwargs): self.rows.append((args, kwargs))

    host = StorageMixin()
    host.history = ["broken", {"title": "Good", "parts": "2"}]
    host.history_tree = Tree()
    host._refresh_history()
    assert len(host.history) == 1
    assert host.history[0]["title"] == "Good"
    assert len(host.history_tree.rows) == 1


def test_add_history_with_empty_folder_never_scans_current_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cover.jpg").write_bytes(b"not-the-book-cover")
    monkeypatch.setattr(storage_module, "save_json", lambda *_args, **_kwargs: None)

    class Host(StorageMixin):
        def __init__(self): self.history = []
        def ui(self, _callback): pass

    host = Host()
    host._add_history({"title": "Book", "url": "https://example.invalid/book"}, "", 1)
    assert host.history[0]["folder"] == ""
    assert host.history[0]["cover_file"] == ""


def test_tray_notification_is_queued_while_restart_is_pending(monkeypatch):
    class AliveThread:
        def is_alive(self): return True

    monkeypatch.setattr(tray_module, "pystray", object())
    monkeypatch.setattr(tray_module, "Image", object())
    monkeypatch.setattr(tray_module, "ImageDraw", object())
    manager = tray_module.TrayManager(SimpleNamespace())
    manager._retiring_thread = AliveThread()
    assert manager.show() is True
    assert manager.notify("Title", "Body") is True
    assert manager._pending_notifications == [("Title", "Body")]


def test_width_conversion_has_no_15_to_16_character_cliff():
    assert ui_kit._pixel_width_to_chars(1) == 1
    assert ui_kit._pixel_width_to_chars(15) <= 3
    assert abs(ui_kit._pixel_width_to_chars(16) - ui_kit._pixel_width_to_chars(15)) <= 1


def test_linux_shortcuts_prefer_logical_keysym_over_physical_keycode(monkeypatch):
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        entry = ui_kit.CTkEntry(root)
        entry.insert(0, "abc")
        entry.selection_range(0, 3)
        called = []
        entry._copy_selection = lambda _event=None: called.append("copy") or "break"
        entry._paste_clipboard = lambda _event=None: called.append("paste") or "break"
        monkeypatch.setattr(ui_kit.sys, "platform", "linux")
        # keycode 55 is the standard X11 physical V position, but a remapped
        # layout may logically report C there. Logical C must win.
        result = entry._physical_edit_shortcut(SimpleNamespace(state=0x0004, keycode=55, keysym="c", char=""))
        assert result == "break"
        assert called == ["copy"]

        called.clear()
        result = entry._physical_edit_shortcut(SimpleNamespace(state=0x0004, keycode=54, keysym="Cyrillic_es", char=""))
        assert result == "break"
        assert called == ["copy"]
    finally:
        root.destroy()


def test_settings_destroy_disposes_tooltips_and_scale_applies_immediately():
    disposed = []
    tab = object.__new__(SettingsTab)
    tab.frame = object()
    tab.tooltips = [SimpleNamespace(dispose=lambda: disposed.append(True))]
    tab._dispose_traces = lambda: None
    tab._on_frame_destroy(None)
    assert disposed == [True]
    assert tab.tooltips == []

    source = Path("audioknigi/ui/settings_tab.py").read_text(encoding="utf-8")
    assert 'variable=app.scale_var, command=lambda _v: app._apply_scale()' in source
    assert 'command=lambda _v: self._save_now()' in source
