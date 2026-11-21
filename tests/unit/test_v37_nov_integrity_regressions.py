"""Offline regressions for November V37 audit: media integrity and Qt state."""
from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from audioknigi.config.settings import AppSettings, migrate_settings
from audioknigi.core import safe_int, safe_name
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.contracts import DownloadCallbacks
from audioknigi.download.engine import _DownloadEngine
from audioknigi.download.errors import MissingMediaSourceError
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.models import Book, Track
from audioknigi.services.download_request import DownloadRequest


@pytest.mark.parametrize("message,expired", [
    ("HTTP error 404 Not Found", True),
    ("Server returned 410 Gone", True),
    ("FFmpeg не смог прочитать HLS: Server returned 404 Not Found", True),
    ("403 Forbidden", False),
    ("Connection timed out", False),
])
def test_ffmpeg_hls_status_triggers_playlist_refresh(message, expired):
    assert BookFlowMixin._is_expired_media_error(RuntimeError(message)) is expired


def test_parallel_hls_404_propagates_without_retrying_ffmpeg(tmp_path, monkeypatch):
    import audioknigi.download.network as network

    def raise_404(*_a, **_kw):
        raise requests.HTTPError("404 Client Error", response=SimpleNamespace(status_code=404))

    monkeypatch.setattr(network, "resolve_executable", lambda _name: "ffmpeg")
    monkeypatch.setattr(network, "stage_hls_vod", raise_404)
    monkeypatch.setattr(network.subprocess, "Popen", lambda *_a, **_kw: pytest.fail("must not invoke ffmpeg"))

    class Downloader(NetworkDownloadMixin):
        runtime_hls_parallel_enabled = True
        runtime_segment_count = "auto"
        runtime_bandwidth_limit = 0
        runtime_audio_preset = "copy"
        runtime_normalization_mode = "off"
        cancel_event = threading.Event()
        _is_expired_media_error = staticmethod(BookFlowMixin._is_expired_media_error)

        def _check_cancel(self):
            pass

        def log(self, _message):
            pass

        def set_status(self, _message):
            pass

        def set_progress(self, _progress):
            pass

    with pytest.raises(requests.HTTPError):
        Downloader()._run_hls_ffmpeg("https://example.test/expired.m3u8", tmp_path / "result.mp3", "")
    assert not list(tmp_path.glob(".*.hls-*.mp3"))


def _engine(tmp_path, *, audio_preset="copy", delete_source=True):
    url = "https://cdn.example.test/book.mp3"
    book = Book(url="https://audioknigi.com.ua/audio-1-test", title="Demo", tracks=[
        Track(index=1, title="One", file=url, duration=60),
        Track(index=2, title="Two", file=url, duration=60),
    ], remote_size=100)
    req = DownloadRequest(book=book, selected_indices=[1, 2], output_dir=tmp_path)
    settings = {
        "audio_preset": audio_preset, "delete_source": delete_source,
        "embed_tags": False, "save_sidecars": False,
    }
    eng = _DownloadEngine(req, settings, threading.Event(), DownloadCallbacks())
    eng._disk_free_for_path = lambda _path: 1_000_000_000
    eng._cached_probe_audio_info = lambda _p: {"codec": "aac", "bit_rate": 128_000}
    eng._save_book_sidecars = lambda *_a, **_kw: None
    eng._scan_audiobookshelf_after_book = lambda *_a, **_kw: None
    eng._add_history = lambda *_a, **_kw: None
    return eng


def test_full_mp3_preflight_rejects_unreadable_or_truncated_files(tmp_path):
    eng = _engine(tmp_path)
    target = tmp_path / "Demo.mp3"
    target.write_bytes(b"not a real mp3")
    eng._book_folder = lambda _book, create=False: tmp_path
    eng._sidecar_metadata_matches_book = lambda *_a: True
    eng._probe_duration = lambda _path: None
    assert eng.duplicate_preflight(full_mp3=True, probe_durations=True).exact_duplicate is False
    eng._probe_duration = lambda _path: 20
    assert eng.duplicate_preflight(full_mp3=True, probe_durations=True).evidence == "full-mp3-incomplete"
    eng._probe_duration = lambda _path: 120
    assert eng.duplicate_preflight(full_mp3=True, probe_durations=True).exact_duplicate is True
    eng._probe_duration = lambda _path: pytest.fail("skip probe when disabled")
    assert eng.duplicate_preflight(full_mp3=True, probe_durations=False).exact_duplicate is True


@pytest.mark.parametrize("fail_encode", [False, True])
def test_full_mp3_transcoding_is_atomic(tmp_path, fail_encode):
    eng = _engine(tmp_path, audio_preset="128k_stereo", delete_source=False)
    eng._book_folder = lambda _book, create=True: tmp_path
    eng._write_resume_manifest = lambda *_a, **_kw: None
    eng._remove_resume_manifest = lambda *_a, **_kw: None
    eng._download_source_with_fallback = lambda _u, _f, path, _r: Path(path).write_bytes(b"original audio")
    eng._effective_mp3_profile = lambda _p: (False, "128k", 2)
    eng._normalization_filter_for_track = lambda *_a: ""
    final = tmp_path / "Demo.mp3"
    final.write_bytes(b"previous complete output")

    def encode(command):
        assert command[-1] != str(final)
        Path(command[-1]).write_bytes(b"new output" if not fail_encode else b"partial output")
        if fail_encode:
            raise RuntimeError("encode interrupted")

    eng._run_ffmpeg = encode
    if fail_encode:
        with pytest.raises(RuntimeError, match="encode interrupted"):
            eng.run_full_mp3()
        assert final.read_bytes() == b"previous complete output"
        assert (tmp_path / ".Demo.full-source").read_bytes() == b"original audio"
    else:
        result = eng.run_full_mp3()
        assert result.target_file == final
        assert final.read_bytes() == b"new output"
    assert not list(tmp_path.glob(".Demo.encode-*.mp3"))


def test_full_mp3_refresh_moves_manifest_and_output_to_updated_book_folder(tmp_path):
    eng = _engine(tmp_path)
    book = eng.request.book
    calls = []

    def folder(book, *, create=True):
        path = tmp_path / book.title
        if create:
            path.mkdir(exist_ok=True, parents=True)
        return path

    eng._book_folder = folder
    eng._write_resume_manifest = lambda book, *_a, **_kw: (folder(book) / "resume.json").write_text("state")
    eng._remove_resume_manifest = lambda *_a, **_kw: None
    eng._effective_mp3_profile = lambda _p: (True, None, None)
    def download(_url, _fallback, dest, _referer):
        calls.append(Path(dest))
        if len(calls) == 1:
            raise MissingMediaSourceError("404 missing")
        Path(dest).write_bytes(b"fresh audio")

    def refresh(book, _selected):
        book.title = "Updated"
        book.tracks[0].file = "https://cdn.example.test/fresh.mp3"
        book.tracks[1].file = "https://cdn.example.test/fresh.mp3"

    eng._download_source_with_fallback = download
    eng._refresh_book_media_playlist = refresh
    result = eng.run_full_mp3()
    assert result.folder == tmp_path / "Updated"
    assert result.target_file == tmp_path / "Updated" / "Updated.mp3"
    assert not (tmp_path / "Demo" / "resume.json").exists()
    assert (tmp_path / "Updated" / "resume.json").exists()
    assert len(calls) == 2
    assert calls[0].parent.name == "Demo" and calls[1].parent.name == "Updated"


def test_exit_save_persists_mapping_without_saving_unsaved_editor_fields(monkeypatch):
    import audioknigi.qt.mixins.lifecycle as lifecycle
    saved = []
    monkeypatch.setattr(lifecycle, "save_app_settings", lambda settings: saved.append(dict(settings)) or True)
    prefs = AppSettings({"output_dir": "D:/Committed", "geometry": ""})
    window = SimpleNamespace(
        settings=prefs,
        queue_store=None,
        player_controller=None,
        _save_window_geometry=lambda: prefs.__setitem__("geometry", "saved-geometry"),
        _settings_from_ui=lambda: pytest.fail("unsaved controls must not persist at exit"),
    )
    lifecycle.LifecycleUiMixin._persist_exit_state_best_effort(window)
    assert saved and saved[0]["output_dir"] == "D:/Committed"
    assert saved[0]["geometry"] == "saved-geometry"


def test_cover_without_url_does_not_request_referer(monkeypatch):
    import audioknigi.engine.cover_fetch as covers
    monkeypatch.setattr(covers, "get_http_session", lambda: pytest.fail("unexpected network call"))
    assert covers.fetch_cover_bytes("", referer="https://example.test/book") is None


def test_old_normalization_true_is_preserved_when_canonical_mode_is_null():
    settings, _ = migrate_settings({"normalization_mode": None, "normalize_audio": True})
    assert settings["normalization_mode"] == "single"


@pytest.mark.parametrize("value,expected", [
    (12.0, 12), (12.5, -1), ("12.0", 12), ("12.5", -1),
    (float("inf"), -1),
])
def test_safe_int_does_not_truncate_fractional_floats(value, expected):
    assert safe_int(value, -1) == expected


def test_windows_reserved_name_with_space_before_extension():
    assert safe_name("NUL .mp3").startswith("_")


def test_analysis_failure_clears_history_redownload_consent_and_stale_modes():
    root = Path(__file__).resolve().parents[2]
    source = (root / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    error = source.split('if kind == "error":', 1)[1].split("book = payload", 1)[0]
    empty = source.split("if not enabled:", 1)[1].split('self.set_status(f"Анализ завершён.', 1)[0]
    assert "self._history_redownload_confirmed = False" in error
    assert "self._history_redownload_confirmed = False" in empty
    assert "self._full_mp3_after_analysis = False" in empty


def test_settings_dns_change_invalidates_existing_http_sessions():
    root = Path(__file__).resolve().parents[2]
    source = (root / "audioknigi/qt/mixins/settings.py").read_text(encoding="utf-8")
    assert 'previous_dns_mode != str(updated.get("dns_mode", "auto") or "auto")' in source
    assert 'app.setProperty("audioknigi_language", self.language)' in source
