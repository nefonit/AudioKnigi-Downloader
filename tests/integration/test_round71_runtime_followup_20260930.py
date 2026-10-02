from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from audioknigi.download.errors import SharedSourceTimelineError
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, SearchResult, Track
from audioknigi.providers import audioknigi_search
from audioknigi.services.book_analysis_service import BookAnalysisService

ROOT = Path(__file__).resolve().parents[2]


def test_playlist_duration_zero_falls_through_to_positive_length():
    service = BookAnalysisService(cancel_event=threading.Event())
    playlist = json.dumps([
        {
            "file": "https://cdn.invalid/a.mp3",
            "title": "Part 1",
            "duration": "0",
            "length": "12.5",
        }
    ])
    book = service._parse_playlist_data(
        url="https://audioknigi.com.ua/audio-1-demo",
        html_text="<html><title>Demo</title></html>",
        page_title="Demo",
        playlist_url="https://cdn.invalid/book.pl.txt",
        playlist_text=playlist,
    )
    assert len(book.tracks) == 1
    assert book.tracks[0].duration == pytest.approx(12.5)


def test_zero_hydration_limit_does_not_construct_zero_worker_pool(monkeypatch):
    source = SearchResult(
        title="Demo",
        author="Author",
        narrator="",
        url="https://audioknigi.com.ua/audio-1-demo",
        source="audioknigi.com.ua",
    )
    monkeypatch.setattr(audioknigi_search, "_MAX_HYDRATED_SEARCH_RESULTS", 0)
    rows = audioknigi_search._group_audioknigi_recordings([source])
    assert rows


def test_clipboard_prompt_compares_canonical_supported_urls():
    source = (ROOT / "audioknigi/qt/mixins/clipboard.py").read_text(encoding="utf-8")
    start = source.index("def _check_clipboard_for_book_link")
    end = source.index("def _insert_clipboard_book_link", start) if "def _insert_clipboard_book_link" in source[start + 1:] else len(source)
    block = source[start:end]
    assert "normalized_clipboard = normalize_supported_url(text)" in block
    assert "normalize_supported_url(value) if valid_site_url(value) else value" in block
    assert "if normalized_clipboard in normalized_current_values:" in block


def test_primary_download_rejects_zero_track_book_explicitly():
    source = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    start = source.index("def _start_primary_download")
    end = source.index("def _update_download_primary_button", start)
    block = source[start:end]
    assert 'len(list(getattr(self.current_book, "tracks", None) or []))' in block
    assert "if total <= 0 or selected <= 0:" in block


@pytest.mark.parametrize(
    ("language", "fragment"),
    [
        ("en", "source is already MP3"),
        ("de", "Quelle ist bereits MP3"),
        ("uk", "джерело вже MP3"),
    ],
)
def test_smart_format_runtime_message_is_localized(language, fragment):
    source = (
        "Smart Format: источник уже MP3 96k/2ch; повышать его до профиля "
        "128k/2ch перекодированием не имеет смысла — сохраняю исходный поток без потери качества."
    )
    translated = localize_runtime_text(language, source)
    assert translated != source
    assert fragment in translated


def test_missing_next_boundary_remains_a_shared_source_integrity_error(tmp_path):
    class Harness(MediaProcessingMixin):
        def _track_path(self, _book, track):
            return tmp_path / f"{track.index}.mp3"

    tracks = [
        Track(index=1, title="One", file="shared.mp3", start=0.0),
        Track(index=2, title="Two", file="shared.mp3", start=None),
    ]
    book = Book(url="https://example.invalid/book", title="Book", tracks=tracks)
    with pytest.raises(SharedSourceTimelineError):
        Harness()._split_track(book, tracks[0], tmp_path / "shared.mp3")


def test_round70_fixes_remain_present():
    player = (ROOT / "audioknigi/qt/player_mixin.py").read_text(encoding="utf-8")
    engine = (ROOT / "audioknigi/download_engine.py").read_text(encoding="utf-8")
    progress = (ROOT / "audioknigi/qt/search_progress.py").read_text(encoding="utf-8")
    settings = (ROOT / "audioknigi/qt/mixins/settings.py").read_text(encoding="utf-8")
    assert '"cover.webp"' in player
    assert "selected_indices=list(full_indices)" in engine
    assert "except OSError:" in engine[engine.index("def duplicate_preflight"):engine.index("def delete_existing_outputs")]
    assert "if side < 16:" in progress
    assert "replace_all(updated)" in settings
