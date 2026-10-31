"""Regressions from October 15 audit of legacy settings and track mappings."""

from types import SimpleNamespace

import pytest

from audioknigi.config.settings import AppSettings, migrate_settings
from audioknigi.download.probe import ProbeMixin
from audioknigi.services.queue_service import task_from_dict
from audioknigi.i18n import localize_runtime_text


@pytest.mark.parametrize("disabled", ["false", "FALSE", "0", "off", "нет", "ні", "nein", False, 0])
def test_legacy_normalize_audio_false_stays_off(disabled):
    settings, _ = migrate_settings({"normalize_audio": disabled})
    assert settings["normalization_mode"] == "off"


@pytest.mark.parametrize("enabled", ["true", "1", "yes", "on", True, 1])
def test_legacy_normalize_audio_true_is_single(enabled):
    settings, _ = migrate_settings({"normalize_audio": enabled})
    assert settings["normalization_mode"] == "single"


def test_legacy_app_settings_false_string_does_not_enable_normalization():
    settings = AppSettings({"normalization_mode": "two_pass"})
    settings["normalize_audio"] = "false"
    assert settings["normalization_mode"] == "off"


@pytest.mark.parametrize("disabled", ["false", "0", "off", False])
def test_legacy_queue_false_normalize_audio_stays_off(disabled):
    task = task_from_dict({"url": "https://audioknigi.com.ua/example", "title": "Legacy", "normalize_audio": disabled})
    assert task.request.normalization_mode == "off"


def test_legacy_queue_true_normalize_audio_is_single():
    task = task_from_dict({"url": "https://audioknigi.com.ua/example", "title": "Legacy", "normalize_audio": "true"})
    assert task.request.normalization_mode == "single"


def test_shared_audio_source_dict_tracks_detect_truncation():
    probe = ProbeMixin()
    probe._probe_remote_duration = lambda _url, _referer: 50.0
    book = SimpleNamespace(url="https://audioknigi.com.ua/book", tracks=[
        {"index": 1, "file": "https://audioknigi.com.ua/shared.mp3", "start": 0, "end": 60},
        {"index": 2, "file": "https://audioknigi.com.ua/shared.mp3", "start": 60, "end": 120},
    ])
    issue = probe._shared_source_timeline_issue(book)
    assert issue is not None
    assert issue["track_indices"] == [1, 2]
    assert issue["reason"] == "duration_short"


def test_missing_media_playlist_prefix_localizes_full_german():
    message = "После обновления плейлиста исчезли выбранные части: 1, 2"
    translated = localize_runtime_text("de", message)
    assert "Playlist" in translated
    assert "1, 2" in translated


def test_queue_track_path_is_json_compatible():
    import json
    from pathlib import Path
    from audioknigi.models import Book, Track
    from audioknigi.services.queue_service import _book_to_dict

    book = Book(url="https://example.com/book", title="Book", tracks=[
        Track(index=1, title="Chapter", file="https://example.com/audio", local_path=Path("/tmp/audio.mp3"))
    ])
    payload = json.loads(json.dumps(_book_to_dict(book), ensure_ascii=False))
    stored_path = payload["tracks"][0]["local_path"]
    assert isinstance(stored_path, str)
    assert Path(stored_path) == Path("/tmp/audio.mp3")
