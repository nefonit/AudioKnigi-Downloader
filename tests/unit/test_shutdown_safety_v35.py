"""V35: shutdown protection and last-chance queue/settings/player state persistence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from audioknigi.qt.mixins import lifecycle
from audioknigi.qt.mixins.lifecycle import LifecycleUiMixin


class Event:
    def __init__(self):
        self.result = None

    def ignore(self):
        self.result = "ignore"

    def accept(self):
        self.result = "accept"


class Controller:
    def __init__(self, events, name, *, fails=False):
        self.events = events
        self.name = name
        self.fails = fails

    def save_position(self, *, force):
        self.events.append((self.name, "save_position", force))
        if self.fails:
            raise OSError("position failure")

    def shutdown(self):
        self.events.append((self.name, "shutdown"))
        if self.fails:
            raise OSError("shutdown failure")


class WorkerThread:
    def __init__(self):
        self.running = True
        self.interruptions = 0
        self.waits = []

    def isRunning(self):
        return self.running

    def requestInterruption(self):
        self.interruptions += 1

    def wait(self, timeout):
        self.waits.append(timeout)
        return not self.running


class QueueStore:
    def __init__(self, events, *, ok=True, raises=False):
        self.events = events
        self.ok = ok
        self.raises = raises

    def save(self, tasks):
        self.events.append(("queue", "save", list(tasks)))
        if self.raises:
            raise OSError("queue failure")
        return self.ok


class Window(LifecycleUiMixin):
    def __init__(self):
        self.actions = []
        self.queue_tasks = ["pending-one", "completed-two"]
        self.queue_store = QueueStore(self.actions)
        self.settings = {"language": "ru"}
        self.player_controller = Controller(self.actions, "player")
        self.event_sound_manager = Controller(self.actions, "sound")
        self.tray_controller = Controller(self.actions, "tray")
        self._media_key_filter = None
        self._download_thread = None
        self._analysis_thread = None
        self._search_thread = None
        self._abs_thread = None
        self._analysis_cancel = None
        self._search_cancel = None
        self._active_queue_task_id = None
        self._queue_running = False
        self._queue_stop_requested = False
        self._exit_requested = False
        self._exit_deadline = None
        self._exit_poll_scheduled = False
        self.visible = True
        self.confirmation = QMessageBox.StandardButton.No

    def _save_window_geometry(self):
        self.actions.append(("window", "geometry"))
        self.settings["geometry"] = "unchanged"

    def _settings_from_ui(self):
        self.actions.append(("settings", "collect"))
        return {"language": "ru", "ui_mode": "easy"}

    def _ask_yes_no(self, title, message, *, default_yes):
        self.actions.append(("confirm", title, default_yes))
        return self.confirmation

    def _request_download_cancel(self):
        self.actions.append(("download", "cancel"))
        return False

    def _schedule_exit_poll(self):
        self.actions.append(("exit", "schedule"))

    def hide(self):
        self.visible = False
        self.actions.append(("window", "hide"))

    def isVisible(self):
        return self.visible

    def restore_from_tray(self):
        self.visible = True
        self.actions.append(("window", "restore"))

    def show(self):
        self.visible = True
        self.actions.append(("window", "show"))

    def set_status(self, message, *, assertive=False):
        self.actions.append(("status", message, assertive))


def patch_settings_save(monkeypatch, tmp_path, actions, *, fail=False, raises=False):
    file = tmp_path / "settings.json"
    monkeypatch.setattr(lifecycle, "SETTINGS_FILE", file)

    def save(path, value):
        actions.append(("settings", "save", dict(value)))
        if raises:
            raise OSError("settings failure")
        if fail:
            return False
        Path(path).write_text(json.dumps(dict(value)), encoding="utf-8")
        return True

    monkeypatch.setattr(lifecycle, "save_json", save)
    return file


def test_accepted_exit_flushes_queue_settings_and_player_before_shutdown(monkeypatch, tmp_path):
    window = Window()
    path = patch_settings_save(monkeypatch, tmp_path, window.actions)
    event = Event()
    window.closeEvent(event)
    assert event.result == "accept"
    labels = [(x[0], x[1]) for x in window.actions]
    assert labels.index(("queue", "save")) < labels.index(("settings", "save"))
    assert labels.index(("settings", "save")) < labels.index(("player", "save_position"))
    assert labels.index(("player", "save_position")) < labels.index(("player", "shutdown"))
    assert labels.index(("player", "shutdown")) < labels.index(("sound", "shutdown"))
    assert labels.index(("sound", "shutdown")) < labels.index(("tray", "shutdown"))
    assert json.loads(path.read_text(encoding="utf-8"))["ui_mode"] == "easy"
    assert ("player", "save_position", True) in window.actions
    assert ("queue", "save", ["pending-one", "completed-two"]) in window.actions


@pytest.mark.parametrize("queue_failure,settings_failure", [
    ("returns_false", "returns_false"),
    ("raises", "raises"),
])
def test_exit_still_saves_position_and_closes_if_other_persistence_fails(
    monkeypatch, tmp_path, queue_failure, settings_failure
):
    window = Window()
    window.queue_store = QueueStore(
        window.actions,
        ok=queue_failure != "returns_false",
        raises=queue_failure == "raises",
    )
    patch_settings_save(
        monkeypatch, tmp_path, window.actions,
        fail=settings_failure == "returns_false",
        raises=settings_failure == "raises",
    )
    event = Event()
    window.closeEvent(event)
    assert event.result == "accept"
    assert ("player", "save_position", True) in window.actions
    assert ("tray", "shutdown") in window.actions


def test_failed_player_backend_shutdown_does_not_skip_sound_and_tray(monkeypatch, tmp_path):
    window = Window()
    patch_settings_save(monkeypatch, tmp_path, window.actions)
    window.player_controller = Controller(window.actions, "player", fails=True)
    event = Event()
    window.closeEvent(event)
    assert event.result == "accept"
    assert ("player", "save_position", True) in window.actions
    assert ("player", "shutdown") in window.actions
    assert ("sound", "shutdown") in window.actions
    assert ("tray", "shutdown") in window.actions


def test_declining_close_while_audiobookshelf_worker_runs_preserves_session(monkeypatch, tmp_path):
    window = Window()
    patch_settings_save(monkeypatch, tmp_path, window.actions)
    window._abs_thread = WorkerThread()
    event = Event()
    window.closeEvent(event)
    assert event.result == "ignore"
    assert window._abs_thread.interruptions == 0
    assert not window._exit_requested
    assert window.visible
    assert ("confirm", "Проверка Audiobookshelf выполняется", False) in window.actions
    assert not any(row[:2] == ("queue", "save") for row in window.actions)
    assert not any(row[:2] == ("player", "shutdown") for row in window.actions)


def test_confirmed_audiobookshelf_close_defers_then_flushes_after_thread_stops(monkeypatch, tmp_path):
    window = Window()
    patch_settings_save(monkeypatch, tmp_path, window.actions)
    window._abs_thread = WorkerThread()
    window.confirmation = QMessageBox.StandardButton.Yes
    event = Event()
    window.closeEvent(event)
    assert event.result == "ignore"
    assert window._exit_requested
    assert not window.visible
    assert window._abs_thread.interruptions == 1
    assert not any(row[:2] == ("queue", "save") for row in window.actions)
    # Another close attempt during the grace period cannot dispose the live worker.
    still_running = Event()
    window.closeEvent(still_running)
    assert still_running.result == "ignore"
    assert not any(row[:2] == ("queue", "save") for row in window.actions)
    # The worker finishes normally and the next poll accepts a single final exit.
    window._abs_thread.running = False
    completed = Event()
    window.closeEvent(completed)
    assert completed.result == "accept"
    assert ("queue", "save", ["pending-one", "completed-two"]) in window.actions
    assert ("player", "save_position", True) in window.actions
    assert ("player", "shutdown") in window.actions


def test_stalled_audiobookshelf_worker_times_out_without_hard_terminate(monkeypatch, tmp_path):
    window = Window()
    patch_settings_save(monkeypatch, tmp_path, window.actions)
    thread = WorkerThread()
    window._abs_thread = thread
    window.confirmation = QMessageBox.StandardButton.Yes
    event = Event()
    window.closeEvent(event)
    assert event.result == "ignore"
    assert not window.visible
    monkeypatch.setattr(lifecycle.time, "monotonic", lambda: 100.0)
    window._exit_deadline = 50.0
    timeout = Event()
    window.closeEvent(timeout)
    assert timeout.result == "ignore"
    assert window.visible
    assert not window._exit_requested
    assert thread.interruptions >= 2
    assert thread.waits
    assert max(thread.waits) <= 750
    assert not any(row[:2] == ("queue", "save") for row in window.actions)
    assert not any(row[:2] == ("player", "shutdown") for row in window.actions)
