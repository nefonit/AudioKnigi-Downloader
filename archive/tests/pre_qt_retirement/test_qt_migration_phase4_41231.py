from pathlib import Path

from audioknigi.models import Book, Track
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.queue_service import QueueStore, next_runnable_index, task_from_dict, task_to_dict


def _request(tmp_path):
    book = Book(
        url="https://knigavuhe.org/book/test-book/",
        title="Test Book",
        author="Author",
        tracks=[
            Track(index=1, title="Part 1", file="https://cdn.test/1.mp3"),
            Track(index=2, title="Part 2", file="https://cdn.test/2.mp3"),
        ],
    )
    return DownloadRequest(book=book, selected_indices=[1, 2], output_dir=tmp_path)


def test_queue_roundtrip_preserves_full_download_request(tmp_path):
    store = QueueStore(tmp_path / "queue.json")
    task = store.new_task(_request(tmp_path))
    assert store.save([task])
    loaded = store.load()
    assert len(loaded) == 1
    assert loaded[0].request.book.title == "Test Book"
    assert [x.index for x in loaded[0].request.book.tracks] == [1, 2]
    assert loaded[0].request.selected_indices == [1, 2]


def test_running_task_restores_as_interrupted(tmp_path):
    store = QueueStore(tmp_path / "queue.json")
    task = store.new_task(_request(tmp_path))
    data = task_to_dict(task)
    data["status"] = "Скачивается"
    data["status_code"] = "running"
    restored = task_from_dict(data)
    assert restored.status_code == "interrupted"
    assert restored.status == "Незавершено"


def test_priority_is_chosen_before_regular_task(tmp_path):
    store = QueueStore(tmp_path / "queue.json")
    first = store.new_task(_request(tmp_path))
    second = store.new_task(_request(tmp_path), priority=True)
    assert next_runnable_index([first, second]) == 1


def test_paused_and_completed_tasks_are_not_auto_run(tmp_path):
    store = QueueStore(tmp_path / "queue.json")
    paused = store.new_task(_request(tmp_path))
    paused.paused = True
    paused.status_code = "paused"
    done = store.new_task(_request(tmp_path))
    done.status_code = "completed"
    assert next_runnable_index([paused, done]) is None


def test_qt_phase4_uses_gui_neutral_queue_service():
    root = Path(__file__).resolve().parents[1]
    text = (root / "audioknigi" / "services" / "queue_service.py").read_text(encoding="utf-8")
    assert "tkinter" not in text
    assert "ui_kit" not in text
    main = (root / "audioknigi" / "qt" / "main_window.py").read_text(encoding="utf-8")
    assert "QueueStore" in main
    assert "add_current_to_queue" in main
    assert "pause_queue_current" in main
    assert "resume_queue_selected" in main
