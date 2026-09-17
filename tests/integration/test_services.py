from pathlib import Path
import threading

from audioknigi.config import normalize_settings
from audioknigi.models import Book, Track
from audioknigi.services.download_request import build_download_request
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict
from audioknigi.services.player_position_store import PlayerPositionStore


def test_download_request_uses_normalized_settings(tmp_path):
    book = Book(url="https://example.invalid", title="Book", tracks=[Track(1, "One", "https://example.invalid/1.mp3")])
    request = build_download_request(book, {"output_dir": str(tmp_path), "auto_chunk_min_kbps": 512}, [1])
    assert request.output_dir == tmp_path
    assert request.selected_indices == [1]


def test_queue_roundtrip_preserves_request(tmp_path):
    book = Book(url="https://example.invalid", title="Book", tracks=[Track(1, "One", "https://example.invalid/1.mp3")])
    request = build_download_request(book, {"output_dir": str(tmp_path)}, [1])
    task = QueueStore.new_task(request)
    restored = task_from_dict(task_to_dict(task))
    assert restored.request.book.title == "Book"
    assert restored.request.selected_indices == [1]


def test_player_position_store_prunes_completed_position(tmp_path):
    store = PlayerPositionStore(tmp_path / "positions.json")
    media = tmp_path / "chapter.mp3"
    store.update(media, 99.0, 100.0)
    assert store.saved_seconds(media, duration=100.0) == 0.0
