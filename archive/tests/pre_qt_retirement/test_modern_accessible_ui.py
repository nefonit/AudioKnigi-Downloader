"""4.8 modern-visual / native-accessibility regression."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from audioknigi import AudioKnigiApp
from audioknigi.ui_kit import (
    CTkButton, CTkEntry, CTkFrame, CTkOptionMenu, CTkSlider, CTkTabview,
    HAS_CUSTOMTKINTER, apply_tree_zebra,
)
from audioknigi.visuals import BG, PANEL, ACCENT, TEXT, MUTED

ROOT = Path(__file__).resolve().parents[1]
req = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
build = (ROOT / "build_ci.ps1").read_text(encoding="utf-8").lower()

assert not HAS_CUSTOMTKINTER
assert "customtkinter" not in req
assert "customtkinter" not in pyproject
assert "ttkbootstrap>=2.2.0" in req
assert "ttkbootstrap" in pyproject
assert '"ttkbootstrap"' in build
assert issubclass(CTkButton, ttk.Button)
assert issubclass(CTkEntry, ttk.Entry)
assert issubclass(CTkOptionMenu, ttk.Combobox)
assert issubclass(CTkSlider, ttk.Scale)
assert issubclass(CTkFrame, tk.Frame)


def _lum(hex_color):
    value = hex_color.lstrip("#")
    channels = [int(value[i:i+2], 16) / 255 for i in (0, 2, 4)]
    channels = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(a, b):
    high, low = sorted((_lum(a), _lum(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


assert _contrast(TEXT, BG) >= 4.5
assert _contrast(MUTED, PANEL) >= 4.5
assert _contrast("#FFFFFF", ACCENT) >= 4.5

app = AudioKnigiApp()
app.update_idletasks()

# Every visible interactive control remains a native widget, including the
# quality cards and notebook tabs.  Decorative frames may be ordinary tk.Frame.
assert isinstance(app.easy_download_btn, ttk.Button)
assert isinstance(app.easy_url_entry, ttk.Entry)
assert isinstance(app.tabview, CTkTabview)
assert isinstance(app.tabview._notebook, ttk.Notebook)
for radio in app.easy_home_view.quality_indicators.values():
    assert isinstance(radio, ttk.Radiobutton)

# No icon-only buttons: text is the accessible name and the icon is supplemental.
def walk(widget):
    for child in widget.winfo_children():
        yield child
        yield from walk(child)

for widget in walk(app):
    if isinstance(widget, ttk.Button):
        assert str(widget.cget("text") or "").strip(), f"icon-only button: {widget}"

# Modern row density and zebra tags remain available without changing semantics.
style = ttk.Style(app)
assert int(float(style.lookup("Treeview", "rowheight") or 0)) >= 30
sample = ttk.Treeview(app, columns=("a",), show="headings")
apply_tree_zebra(sample)
sample.insert("", "end", tags=("row-even",), values=("one",))
sample.insert("", "end", tags=("row-odd",), values=("two",))
assert sample.item(sample.get_children()[0], "tags") == ("row-even",)
assert sample.item(sample.get_children()[1], "tags") == ("row-odd",)
sample.destroy()

app.destroy()
print("NO CUSTOMTKINTER RUNTIME: OK")
print("TTKBOOTSTRAP THEME DEPENDENCY: OK")
print("NATIVE INTERACTIVE CONTROLS: OK")
print("WCAG AA CORE PALETTE: OK")
print("TEXT-NAMED BUTTONS: OK")
print("TREEVIEW DENSITY/ZEBRA: OK")
print("MODERN ACCESSIBLE UI 4.8: OK")
