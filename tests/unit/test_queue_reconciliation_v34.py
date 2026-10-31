"""V34: reconcile outputs, queue state and history after a process crash."""

import json
import threading
from pathlib import Path

import pytest

from audioknigi.download.contracts import DownloadCallbacks, DownloadResult, DuplicatePreflight
from audioknigi.download.engine import _DownloadEngine
from audioknigi.download.service import DownloadService
from audioknigi.models import Book, Track
from audioknigi.qt import workers
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.queue_service import QueueStore, task_from_dict


def request(tmp_path, selected=None, *, count=1):
    book = Book(
        url="https://knigavuhe.org/book/v34/",
        title="Recovered Book",
        tracks=[
            Track(index=i, title=f"Chapter {i}", file=f"https://cdn.invalid/{i}.mp3")
            for i in range(1, count + 1)
        ],
    )
    return DownloadRequest(book=book, selected_indices=selected, output_dir=tmp_path)


class FakeEngine:
    created = []

    def __init__(self, req, settings, cancel_event, callbacks):
        self.req = req
        self.settings = settings
        self.cancel_event = cancel_event
        self.callbacks = callbacks
        self.preflight = None
        self.history = []
        self.manifest_removed = False
        self.calls = []
        FakeEngine.created.append(self)

    def _check_cancel(self):
        if self.cancel_event.is_set():
            from audioknigi.core import Cancelled
            raise Cancelled("cancelled")

    def duplicate_preflight(self, *, full_mp3=False, probe_durations=True):
        self.calls.append(("preflight", full_mp3, probe_durations))
        return DuplicatePreflight(self.preflight is not False, Path(self.req.output_dir), "metadata.json")

    def _add_history(self, book, folder, parts):
        self.calls.append(("history", parts))
        if self.preflight != "failed-history":
            self.history = [(book.url, str(folder), parts)]

    def _history_metadata_matches_book(self, book, folder, *, expected_parts):
        self.calls.append(("verify-history", expected_parts))
        return (book.url, str(folder), expected_parts) in self.history

    def _remove_resume_manifest(self, book):
        self.calls.append(("remove-manifest", book.url))
        self.manifest_removed = True

    def _full_mp3_target(self, book, folder):
        return folder / "book.mp3"


def _install_fake_engine(monkeypatch):
    import audioknigi.download_engine as engine_alias
    FakeEngine.created = []
    monkeypatch.setattr(engine_alias, "_DownloadEngine", FakeEngine)


@pytest.mark.parametrize("full_mp3,parts", [(False, 2), (True, 1)])
def test_completed_outputs_reconcile_to_history_then_cleanup_manifest(monkeypatch, tmp_path, full_mp3, parts):
    _install_fake_engine(monkeypatch)
    req = request(tmp_path, count=2)
    result = DownloadService().recover_completed_download(req, full_mp3=full_mp3)
    assert isinstance(result, DownloadResult)
    assert result.folder == tmp_path
    assert result.target_file == tmp_path / "book.mp3" if full_mp3 else result.target_file is None
    engine = FakeEngine.created[-1]
    assert engine.calls == [
        ("preflight", full_mp3, True),
        ("history", parts),
        ("verify-history", parts),
        ("remove-manifest", req.book.url),
    ]


def test_missing_or_unproven_output_uses_normal_resume_without_history_write(monkeypatch, tmp_path):
    _install_fake_engine(monkeypatch)
    req = request(tmp_path)
    # Explicitly mark a negative preflight; no history or manifest changes.
    original = FakeEngine.duplicate_preflight

    def negative(self, **kwargs):
        self.preflight = False
        return original(self, **kwargs)

    monkeypatch.setattr(FakeEngine, "duplicate_preflight", negative)
    assert DownloadService().recover_completed_download(req) is None
    engine = FakeEngine.created[-1]
    assert engine.calls == [("preflight", False, True)]


def test_failed_history_repair_does_not_claim_queue_completion(monkeypatch, tmp_path):
    _install_fake_engine(monkeypatch)
    original = FakeEngine.duplicate_preflight

    def with_failed_save(self, **kwargs):
        self.preflight = "failed-history"
        return original(self, **kwargs)

    monkeypatch.setattr(FakeEngine, "duplicate_preflight", with_failed_save)
    assert DownloadService().recover_completed_download(request(tmp_path)) is None
    engine = FakeEngine.created[-1]
    assert not engine.manifest_removed
    assert engine.calls[-1] == ("verify-history", 1)


def test_cancellation_during_reconciliation_propagates_without_touching_history(monkeypatch, tmp_path):
    _install_fake_engine(monkeypatch)
    event = threading.Event()
    event.set()
    with pytest.raises(Exception, match="cancelled"):
        DownloadService(cancel_event=event).recover_completed_download(request(tmp_path))
    assert FakeEngine.created[-1].calls == []


def test_worker_uses_recovered_result_without_redownloading(monkeypatch, tmp_path):
    req = request(tmp_path)
    recovered = DownloadResult(folder=tmp_path, selected_indices=[1], skipped_indices=[], book=req.book)
    seen = []

    class Service:
        def __init__(self, **kwargs):
            pass

        def recover_completed_download(self, req, *, full_mp3):
            seen.append(("reconcile", full_mp3))
            return recovered

        def download(self, req):
            raise AssertionError("Worker must not redownload recovered book")

        def download_full_mp3(self, req):
            raise AssertionError("Worker must not redownload recovered MP3")

    monkeypatch.setattr(workers, "DownloadService", Service)
    worker = workers.DownloadWorker(req, {}, threading.Event(), mode="full_mp3", recover_existing=True)
    worker.finished.connect(lambda result: seen.append(result))
    worker.run()
    assert seen[0] == ("reconcile", True)
    assert seen[1] == ("ok", recovered)


def test_worker_falls_back_to_original_download_when_recovery_finds_incomplete_files(monkeypatch, tmp_path):
    req = request(tmp_path)
    expected = DownloadResult(folder=tmp_path, selected_indices=[1], skipped_indices=[], book=req.book)
    seen = []

    class Service:
        def __init__(self, **kwargs):
            pass

        def recover_completed_download(self, req, *, full_mp3):
            seen.append("reconcile")
            return None

        def download(self, req):
            seen.append("download")
            return expected

    monkeypatch.setattr(workers, "DownloadService", Service)
    worker = workers.DownloadWorker(req, {}, threading.Event(), recover_existing=True)
    worker.finished.connect(lambda result: seen.append(result))
    worker.run()
    assert seen == ["reconcile", "download", ("ok", expected)]


def test_regular_worker_skips_crash_reconciliation(monkeypatch, tmp_path):
    req = request(tmp_path)
    seen = []

    class Service:
        def __init__(self, **kwargs):
            pass

        def recover_completed_download(self, *args, **kwargs):
            raise AssertionError("No recovery for ordinary download")

        def download(self, req):
            seen.append("normal")
            return DownloadResult(folder=tmp_path, selected_indices=[1], skipped_indices=[], book=req.book)

    monkeypatch.setattr(workers, "DownloadService", Service)
    worker = workers.DownloadWorker(req, {}, threading.Event())
    worker.run()
    assert seen == ["normal"]


def test_full_mp3_real_preflight_rebuilds_history_after_crash_without_touching_output(monkeypatch, tmp_path):
    from audioknigi.download import engine as engine_module

    req = request(tmp_path)
    history = tmp_path / "history.json"
    monkeypatch.setattr(engine_module, "HISTORY_FILE", history)
    worker = _DownloadEngine(req, {}, threading.Event(), DownloadCallbacks())
    folder = Path(worker._book_folder(req.book, create=True))
    target = worker._full_mp3_target(req.book, folder)
    target.parent.mkdir(parents=True, exist_ok=True)
    original = b"completed output bytes"
    target.write_bytes(original)
    sidecar = {
        "source_url": req.book.url, "title": req.book.title,
        "author": req.book.author, "narrator": req.book.narrator,
        "tracks": [{"index": 1, "title": "Chapter 1", "start": None, "end": None}],
    }
    (folder / "metadata.json").write_text(json.dumps(sidecar), encoding="utf-8")
    (folder / "resume.json").write_text(json.dumps({"url": req.book.url}), encoding="utf-8")
    assert worker.duplicate_preflight(full_mp3=True).exact_duplicate

    service = DownloadService()
    recovered = service.recover_completed_download(req, full_mp3=True)
    assert recovered is not None
    assert recovered.target_file == target
    assert target.read_bytes() == original
    assert not (folder / "resume.json").exists()
    assert len(json.loads(history.read_text(encoding="utf-8"))) == 1
    # Repeated crash recovery must not duplicate the history entry.
    assert service.recover_completed_download(req, full_mp3=True) is not None
    assert len(json.loads(history.read_text(encoding="utf-8"))) == 1


def test_real_reconciliation_rejects_incomplete_full_mp3(monkeypatch, tmp_path):
    from audioknigi.download import engine as engine_module

    req = request(tmp_path)
    monkeypatch.setattr(engine_module, "HISTORY_FILE", tmp_path / "history.json")
    assert DownloadService().recover_completed_download(req, full_mp3=True) is None
    assert not (tmp_path / "history.json").exists()


def test_queue_crash_status_round_trip_and_ui_worker_flag_contract(tmp_path):
    req = request(tmp_path)
    store = QueueStore(tmp_path / "qt_queue.json")
    task = store.new_task(req)
    task.status_code = "running"
    task.status = "Скачивается"
    assert store.save([task])
    loaded = store.load()[0]
    assert loaded.status_code == "interrupted"
    assert not loaded.paused
    assert loaded.request.book.url == req.book.url

    source = (Path(__file__).resolve().parents[2] / "audioknigi/qt/mixins/queue.py").read_text(encoding="utf-8")
    assert 'recover_existing = task.status_code == "interrupted"' in source
    assert "mode=task.download_mode, recover_existing=recover_existing" in source
