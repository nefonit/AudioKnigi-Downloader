import threading
from pathlib import Path

import pytest

import audioknigi.downloader as downloader_module
from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, SearchResult, Track


class Host(DownloaderMixin):
    def __init__(self):
        self.cancel_event = threading.Event()
        self.messages = []

    def log(self, message):
        self.messages.append(str(message))

    def ui(self, callback):
        callback()

    def _check_cancel(self):
        if self.cancel_event.is_set():
            raise RuntimeError("cancelled")


def shared_book():
    source = "https://media.example/stalker.mp3"
    return Book(
        url="https://audioknigi.com.ua/audio-123-stalker-20.html",
        title="Подрыгин Иван - Сталкер 2.0",
        author="Иван Подрыгин",
        narrator="Роман Ефимов",
        tracks=[
            Track(1, "Глава 1", source, start=0, end=2320, duration=2320),
            Track(2, "Глава 2", source, start=2320, end=7564, duration=5244),
            Track(3, "Глава 3", source, start=7564, end=12821, duration=5257),
            Track(4, "Глава 4", source, start=12821, end=14068, duration=1247),
        ],
    )


def fallback_book():
    return Book(
        url="https://knigavuhe.org/book/stalker-20/",
        title="Сталкер 2.0",
        author="Иван Подрыгин",
        narrator="Роман Ефимов",
        tracks=[
            Track(1, "001", "https://cdn.example/01.mp3", duration=2320),
            Track(2, "002", "https://cdn.example/02.mp3", duration=5244),
            Track(3, "003", "https://cdn.example/03.mp3", duration=5257),
            Track(4, "004", "https://cdn.example/04.mp3", duration=1247),
        ],
    )


def test_shared_source_timeline_accepts_complete_remote_source(monkeypatch):
    host = Host()
    monkeypatch.setattr(host, "_probe_remote_duration", lambda *_args, **_kwargs: 14070.0)
    assert host._shared_source_timeline_issue(shared_book()) is None


def test_shared_source_timeline_detects_real_stalker_short_source(monkeypatch):
    host = Host()
    monkeypatch.setattr(host, "_probe_remote_duration", lambda *_args, **_kwargs: 12254.0)
    issue = host._shared_source_timeline_issue(shared_book())
    assert issue is not None
    assert issue["expected_end"] == 14068.0
    assert issue["actual_duration"] == 12254.0
    assert issue["track_indices"] == [1, 2, 3, 4]


def test_short_audioknigi_source_switches_to_matching_knigavuhe(monkeypatch):
    host = Host()
    monkeypatch.setattr(host, "_probe_remote_duration", lambda *_args, **_kwargs: 12254.0)
    monkeypatch.setattr(
        downloader_module,
        "search_knigavuhe_books",
        lambda _query: [
            SearchResult(
                title="Сталкер 2.0",
                author="Иван Подрыгин",
                narrator="Роман Ефимов",
                url="https://knigavuhe.org/book/stalker-20/",
                source="knigavuhe.org",
            )
        ],
    )
    monkeypatch.setattr(downloader_module, "fetch_knigavuhe_book", lambda _url: fallback_book())

    recovered = host._recover_short_audioknigi_source(shared_book())

    assert recovered.url.startswith("https://knigavuhe.org/book/")
    assert recovered.title == "Сталкер 2.0"
    assert any("Переключаю книгу автоматически" in msg for msg in host.messages)


def test_short_source_does_not_switch_to_wrong_author(monkeypatch):
    host = Host()
    monkeypatch.setattr(host, "_probe_remote_duration", lambda *_args, **_kwargs: 12254.0)
    monkeypatch.setattr(
        downloader_module,
        "search_knigavuhe_books",
        lambda _query: [
            SearchResult(
                title="Сталкер 2.0",
                author="Другой Автор",
                narrator="Роман Ефимов",
                url="https://knigavuhe.org/book/wrong/",
                source="knigavuhe.org",
            )
        ],
    )
    with pytest.raises(RuntimeError, match="неполным"):
        host._recover_short_audioknigi_source(shared_book())


def test_local_source_guard_uses_real_downloaded_duration(tmp_path, monkeypatch):
    host = Host()
    book = shared_book()
    local_source = tmp_path / "_source.mp3"
    local_source.write_bytes(b"not-empty")
    monkeypatch.setattr(host, "_probe_duration", lambda _path: 12254.0)

    issue = host._shared_source_timeline_issue(
        book,
        local_map={book.tracks[0].file: local_source},
    )

    assert issue is not None
    assert issue["actual_duration"] == 12254.0
    assert issue["expected_end"] == 14068.0


def test_audioknigi_fast_analysis_runs_short_source_recovery(monkeypatch):
    host = Host()
    original = shared_book()
    replacement = fallback_book()
    monkeypatch.setattr(host, "_analyze_book_requests", lambda _url: original)
    monkeypatch.setattr(host, "_recover_short_audioknigi_source", lambda book: replacement if book is original else book)

    result = host._analyze_book("https://audioknigi.com.ua/audio-123-stalker-20.html")

    assert result is replacement


def test_local_packet_guard_rejects_truncated_vbr_even_when_header_claims_full_duration(tmp_path, monkeypatch):
    host = Host()
    book = shared_book()
    local_source = tmp_path / "_source.mp3"
    local_source.write_bytes(b"not-empty")
    # Simulate a stale Xing/VBR header that still claims the original 3:54:28.
    monkeypatch.setattr(host, "_probe_duration", lambda _path: 14068.0)
    monkeypatch.setattr(host, "_local_audio_has_packets_near", lambda *_args, **_kwargs: False)

    issue = host._shared_source_timeline_issue(
        book,
        local_map={book.tracks[0].file: local_source},
    )

    assert issue is not None
    assert issue["reason"] == "no_packets_near_expected_end"
    assert issue["expected_end"] == 14068.0


def test_local_packet_probe_requires_packets_close_to_requested_timestamp(tmp_path, monkeypatch):
    host = Host()
    local_source = tmp_path / "source.mp3"
    local_source.write_bytes(b"not-empty")
    monkeypatch.setattr(downloader_module, "resolve_executable", lambda name: "ffprobe" if name == "ffprobe" else None)

    monkeypatch.setattr(host, "_run_ffprobe_text_command", lambda *_args, **_kwargs: "14054.2\n14055.0\n")
    assert host._local_audio_has_packets_near(local_source, 14053.0, window=8.0) is True

    monkeypatch.setattr(host, "_run_ffprobe_text_command", lambda *_args, **_kwargs: "")
    assert host._local_audio_has_packets_near(local_source, 14053.0, window=8.0) is False


def test_process_book_automatically_switches_after_local_shared_source_failure(monkeypatch, tmp_path):
    host = Host()
    original = shared_book()
    replacement = fallback_book()
    calls = []

    def process_once(book, selected, _callback):
        calls.append((book.url, set(selected)))
        if len(calls) == 1:
            raise downloader_module.SharedSourceTimelineError({
                "expected_end": 14068.0,
                "actual_duration": 14068.0,
                "reason": "no_packets_near_expected_end",
            })
        return tmp_path / "ok"

    monkeypatch.setattr(host, "_process_book_once", process_once)
    monkeypatch.setattr(host, "_knigavuhe_fallback_candidate", lambda _book: replacement)
    monkeypatch.setattr(host, "_populate_missing_track_durations", lambda _book: 0)

    result = host._process_book(original, [1, 2, 3, 4])

    assert result == tmp_path / "ok"
    assert calls[0][0].startswith("https://audioknigi.com.ua/")
    assert calls[1][0].startswith("https://knigavuhe.org/")
    assert calls[1][1] == {1, 2, 3, 4}
    assert any("Переключаю загрузку автоматически" in msg for msg in host.messages)


def test_process_book_stops_safely_when_local_source_is_short_and_fallback_unavailable(monkeypatch):
    host = Host()
    original = shared_book()

    monkeypatch.setattr(
        host,
        "_process_book_once",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            downloader_module.SharedSourceTimelineError({
                "expected_end": 14068.0,
                "actual_duration": 14068.0,
                "reason": "no_packets_near_expected_end",
            })
        ),
    )
    monkeypatch.setattr(host, "_knigavuhe_fallback_candidate", lambda _book: None)

    with pytest.raises(RuntimeError, match="резервный источник"):
        host._process_book(original, [1, 2, 3, 4])
