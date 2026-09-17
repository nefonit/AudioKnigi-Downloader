"""4.8.6 regression coverage for chapter timing columns."""
import json

from audioknigi import AudioKnigiApp
from audioknigi.core import display_track_timeline, effective_track_duration, parse_time_seconds
from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, Track


class _DownloaderProbe(DownloaderMixin):
    def __init__(self):
        self.messages = []

    def _check_cancel(self):
        return None

    def log(self, text):
        self.messages.append(str(text))

    def _remote_size(self, *_args, **_kwargs):
        return 0

    def _fetch_cover_bytes(self, *_args, **_kwargs):
        return None


def test_playlist_clock_values_are_parsed_and_used_as_duration():
    assert parse_time_seconds("42:49") == 2569
    assert parse_time_seconds("01:02:03.5") == 3723.5
    assert parse_time_seconds("45.25") == 45.25

    probe = _DownloaderProbe()
    playlist = json.dumps([
        {"title": "01", "file": "https://cdn.invalid/01.mp3", "duration": "00:01:30"},
        {"title": "02", "file": "https://cdn.invalid/02.mp3", "length": "00:00:45.5"},
    ])
    book = probe._parse_playlist_data(
        url="https://audioknigi.com.ua/audio-test",
        html_text="<title>Test Book</title>",
        page_title="Test Book",
        playlist_url="https://cdn.invalid/book.pl.txt",
        playlist_text=playlist,
    )
    assert [round(t.duration, 1) for t in book.tracks] == [90.0, 45.5]
    assert display_track_timeline(book.tracks) == [
        (0.0, 90.0, 90.0),
        (90.0, 135.5, 45.5),
    ]


def test_actual_local_duration_drives_display_without_overwriting_trim_fields():
    tracks = [
        Track(index=1, title="01", file="https://cdn.invalid/01.mp3", actual_duration=30.0),
        Track(index=2, title="02", file="https://cdn.invalid/02.mp3", actual_duration=40.0),
    ]
    rows = display_track_timeline(tracks)
    assert rows == [(0.0, 30.0, 30.0), (30.0, 70.0, 40.0)]
    assert tracks[0].start is None and tracks[0].end is None and tracks[0].duration is None
    assert effective_track_duration(tracks[1]) == 40.0


def test_missing_unique_remote_durations_are_filled_but_shared_source_is_not(monkeypatch):
    probe = _DownloaderProbe()
    book = Book(
        url="https://audioknigi.com.ua/audio-test",
        title="Test",
        tracks=[
            Track(index=1, title="01", file="https://cdn.invalid/01.mp3"),
            Track(index=2, title="02", file="https://cdn.invalid/02.mp3"),
            Track(index=3, title="03", file="https://cdn.invalid/shared.mp3"),
            Track(index=4, title="04", file="https://cdn.invalid/shared.mp3"),
        ],
    )
    durations = {"https://cdn.invalid/01.mp3": 10.0, "https://cdn.invalid/02.mp3": 20.0}
    monkeypatch.setattr(probe, "_probe_remote_duration", lambda url, _referer="": durations.get(url))
    assert probe._populate_missing_track_durations(book) == 2
    assert [t.duration for t in book.tracks] == [10.0, 20.0, None, None]


def test_tree_columns_use_measured_duration_and_refresh_live():
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        book = Book(
            url="https://audioknigi.com.ua/audio-test",
            title="Timing Book",
            tracks=[
                Track(index=1, title="01", file="https://cdn.invalid/01.mp3", local_status="есть", actual_duration=30.0),
                Track(index=2, title="02", file="https://cdn.invalid/02.mp3", local_status="есть", actual_duration=40.0),
            ],
        )
        app.current_book = book
        app._show_book(book)
        app.update_idletasks()
        first, second = app.tree.get_children()[:2]
        assert app.tree.item(first, "values")[3:6] == ("00:00:00", "00:00:30", "00:00:30")
        assert app.tree.item(second, "values")[3:6] == ("00:00:30", "00:01:10", "00:00:40")
        assert "Длительность: 00:01:10" in app.summary_var.get()

        # Simulate a newly verified third chapter appearing during a download.
        third = Track(index=3, title="03", file="https://cdn.invalid/03.mp3")
        book.tracks.append(third)
        app._show_book(book)
        third.actual_duration = 50.0
        third.local_status = "готово"
        app._refresh_book_timing_ui(book)
        row = app.tree.get_children()[2]
        assert app.tree.item(row, "values")[3:6] == ("00:01:10", "00:02:00", "00:00:50")
    finally:
        app.destroy()
