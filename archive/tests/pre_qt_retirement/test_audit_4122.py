from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import tkinter as tk

import pytest

from audioknigi.accessibility import AccessibilityManager, ScreenReaderBridge
from audioknigi.actions import ActionsMixin
from audioknigi.dnd import DragDropMixin
from audioknigi.help_center import HelpCenter
from audioknigi.i18n import tr
from audioknigi.knigavuhe import _hydrate_search_result_titles
from audioknigi.models import SearchResult
from audioknigi.onboarding import FirstRunWizard
from audioknigi.player import PlayerMixin
from audioknigi.poleknig import _parse_playlist_objects, parse_search_results
from audioknigi.storage import StorageMixin
from audioknigi.ui_kit import CTkOptionMenu, CTkScrollableFrame


class _Var:
    def __init__(self, value=None):
        self.value = value
    def get(self):
        return self.value
    def set(self, value):
        self.value = value


def test_screen_reader_duplicate_debounce_uses_latest_duplicate(monkeypatch):
    spoken = []
    bridge = ScreenReaderBridge()
    bridge.backend = SimpleNamespace(
        features=SimpleNamespace(supports_output=True, supports_speak=False, supports_braille=False),
        output=lambda text, interrupt=False: spoken.append(text),
    )
    clock = iter([0.0, 0.2, 0.4])
    monkeypatch.setattr("audioknigi.accessibility.time.monotonic", lambda: next(clock))

    assert bridge.announce("Одинаковый текст") is True
    assert bridge.announce("Одинаковый текст") is False
    assert bridge.announce("Одинаковый текст") is False
    assert spoken == ["Одинаковый текст"]


def test_accessibility_install_is_idempotent():
    class App:
        def __init__(self):
            self.calls = []
        def after(self, delay, callback):
            token = f"after-{len(self.calls)}"
            self.calls.append((token, delay, callback))
            return token
        def after_cancel(self, _token):
            pass
    app = App()
    manager = AccessibilityManager(app)
    manager._walk = lambda _root: None
    manager.install()
    manager.install()
    assert len(app.calls) == 3
    manager.close()


def test_nearby_label_does_not_resolve_empty_root_parent():
    class RootLike:
        called = False
        def winfo_parent(self): return ""
        def nametowidget(self, _name):
            self.called = True
            raise AssertionError("nametowidget must not be called for root")
    root = RootLike()
    assert AccessibilityManager._nearby_label(root) == ""
    assert root.called is False


def test_dependency_status_tolerates_tray_object_without_available():
    host = ActionsMixin()
    host.dependencies_var = _Var("")
    host.tray_manager = object()
    host.dnd_available = False
    host._update_dependency_status()
    assert "Tray: нет" in host.dependencies_var.get()


def test_clipboard_focus_does_not_rearm_while_dialog_is_open():
    host = ActionsMixin()
    host._clipboard_dialog_open = True
    host.clipboard_auto_var = _Var(True)
    host.busy = False
    host.after = lambda *_args: (_ for _ in ()).throw(AssertionError("after should not be scheduled"))
    assert host._on_window_focus_for_clipboard() is None


def test_drop_main_tolerates_host_without_busy_attribute():
    host = DragDropMixin()
    host._extract_urls_from_drop_data = lambda _data: ["https://poleknig.com/books/1"]
    host.ui_mode_var = _Var("Простой")
    host.url_var = _Var("")
    host.url_entry = None
    host.easy_url_entry = None
    host.set_status = lambda _text: None
    scheduled = []
    host.after = lambda delay, cb: scheduled.append((delay, cb))
    host.analyze = lambda: None
    host.easy_download_book = lambda: None
    result = host._on_drop_main(SimpleNamespace(data="x", action="copy"))
    assert host.url_var.get().endswith("/books/1")
    assert scheduled and scheduled[0][0] == 80
    assert result == "copy"


def test_knigavuhe_reader_only_card_is_hydrated_for_author_filter(monkeypatch):
    original = SearchResult(
        title="Название книги",
        url="https://knigavuhe.org/book/test/",
        narrator="Известный чтец",
        author="",
        source="knigavuhe.org",
    )
    resolved = SearchResult(
        title="Название книги",
        url=original.url,
        narrator="Известный чтец",
        author="Нужный Автор",
        source="knigavuhe.org",
    )
    monkeypatch.setattr("audioknigi.knigavuhe._resolve_search_result_title", lambda _item: resolved)
    rows = _hydrate_search_result_titles([original], query="Нужный Автор")
    assert rows and rows[0].author == "Нужный Автор"


def test_first_run_strings_exist_in_all_languages():
    keys = (
        "wizard_start_question", "wizard_start_search_button", "wizard_start_link_button",
        "wizard_start_search_note", "wizard_start_link_note", "wizard_start_steps",
        "wizard_start_search_after", "wizard_start_link_after",
    )
    for lang in ("ru", "uk", "de", "en"):
        for key in keys:
            value = tr(lang, key)
            assert value and value != key


def test_player_seek_to_beginning_clears_old_resume_marker(tmp_path):
    host = PlayerMixin()
    path = tmp_path / "chapter.mp3"
    path.write_bytes(b"x")
    host.player_file = path
    host.player_duration = 3600.0
    host.player_position_var = _Var(0.5)
    key = host._player_position_key(path)
    host.player_positions = {key: {"position": 900.0, "duration": 3600.0}}
    host._write_player_positions = lambda snapshot, sync=False: setattr(host, "written", snapshot)
    host._save_current_player_position(force=True)
    assert key not in host.player_positions
    assert key not in host.written


def test_player_play_routes_m4a_to_external_path(tmp_path):
    host = PlayerMixin()
    path = tmp_path / "book.m4a"
    path.write_bytes(b"x")
    host.current_book = None
    host.player_file = path
    host._current_tree_track = lambda: None
    called = []
    host.player_play_file = lambda p: called.append(Path(p))
    host.player_play()
    assert called == [path]


def test_poleknig_search_prefers_real_title_over_badge():
    html = '''
    <a href="/books/7" title="Новинка">
      Новинка
      <img alt="Автор - Преступление и наказание">
    </a>
    '''
    rows = parse_search_results(html)
    assert rows[0].title == "Преступление и наказание"


def test_poleknig_unquoted_playlist_handles_nested_objects_and_braces_in_strings():
    raw = '''[
      {title: "Первая {глава}", meta: {quality: "high"}, file: "/a.mp3"},
      {title: "Вторая", file: "/b.mp3"}
    ]'''
    tracks = _parse_playlist_objects(raw, "https://poleknig.com/books/1")
    assert [track.file for track in tracks] == [
        "https://poleknig.com/a.mp3", "https://poleknig.com/b.mp3"
    ]
    assert [track.title for track in tracks] == ["Первая {глава}", "Вторая"]


def test_history_without_folder_does_not_probe_current_directory_cover(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cover.jpg").write_bytes(b"foreign")

    class Tree:
        def get_children(self): return ()
        def delete(self, _row): pass
        def tag_configure(self, *_args, **_kwargs): pass
        def insert(self, *_args, **_kwargs): pass
    host = StorageMixin()
    host.history = [{"title": "Без папки", "url": "https://example/book", "folder": "", "cover_file": ""}]
    host.history_tree = Tree()
    host._history_cover_images = {}
    captured = []
    host._prune_image_cache = lambda _cache, prefixes: captured.extend(prefixes)
    host._refresh_history()
    assert captured == ["h:https://example/book"]


def test_ctk_option_menu_configure_converts_pixel_width():
    root = tk.Tk()
    root.withdraw()
    try:
        widget = CTkOptionMenu(root, values=("one", "two"), width=120)
        widget.configure(width=200)
        assert int(widget.cget("width")) < 100
    finally:
        root.destroy()


def test_scrollable_frame_pack_configure_targets_public_viewport():
    root = tk.Tk()
    root.withdraw()
    try:
        frame = CTkScrollableFrame(root)
        frame.pack()
        frame.pack_configure(padx=13)
        info = frame.pack_info()
        assert int(info["padx"]) == 13
    finally:
        root.destroy()
