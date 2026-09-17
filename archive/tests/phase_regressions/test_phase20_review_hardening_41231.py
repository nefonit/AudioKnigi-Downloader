from __future__ import annotations

from pathlib import Path
import threading

import pytest


def make_request(tmp_path: Path, *, use_templates: bool = False):
    from audioknigi.models import Book, Track
    from audioknigi.services.download_request import DownloadRequest

    book = Book(
        url="https://knigavuhe.org/book/example/",
        title="Example Book",
        author="Example Author",
        tracks=[Track(1, "One", "https://media.example/one.mp3")],
    )
    return DownloadRequest(
        book=book,
        selected_indices=[1],
        output_dir=tmp_path,
        use_templates=use_templates,
        folder_template="{Author}/{Book_Title}",
    )


@pytest.mark.parametrize("use_templates", [False, True])
def test_duplicate_preflight_does_not_create_output_folder(tmp_path, use_templates):
    from audioknigi.download_engine import _DownloadEngine

    request = make_request(tmp_path, use_templates=use_templates)
    engine = _DownloadEngine(request, {}, threading.Event(), None)

    result = engine.duplicate_preflight()

    assert result.exact_duplicate is False
    assert result.folder.exists() is False
    if use_templates:
        assert (tmp_path / "Example Author").exists() is False
    else:
        assert (tmp_path / "Example Book").exists() is False


def test_direct_knigavuhe_analysis_receives_cancel_event(monkeypatch, tmp_path):
    import audioknigi.downloader as downloader
    from audioknigi.download_engine import _DownloadEngine
    from audioknigi.models import Book, Track

    request = make_request(tmp_path)
    cancel_event = threading.Event()
    engine = _DownloadEngine(request, {}, cancel_event, None)
    seen = []

    def fake_fetch(url, cancel_event=None):
        seen.append(cancel_event)
        return Book(url=url, title="Book", tracks=[Track(1, "One", "https://media.example/1.mp3")])

    monkeypatch.setattr(downloader, "fetch_knigavuhe_book", fake_fetch)
    monkeypatch.setattr(engine, "_populate_missing_track_durations", lambda _book: 0)
    monkeypatch.setattr(engine, "log", lambda *_a, **_k: None)

    engine._analyze_book("https://knigavuhe.org/book/example/")
    assert seen == [cancel_event]


def test_shared_source_fallback_is_attempted_only_once(monkeypatch, tmp_path):
    from audioknigi.download_engine import _DownloadEngine
    from audioknigi.downloader import SharedSourceTimelineError
    from audioknigi.models import Book, Track
    from audioknigi.services.download_request import DownloadRequest

    original = Book(
        url="https://audioknigi.com.ua/audio-1",
        title="Book",
        tracks=[Track(1, "One", "https://bad.example/all.mp3", start=0, end=10)],
    )
    # Pathological fallback: it still identifies as audioknigi.  The explicit
    # fallback budget must prevent repeated source switching in this case.
    malformed_fallback = Book(
        url="https://audioknigi.com.ua/audio-2",
        title="Book fallback",
        tracks=[Track(1, "One", "https://bad.example/all2.mp3", start=0, end=10)],
    )
    request = DownloadRequest(original, [1], tmp_path)
    engine = _DownloadEngine(request, {}, threading.Event(), None)

    attempts = {"process": 0, "fallback": 0}

    def process_once(_book, _selected, _status):
        attempts["process"] += 1
        if attempts["process"] > 2:
            pytest.fail("fallback loop was not bounded")
        raise SharedSourceTimelineError({"expected_end": 10, "actual_duration": 5, "reason": "short"})

    def fallback_candidate(_book):
        attempts["fallback"] += 1
        return malformed_fallback

    monkeypatch.setattr(engine, "_process_book_once", process_once)
    monkeypatch.setattr(engine, "_knigavuhe_fallback_candidate", fallback_candidate)
    monkeypatch.setattr(engine, "_populate_missing_track_durations", lambda _book: 0)
    monkeypatch.setattr(engine, "_log_book_flow", lambda *_a, **_k: None)
    monkeypatch.setattr(engine, "log", lambda *_a, **_k: None)

    with pytest.raises(RuntimeError, match="Резервный источник уже использовался один раз"):
        engine._process_book(original, {1}, None)

    assert attempts == {"process": 2, "fallback": 1}
