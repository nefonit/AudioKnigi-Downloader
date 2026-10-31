"""V33 crash recovery of queue and history; all state files stay under tmp_path."""

import json
import threading
from pathlib import Path

import pytest

from audioknigi.download.contracts import DownloadCallbacks
from audioknigi.download.engine import _DownloadEngine
from audioknigi.models import Book, Track
from audioknigi.services import library_service, state_recovery
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.queue_service import QueueStore, next_runnable_index


def _request(tmp_path):
    book = Book(
        url="https://knigavuhe.org/book/example/",
        title="Example audiobook",
        tracks=[Track(index=1, title="First", file="https://cdn.invalid/1.mp3")],
    )
    return DownloadRequest(book=book, selected_indices=[1], output_dir=tmp_path)


def test_crashed_running_queue_task_restores_as_interrupted_without_losing_other_tasks(tmp_path):
    store = QueueStore(tmp_path / "qt_queue.json")
    running = store.new_task(_request(tmp_path), download_mode="full_mp3", priority=True)
    running.status_code = "running"
    running.status = "Скачивается"
    running.attempts = 2
    done = store.new_task(_request(tmp_path))
    done.status_code = "completed"
    done.status = "Готово"
    paused = store.new_task(_request(tmp_path))
    paused.status_code = "pending"
    paused.paused = True

    assert store.save([running, done, paused])
    mirror = state_recovery.last_good_path(store.path)
    assert mirror.is_file()
    loaded = store.load()
    assert [t.id for t in loaded] == [running.id, done.id, paused.id]
    assert [t.status_code for t in loaded] == ["interrupted", "completed", "pending"]
    assert [t.paused for t in loaded] == [False, False, True]
    assert loaded[0].attempts == 2
    assert loaded[0].download_mode == "full_mp3"
    assert loaded[0].request.selected_indices == [1]
    assert next_runnable_index(loaded) == 0


def test_corrupt_queue_reloads_last_valid_snapshot_and_preserves_exact_bad_bytes(tmp_path):
    store = QueueStore(tmp_path / "qt_queue.json")
    task = store.new_task(_request(tmp_path))
    assert store.save([task])
    bad = b'{"unfinished": [\xff; broken'
    store.path.write_bytes(bad)
    loaded = store.load()
    assert len(loaded) == 1 and loaded[0].id == task.id
    assert store.path.read_bytes() == bad   # Reading must not replace the original.
    preserved = sorted(tmp_path.glob("qt_queue.corrupt-*.json"))
    assert len(preserved) == 1
    assert preserved[0].read_bytes() == bad
    assert store.save(loaded)
    assert json.loads(store.path.read_text(encoding="utf-8"))[0]["id"] == task.id


def test_empty_primary_queue_never_resurrects_old_mirrored_task(tmp_path):
    store = QueueStore(tmp_path / "qt_queue.json")
    assert store.save([store.new_task(_request(tmp_path))])
    store.path.write_text("[]", encoding="utf-8")
    assert store.load() == []
    store.path.unlink()
    assert store.load() == []


def test_bad_primary_without_usable_mirror_keeps_damage_for_diagnostics(tmp_path):
    store = QueueStore(tmp_path / "qt_queue.json")
    store.path.write_text('{"wrong": "top-level shape"}', encoding="utf-8")
    state_recovery.last_good_path(store.path).write_text("{ invalid", encoding="utf-8")
    assert store.load() == []
    assert list(tmp_path.glob("qt_queue.corrupt-*.json"))
    assert store.path.read_text(encoding="utf-8").startswith('{"wrong"')


def test_history_records_restore_but_intentionally_cleared_history_stays_empty(monkeypatch, tmp_path):
    history = tmp_path / "history.json"
    monkeypatch.setattr(library_service, "HISTORY_FILE", history)
    entries = [{"title": "Saved", "url": "https://knigavuhe.org/book/example/"}]
    assert library_service.save_history_records(entries)
    bad = b'["broken" :'
    history.write_bytes(bad)
    assert library_service.load_history_records() == entries
    assert history.read_bytes() == bad
    assert list(tmp_path.glob("history.corrupt-*.json"))
    assert library_service.clear_history()
    assert library_service.load_history_records() == []
    assert json.loads(state_recovery.last_good_path(history).read_text(encoding="utf-8")) == []


def test_completed_download_updates_history_and_last_good_snapshot(monkeypatch, tmp_path):
    from audioknigi.download import engine

    history_path = tmp_path / "history.json"
    monkeypatch.setattr(engine, "HISTORY_FILE", history_path)
    request = _request(tmp_path)
    worker = _DownloadEngine(request, {}, threading.Event(), DownloadCallbacks())
    worker._add_history(request.book, tmp_path, 1)
    rows = state_recovery.load_recoverable_list(history_path)
    assert len(rows) == 1
    assert rows[0]["title"] == "Example audiobook"
    assert state_recovery.load_recoverable_list(
        state_recovery.last_good_path(history_path)
    ) == rows


def test_history_read_in_duplicate_lookup_survives_invalid_primary(monkeypatch, tmp_path):
    from audioknigi.download import engine

    history_path = tmp_path / "history.json"
    monkeypatch.setattr(engine, "HISTORY_FILE", history_path)
    request = _request(tmp_path)
    worker = _DownloadEngine(request, {}, threading.Event(), DownloadCallbacks())
    worker._add_history(request.book, tmp_path, 1)
    history_path.write_text("garbled json", encoding="utf-8")
    # The duplicate-history lookup uses the recovered list, not an empty one.
    assert isinstance(worker._history_metadata_matches_book(request.book, tmp_path), bool)
    assert list(tmp_path.glob("history.corrupt-*.json"))


def test_save_failure_leaves_original_state_and_lastgood_untouched(monkeypatch, tmp_path):
    path = tmp_path / "qt_queue.json"
    assert state_recovery.save_recoverable_list(path, [{"id": "old"}])
    original = path.read_bytes()
    mirrored = state_recovery.last_good_path(path).read_bytes()
    monkeypatch.setattr(state_recovery, "save_json", lambda target, _data: False)
    assert not state_recovery.save_recoverable_list(path, [{"id": "new"}])
    assert path.read_bytes() == original
    assert state_recovery.last_good_path(path).read_bytes() == mirrored


def test_snapshot_failure_does_not_report_primary_save_as_failure(monkeypatch, tmp_path):
    path = tmp_path / "history.json"
    original_save = state_recovery.save_json

    def fail_mirror(destination, payload):
        if Path(destination) == state_recovery.last_good_path(path):
            return False
        return original_save(destination, payload)

    monkeypatch.setattr(state_recovery, "save_json", fail_mirror)
    assert state_recovery.save_recoverable_list(path, [{"title": "new"}])
    assert state_recovery.load_recoverable_list(path) == [{"title": "new"}]
    assert not state_recovery.last_good_path(path).exists()


def test_invalid_primary_is_recovered_only_from_valid_list_snapshot(tmp_path):
    path = tmp_path / "history.json"
    assert state_recovery.save_recoverable_list(path, [{"title": "book"}])
    path.write_text("{}", encoding="utf-8")
    assert state_recovery.load_recoverable_list(path) == [{"title": "book"}]
    path.write_text("[]", encoding="utf-8")
    assert state_recovery.load_recoverable_list(path) == []


def test_restoring_backup_refreshes_history_snapshot_after_full_transaction(monkeypatch, tmp_path):
    import zipfile

    history = tmp_path / "history.json"
    queue = tmp_path / "qt_queue.json"
    archive = tmp_path / "backup.zip"
    monkeypatch.setattr(library_service, "APP_DIR", tmp_path)
    monkeypatch.setattr(library_service, "BACKUP_MEMBERS", {
        "history.json": history, "qt_queue.json": queue,
    })
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("history.json", json.dumps([{"title": "restored"}]))
        z.writestr("qt_queue.json", "[]")
    assert library_service.restore_backup(archive) == ["history.json", "qt_queue.json"]
    assert state_recovery.load_recoverable_list(
        state_recovery.last_good_path(history)
    ) == [{"title": "restored"}]
    assert state_recovery.load_recoverable_list(
        state_recovery.last_good_path(queue)
    ) == []
