"""Focused regressions for the 2026-10-13 source-code review."""

import base64
import json
from pathlib import Path

from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.source_analysis import SourceAnalysisMixin
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, Track
from audioknigi.services.queue_service import QueueStore, _book_from_dict, _MAX_PERSISTED_COVER_BYTES
from audioknigi.templates import render_track_filename


class _SelectionEngine(BookFlowMixin):
    def _process_book_once(self, book, selected_indices, status_callback):
        return set(selected_indices)


def test_whole_book_selection_accepts_mapping_tracks():
    book = Book(url="https://example.test/book", title="Book", tracks=[
        {"index": 1, "title": "First", "file": "first.mp3"},
        {"index": 2, "title": "Second", "file": "second.mp3"},
    ])
    assert _SelectionEngine()._process_book(book) == {1, 2}


def test_source_analysis_mixin_can_create_service_without_logger():
    service = SourceAnalysisMixin()._service()
    assert service.progress is None


def test_queue_loader_keeps_invalid_items_in_recovery_file(tmp_path):
    queue_path = tmp_path / "queue.json"
    broken = {"request": {"book": "invalid"}, "id": "keep-my-data"}
    legacy = {"id": "valid", "url": "https://example.test/book", "title": "Old book"}
    queue_path.write_text(json.dumps([broken, legacy]), encoding="utf-8")
    loaded = QueueStore(queue_path).load()
    assert len(loaded) == 1
    assert loaded[0].id == "valid"
    recoveries = list(tmp_path.glob("queue.recovery-*.json"))
    assert len(recoveries) == 1
    assert json.loads(recoveries[0].read_text(encoding="utf-8"))[0] == broken
    assert len(QueueStore(queue_path).load()) == 1
    assert len(list(tmp_path.glob("queue.recovery-*.json"))) == 1


def test_queue_loader_ignores_oversized_persisted_cover():
    enormous = base64.b64encode(b"x" * (_MAX_PERSISTED_COVER_BYTES + 1)).decode("ascii")
    book = _book_from_dict({"url": "https://example.test", "title": "Book", "cover_cache_b64": enormous})
    assert book.cover_cache is None


def test_filename_does_not_duplicate_index_from_numbered_source_filename():
    track = Track(index=1, file="https://example.test/1.mp3", title="01.mp3")
    book = Book(url="https://example.test", title="Test", tracks=[track])
    assert render_track_filename("{Track_Number}. {Track_Title}", book, track) == "01.mp3"
    assert render_track_filename("{Track_Title}", book, track) == "01.mp3"


def test_shared_source_timeline_error_is_localized():
    text = "Скачанный общий аудиофайл не покрывает все таймкоды плейлиста."
    for language in ("en", "de", "uk"):
        assert localize_runtime_text(language, text) != text


def test_missing_parts_extra_count_is_fully_localized():
    text = "После обновления плейлиста исчезли выбранные части: 1, 2 (и ещё 3)"
    assert localize_runtime_text("en", text).endswith("(and 3 more)")
    assert localize_runtime_text("de", text).endswith("(und 3 weitere)")
    assert localize_runtime_text("uk", text).endswith("(і ще 3)")


