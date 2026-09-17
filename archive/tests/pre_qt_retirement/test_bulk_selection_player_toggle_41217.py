from types import SimpleNamespace

from audioknigi.actions import ActionsMixin
from audioknigi.player import PlayerMixin


class ButtonProbe:
    def __init__(self):
        self.options = {}

    def configure(self, **kwargs):
        self.options.update(kwargs)


class TreeProbe:
    def __init__(self, rows):
        self.rows = {row: ["☑", str(i + 1)] for i, row in enumerate(rows)}

    def exists(self, row):
        return row in self.rows

    def item(self, row, option=None, **kwargs):
        if "values" in kwargs:
            self.rows[row] = list(kwargs["values"])
            return None
        if option == "values":
            return tuple(self.rows[row])
        return {"values": tuple(self.rows[row])}


def test_bulk_selection_handles_one_hundred_tracks_in_one_action():
    tracks = [SimpleNamespace(selected=True) for _ in range(100)]
    rows = [f"track-{i}" for i in range(1, 101)]
    host = SimpleNamespace(
        current_book=SimpleNamespace(tracks=tracks),
        tree=TreeProbe(rows),
        _track_tree_map=dict(zip(rows, tracks)),
    )

    ActionsMixin._select_all(host, False)
    assert not any(track.selected for track in tracks)
    assert all(host.tree.item(row, "values")[0] == "☐" for row in rows)

    ActionsMixin._select_all(host, True)
    assert all(track.selected for track in tracks)
    assert all(host.tree.item(row, "values")[0] == "☑" for row in rows)


def test_single_player_button_reflects_play_pause_and_stop_states():
    host = SimpleNamespace(
        player_play_btn=ButtonProbe(),
        player_playing=False,
        player_paused=False,
    )
    PlayerMixin._sync_player_play_pause_button(host)
    assert host.player_play_btn.options["text"] == "▶ Воспроизвести"

    host.player_playing = True
    PlayerMixin._sync_player_play_pause_button(host)
    assert host.player_play_btn.options["text"] == "⏸ Пауза"

    host.player_paused = True
    PlayerMixin._sync_player_play_pause_button(host)
    assert host.player_play_btn.options["text"] == "▶ Воспроизвести"

    host.player_playing = False
    host.player_paused = False
    PlayerMixin._sync_player_play_pause_button(host)
    assert host.player_play_btn.options["text"] == "▶ Воспроизвести"


def test_player_toggle_dispatches_to_pause_while_playing_and_play_otherwise():
    calls = []

    class Host(PlayerMixin):
        def __init__(self):
            self.player_playing = False
        def player_play(self):
            calls.append("play")
        def player_pause(self):
            calls.append("pause")

    host = Host()
    host.player_toggle_play_pause()
    host.player_playing = True
    host.player_toggle_play_pause()
    assert calls == ["play", "pause"]
