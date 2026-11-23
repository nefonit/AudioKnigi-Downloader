"""Keyboard and accessible Qt workflow safety regressions."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import threading

from audioknigi.qt.player_mixin import PlayerUiMixin
from audioknigi.qt.event_sounds import QtEventSoundManager
from audioknigi.qt.mixins.search import SearchUiMixin
from audioknigi.qt.mixins.settings import SettingsUiMixin
from audioknigi.qt.mixins.history import HistoryUiMixin
from audioknigi.qt.mixins.queue import QueueUiMixin
from audioknigi.qt.mixins.clipboard import ClipboardUiMixin
from audioknigi.services.search_service import SearchOutcome


def test_player_position_signal_preserves_keyboard_seek_preview():
    changes = []
    class Slider:
        def setValue(self, value): changes.append(("position", value))
        def blockSignals(self, value): changes.append(("block", value))
        def maximum(self): return 120
    stub = SimpleNamespace(
        _player_seek_active=False,
        _player_keyboard_seek_timer=SimpleNamespace(isActive=lambda: True),
        player_seek_slider=Slider(),
    )
    PlayerUiMixin._player_position_changed(stub, 12000, 120000)
    assert changes == []


def test_delayed_old_event_sound_cannot_play_after_new_event():
    events = []
    def disconnect(callback):
        events.append(("disconnect", callback))
    player = SimpleNamespace(
        mediaStatusChanged=SimpleNamespace(disconnect=disconnect),
        stop=lambda: events.append(("stop",)),
    )
    pending = lambda *_: None
    stub = SimpleNamespace(
        _players={"old": (player, object())},
        _pending_media_callbacks={"old": pending},
    )
    QtEventSoundManager._stop_media_players(stub, except_key=None)
    assert events == [("disconnect", pending), ("stop",)]
    assert stub._pending_media_callbacks == {}


def test_cancelled_search_is_not_announced_as_no_results_or_error():
    events = []
    stub = SimpleNamespace(
        _exit_requested=False,
        search_model=SimpleNamespace(set_results=lambda *_a, **_kw: events.append("clear")),
        _set_search_results_active=lambda v: events.append(("active", v)),
        _update_search_action_states=lambda: events.append("controls"),
        set_status=lambda text, **_kw: events.append(("status", text)),
        _l=lambda x: x,
        _play_event_sound=lambda x: events.append(("sound", x)),
    )
    SearchUiMixin._apply_search_outcome(
        stub, SearchOutcome("Demo", [], []), cancelled=True,
    )
    assert ("status", "Поиск отменён пользователем.") in events
    assert not any(isinstance(x, tuple) and x[0] == "sound" for x in events)


def test_save_settings_does_not_switch_tabs_when_mode_is_unchanged(monkeypatch):
    import audioknigi.qt.mixins.settings as settings_module
    monkeypatch.setattr(settings_module, "save_app_settings", lambda *_a, **_kw: True)
    monkeypatch.setattr(settings_module, "configure_user_proxy", lambda *_a: False)
    monkeypatch.setattr(settings_module, "configure_proxy_hosts", lambda *_a: False)
    monkeypatch.setattr(settings_module, "install_cloudflare_dns", lambda **_kw: None)
    monkeypatch.setattr(settings_module, "QApplication", SimpleNamespace(instance=lambda: None))
    switched = []
    stub = SimpleNamespace(
        settings={"ui_mode": "advanced", "dns_mode": "auto"},
        _settings_from_ui=lambda: {"ui_mode": "advanced", "dns_mode": "auto"},
        current_ui_mode=lambda: "advanced",
        set_ui_mode=lambda mode, **_kw: switched.append(mode),
        language="ru",
        event_sound_manager=SimpleNamespace(configure=lambda **_kw: None),
        _refresh_context_guidance=lambda **_kw: None,
        _apply_large_mode=lambda: None,
        _apply_source_visibility=lambda: None,
        _refresh_unfinished=lambda: None,
        set_status=lambda *_a, **_kw: None,
    )
    assert SettingsUiMixin._save_settings(stub) is True
    assert switched == []


def test_redownload_while_downloading_does_not_arm_delayed_delete():
    state = []
    active = SimpleNamespace(isRunning=lambda: True)
    stub = SimpleNamespace(
        _analysis_thread=None, _download_thread=active,
        _selected_history=lambda: (0, {"url": "https://knigavuhe.org/book/123/"}),
        _download_after_analysis=False, _history_redownload_confirmed=False,
        set_status=lambda text, **_kw: state.append(text),
    )
    HistoryUiMixin.history_redownload(stub)
    assert stub._download_after_analysis is False
    assert stub._history_redownload_confirmed is False
    assert state


def test_queue_urls_stay_pending_while_downloading():
    pending = ["https://knigavuhe.org/book/123/"]
    active = SimpleNamespace(isRunning=lambda: True)
    stub = SimpleNamespace(
        _download_thread=active,
        _pending_queue_urls=list(pending),
        _queue_after_analysis=False,
    )
    QueueUiMixin._queue_next_dropped_url(stub)
    assert stub._pending_queue_urls == pending
    assert stub._queue_after_analysis is False


def test_resume_enters_advanced_mode_preserving_precise_audio_profile():
    actions = []
    record = SimpleNamespace(
        selected_indices=[1], download_mode="parts",
        naming_mode="number", audio_preset="96k_mono",
        normalization_mode="single",
        use_templates=None, folder_template=None, track_template=None,
        title="Book", url="https://knigavuhe.org/book/123/",
    )
    stub = SimpleNamespace(
        _refresh_unfinished=lambda: None,
        _unfinished_records=[record],
        settings={"quality_preset": "phone"},
        _apply_settings_to_qt_controls=lambda: actions.append("apply"),
        set_ui_mode=lambda mode, **kw: actions.append(("mode", mode)),
        book_url_edit=SimpleNamespace(setText=lambda *_: None),
        tabs=SimpleNamespace(setCurrentIndex=lambda *_: None), TAB_BOOK=0,
        set_status=lambda *_a, **_kw: None,
        _play_event_sound=lambda *_a: None,
        start_analysis=lambda: actions.append("analyze"),
    )
    ClipboardUiMixin.continue_unfinished(stub)
    assert stub.settings["audio_preset"] == "96k_mono"
    assert stub.settings["normalization_mode"] == "single"
    assert stub.settings["quality_preset"] == "standard"
    assert actions[:2] == [("mode", "advanced"), "apply"]
