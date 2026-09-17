import os
from pathlib import Path

import pytest

from audioknigi import downloader


def test_atomic_metadata_writer_preserves_old_file_if_replace_fails(tmp_path, monkeypatch):
    target = tmp_path / "metadata.json"
    target.write_text('{"old": true}', encoding="utf-8")

    def fail_replace(src, dst):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(downloader.os, "replace", fail_replace)
    with pytest.raises(OSError):
        downloader._atomic_write_text(target, '{"new": true}')

    assert target.read_text(encoding="utf-8") == '{"old": true}'
    assert not list(tmp_path.glob(".metadata.json.*.tmp"))


def test_mp3_only_settings_and_single_bulk_button_are_really_wired():
    root = Path(__file__).parents[1]
    settings = (root / "audioknigi" / "ui" / "settings_tab.py").read_text(encoding="utf-8")
    main_tab = (root / "audioknigi" / "ui" / "main_tab.py").read_text(encoding="utf-8")
    assert "output_mode_var" not in settings
    assert "Один M4B" not in settings
    assert "MP3 + M4B" not in settings
    assert "app.bulk_select_tracks_btn = CTkButton" in main_tab
    assert "app.select_all_tracks_btn = app.bulk_select_tracks_btn" in main_tab
    assert "clear_all_btn" not in main_tab
