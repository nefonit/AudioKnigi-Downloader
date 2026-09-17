from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.sources import is_supported_url, normalize_supported_url
from audioknigi import poleknig
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.services import book_analysis_service as analysis_module
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.models import Book, SearchResult


ROOT = Path(__file__).resolve().parents[2]


def test_poleknig_slash_slug_is_supported_and_canonicalized() -> None:
    raw = "https://www.poleknig.com/books/12345/some-slug?utm_source=test#fragment"
    assert is_supported_url(raw)
    assert normalize_supported_url(raw) == "https://poleknig.com/books/12345"
    assert poleknig._canonical_book_url("https://poleknig.com/", raw) == "https://poleknig.com/books/12345"
    assert poleknig._canonical_book_url("https://poleknig.com/", "/books/12345/some-slug") == "https://poleknig.com/books/12345"


def test_split_track_does_not_infer_duration_from_next_different_source(tmp_path) -> None:
    class Dummy(MediaProcessingMixin):
        def _track_path(self, _book, _track):
            return tmp_path / "out.mp3"
        def _effective_mp3_profile(self, _source):
            return True, None, None
        def _run_ffmpeg(self, cmd):
            self.cmd = list(cmd)
        def _normalization_filter_for_track(self, *_args):
            return ""
        def log(self, *_args, **_kwargs):
            pass

    current = SimpleNamespace(index=1, start=10, end=None, duration=None, actual_duration=None, file="part1.mp3")
    following = SimpleNamespace(index=2, start=20, end=None, duration=None, actual_duration=None, file="part2.mp3")
    book = SimpleNamespace(tracks=[current, following])
    dummy = Dummy()
    dummy._split_track(book, current, tmp_path / "part1.mp3")
    assert "-ss" in dummy.cmd
    assert "-t" not in dummy.cmd


def test_knigavuhe_fallback_prefers_known_matching_narrator(monkeypatch) -> None:
    original = Book(title="Book", author="Author", narrator="Exact Narrator", url="https://audioknigi.com.ua/audio-1")
    results = [
        SearchResult(title="Book", author="Author", narrator="", url="https://knigavuhe.org/book/unknown/", source="knigavuhe"),
        SearchResult(title="Book", author="Author", narrator="Exact Narrator", url="https://knigavuhe.org/book/exact/", source="knigavuhe"),
    ]
    monkeypatch.setattr(analysis_module, "search_knigavuhe_books", lambda *_a, **_k: results)

    def fake_fetch(url, **_kwargs):
        narrator = "" if "unknown" in url else "Exact Narrator"
        return Book(title="Book", author="Author", narrator=narrator, url=url)

    monkeypatch.setattr(analysis_module, "fetch_knigavuhe_book", fake_fetch)
    selected = BookAnalysisService()._knigavuhe_fallback_candidate(original)
    assert selected is not None
    assert selected.url.endswith("/exact/")


def test_round19_windows_file_retry_contracts_are_used() -> None:
    network = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    flow = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    assert "replace_with_retry(part, target)" in network
    assert "from .common import unlink_with_retry" in flow
    assert "unlink_with_retry(path, missing_ok=False)" in flow


def test_round19_duplicate_metadata_uses_mapping_aware_book_fields() -> None:
    source = (ROOT / "audioknigi/download_engine.py").read_text(encoding="utf-8")
    history = source.split("def _history_metadata_matches_book", 1)[1].split("def _sidecar_metadata_matches_book", 1)[0]
    sidecar = source.split("def _sidecar_metadata_matches_book", 1)[1].split("def _full_mp3_target", 1)[0]
    assert 'self._book_field(book, "url", "")' in history
    assert 'self._book_field(book, "tracks", [])' in history
    assert "self._book_field(book, name, \"\")" in history
    assert 'self._book_field(book, "url", "")' in sidecar
    assert 'self._book_field(book, "tracks", [])' in sidecar


def test_round19_easy_mode_free_text_search_is_not_treated_as_stale_url() -> None:
    source = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    block = source.split("def _update_easy_action_text", 1)[1].split("def _l", 1)[0]
    assert "incoming_url = normalize_supported_url(value) if is_url and valid_site_url(value) else \"\"" in block
    assert "easy_stale = bool(is_url and not" in block


def test_round19_player_dialogs_and_f1_help_are_localized_and_consistent() -> None:
    player = (ROOT / "audioknigi/qt/player_mixin.py").read_text(encoding="utf-8")
    accessibility = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    assert 'self._l("Файл не найден")' in player
    assert 'self._l("Ошибка плеера")' in player
    assert 'show_context_help(topic="shortcuts")' in accessibility


def test_round19_full_mp3_uses_whole_book_selection_contract() -> None:
    source = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    block = source.split("def start_full_mp3", 1)[1].split("def ", 1)[0]
    assert "build_download_request(self.current_book, live_settings, None)" in block
    assert "[DownloadRequest.track_index(track)" not in block
