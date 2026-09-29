from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from audioknigi.download.media import MediaProcessingMixin
from audioknigi.download.probe import ProbeMixin
from audioknigi.models import Book, Track, TRACK_STATUS_READY
from audioknigi.providers.audioknigi_search import _response_html_text
from audioknigi.services.player_position_store import PlayerPositionStore

ROOT = Path(__file__).resolve().parents[2]


def test_probe_accepts_track_objects_as_selected_indices(tmp_path):
    class Harness(ProbeMixin):
        runtime_audio_preset = "copy"

        def _book_folder(self, _book, *, create=True):
            return tmp_path

    track = Track(index=1, title="One", file="https://example.invalid/1.mp3", local_status=TRACK_STATUS_READY)
    book = Book(url="https://example.invalid/book", title="Book", tracks=[track])
    assert Harness()._estimate_required_space(book, [track]) == 0


def test_response_html_prefers_detected_encoding_before_http_default_latin1():
    original = "Исполнитель: Илья Кривошеев"

    class Response:
        content = original.encode("cp1251")
        encoding = "ISO-8859-1"
        apparent_encoding = "windows-1251"
        text = ""

    assert _response_html_text(Response()) == original


def test_non_german_locales_do_not_leak_german_key_names():
    messages = json.loads((ROOT / "audioknigi/locales/messages.json").read_text(encoding="utf-8"))
    literals = json.loads((ROOT / "audioknigi/locales/legacy_literals.json").read_text(encoding="utf-8"))
    for language in ("en", "ru", "uk"):
        combined = "\n".join(str(value) for value in messages[language].values())
        if language in literals:
            combined += "\n" + "\n".join(str(value) for value in literals[language].values())
        assert "Leertaste" not in combined
        assert "Umschalt" not in combined
    assert "Space" in messages["en"]["help_shortcuts_body"]
    assert "Пробел" in messages["ru"]["help_shortcuts_body"]
    assert "Пробіл" in messages["uk"]["help_shortcuts_body"]
    assert "Shift+F10" in messages["en"]["help_shortcuts_body"]
    assert "Shift+F10" in messages["ru"]["help_shortcuts_body"]
    assert "Shift+F10" in messages["uk"]["help_shortcuts_body"]


def test_reported_german_and_ukrainian_wording_is_consistent():
    literals = json.loads((ROOT / "audioknigi/locales/legacy_literals.json").read_text(encoding="utf-8"))
    assert literals["de"]["Вставьте ссылку на книгу или введите название/автора для поиска, затем выберите нужные части."] == (
        "Fügen Sie einen Buch-Link ein oder suchen Sie nach Titel/Autor und wählen Sie anschließend die gewünschten Teile."
    )
    assert literals["de"]["Вставьте ссылку на книгу или введите название/автора для поиска."] == (
        "Fügen Sie einen Buch-Link ein oder geben Sie Titel/Autor für die Suche ein."
    )
    assert literals["uk"]["Главы текущей книги"] == "Розділи поточної книги"


def test_player_position_keys_preserve_case_on_posix(tmp_path):
    upper = tmp_path / "Track.mp3"
    lower = tmp_path / "track.mp3"
    upper.write_bytes(b"A")
    lower.write_bytes(b"B")
    if os.name == "nt":
        pytest.skip("Windows intentionally normalizes case")
    assert PlayerPositionStore.key(upper) != PlayerPositionStore.key(lower)


def test_audio_info_cache_refreshes_hits_before_eviction(tmp_path, monkeypatch):
    from audioknigi.download import media as media_module

    monkeypatch.setattr(media_module, "_AUDIO_INFO_CACHE_MAX", 2)

    class Harness(MediaProcessingMixin):
        def __init__(self):
            self.calls = []

        def _probe_audio_info(self, path):
            self.calls.append(Path(path).name)
            return {"codec": "mp3", "channels": 2, "bit_rate": 128000}

    files = [tmp_path / name for name in ("one.mp3", "two.mp3", "three.mp3")]
    for index, path in enumerate(files):
        path.write_bytes(bytes([index + 1]))

    harness = Harness()
    harness._cached_probe_audio_info(files[0])
    harness._cached_probe_audio_info(files[1])
    harness._cached_probe_audio_info(files[0])  # refresh one as most recently used
    harness._cached_probe_audio_info(files[2])

    cached_paths = {key[0] for key in harness._audio_info_cache}
    assert str(files[0].resolve()) in cached_paths
    assert str(files[2].resolve()) in cached_paths
    assert str(files[1].resolve()) not in cached_paths


def test_loudnorm_filter_complex_keeps_requested_range(monkeypatch):
    from audioknigi.download import media as media_module

    captured = {}
    monkeypatch.setattr(media_module, "resolve_executable", lambda _name: "ffmpeg")

    class Harness(MediaProcessingMixin):
        def _run_ffmpeg_capture(self, cmd, timeout):
            captured["cmd"] = list(cmd)
            return '{"input_i":"-20","input_lra":"4","input_tp":"-2","input_thresh":"-30","target_offset":"1"}'

    Harness()._measure_loudnorm(
        "source.mp3",
        start=12.5,
        duration=30,
        filter_complex="[0:a]anull[a]",
        map_label="a",
    )
    cmd = captured["cmd"]
    assert cmd[cmd.index("-ss") + 1] == "12.5"
    assert cmd[cmd.index("-t") + 1] == "30"


def test_history_lock_contracts_and_dead_privacy_bookkeeping_removed():
    support = (ROOT / "audioknigi/diagnostics/support_bundle.py").read_text(encoding="utf-8")
    library = (ROOT / "audioknigi/services/library_service.py").read_text(encoding="utf-8")
    engine = (ROOT / "audioknigi/download_engine.py").read_text(encoding="utf-8")
    assert "original_was_absolute_path" in support
    assert "if collapse_whole_path and original_was_absolute_path" in support
    assert "if target == HISTORY_FILE:\n                        with HISTORY_LOCK:\n                            target.unlink" in library
    block = engine.split("def _history_metadata_matches_book", 1)[1].split("def _sidecar_metadata_matches_book", 1)[0]
    assert "with HISTORY_LOCK:" in block
    assert "history = load_json(HISTORY_FILE, [])" in block
