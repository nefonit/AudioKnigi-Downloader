from __future__ import annotations

import inspect
import threading
from types import SimpleNamespace

from audioknigi.actions import ActionsMixin
from audioknigi.app import AudioKnigiApp
from audioknigi.library_visuals import LibraryVisualMixin
from audioknigi.models import QueueItem
from audioknigi.onboarding import FirstRunWizard
from audioknigi.queue_manager import QueueMixin


class _Tree:
    def __init__(self, selected=("0",)):
        self.selected = selected
        self.last_selection = None
    def selection(self):
        return self.selected
    def selection_set(self, value):
        self.last_selection = str(value)
        self.selected = (str(value),)
    def focus(self, *_args):
        return None


class _QueueHost(QueueMixin):
    def __init__(self):
        self._queue_lock = threading.RLock()
        self._queue_run_token = 0
        self.queue_running = False
        self.queue_items = [QueueItem(url="a", title="A"), QueueItem(url="b", title="B")]
        self.queue_tree = _Tree()
        self.refreshed = 0
    def _refresh_queue(self):
        self.refreshed += 1
    def ui(self, callback):
        callback()


def test_queue_start_and_retry_refuse_duplicate_worker(monkeypatch):
    host = _QueueHost()
    host.queue_running = True
    assert host.start_queue() is False
    monkeypatch.setattr("audioknigi.queue_manager.messagebox.showinfo", lambda *a, **k: None)
    host.queue_items[0].status = "Ошибка"
    assert host.queue_retry_failed() is False
    assert host.queue_items[0].status == "Ошибка"


def test_queue_status_tracks_item_identity_and_priority_toggle_restores_position():
    host = _QueueHost()
    first, second = host.queue_items
    host.queue_items[:] = [second, first]
    host._queue_status(first, "Готово")
    assert first.status == "Готово"
    assert second.status == "Ожидает"

    # Select the second row (A), promote it, then remove priority: its previous
    # position is restored rather than leaving it permanently at index zero.
    host.queue_tree.selected = ("1",)
    host.queue_toggle_priority()
    assert host.queue_items[0] is first and first.priority is True
    host.queue_tree.selected = ("0",)
    host.queue_toggle_priority()
    assert host.queue_items[1] is first and first.priority is False
    assert first.priority_restore_index is None


def test_segment_threshold_is_runtime_configurable():
    app = AudioKnigiApp()
    try:
        app.segment_threshold_mb_var.set("32")
        app._capture_runtime_options()
        assert app.runtime_segment_threshold_mb == 32
        assert "segment_threshold_mb_var" in inspect.getsource(ActionsMixin._save_settings)
    finally:
        app.destroy()


def test_speed_metric_name_documents_bytes_per_second():
    params = inspect.signature(ActionsMixin.record_transfer_metrics).parameters
    assert "speed_bytes_per_sec" in params
    assert "speed_bps" not in params


def test_player_tree_play_updates_now_playing_label_source():
    source = inspect.getsource(__import__("audioknigi.player", fromlist=["PlayerMixin"]).PlayerMixin.player_play)
    assert 'self.player_file_var.set(f"Сейчас играет:' in source


class _FakeWin:
    def grab_release(self):
        pass
    def destroy(self):
        pass


class _WizardApp:
    def __init__(self):
        self.settings = {}
        self.saved = None
        self.after_called = False
    def _save_settings(self, extra=None):
        self.saved = dict(extra or {})
    def _after_onboarding(self):
        self.after_called = True


def test_wizard_close_means_skip_and_does_not_reappear_next_launch():
    wizard = FirstRunWizard.__new__(FirstRunWizard)
    wizard.app = _WizardApp()
    wizard.win = _FakeWin()
    wizard.cancel()
    assert wizard.app.settings["first_run_complete"] is True
    assert wizard.app.saved == {"first_run_complete": True}
    assert wizard.app.after_called is True


def test_cover_payload_key_supports_tobytes_payloads():
    class Payload:
        mode = "RGB"
        size = (2, 2)
        def tobytes(self):
            return b"\x00\x01\x02\x03"
    key = LibraryVisualMixin._payload_key("q", "book", Payload())
    assert key.startswith("q:book:")
    assert key != "q:book:"


def test_tab_cleanup_avoids_destroy_event_recursion():
    from pathlib import Path
    base = Path(__file__).resolve().parents[1] / "audioknigi" / "ui"
    for name in ("main_tab.py", "search_tab.py", "queue_tab.py", "history_tab.py", "settings_tab.py", "easy_home.py"):
        source = (base / name).read_text(encoding="utf-8")
        assert "install_destroy_cleanup(self.frame, self._on_frame_destroy)" in source
        assert 'bind("<Destroy>"' not in source
