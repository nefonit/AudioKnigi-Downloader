from __future__ import annotations

import inspect
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import audioknigi.actions as actions_module
import audioknigi.player as player_module
from audioknigi.actions import ActionsMixin
from audioknigi.core import save_json
from audioknigi.models import Book, Track
from audioknigi.player import PlayerMixin
from audioknigi.search import SearchMixin

ROOT = Path(__file__).resolve().parents[1]


class _DownloadHost(ActionsMixin):
    def __init__(self):
        self.cancel_event = threading.Event()
        self.busy = False
        self.current_book = Book(url="https://example.test/book", title="Book", tracks=[Track(index=1, title="1", file="x", selected=True)])
        self.started = []
        self.status = []
    def _capture_runtime_options(self): pass
    def _exact_duplicate_download(self, *_a): return False
    def _check_disk_space(self, *_a, **_k): return True
    def set_busy(self, value): self.busy = bool(value)
    def set_progress(self, *_a): pass
    def set_stage(self, *_a): pass
    def set_status(self, value): self.status.append(value)
    def _play_event_sound(self, *_a, **_k): pass
    def _spawn_worker(self, target, args=(), **_kwargs):
        self.started.append((target, args))
        return SimpleNamespace(is_alive=lambda: True)


def test_second_download_cannot_clear_cancel_or_start_second_worker():
    host = _DownloadHost()
    assert host.download_selected() is True
    assert len(host.started) == 1
    first_id = host._active_operation_id
    host.cancel_event.set()
    assert host.download_selected() is False
    assert host._active_operation_id == first_id
    assert host.cancel_event.is_set() is True
    assert len(host.started) == 1


def test_operation_token_is_exclusive_across_kinds():
    host = _DownloadHost()
    first = host._begin_operation("analysis")
    assert first == 1
    assert host._begin_operation("queue") is None
    assert host._handoff_operation(first, "download") is True
    assert host._active_operation_kind == "download"
    assert host._finish_operation(first, release_busy=False) is True
    second = host._begin_operation("queue")
    assert second == 2


class _Var:
    def __init__(self, value=""): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


class _SearchHost(SearchMixin):
    def __init__(self):
        self.search_query_var = _Var()
        self.busy = False
        self.search_results = []
        self._search_generation = 0
        self._search_lock = threading.RLock()
        self.workers = []
    def _refresh_search_results(self): pass
    def set_status(self, *_a): pass
    def log(self, *_a): pass
    def ui(self, callback): callback()
    def _search_audioknigi(self, query):
        time.sleep(0.10 if query == "AAA" else 0.01)
        return [SimpleNamespace(url=query, title=query, source="audioknigi")]
    def _search_knigavuhe(self, _query): return []
    def _search_poleknig(self, _query): return []
    def _spawn_worker(self, target, args=(), **_kwargs):
        thread = threading.Thread(target=target, args=args)
        thread.start()
        self.workers.append(thread)
        return thread


def test_stale_search_cannot_replace_newer_results():
    host = _SearchHost()
    host.search_query_var.set("AAA")
    host.search_books()
    time.sleep(0.01)
    host.search_query_var.set("BBB")
    host.search_books()
    for worker in host.workers:
        worker.join(timeout=1)
    assert [item.title for item in host.search_results] == ["BBB"]


def test_search_result_actions_refuse_to_replace_book_while_busy():
    source = inspect.getsource(SearchMixin.use_selected_search_result)
    easy = inspect.getsource(SearchMixin.use_selected_easy_search_result)
    assert 'getattr(self, "busy", False)' in source
    assert 'getattr(self, "busy", False)' in easy


def test_stale_cover_is_rejected(monkeypatch):
    class FakeImage:
        size = (10, 10)
        def thumbnail(self, _size): pass
        def copy(self): return self
    class FakeImageModule:
        @staticmethod
        def open(_stream): return FakeImage()
    class FakeImageTk:
        @staticmethod
        def PhotoImage(_img, master=None): return object()
    class Host(ActionsMixin):
        def __init__(self):
            self.current_book = SimpleNamespace(url="https://example.test/new")
            self._cover_generation = 2
            self.cover_label = object()
            self.applied = 0
        def ui(self, cb): cb()
        def _configure_image_label(self, *_a, **_k): self.applied += 1
    monkeypatch.setattr(actions_module, "Image", FakeImageModule)
    monkeypatch.setattr(actions_module, "ImageOps", None)
    monkeypatch.setattr(actions_module, "ImageTk", FakeImageTk)
    monkeypatch.setattr(actions_module, "HAS_CUSTOMTKINTER", False)
    host = Host()
    host._load_cover_preview("cover", "https://example.test/old", (b"x", "image/jpeg"), 1)
    assert host.applied == 0


def test_analysis_publishes_current_book_only_via_ui_callback():
    class Host(ActionsMixin):
        def __init__(self):
            self.auto_download_after_analysis = False
            self.resume_selected_indices = None
            self.current_book = None
            self.callbacks = []
            self.cancel_event = threading.Event()
            self._operation_lock = threading.RLock()
            self._active_operation_id = 1
            self._operation_generation = 1
            self._audioknigi_closing = False
        def _analyze_book(self, url): return Book(url=url, title="B", tracks=[Track(index=1, title="1", file="x")])
        def _scan_book_files(self, book): return {"total": 1, "existing": 0, "damaged": 0}
        def _show_book(self, _book): pass
        def ui(self, cb): self.callbacks.append(cb)
        def set_status(self, *_a): pass
        def set_stage(self, *_a): pass
        def set_progress(self, *_a): pass
        def set_busy(self, *_a): pass
        def log(self, *_a): pass
        def _play_event_sound(self, *_a, **_k): pass
    host = Host()
    host._analysis_worker("https://example.test/book", 1)
    assert host.current_book is None
    assert host.callbacks
    host.callbacks[0]()
    assert host.current_book is not None
    assert host.current_book.title == "B"


class _Button:
    def configure(self, **_kwargs): pass


class _PlayerHost(PlayerMixin):
    def __init__(self):
        self.player_position_var = _Var(0)
        self.player_file_var = _Var("")
        self.player_scale = _Button()
        self.player_stop_btn = _Button()
        self.player_playing = False
        self.player_paused = False
        self.workers = []
        self.probe_calls = 0
    def _player_init(self): return True
    def _apply_saved_position(self, *_a, **_k): return 0.0
    def _sync_player_play_pause_button(self): pass
    def set_status(self, *_a): pass
    def _probe_duration(self, _path):
        self.probe_calls += 1
        return 12.0
    def _spawn_worker(self, target, args=(), **_kwargs):
        self.workers.append((target, args))
        return object()


def test_player_does_not_probe_duration_synchronously(monkeypatch, tmp_path):
    calls = []
    music = SimpleNamespace(load=lambda p: calls.append(("load", p)), play=lambda *a: calls.append(("play", a)))
    monkeypatch.setattr(player_module, "pygame", SimpleNamespace(mixer=SimpleNamespace(music=music)))
    path = tmp_path / "book.mp3"
    path.write_bytes(b"fake")
    host = _PlayerHost()
    assert host.player_play_file(path) is True
    assert host.probe_calls == 0
    assert len(host.workers) == 1
    assert calls and calls[0][0] == "load"


def test_probe_audio_info_is_cooperative_popen_not_blocking_run():
    from audioknigi.downloader import DownloaderMixin
    source = inspect.getsource(DownloaderMixin._probe_audio_info)
    assert "subprocess.Popen" in source
    assert "self._check_cancel()" in source
    assert "subprocess.run" not in source


def test_save_json_reports_failure_and_can_raise(tmp_path):
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("x", encoding="utf-8")
    target = parent_file / "data.json"
    assert save_json(target, {"x": 1}) is False
    with pytest.raises(Exception):
        save_json(target, {"x": 1}, raise_errors=True)


def test_package_model_import_does_not_eagerly_import_gui():
    code = "import sys; import audioknigi.models; print(int('audioknigi.app' in sys.modules))"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, check=True)
    assert result.stdout.strip() == "0"


def test_logging_import_survives_unwritable_home(tmp_path):
    home_file = tmp_path / "home-as-file"
    home_file.write_text("x", encoding="utf-8")
    code = "import audioknigi.logging_utils; print('OK')"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    if os.name == "nt":
        env["APPDATA"] = str(home_file / "appdata")
    else:
        env["HOME"] = str(home_file)
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_shutdown_interrupts_network_subprocesses_and_joins(monkeypatch):
    class Closeable:
        def __init__(self): self.closed = False
        def close(self): self.closed = True
    class Host(ActionsMixin):
        def __init__(self):
            self.cancel_event = threading.Event()
            self.network = self.processes = self.joined = self.destroyed = False
            self.event_sound_manager = Closeable()
            self.tray_manager = SimpleNamespace(hide=lambda: None)
            self.accessibility = Closeable()
            self.event_bus = Closeable()
        def _save_settings(self): pass
        def _cancel_system_theme_watch(self): pass
        def _save_current_player_position(self, **_kwargs): pass
        def _cancel_active_network_io(self): self.network = True
        def _cancel_active_subprocesses(self): self.processes = True
        def _join_background_workers(self, timeout=0): self.joined = timeout > 0
        def destroy(self): self.destroyed = True
    monkeypatch.setattr(actions_module, "pygame", None)
    host = Host()
    host.on_close()
    assert host.cancel_event.is_set()
    assert host.network and host.processes and host.joined and host.destroyed


def test_periodic_accessibility_diagnostics_do_not_run_tasklist_on_tk_path():
    from audioknigi.accessibility import AccessibilityManager, ScreenReaderBridge
    diagnostic = inspect.getsource(ScreenReaderBridge.diagnostic_summary)
    poll = inspect.getsource(AccessibilityManager._poll_screen_reader)
    assert "_running_reader_processes" not in diagnostic
    assert "threading.Thread" in poll


def test_source_cleanup_ignores_missing_files_without_miscounting():
    from audioknigi.downloader import DownloaderMixin
    source = inspect.getsource(DownloaderMixin._process_book_once)
    assert "except FileNotFoundError" in source
    assert "Path(path).unlink(missing_ok=True)" not in source


def test_i18n_placeholders_are_parseable_and_consistent_across_languages():
    from string import Formatter
    from audioknigi.i18n import STRINGS

    formatter = Formatter()
    keys = set().union(*(mapping.keys() for mapping in STRINGS.values()))
    assert keys
    for key in keys:
        by_language = {}
        for language, mapping in STRINGS.items():
            if key not in mapping:
                continue
            fields = {
                field_name.split(".")[0].split("[")[0]
                for _literal, field_name, _format_spec, _conversion in formatter.parse(mapping[key])
                if field_name
            }
            by_language[language] = fields
        assert len({frozenset(fields) for fields in by_language.values()}) <= 1, (key, by_language)
