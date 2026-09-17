from pathlib import Path

from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, Track


def _book_with_five_sources():
    return Book(
        url="https://knigavuhe.org/book/test/",
        title="Mapping",
        tracks=[
            Track(index=i, title=str(i), file=f"https://cdn.invalid/{i}.mp3", duration=100.0)
            for i in range(1, 6)
        ],
    )


def test_partial_retry_keeps_original_source_slots(tmp_path):
    host = object.__new__(DownloaderMixin)
    book = _book_with_five_sources()
    urls = [book.tracks[1].file, book.tracks[2].file, book.tracks[4].file]

    assignments = host._source_target_assignments(book, urls, tmp_path)

    assert [(slot, path.name) for slot, _url, path in assignments] == [
        (2, "_source_02.mp3"),
        (3, "_source_03.mp3"),
        (5, "_source_05.mp3"),
    ]


def test_single_shared_source_keeps_legacy_single_source_name(tmp_path):
    host = object.__new__(DownloaderMixin)
    shared = "https://cdn.invalid/full-book.mp3"
    book = Book(
        url="https://example.invalid/book",
        title="Shared",
        tracks=[
            Track(index=1, title="1", file=shared, start=0, end=60),
            Track(index=2, title="2", file=shared, start=60, end=120),
        ],
    )

    assignments = host._source_target_assignments(book, [shared], tmp_path)

    assert len(assignments) == 1
    assert assignments[0][0] == 1
    assert assignments[0][2].name == "_source.mp3"


def test_duration_verification_accepts_small_metadata_drift(tmp_path):
    class Host(DownloaderMixin):
        def _track_path(self, _book, _track):
            return tmp_path / "02.mp3"

        def _probe_duration(self, _path):
            return 2904.0  # 48:24 actual vs 48:21 playlist metadata

    path = tmp_path / "02.mp3"
    path.write_bytes(b"ID3" + b"x" * 2048)
    track = Track(index=2, title="2", file="u2", duration=2901.0)
    book = Book(url="u", title="Book", tracks=[track])

    status, actual, out = Host()._verify_track_file(book, track)

    assert status == "готово"
    assert actual == 2904.0
    assert out == path


def test_duration_verification_still_rejects_wrong_chapter(tmp_path):
    class Host(DownloaderMixin):
        def _track_path(self, _book, _track):
            return tmp_path / "02.mp3"

        def _probe_duration(self, _path):
            return 1266.0  # 21:06: obviously the wrong chapter for 48:21

    path = tmp_path / "02.mp3"
    path.write_bytes(b"ID3" + b"x" * 2048)
    track = Track(index=2, title="2", file="u2", duration=2901.0)
    book = Book(url="u", title="Book", tracks=[track])

    status, actual, _out = Host()._verify_track_file(book, track)

    assert status == "повреждён"
    assert actual == 1266.0
