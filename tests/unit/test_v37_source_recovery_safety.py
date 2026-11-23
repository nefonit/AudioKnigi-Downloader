"""Regressions for safe chapter commits and interrupted-source recovery."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import threading

import pytest

from audioknigi.core import Cancelled
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.download.probe import ProbeMixin
from audioknigi.download import source_analysis as source_analysis_module
from audioknigi.download.source_analysis import SourceAnalysisMixin
from audioknigi.models import Book, Track
from audioknigi.services import book_analysis_service as analysis_service


def _book(url, *, restricted=False, playable=True):
    tracks = [Track(index=1, title="One", file="https://example.org/part1.mp3")] if playable else []
    return SimpleNamespace(
        url=url, title="Alpha Book", author="Writer", narrator="Reader",
        restricted=restricted, tracks=tracks,
    )


def _fallback_stub():
    return SimpleNamespace(
        cancel_event=threading.Event(),
        _check_cancel=lambda: None,
        _book_identity_hints=lambda book: (book.title, book.author, book.narrator),
        _identity_tokens=lambda value: set(str(value or "").casefold().split()),
    )


@pytest.mark.parametrize("analysis", [False, True])
def test_restricted_and_empty_fallbacks_are_skipped(monkeypatch, analysis):
    results = [
        SimpleNamespace(title="Alpha Book", author="Writer", narrator="Reader",
                        url=f"https://knigavuhe.org/book/{index}/", narration_variants=[])
        for index in range(1, 4)
    ]
    alternatives = {
        results[0].url: _book(results[0].url, restricted=True),
        results[1].url: _book(results[1].url, playable=False),
        results[2].url: _book(results[2].url),
    }
    if analysis:
        monkeypatch.setattr(analysis_service, "search_knigavuhe_books", lambda *_a, **_kw: results)
        monkeypatch.setattr(analysis_service, "fetch_knigavuhe_book", lambda url, **_kw: alternatives[url])
        found = analysis_service.BookAnalysisService._knigavuhe_fallback_candidate(
            _fallback_stub(), _book("https://audioknigi.com.ua/audio-1")
        )
    else:
        monkeypatch.setattr(source_analysis_module, "search_knigavuhe_books", lambda *_a, **_kw: results)
        monkeypatch.setattr(
            source_analysis_module, "provider_for_key",
            lambda *_a: SimpleNamespace(fetch_book=lambda url, **_kw: alternatives[url]),
        )
        found = SourceAnalysisMixin._knigavuhe_fallback_candidate(
            _fallback_stub(), _book("https://audioknigi.com.ua/audio-1")
        )
    assert found is alternatives[results[2].url]


def test_split_track_failed_encoder_keeps_existing_chapter(tmp_path):
    output = tmp_path / "01.mp3"
    output.write_bytes(b"VERIFIED COMPLETED OLD CHAPTER")
    tracked = []
    class Split(MediaProcessingMixin):
        def _track_path(self, *_a):
            return output
        def _effective_mp3_profile(self, *_a):
            return False, "96k", 2
        def _normalization_filter_for_track(self, *_a):
            return ""
        def _run_ffmpeg(self, cmd):
            stage = Path(cmd[-1])
            tracked.append(stage)
            stage.write_bytes(b"BAD PARTIAL AUDIO")
            raise Cancelled("cancelled")
        def _check_cancel(self): pass
    item = Track(index=1, title="One", file="https://example.org/part1.mp3")
    with pytest.raises(Cancelled):
        Split()._split_track(_book("https://example.org/book/"), item, tmp_path / "source.mp3")
    assert output.read_bytes() == b"VERIFIED COMPLETED OLD CHAPTER"
    assert len(tracked) == 1 and tracked[0] != output
    assert not tracked[0].exists()


def test_split_track_success_replaces_old_chapter_atomically(tmp_path):
    output = tmp_path / "01.mp3"
    output.write_bytes(b"OLD COMPLETED CHAPTER")
    tracked = []
    class Split(MediaProcessingMixin):
        def _track_path(self, *_a): return output
        def _effective_mp3_profile(self, *_a): return False, "96k", 2
        def _normalization_filter_for_track(self, *_a): return ""
        def _run_ffmpeg(self, cmd):
            stage = Path(cmd[-1])
            tracked.append(stage)
            assert stage != output
            stage.write_bytes(b"NEW COMPLETED CHAPTER")
        def _check_cancel(self): pass
    item = Track(index=1, title="One", file="https://example.org/part1.mp3")
    assert Split()._split_track(_book("https://example.org/book/"), item, tmp_path / "source.mp3") == output
    assert output.read_bytes() == b"NEW COMPLETED CHAPTER"
    assert len(tracked) == 1 and not tracked[0].exists()


def test_shared_source_partial_repair_does_not_probe_unneeded_sources():
    source = "https://example.org/old-shared.mp3"
    tracks = [
        Track(index=1, title="One", file=source, start=0, end=20),
        Track(index=2, title="Two", file=source, start=20, end=40),
    ]
    class Probe:
        def _probe_remote_duration(self, *_a):
            pytest.fail("unselected source must not trigger remote ffprobe")
    book = SimpleNamespace(url="https://example.org/book", tracks=tracks)
    assert ProbeMixin._shared_source_timeline_issue(Probe(), book, local_map={}) is None


def test_final_scan_and_history_precede_resume_manifest_removal():
    root = Path(__file__).resolve().parents[2]
    source = (root / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    end = source[source.index("        self._save_book_sidecars(book, folder,"):source.index('            "download_complete", book')]
    assert end.index("self._scan_book_files(book)") < end.index("self._add_history(book, folder")
    assert end.index("self._add_history(book, folder") < end.index("self._remove_resume_manifest(book)")


def test_full_mp3_records_expected_hls_duration_for_refresh():
    root = Path(__file__).resolve().parents[2]
    source = (root / "audioknigi/download/engine.py").read_text(encoding="utf-8")
    block = source[source.index("    def run_full_mp3("):source.index("    def run(", source.index("    def run_full_mp3("))]
    assert "self._hls_expected_durations =" in block
    assert block.count("update_hls_expected_durations()") >= 2
