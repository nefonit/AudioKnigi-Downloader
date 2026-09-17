from __future__ import annotations

import inspect
import threading
from types import SimpleNamespace

from audioknigi.actions import ActionsMixin
from audioknigi.models import Book, Track
from audioknigi.storage import StorageMixin


class _Var:
    def __init__(self, value=None):
        self.value = value
    def get(self):
        return self.value
    def set(self, value):
        self.value = value


class _DownloadFailureProbe(ActionsMixin):
    def __init__(self):
        self.busy = True
        self.runtime_ui_mode = "easy"
        self.current_book = None
        self.statuses = []
        self.stages = []
        self.logs = []
        self.progress = []
        self.refreshes = 0

    def _process_book(self, _book, _selected):
        raise OSError("disk failure")

    def set_status(self, value):
        self.statuses.append(value)

    def set_stage(self, number, text):
        self.stages.append((number, text))

    def set_progress(self, value):
        self.progress.append(value)

    def set_busy(self, value):
        self.busy = bool(value)

    def log(self, value):
        self.logs.append(str(value))

    def ui(self, callback):
        # Do not execute modal messageboxes in this unit test; the final refresh
        # is safe to execute and is what we care about here.
        name = getattr(callback, "__name__", "")
        if name == "_refresh_unfinished_indicator":
            callback()

    def _refresh_unfinished_indicator(self):
        self.refreshes += 1


class _ThreadTree:
    def __init__(self):
        self.calls = []
        self.values = {"row-1": ["x", "1", "⚪ Не скачано", "—", "—", "—"]}

    def _assert_main(self):
        assert threading.current_thread() is threading.main_thread()

    def exists(self, row):
        self._assert_main()
        self.calls.append(("exists", row))
        return row in self.values

    def item(self, row, option=None, **kwargs):
        self._assert_main()
        self.calls.append(("item", row, option, kwargs))
        if "values" in kwargs:
            self.values[row] = list(kwargs["values"])
            return None
        if option == "values":
            return tuple(self.values[row])
        return {"values": tuple(self.values[row])}


class _TimingProbe(ActionsMixin):
    def __init__(self, book):
        self.current_book = book
        self.tree = _ThreadTree()
        self._track_tree_map = {"row-1": book.tracks[0]}
        self.posted = []

    def ui(self, callback):
        self.posted.append(callback)


class _StorageProbe(StorageMixin):
    def __init__(self, manifests):
        self._manifests = manifests
        self._unfinished_records = []
        self.resume_selected_indices = {99}
        self.queue_items = []
        self.selected_tabs = []
        self.refreshed = 0
        self.logs = []

    def _scan_unfinished_records(self):
        return list(self._manifests), []

    def _capture_runtime_options(self):
        raise AttributeError("partial UI")

    def _select_advanced_tab(self, key):
        self.selected_tabs.append(key)

    def _refresh_queue(self):
        self.refreshed += 1

    def log(self, text):
        self.logs.append(str(text))


def test_main_download_worker_always_releases_busy_on_unexpected_error():
    probe = _DownloadFailureProbe()
    probe._main_download_worker(SimpleNamespace(url="u"), [1])
    assert probe.busy is False
    assert probe.refreshes == 1
    assert any("disk failure" in line for line in probe.logs)
    assert probe.stages[-1] == (0, "ошибка")


def test_timing_tree_update_from_worker_is_marshaled_to_main_thread():
    book = Book(
        url="https://audioknigi.com.ua/audio-test",
        title="Timing",
        tracks=[Track(index=1, title="01", file="01.mp3", local_status="готово", actual_duration=12.0)],
    )
    probe = _TimingProbe(book)

    thread = threading.Thread(target=probe._refresh_book_timing_ui, args=(book,))
    thread.start()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert probe.tree.calls == []
    assert len(probe.posted) == 1

    probe.posted.pop(0)()
    assert probe.tree.values["row-1"][3:6] == ["00:00:00", "00:00:12", "00:00:12"]


def test_clipboard_focus_is_safe_even_if_timer_attribute_is_missing():
    class Probe(ActionsMixin):
        def __init__(self):
            self.clipboard_auto_var = _Var(True)
            self.busy = False
            self.scheduled = []
        def after(self, delay, callback):
            self.scheduled.append((delay, callback))
            return "after-id"
        def _check_clipboard_link(self):
            return None

    probe = Probe()
    probe._on_window_focus_for_clipboard()
    assert probe._clipboard_offer_after == "after-id"
    assert len(probe.scheduled) == 1


def test_multi_resume_clears_stale_manual_selection_and_survives_partial_ui(monkeypatch):
    manifests = [
        {"url": "https://audioknigi.com.ua/audio-one", "title": "One", "selected_indices": ["1", 2]},
        {"url": "https://audioknigi.com.ua/audio-two", "title": "Two", "selected_indices": ["3"]},
    ]
    probe = _StorageProbe(manifests)
    monkeypatch.setattr("audioknigi.storage.messagebox.askyesno", lambda *a, **k: False)
    probe.continue_unfinished()
    assert probe.resume_selected_indices is None
    assert len(probe.queue_items) == 2
    assert probe.queue_items[0].selected_indices == [1, 2]
    assert probe.selected_tabs == ["queue"]
    assert probe.refreshed == 1


def test_single_resume_without_url_variable_fails_cleanly_and_clears_selection():
    manifest = {
        "url": "https://audioknigi.com.ua/audio-one",
        "title": "One",
        "selected_indices": ["1", 2],
        "normalization_mode": "off",
    }
    probe = _StorageProbe([manifest])
    probe.continue_unfinished()
    assert probe.resume_selected_indices is None
    assert any("поле URL" in line for line in probe.logs)


def test_ui_kit_source_is_complete_not_truncated():
    from audioknigi import ui_kit
    source = inspect.getsource(ui_kit.AccessibleLabel._apply_theme_colors)
    compile(source.replace("    def _apply_theme_colors", "def _apply_theme_colors", 1), "<accessible-label>", "exec")
