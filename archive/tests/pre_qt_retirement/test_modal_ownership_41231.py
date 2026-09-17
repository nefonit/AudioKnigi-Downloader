from __future__ import annotations

import ast
from pathlib import Path

import pytest

from audioknigi.ui_kit import CTk, CTkButton, CTkToplevel, activate_modal_window


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "audioknigi"


def test_every_tk_messagebox_has_explicit_parent():
    """Native messageboxes must be owned so they cannot hide behind the app."""
    missing = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "messagebox"
            ):
                continue
            if not any(keyword.arg == "parent" for keyword in node.keywords):
                missing.append(f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}:{func.attr}")
    assert missing == []



def test_every_tk_filedialog_has_explicit_parent():
    missing = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "filedialog"
                and func.attr.startswith("ask")
            ):
                continue
            if not any(keyword.arg == "parent" for keyword in node.keywords):
                missing.append(f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}:{func.attr}")
    assert missing == []

def test_custom_question_windows_use_modal_helper():
    expected = {
        "audioknigi/actions.py": [
            "activate_modal_window(win, self, focus_widget=primary)",
            "activate_modal_window(window, self, focus_widget=stop_button)",
        ],
        "audioknigi/onboarding.py": [
            "activate_modal_window(self.win, app, focus_widget=self.next_btn)"
        ],
    }
    for relative, markers in expected.items():
        source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in source, f"{relative}: {marker}"

    # Phase 3 migration deliberately moved the missing-media Tk dialog out of
    # the shared downloader core. The core must stay GUI-neutral so Qt can use
    # it without importing or bundling Tk.
    downloader = (PROJECT_ROOT / "audioknigi/downloader.py").read_text(encoding="utf-8")
    assert "activate_modal_window" not in downloader
    assert "messagebox" not in downloader
    assert "tkinter" not in downloader


def test_activate_modal_window_owns_and_grabs_dialog():
    try:
        root = CTk()
    except Exception as exc:  # pragma: no cover - headless hosts without Tk
        pytest.skip(f"Tk is unavailable: {exc}")
    root.geometry("420x220+20+20")
    top = None
    try:
        root.update_idletasks()
        root.update()
        top = CTkToplevel(root)
        top.geometry("280x140+60+60")
        button = CTkButton(top, text="OK")
        button.pack(padx=20, pady=20)

        activate_modal_window(top, root, focus_widget=button)
        root.update_idletasks()
        root.update()

        assert str(top.transient()) == str(root)
        assert top.grab_current() is top
        assert button.focus_get() in (button, top)

        top.destroy()
        top = None
        root.update_idletasks()
        root.update()
        assert root.grab_current() is None
    finally:
        try:
            if top is not None and top.winfo_exists():
                top.destroy()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass
