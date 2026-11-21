"""Regression checks for safe V37 backup recovery and invalid source cleanup."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.config.settings import AppSettings
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.models import Book, Track
from audioknigi.qt.mixins import history as history_ui
from audioknigi.qt.mixins.history import HistoryUiMixin


def test_refresh_cleanup_removes_only_engine_owned_hls_caches(tmp_path):
    owned = tmp_path / "._source_02.hls-cache"
    owned.mkdir()
    (owned / "signed-manifest.json").write_text("stale", encoding="utf-8")
    other = tmp_path / "My.Book.hls-cache"
    other.mkdir()
    (other / "keep.txt").write_text("user content", encoding="utf-8")
    stranger = tmp_path / "._source of wisdom.hls-cache"
    stranger.mkdir()
    (stranger / "keep.txt").write_text("not ours", encoding="utf-8")
    partial = tmp_path / "_source.mp3.part"
    partial.write_bytes(b"broken")

    class Flow(BookFlowMixin):
        def _book_folder(self, _book, *, create=False):
            return tmp_path

        def log(self, *_args):
            pass

    removed = Flow()._clear_stale_source_downloads(None)
    assert removed == 2
    assert not owned.exists() and not partial.exists()
    assert (other / "keep.txt").exists()
    assert (stranger / "keep.txt").exists()


@pytest.mark.parametrize("start,end", [(30, 20), (30, 30), ("00:40", "00:10")])
def test_split_invalid_explicit_boundaries_fail_before_overwriting_audio(start, end):
    class Flow(MediaProcessingMixin):
        def _track_path(self, *_args, **_kw):
            raise AssertionError("must not touch a complete chapter on invalid timings")

    book = Book(
        title="Book", url="https://audioknigi.com.ua/audio-1-test",
        tracks=[Track(index=1, title="Chapter", file="https://cdn.example/audio.mp3", start=start, end=end)],
    )
    with pytest.raises(RuntimeError, match="Некорректные границы части"):
        Flow()._split_track(book, book.tracks[0], Path("existing.mp3"))


def test_restored_runtime_settings_apply_dns_proxy_language_and_sound(monkeypatch):
    calls = []
    monkeypatch.setattr(history_ui, "configure_user_proxy", lambda url: calls.append(("proxy", url)))
    monkeypatch.setattr(history_ui, "configure_proxy_hosts", lambda hosts: calls.append(("hosts", hosts)))
    monkeypatch.setattr(history_ui, "install_cloudflare_dns", lambda *, mode: calls.append(("dns", mode)))
    monkeypatch.setattr(history_ui, "refresh_http_session_profile", lambda: calls.append(("refresh",)))
    fake_app = SimpleNamespace(setProperty=lambda *args: calls.append(("property", *args)))
    monkeypatch.setattr(history_ui, "QApplication", SimpleNamespace(instance=lambda: fake_app))

    sound = SimpleNamespace(configure=lambda **kw: calls.append(("sound", kw)))
    window = SimpleNamespace(
        settings=AppSettings({
            "proxy_url": "",
            "proxy_only_hosts": "cdn.example",
            "dns_mode": "system",
            "language": "de",
            "event_sounds_enabled": False,
            "event_sound_volume": 40,
        }),
        language="ru",
        event_sound_manager=sound,
    )
    HistoryUiMixin._apply_restored_runtime_settings(window)
    assert window.language == "de"
    assert ("dns", "system") in calls
    assert ("refresh",) in calls
    assert ("property", "audioknigi_language", "de") in calls
    assert ("sound", {"enabled": False, "volume": 0.4, "language": "de"}) in calls


def test_restored_settings_keep_mapping_identity_for_existing_controllers():
    original = AppSettings({"language": "ru"})
    reference_held_by_controller = original
    restored = AppSettings({"language": "uk", "dns_mode": "cloudflare"})
    original.replace_all(restored.to_dict())
    assert reference_held_by_controller is original
    assert reference_held_by_controller["language"] == "uk"
    assert reference_held_by_controller["dns_mode"] == "cloudflare"
