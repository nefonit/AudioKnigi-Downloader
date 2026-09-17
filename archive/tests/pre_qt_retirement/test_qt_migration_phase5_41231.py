from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from audioknigi.services.player_position_store import PlayerPositionStore


ROOT = Path(__file__).resolve().parents[1]


def test_player_position_store_roundtrip_uses_legacy_schema(tmp_path):
    state = tmp_path / "player_positions.json"
    audio = tmp_path / "Book" / "01.mp3"
    audio.parent.mkdir()
    audio.write_bytes(b"test")
    store = PlayerPositionStore(state)
    assert store.update(audio, 12.5, 100.0)

    raw = json.loads(state.read_text(encoding="utf-8"))
    key = PlayerPositionStore.key(audio)
    assert raw[key]["position"] == 12.5
    assert raw[key]["duration"] == 100.0
    assert raw[key]["file"] == "01.mp3"
    assert PlayerPositionStore(state).saved_seconds(audio) == 12.5


def test_player_position_store_clears_start_and_completed_positions(tmp_path):
    state = tmp_path / "player_positions.json"
    audio = tmp_path / "01.mp3"
    audio.write_bytes(b"test")
    store = PlayerPositionStore(state)
    store.update(audio, 20.0, 100.0)
    assert store.saved_seconds(audio) == 20.0
    store.update(audio, 1.5, 100.0)
    assert store.saved_seconds(audio) == 0.0
    store.update(audio, 50.0, 100.0)
    store.update(audio, 98.0, 100.0)
    assert store.saved_seconds(audio) == 0.0


def test_player_position_store_saved_seconds_ignores_near_end_legacy_record(tmp_path):
    state = tmp_path / "player_positions.json"
    audio = tmp_path / "01.mp3"
    audio.write_bytes(b"test")
    key = PlayerPositionStore.key(audio)
    state.write_text(json.dumps({key: {"position": 99, "duration": 100, "file": "01.mp3"}}), encoding="utf-8")
    store = PlayerPositionStore(state)
    assert store.saved_seconds(audio, duration=100.0) == 0.0


def test_player_position_store_import_does_not_load_gui_toolkits():
    code = (
        "import sys; import audioknigi.services.player_position_store; "
        "assert 'tkinter' not in sys.modules; assert 'PySide6' not in sys.modules"
    )
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(ROOT)
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_qt_player_controller_uses_qt_multimedia_without_pygame_or_tk():
    text = (ROOT / "audioknigi" / "qt" / "player_controller.py").read_text(encoding="utf-8")
    for needle in (
        "QMediaPlayer",
        "QAudioOutput",
        "QUrl.fromLocalFile",
        "setPlaybackRate",
        "setPosition",
        "MediaStatus.EndOfMedia",
        "errorOccurred.connect",
        "PlayerPositionStore",
    ):
        assert needle in text
    assert "pygame" not in text
    assert "tkinter" not in text
    assert "ui_kit" not in text


def test_qt_main_window_wires_accessible_player_phase5():
    text = (ROOT / "audioknigi" / "qt" / "main_window.py").read_text(encoding="utf-8")
    for needle in (
        'self.tabs.addTab(self._build_player_tab(), "Плеер")',
        "def _init_player(self):",
        "QtPlayerController(parent=self)",
        "def play_selected_track(self):",
        "def open_audio_file(self):",
        'identifier="player_play_pause"',
        'identifier="player_seek"',
        'identifier="player_volume"',
        'identifier="player_rate"',
        "player_controller.shutdown()",
        "self.TAB_PLAYER",
    ):
        assert needle in text
    assert "import pygame" not in text
    assert "from tkinter" not in text
    assert "import tkinter" not in text


def test_qt_settings_persist_player_volume_and_rate():
    text = (ROOT / "audioknigi" / "qt" / "main_window.py").read_text(encoding="utf-8")
    assert 'updated["player_volume"]' in text
    assert 'updated["player_rate"]' in text
    assert 'self.settings.get("player_volume", 80)' in text
    assert 'self.settings.get("player_rate", 1.0)' in text


def test_qt_build_checks_multimedia_and_excludes_legacy_pygame():
    bat = (ROOT / "build_qt_exe.bat").read_text(encoding="utf-8")
    ps = (ROOT / "build_qt_ci.ps1").read_text(encoding="utf-8")
    assert "PySide6.QtMultimedia import QMediaPlayer,QAudioOutput" in bat or "PySide6.QtMultimedia import QMediaPlayer, QAudioOutput" in bat
    assert '"--exclude-module", "pygame"' in ps
