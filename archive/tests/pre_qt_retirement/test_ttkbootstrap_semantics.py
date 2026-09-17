"""Semantic ttkbootstrap facade remains native ttk and regression-safe."""
from tkinter import ttk

from audioknigi.ui_kit import (
    CTk,
    CTkButton,
    CTkEntry,
    CTkOptionMenu,
    CTkProgressBar,
    StatusBadge,
    configure_accessible_styles,
)


def test_semantic_bootstyles_use_native_ttk_widgets():
    root = CTk()
    root.withdraw()
    configure_accessible_styles(root, dark=True)

    primary = CTkButton(root, text="Primary", bootstyle="primary")
    outline = CTkButton(root, text="Outline", bootstyle="secondary-outline")
    danger = CTkButton(root, text="Danger", bootstyle="danger")
    entry = CTkEntry(root, bootstyle="search")
    combo = CTkOptionMenu(root, values=["A", "B"], bootstyle="primary")
    progress = CTkProgressBar(root, bootstyle="success")
    badge = StatusBadge(root, text="OK", bootstyle="info")

    assert isinstance(primary, ttk.Button)
    assert isinstance(entry, ttk.Entry)
    assert isinstance(combo, ttk.Combobox)
    assert isinstance(progress, ttk.Progressbar)
    assert isinstance(badge, ttk.Label)

    assert primary.cget("style") == "AudioKnigi.Primary.TButton"
    assert outline.cget("style") == "AudioKnigi.SecondaryOutline.TButton"
    assert danger.cget("style") == "AudioKnigi.Danger.TButton"
    assert entry.cget("style") == "AudioKnigi.Search.TEntry"
    assert combo.cget("style") == "AudioKnigi.Primary.TCombobox"
    assert progress.cget("style") == "AudioKnigi.Success.Horizontal.TProgressbar"
    assert badge.cget("style") == "AudioKnigi.InfoBadge.TLabel"

    root.destroy()
