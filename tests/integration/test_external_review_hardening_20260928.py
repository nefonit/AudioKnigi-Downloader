from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import socket
import threading

import pytest

from audioknigi.core import Cancelled
from audioknigi.diagnostics.support_bundle import _privacy_path, _sanitize_setting_value
from audioknigi.network_dns import _read_http_head
from audioknigi.providers.audioknigi_search import (
    _audioknigi_page_metadata,
    _looks_like_author_prefix,
    _same_author_identity,
)
from audioknigi.services.book_analysis_service import _playlist_track_title
from audioknigi.services.player_position_store import PlayerPositionStore

ROOT = Path(__file__).resolve().parents[2]


def test_support_bundle_redacts_posix_configured_and_embedded_paths():
    assert _privacy_path("/mnt/storage/Audiobooks") == "<configured-path>"
    assert _sanitize_setting_value("output_dir", "/media/user/Disk/Audiobooks") == "<configured-path>"
    text = _privacy_path(
        "download failed at /mnt/storage/Audiobooks/Private Book/01.mp3; retrying",
        collapse_whole_path=False,
    )
    assert "/mnt/storage" not in text
    assert "<configured-path>" in text
    assert _privacy_path("https://example.com/library/book.mp3", collapse_whole_path=False) == "https://example.com/library/book.mp3"


def test_audioknigi_partial_initial_expansion_and_long_initial_names():
    assert _same_author_identity("А. С. Пушкин", "Александр Пушкин")
    assert _same_author_identity("А. С. Пушкин", "Александр Сергеевич Пушкин")
    assert _looks_like_author_prefix("Дж. Р. Р. Толкин мл.")
    assert not _looks_like_author_prefix("S.T.A.L.K.E.R.")


def test_audioknigi_metadata_honors_pre_cancel_without_http():
    called = False

    def session_factory():
        nonlocal called
        called = True
        raise AssertionError("HTTP session must not be created after cancellation")

    event = threading.Event()
    event.set()
    with pytest.raises(Cancelled):
        _audioknigi_page_metadata(
            type("Result", (), {"url": "https://audioknigi.com.ua/test"})(),
            cancel_event=event,
            session_factory=session_factory,
        )
    assert called is False


@pytest.mark.parametrize("title", ["Chapter_01", "Track-01", "Part_1", "CD1_01"])
def test_meaningful_numbered_playlist_titles_are_preserved(title):
    assert _playlist_track_title(title, "https://example.com/raw_audio_01.mp3", 1, "Book", 5) == title


def test_machine_playlist_slug_is_still_replaced():
    assert _playlist_track_title(
        "audio_01_320kbps_final_1",
        "https://example.com/different.mp3",
        1,
        "Book",
        5,
    ) == "Book — 01"


def test_player_position_timestamp_is_timezone_aware(tmp_path):
    store = PlayerPositionStore(tmp_path / "positions.json")
    audio = tmp_path / "chapter.mp3"
    audio.write_bytes(b"x")
    assert store.update(audio, 10.0, 100.0, persist=False)
    record = next(iter(store.snapshot().values()))
    parsed = datetime.fromisoformat(str(record["updated"]))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() is not None


def test_proxy_header_reader_accepts_lf_only_headers():
    left, right = socket.socketpair()
    try:
        right.sendall(b"CONNECT example.com:443 HTTP/1.1\nHost: example.com\n\nTAIL")
        head, remainder = _read_http_head(left, deadline_seconds=1.0)
    finally:
        left.close()
        right.close()
    assert b"CONNECT example.com:443" in head
    assert remainder == b"TAIL"


def test_round59_source_contracts():
    media = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    network = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    book_flow = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    event_sounds = (ROOT / "audioknigi/qt/event_sounds.py").read_text(encoding="utf-8")
    track_model = (ROOT / "audioknigi/qt/track_model.py").read_text(encoding="utf-8")
    clipboard = (ROOT / "audioknigi/qt/mixins/clipboard.py").read_text(encoding="utf-8")
    queue = (ROOT / "audioknigi/qt/mixins/queue.py").read_text(encoding="utf-8")
    analysis = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    settings_sync = (ROOT / "audioknigi/qt/settings_sync.py").read_text(encoding="utf-8")
    application = (ROOT / "audioknigi/qt/application.py").read_text(encoding="utf-8")
    player = (ROOT / "audioknigi/qt/player_controller.py").read_text(encoding="utf-8")
    entry = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")

    assert "normalize_cover_cache(self._cover_bytes(book))" in media
    assert "last_observe = [0.0]" in network
    assert "tag_jobs = []" in book_flow
    assert "_queued_configure = Signal(object, object, object)" in event_sounds
    assert "def set_selected_indices" in track_model
    assert "self.dataChanged.emit(left, right, [])" in track_model
    assert "previous_selection = list(self.track_model.selected_indices())" in clipboard
    assert "self.queue_table.clearSelection()" in queue
    assert "_pending_narration_selected_all" in analysis
    assert "old_count == len(book.tracks)" in analysis
    assert 'blocker = getattr(self.quality_combo, "blockSignals", None)' in settings_sync
    assert 'blocker = getattr(self.easy_quality_combo, "blockSignals", None)' in settings_sync
    assert 'app_logger.debug("Failed to build Qt crash report"' in application
    assert "zero-duration instant completion" in player
    assert "QCoreApplication.sendPostedEvents()" in entry
    assert "send_posted_events(None" not in entry


def test_changelog_and_runtime_translation_format_are_clean():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "\\n\\n" not in changelog
    assert "Acceptance parser, cancellation and diagnostics hardening (2026-09-18)" in changelog
    assert "Post-release audit updates through 2026-09-29" in changelog

    raw = (ROOT / "audioknigi/locales/runtime_exact.json").read_text(encoding="utf-8")
    assert raw.count('"Проверить системный звук":') == 1
    data = json.loads(raw)
    for key in ("Проверить звук события", "Проверить системный звук"):
        assert list(data[key])[:3] == ["de", "en", "uk"]
