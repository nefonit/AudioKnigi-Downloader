"""4.12.31 regressions for editor speech, layout-independent shortcuts and search focus."""
from __future__ import annotations

from types import SimpleNamespace
import sys

import pytest

from audioknigi import AudioKnigiApp
from audioknigi import actions as actions_module
from audioknigi import accessibility as accessibility_module
from audioknigi.models import SearchResult


@pytest.fixture
def app():
    instance = AudioKnigiApp()
    instance.update_idletasks()
    instance.ui_mode_var.set("Простой")
    instance._apply_ui_mode()
    instance.runtime_ui_mode = "easy"
    yield instance
    try:
        instance.destroy()
    except Exception:
        pass


def test_universal_book_editor_has_explicit_accessibility_name(app):
    assert app.easy_url_entry.accessible_name == "Название, автор или ссылка"
    assert "Insert+стрелка вверх" in app.easy_url_entry.accessible_description


def test_accessibility_fallback_speaks_text_from_focused_book_editor(app, monkeypatch):
    spoken = []
    monkeypatch.setattr(
        app.accessibility.bridge,
        "announce",
        lambda text, interrupt=False: (spoken.append((text, interrupt)) or True),
    )
    app.url_var.set("Толстой Война и мир")
    app.easy_url_entry.focus_force()
    app.update()

    assert app.accessibility.announce_focused_editable_text() is True
    assert spoken
    assert "Название, автор или ссылка" in spoken[-1][0]
    assert "Толстой Война и мир" in spoken[-1][0]


def test_insert_up_physical_fallback_invokes_editor_reader(app, monkeypatch):
    calls = []
    monkeypatch.setattr(
        app.accessibility,
        "announce_focused_editable_text",
        lambda *args, **kwargs: (calls.append("read") or True),
    )

    # VK_INSERT followed by VK_UP, independent of the printable keyboard layout.
    assert app._physical_global_shortcut(SimpleNamespace(state=0, keycode=45, keysym="Insert")) is None
    assert app._physical_global_shortcut(SimpleNamespace(state=0, keycode=38, keysym="Up")) == "break"
    assert calls == ["read"]

    app._physical_global_shortcut_key_release(SimpleNamespace(state=0, keycode=45, keysym="Insert"))
    assert app._physical_global_shortcut(SimpleNamespace(state=0, keycode=38, keysym="Up")) is None
    assert calls == ["read"]


def test_windows_global_ctrl_shortcuts_use_layout_independent_virtual_keys(app, monkeypatch):
    calls = []
    monkeypatch.setattr(actions_module.sys, "platform", "win32")
    monkeypatch.setattr(app, "_focus_url", lambda: calls.append("focus"))
    monkeypatch.setattr(app, "_shortcut_download", lambda: calls.append("download"))
    monkeypatch.setattr(app, "_open_tab_shortcut", lambda index: (calls.append(f"tab:{index}") or "break"))

    # Physical L/D/F/Q/H positions while a Russian/Ukrainian Cyrillic layout is active.
    events = (
        (76, "Cyrillic_de", "focus"),
        (68, "Cyrillic_ve", "download"),
        (70, "Cyrillic_ef", "tab:1"),
        (81, "Cyrillic_shorti", "tab:2"),
        (72, "Cyrillic_er", "tab:3"),
    )
    for keycode, keysym, expected in events:
        result = app._physical_global_shortcut(SimpleNamespace(state=0x0004, keycode=keycode, keysym=keysym))
        assert result == "break"
        assert calls[-1] == expected

    # Latin keysyms stay on the existing specific Tk bindings, preventing double execution.
    before = list(calls)
    assert app._physical_global_shortcut(SimpleNamespace(state=0x0004, keycode=76, keysym="l")) is None
    assert calls == before


def test_advanced_search_moves_focus_to_table_and_announces(app, monkeypatch):
    spoken = []
    monkeypatch.setattr(
        app.accessibility,
        "announce",
        lambda text, interrupt=False: (spoken.append((text, interrupt)) or True),
    )
    app.open_advanced_tab("search")
    app.search_results = [
        SearchResult(title="Книга", author="Автор", url="https://poleknig.com/books/1", source="poleknig.com")
    ]
    app._refresh_search_results()
    app.update()

    assert app.focus_get() == app.search_tree
    assert app.search_tree.selection() == ("0",)
    assert any("Фокус переведён в таблицу" in text for text, _ in spoken)
    assert any("Найдено 1" in text for text, _ in spoken)


def test_easy_search_moves_focus_to_table_and_announces(app, monkeypatch):
    spoken = []
    monkeypatch.setattr(
        app.accessibility,
        "announce",
        lambda text, interrupt=False: (spoken.append((text, interrupt)) or True),
    )
    app.search_results = [
        SearchResult(title="Книга", author="Автор", url="https://knigavuhe.org/book/1", source="knigavuhe.org")
    ]
    app._refresh_search_results()
    app.update()

    assert app.focus_get() == app.easy_search_tree
    assert app.easy_search_tree.selection() == ("0",)
    assert any("Фокус переведён в таблицу" in text for text, _ in spoken)


def test_windows_tk_uia_provider_is_enabled_gracefully(monkeypatch):
    calls = []
    fake = SimpleNamespace(enable=lambda root: calls.append(root))
    monkeypatch.setattr(accessibility_module.os, "name", "nt")
    monkeypatch.setitem(sys.modules, "tk_uia", fake)
    root = SimpleNamespace()

    assert accessibility_module.enable_windows_uia(root) is True
    assert calls == [root]
    assert root._tk_uia_module is fake
    assert root._tk_uia_enabled is True


def test_windows_uia_dependency_is_declared_for_source_and_package_metadata():
    from pathlib import Path
    project = Path(__file__).resolve().parents[1]
    requirements = (project / "requirements.txt").read_text(encoding="utf-8")
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'tk-uia>=0.8.0,<0.9; platform_system == "Windows"' in requirements
    assert "tk-uia>=0.8.0,<0.9; platform_system == 'Windows'" in pyproject


def test_windows_exe_build_collects_and_selftests_tk_uia_provider():
    from pathlib import Path
    project = Path(__file__).resolve().parents[1]
    build_ci = (project / "build_ci.ps1").read_text(encoding="utf-8")
    build_bat = (project / "build_exe.bat").read_text(encoding="utf-8")
    gui = (project / "audioknigi_gui.py").read_text(encoding="utf-8")

    assert '"--collect-all", "tk_uia"' in build_ci
    assert '"--copy-metadata", "tk-uia"' in build_ci
    assert "m.version('tk-uia')" in build_ci
    assert "import tk_uia" in build_ci
    assert "m.version('tk-uia')" in build_bat
    assert "import tk_uia" in build_bat
    assert 'metadata.version("tk-uia")' in gui
    assert "import tk_uia" in gui
