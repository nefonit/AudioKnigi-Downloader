from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

import audioknigi.config.settings as settings_module
import audioknigi.diagnostics.support_bundle as support_bundle
import audioknigi.services.player_position_store as position_module
from audioknigi.download.errors import SharedSourceTimelineError
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.models import Book, Track
from audioknigi.poleknig import _parse_playlist_objects
from audioknigi.providers.audioknigi_search import parse_audioknigi_results
from audioknigi.services.player_position_store import PlayerPositionStore

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_existing_profile_without_onboarding_flag_does_not_reopen_first_run() -> None:
    migrated, changed = settings_module.migrate_settings({"language": "de", "scale": 100})
    assert changed is True
    assert migrated["first_run_complete"] is True

    fresh, _changed = settings_module.migrate_settings({})
    assert fresh["first_run_complete"] is False

    explicit, _changed = settings_module.migrate_settings({"first_run_complete": False})
    assert explicit["first_run_complete"] is False

    plugin_only, _changed = settings_module.migrate_settings({"plugin_future_value": 42})
    assert plugin_only["first_run_complete"] is False


def test_support_settings_sanitizer_recurses_into_nested_mappings_and_sequences(monkeypatch) -> None:
    monkeypatch.setattr(support_bundle.os, "name", "nt", raising=False)
    monkeypatch.setattr(support_bundle.Path, "home", classmethod(lambda cls: Path(r"C:\Users\Alice")))
    payload = {
        "plugins": {
            "reader": {
                "api_key": "nested-secret",
                "download_dir": r"C:\Users\Alice\Books",
                "headers": [
                    {"token": "header-secret"},
                    "Authorization: Bearer nested-bearer-secret",
                ],
            }
        }
    }
    cleaned = support_bundle.sanitized_settings(payload)
    reader = cleaned["plugins"]["reader"]
    assert reader["api_key"] == "<redacted>"
    assert reader["headers"][0]["token"] == "<redacted>"
    assert "nested-bearer-secret" not in reader["headers"][1]
    assert "Alice" not in reader["download_dir"]


def test_support_log_sanitizer_redacts_entire_quoted_secret_values() -> None:
    raw = (
        b'{"api_key": "abc def", "password": "p a s s"}\n'
        b"token='quoted token with spaces'\n"
        b"https://example.test/?access_token=URLSECRET&part=1\n"
    )
    cleaned = support_bundle._sanitize_log_bytes(raw).decode("utf-8")
    for secret in ("abc def", "p a s s", "quoted token with spaces", "URLSECRET"):
        assert secret not in cleaned
    assert '"api_key": "<redacted>"' in cleaned
    assert '"password": "<redacted>"' in cleaned
    assert "token='<redacted>'" in cleaned


def test_audioknigi_relative_book_links_resolve_from_site_root_on_nested_search_pages() -> None:
    html = '<a href="audio-12345-test-book">Тестовая книга</a>'
    results = parse_audioknigi_results(
        html,
        "https://audioknigi.com.ua/search/page/2/",
        "Тестовая",
    )
    assert len(results) == 1
    assert results[0].url == "https://audioknigi.com.ua/audio-12345-test-book"


def test_player_position_store_keeps_state_reads_live_while_disk_write_is_blocked(monkeypatch, tmp_path) -> None:
    writes: list[float] = []
    first_started = threading.Event()
    release_first = threading.Event()

    monkeypatch.setattr(position_module, "load_json", lambda _path, default: dict(default))

    def fake_save_json(_path, payload):
        position = float(next(iter(payload.values()))["position"])
        if position == 10.0:
            first_started.set()
            assert release_first.wait(timeout=2.0)
        writes.append(position)
        return True

    monkeypatch.setattr(position_module, "save_json", fake_save_json)
    media = tmp_path / "book.mp3"
    store = PlayerPositionStore(tmp_path / "positions.json")

    first = threading.Thread(target=lambda: store.update(media, 10.0, 100.0))
    second = threading.Thread(target=lambda: store.update(media, 20.0, 100.0))
    first.start()
    assert first_started.wait(timeout=2.0)
    second.start()

    deadline = time.monotonic() + 1.0
    while store.saved_seconds(media, duration=100.0) != 20.0 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert store.saved_seconds(media, duration=100.0) == 20.0
    assert first.is_alive()

    release_first.set()
    first.join(timeout=2.0)
    second.join(timeout=2.0)
    assert not first.is_alive() and not second.is_alive()
    assert writes[-1] == 20.0


def test_poleknig_equal_zero_markers_do_not_create_zero_length_chapters() -> None:
    tracks = _parse_playlist_objects(
        "[00:00]https://cdn.test/one.mp3,[00:00]https://cdn.test/two.mp3",
        "https://poleknig.com/book/",
    )
    assert len(tracks) == 2
    assert tracks[0].start == 0
    assert tracks[1].start == 0
    assert tracks[0].duration is None
    assert tracks[0].end is None


class _SplitDummy(MediaProcessingMixin):
    def __init__(self, target: Path):
        self.target = target

    def _track_path(self, _book, _track):
        return self.target

    def log(self, _message):
        pass


def test_shared_source_middle_track_requires_strictly_increasing_boundary(tmp_path) -> None:
    first = Track(index=1, title="One", file="https://cdn.test/book.mp3", start=0)
    second = Track(index=2, title="Two", file="https://cdn.test/book.mp3", start=0)
    book = Book(url="https://example.test/book", title="Book", tracks=[first, second])
    with pytest.raises(SharedSourceTimelineError) as exc:
        _SplitDummy(tmp_path / "1.mp3")._split_track(book, first, tmp_path / "source.mp3")
    assert exc.value.issue["reason"] == "non_increasing_middle_boundary"


def test_media_key_shutdown_guards_zero_hwnd_before_ctypes_conversion() -> None:
    source = src("audioknigi/qt/media_keys.py")
    start = source.index("def unregister_global_hotkeys")
    end = source.index("def shutdown", start)
    block = source[start:end]
    assert "if not self._hwnd:" in block
    assert block.index("if not self._hwnd:") < block.index("ctypes.c_void_p(self._hwnd or 0).value")


def test_output_directory_resume_scan_runs_after_editing_not_each_character() -> None:
    source = src("audioknigi/qt/mixins/settings.py")
    wire_start = source.index("def _wire_output_dir_sync")
    wire_end = source.index("def _easy_quality_preset_changed", wire_start)
    wire = source[wire_start:wire_end]
    assert "edit.editingFinished.connect(self._schedule_unfinished_refresh)" in wire

    sync_start = source.index("def _sync_output_dir_text")
    sync_end = source.index("def _schedule_unfinished_refresh", sync_start)
    sync = source[sync_start:sync_end]
    assert "_schedule_unfinished_refresh" not in sync

    choose_start = source.index("def _choose_output_dir")
    choose_end = source.index("def _preview_theme", choose_start)
    choose = source[choose_start:choose_end]
    assert "self._schedule_unfinished_refresh()" in choose


def test_audiobookshelf_ui_probe_timeout_fits_exit_grace_window() -> None:
    source = src("audioknigi/qt/workers.py")
    start = source.index("class AudiobookshelfWorker")
    end = source.index("class AnalysisWorker", start)
    block = source[start:end]
    assert "timeout: float = 4.0" in block
    assert "timeout=self.timeout" in block


def test_segmented_download_rejects_nonpositive_size_before_division() -> None:
    source = src("audioknigi/download/network.py")
    start = source.index("def _download_segmented")
    block = source[start:]
    guard = "if total_size <= 0:"
    assert guard in block
    assert block.index(guard) < block.index("total_size // min_chunk")
    assert "raise RangeUnsupported" in block[block.index(guard):block.index("target = Path(target)")]


def test_redownload_releases_player_source_and_aborts_if_old_file_cannot_be_removed() -> None:
    source = src("audioknigi/qt/mixins/clipboard.py")
    start = source.index("elif action is redownload:")
    end = source.index("elif action is download:", start)
    block = source[start:end]
    assert "controller.unload_if_path(path)" in block
    assert "except Exception as exc:" in block
    assert "return" in block
    assert block.index("return") < block.index("track.local_status = TRACK_STATUS_MISSING")


def test_player_controller_can_unload_current_windows_file_and_ui_handles_empty_source() -> None:
    controller = src("audioknigi/qt/player_controller.py")
    assert "def unload(self, *, save_position: bool = True)" in controller
    assert "self.player.setSource(QUrl())" in controller
    assert 'self.sourceChanged.emit("")' in controller
    assert "def unload_if_path" in controller

    mixin = src("audioknigi/qt/player_mixin.py")
    start = mixin.index("def _player_source_changed")
    end = mixin.index("def _player_position_changed", start)
    block = mixin[start:end]
    assert "if not source_text:" in block
    assert "button.setEnabled(False)" in block
    assert "self.player_seek_slider.setEnabled(False)" in block


def test_keyboard_seek_is_coalesced_before_touching_media_backend() -> None:
    source = src("audioknigi/qt/player_mixin.py")
    init_start = source.index("def _init_player")
    init_end = source.index("def _selected_track", init_start)
    init = source[init_start:init_end]
    assert "self._player_keyboard_seek_timer = QTimer(self)" in init
    assert "setSingleShot(True)" in init
    assert "setInterval(120)" in init

    preview_start = source.index("def _player_seek_preview")
    preview_end = source.index("def _on_player_volume_slider_moved", preview_start)
    preview = source[preview_start:preview_end]
    assert "self._player_keyboard_seek_timer.start()" in preview
    assert "self.player_controller.seek(int(value) * 1000)" not in preview

    commit_start = source.index("def _commit_keyboard_seek")
    commit_end = source.index("def _player_seek_preview", commit_start)
    commit = source[commit_start:commit_end]
    assert "value = self.player_seek_slider.value()" in commit
    assert "self.player_controller.seek(int(value) * 1000)" in commit
