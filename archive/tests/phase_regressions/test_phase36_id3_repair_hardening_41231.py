from __future__ import annotations

import inspect
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_brand_module_is_real_python_module_and_importable():
    brand_path = ROOT / "audioknigi" / "brand.py"
    assert brand_path.is_file()
    from audioknigi.brand import DISPLAY_NAME

    assert DISPLAY_NAME == "AudioKnigi Downloader"


def test_search_service_accepts_sources_filter_used_by_qt_worker():
    from audioknigi.services.search_service import search_all_sources

    signature = inspect.signature(search_all_sources)
    assert "sources" in signature.parameters
    workers = text("audioknigi/qt/workers.py")
    assert "sources=self.sources" in workers


def test_id3_preserves_meaningful_track_title(tmp_path):
    mutagen = pytest.importorskip("mutagen.id3")
    from audioknigi.downloader import DownloaderMixin
    from audioknigi.models import Book, Track

    class Dummy:
        runtime_embed_tags = True

        def log(self, *_args, **_kwargs):
            pass

    target = tmp_path / "chapter.mp3"
    target.write_bytes(b"")
    book = Book(url="https://example.invalid/book", title="Замок", author="Автор")
    track = Track(index=1, title="Глава 1. Прибытие", file="https://example.invalid/1.mp3")

    DownloaderMixin._write_id3(Dummy(), target, book, 1, 2, None, track)

    tags = mutagen.ID3(target)
    assert tags["TIT2"].text == ["Замок — Глава 1. Прибытие"]
    assert tags["TALB"].text == ["Замок"]
    assert tags["TRCK"].text == ["1/2"]


def test_id3_avoids_duplicate_book_title_and_keeps_legacy_fallback(tmp_path):
    mutagen = pytest.importorskip("mutagen.id3")
    from audioknigi.downloader import DownloaderMixin
    from audioknigi.models import Book, Track

    class Dummy:
        runtime_embed_tags = True

        def log(self, *_args, **_kwargs):
            pass

    book = Book(url="https://example.invalid/book", title="Замок")

    already_prefixed = tmp_path / "prefixed.mp3"
    already_prefixed.write_bytes(b"")
    track = Track(index=2, title="Замок — Глава 2", file="https://example.invalid/2.mp3")
    DownloaderMixin._write_id3(Dummy(), already_prefixed, book, 2, 2, None, track)
    assert mutagen.ID3(already_prefixed)["TIT2"].text == ["Замок — Глава 2"]

    no_title = tmp_path / "fallback.mp3"
    no_title.write_bytes(b"")
    DownloaderMixin._write_id3(Dummy(), no_title, book, 2, 2, None, None)
    assert mutagen.ID3(no_title)["TIT2"].text == ["Замок — часть 02"]


def test_repair_source_is_fresh_and_cleanup_tracks_original_and_repair_paths():
    source = text("audioknigi/downloader.py")
    process = source[source.index("def _process_book_once"):source.index("def _is_transient_error", source.index("def _process_book_once"))]

    # All original _source targets are captured before local_map can be replaced.
    assert "cleanup_sources = set(local_map.values())" in process
    # A damaged verified track forces a fresh repair download rather than trusting
    # the cached source that may itself be corrupt.
    damaged = process[process.index('if status == "повреждён":'):]
    assert "repaired_sources.get(source_key_value)" in damaged
    assert "repaired_sources[source_key_value] = src" in damaged
    assert 'src = folder / f"_repair_{source_name}.mp3"' in damaged
    assert "src.unlink(missing_ok=True)" in damaged
    assert "cleanup_sources.add(src)" in damaged
    assert "local_map[source_key_value] = src" in damaged
    # Final cleanup uses the stable set, so replacing local_map cannot orphan the
    # original broken _source*.mp3 on disk.
    assert "for path in cleanup_sources:" in process
    assert "planned=len(cleanup_sources)" in process


def test_supported_qt_minimum_makes_qaccessible_announcement_import_valid():
    pyproject = text("pyproject.toml")
    assert '"PySide6>=6.8,<7"' in pyproject
