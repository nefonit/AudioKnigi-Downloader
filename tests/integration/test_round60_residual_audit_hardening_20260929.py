from __future__ import annotations

import json
from pathlib import Path
import threading
import time

import pytest

from audioknigi.config import settings as settings_module
from audioknigi.core import Cancelled
from audioknigi.models import Book, Track
from audioknigi.providers import audioknigi_search
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.library_service import scan_unfinished
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict
from audioknigi.services import search_service


def _book() -> Book:
    return Book(
        url="https://audioknigi.com.ua/audio-1-test",
        title="Test",
        tracks=[Track(index=1, title="Part 1", file="https://example.com/1.mp3")],
    )


def test_scale_is_clamped_after_ui_migration(monkeypatch):
    def migrate(payload):
        data = dict(payload)
        data["scale"] = 999
        return data, True

    monkeypatch.setattr(settings_module, "migrate_ui_scale_settings", migrate)
    normalized, migrated = settings_module.migrate_settings({"scale": 100})

    assert migrated is True
    assert normalized["scale"] == 200


def test_queue_roundtrip_preserves_optional_and_empty_template_values(tmp_path):
    request = DownloadRequest(
        book=_book(),
        selected_indices=[1],
        output_dir=tmp_path,
        use_templates=None,
        folder_template="",
        track_template="",
    )
    task = QueueTask(id="round60", request=request, title="Test")

    restored = task_from_dict(task_to_dict(task))

    assert restored.request.use_templates is None
    assert restored.request.folder_template == ""
    assert restored.request.track_template == ""


def test_scan_unfinished_missing_template_fields_inherit_global_settings(tmp_path):
    folder = tmp_path / "book"
    folder.mkdir()
    (folder / "resume.json").write_text(
        json.dumps(
            {
                "url": "https://audioknigi.com.ua/audio-1-test",
                "title": "Test",
                "selected_indices": [1],
            }
        ),
        encoding="utf-8",
    )

    record = scan_unfinished(tmp_path)[0]

    assert record.use_templates is None
    assert record.folder_template is None
    assert record.track_template is None


def test_scan_unfinished_preserves_explicit_empty_templates(tmp_path):
    folder = tmp_path / "book"
    folder.mkdir()
    (folder / "resume.json").write_text(
        json.dumps(
            {
                "url": "https://audioknigi.com.ua/audio-1-test",
                "title": "Test",
                "selected_indices": [1],
                "use_templates": False,
                "folder_template": "",
                "track_template": "",
            }
        ),
        encoding="utf-8",
    )

    record = scan_unfinished(tmp_path)[0]

    assert record.use_templates is False
    assert record.folder_template == ""
    assert record.track_template == ""


def test_ffprobe_stop_request_is_single_owner_across_threads():
    class FakeProcess:
        def __init__(self):
            self.kill_count = 0
            self._lock = threading.Lock()

        def poll(self):
            return None

        def kill(self):
            with self._lock:
                self.kill_count += 1

    service = BookAnalysisService()
    proc = FakeProcess()
    service._register_duration_probe_process(proc)

    threads = [
        threading.Thread(target=service._request_duration_probe_stop, args=(proc,))
        for _ in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=1)

    assert proc.kill_count == 1
    service._unregister_duration_probe_process(proc)


def test_audioknigi_search_socket_wait_is_bounded():
    assert audioknigi_search.SEARCH_HTTP_TIMEOUT == (4.0, 8.0)


def test_multi_source_search_cooperative_cancel_returns_promptly(monkeypatch):
    class Provider:
        key = "fake"
        display_name = "fake.example"

        def search(self, query, *, cancel_event=None):
            while cancel_event is None or not cancel_event.is_set():
                time.sleep(0.01)
            raise Cancelled("cancelled")

        def enrich_search_results(self, results, *, cancel_event=None):
            return list(results)

    monkeypatch.setattr(search_service, "registered_providers", lambda: [Provider()])
    cancel = threading.Event()
    outcome = {}

    def run():
        try:
            search_service.search_all_sources("test", cancel_event=cancel)
        except BaseException as exc:
            outcome["error"] = exc

    thread = threading.Thread(target=run)
    thread.start()
    time.sleep(0.05)
    cancel.set()
    thread.join(timeout=1.0)

    assert not thread.is_alive()
    assert isinstance(outcome.get("error"), Cancelled)


def test_resume_ui_only_overwrites_template_settings_when_manifest_stored_them():
    source = Path("audioknigi/qt/mixins/clipboard.py").read_text(encoding="utf-8")
    assert 'for key in ("use_templates", "folder_template", "track_template"):' in source
    assert "if value is not None:" in source
