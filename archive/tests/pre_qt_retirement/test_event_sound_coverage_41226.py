from pathlib import Path
from types import SimpleNamespace

import audioknigi.event_sounds as sound_module
from audioknigi.event_sounds import (
    EVENT_FILES,
    SYSTEM_ONLY_EVENTS,
    SUPPORTED_SOUND_EVENTS,
    EventSoundManager,
)


class FakeWinSound:
    MB_OK = 0
    MB_ICONASTERISK = 64
    MB_ICONEXCLAMATION = 48
    MB_ICONHAND = 16
    MB_ICONQUESTION = 32

    def __init__(self):
        self.calls = []

    def MessageBeep(self, flag):
        self.calls.append(flag)


def test_all_voice_assets_are_valid_mp3_files():
    from mutagen.mp3 import MP3

    root = Path(__file__).resolve().parents[1] / "assets" / "sounds"
    files = sorted(root.rglob("*.mp3"))
    assert len(files) == 34
    for path in files:
        audio = MP3(path)
        assert audio.info.length > 0.05
        assert path.stat().st_size > 1000


def test_every_voice_event_has_runtime_trigger_except_future_update_checker():
    root = Path(__file__).resolve().parents[1] / "audioknigi"
    runtime = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in root.rglob("*.py")
        if path.name != "event_sounds.py"
    )
    missing = {event for event in EVENT_FILES if f'"{event}"' not in runtime and f"'{event}'" not in runtime}
    assert missing == {"update_available"}


def test_system_only_events_are_registered_without_voice_files():
    assert SYSTEM_ONLY_EVENTS == {"app_ready", "attention", "completed_files_missing"}
    assert set(EVENT_FILES).isdisjoint(SYSTEM_ONLY_EVENTS)
    assert set(SUPPORTED_SOUND_EVENTS) == set(EVENT_FILES) | set(SYSTEM_ONLY_EVENTS)


def test_system_only_event_does_not_require_pygame(monkeypatch):
    fake = FakeWinSound()
    monkeypatch.setattr(sound_module, "winsound", fake)
    monkeypatch.setattr(sound_module, "pygame", None)
    manager = EventSoundManager(enabled=True)

    manager._play_worker("app_ready", False)

    assert fake.calls == [fake.MB_ICONASTERISK]


def test_voice_failure_falls_back_to_windows_system_sound(monkeypatch):
    fake = FakeWinSound()
    monkeypatch.setattr(sound_module, "winsound", fake)
    monkeypatch.setattr(sound_module, "pygame", None)
    messages = []
    manager = EventSoundManager(enabled=True, logger=messages.append)

    manager._play_worker("error", False)

    assert fake.calls == [fake.MB_ICONHAND]
    assert messages and "системный звук Windows" in messages[0]


def test_disabled_sounds_disable_system_service_cues(monkeypatch):
    fake = FakeWinSound()
    monkeypatch.setattr(sound_module, "winsound", fake)
    manager = EventSoundManager(enabled=False)

    assert manager.play("app_ready") is False
    manager._play_worker("app_ready", False)
    assert fake.calls == []


def test_new_important_service_events_have_call_sites():
    root = Path(__file__).resolve().parents[1] / "audioknigi"
    app = (root / "app.py").read_text(encoding="utf-8")
    actions = (root / "actions.py").read_text(encoding="utf-8")
    queue = (root / "queue_manager.py").read_text(encoding="utf-8")
    search = (root / "search.py").read_text(encoding="utf-8")
    player = (root / "player.py").read_text(encoding="utf-8")
    downloader = (root / "downloader.py").read_text(encoding="utf-8")

    assert '_play_event_sound("app_ready")' in app
    assert '_play_event_sound("attention")' in actions
    assert 'play_sound("completed_files_missing")' in queue
    assert 'play_sound("error")' in search
    assert 'play_sound("error")' in player
    assert 'play_sound("error")' in downloader


def test_settings_exposes_both_voice_and_system_sound_previews():
    root = Path(__file__).resolve().parents[1] / "audioknigi"
    settings = (root / "ui" / "settings_tab.py").read_text(encoding="utf-8")
    app = (root / "app.py").read_text(encoding="utf-8")
    assert 'text="Голосовой"' in settings
    assert 'text="Системный"' in settings
    assert "def preview_system_sound" in app
