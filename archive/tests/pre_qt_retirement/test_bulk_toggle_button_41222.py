from pathlib import Path
from types import SimpleNamespace

from audioknigi.actions import ActionsMixin


ROOT = Path(__file__).resolve().parents[1]


class ButtonProbe:
    def __init__(self):
        self.options = {}
        self.accessible_name = ""

    def configure(self, **kwargs):
        self.options.update(kwargs)


class TreeProbe:
    def __init__(self, tracks):
        self.rows = {
            f"track-{i}": ["☑" if tr.selected else "☐", str(i)]
            for i, tr in enumerate(tracks, start=1)
        }

    def exists(self, row):
        return row in self.rows

    def item(self, row, option=None, **kwargs):
        if "values" in kwargs:
            self.rows[row] = list(kwargs["values"])
            return None
        if option == "values":
            return tuple(self.rows[row])
        return {"values": tuple(self.rows[row])}


def _host(count=100, selected=True):
    tracks = [SimpleNamespace(selected=selected) for _ in range(count)]
    tree = TreeProbe(tracks)
    button = ButtonProbe()
    return SimpleNamespace(
        current_book=SimpleNamespace(tracks=tracks),
        tree=tree,
        _track_tree_map={f"track-{i}": tr for i, tr in enumerate(tracks, start=1)},
        bulk_select_tracks_btn=button,
    )


def test_book_tab_uses_one_visual_bulk_selection_button():
    source = (ROOT / "audioknigi" / "ui" / "main_tab.py").read_text(encoding="utf-8")
    assert "bulk_select_tracks_btn = CTkButton" in source
    assert "command=app._toggle_all_tracks_selection" in source
    assert "clear_all_tracks_btn = CTkButton" not in source


def test_all_selected_shows_clear_all_then_toggles_to_select_all():
    host = _host(100, selected=True)
    ActionsMixin._sync_bulk_select_button(host)
    assert host.bulk_select_tracks_btn.options["text"] == "Снять все"

    ActionsMixin._toggle_all_tracks_selection(host)
    assert not any(track.selected for track in host.current_book.tracks)
    assert host.bulk_select_tracks_btn.options["text"] == "Выбрать все"
    assert all(host.tree.item(row, "values")[0] == "☐" for row in host._track_tree_map)

    ActionsMixin._toggle_all_tracks_selection(host)
    assert all(track.selected for track in host.current_book.tracks)
    assert host.bulk_select_tracks_btn.options["text"] == "Снять все"
    assert all(host.tree.item(row, "values")[0] == "☑" for row in host._track_tree_map)


def test_partial_manual_selection_changes_button_to_select_all():
    host = _host(4, selected=True)
    host.current_book.tracks[2].selected = False
    host.tree.rows["track-3"][0] = "☐"
    ActionsMixin._sync_bulk_select_button(host)
    assert host.bulk_select_tracks_btn.options["text"] == "Выбрать все"
    assert host.bulk_select_tracks_btn.accessible_name == "Выбрать все части книги"
