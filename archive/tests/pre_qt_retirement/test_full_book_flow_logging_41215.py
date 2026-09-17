from __future__ import annotations

import threading
from pathlib import Path

import pytest

from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, NarrationVariant, Track
from audioknigi import storage as storage_module
from audioknigi.storage import StorageMixin


class FlowHost(DownloaderMixin):
    def __init__(self, output_dir):
        self.runtime_output_dir = str(output_dir)
        self.runtime_use_templates = False
        self.runtime_naming_mode = "number"
        self.runtime_output_mode = "mp3"
        self.runtime_audio_preset = "copy"
        self.runtime_normalization_mode = "off"
        self.runtime_embed_tags = False
        self.runtime_save_sidecars = False
        self.runtime_delete_source = False
        self.runtime_abs_enabled = False
        self.runtime_parallel_single_source = False
        self.cancel_event = threading.Event()
        self.events = []

    def _log_book_flow(self, event, book=None, *, level="info", **details):
        self.events.append((event, level, details))

    def _check_cancel(self):
        if self.cancel_event.is_set():
            raise RuntimeError("cancelled")

    def _scan_book_files(self, book):
        return {"total": len(book.tracks), "existing": len(book.tracks), "damaged": 0}

    def _check_disk_space(self, *args, **kwargs):
        return True

    def _write_resume_manifest(self, *args, **kwargs):
        return None

    def _remove_resume_manifest(self, *args, **kwargs):
        return None

    def _verify_track_file(self, book, track):
        path = self._track_path(book, track)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"ID3" + b"x" * 2048)
        return "есть", 10.0, path

    def _add_history(self, *args, **kwargs):
        return None

    def set_stage(self, *args, **kwargs):
        return None

    def set_progress(self, *args, **kwargs):
        return None

    def set_status(self, *args, **kwargs):
        return None

    def ui(self, callback):
        return callback()


@pytest.fixture
def simple_book():
    track = Track(index=1, title="One", file="https://example.invalid/audio.mp3", duration=10)
    track.local_status = "есть"
    return Book(
        url="https://knigavuhe.org/book/test/",
        title="Flow Book",
        author="Author",
        narrator="Reader",
        tracks=[track],
    )


def test_process_book_once_logs_successful_lifecycle(monkeypatch, tmp_path, simple_book):
    monkeypatch.setattr("audioknigi.downloader.resolve_executable", lambda name: f"/{name}")
    host = FlowHost(tmp_path)

    folder = host._process_book_once(simple_book, [1])

    assert Path(folder).is_dir()
    events = [name for name, _level, _details in host.events]
    for required in (
        "download_start",
        "download_plan",
        "verify_start",
        "cover_state",
        "verify_complete",
        "id3_skipped",
        "sidecars_skipped",
        "download_complete",
    ):
        assert required in events
    complete = next(details for name, _level, details in host.events if name == "download_complete")
    assert complete["parts"] == 1
    assert "elapsed" in complete


def test_structured_log_helper_contains_book_context(monkeypatch, simple_book):
    messages = []
    monkeypatch.setattr("audioknigi.downloader.app_logger.info", lambda message, *args, **kwargs: messages.append(message % args if args else message))
    host = object.__new__(DownloaderMixin)

    host._log_book_flow("analysis_complete", simple_book, parts=1, narration_variants=2)

    assert messages
    text = messages[-1]
    assert "BOOK FLOW" in text
    assert "event=analysis_complete" in text
    assert "title=Flow Book" in text
    assert "narrator=Reader" in text
    assert "source=knigavuhe" in text
    assert "parts=1" in text


def test_history_save_is_logged(monkeypatch, tmp_path, simple_book):
    messages = []
    monkeypatch.setattr(storage_module, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(storage_module.app_logger, "info", lambda message, *args, **kwargs: messages.append(message % args if args else message))

    class Host(StorageMixin):
        def __init__(self):
            self.history = []

        def ui(self, callback):
            return None

    host = Host()
    folder = tmp_path / "Flow Book"
    folder.mkdir()
    host._add_history(simple_book, folder, 1)

    assert any("event=history_saved" in message and "title=Flow Book" in message for message in messages)


def test_narration_selection_emits_flow_event(monkeypatch):
    # Use the production app only in GUI-capable test runs. This test is kept
    # lightweight by exercising the existing selector method on a tiny host.
    from audioknigi.actions import ActionsMixin

    current = "https://knigavuhe.org/book/current/"
    other = "https://knigavuhe.org/book/other/"
    book = Book(
        url=current,
        title="Variants",
        narrator="Reader A",
        narration_variants=[
            NarrationVariant(url=current, narrator="Reader A", current=True, available=True),
            NarrationVariant(url=other, narrator="Reader B", available=True),
        ],
        tracks=[Track(index=1, title="1", file="x")],
    )

    class Var:
        def __init__(self, value=""):
            self.value = value
        def get(self): return self.value
        def set(self, value): self.value = value

    class Host(ActionsMixin):
        def __init__(self):
            self.busy = False
            self.current_book = book
            self.narration_var = Var("Reader B — доступно")
            self.url_var = Var(current)
            self._narration_variant_map = {"Reader B — доступно": other}
            self.events = []
            self.sounds = []
            self.scheduled = []
        def _log_book_flow(self, event, book=None, **details): self.events.append((event, details))
        def _play_event_sound(self, event, **kwargs): self.sounds.append(event)
        def after(self, delay, callback): self.scheduled.append((delay, callback))
        def analyze(self): return None

    host = Host()
    host.select_narration_variant()

    assert host.url_var.get() == other
    assert host.events and host.events[-1][0] == "narration_selected"
    assert host.events[-1][1]["label"] == "Reader B — доступно"
    assert host.sounds == ["narration_changed"]
    assert host.scheduled and host.scheduled[0][0] == 50
