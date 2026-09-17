from pathlib import Path
from types import SimpleNamespace

import audioknigi.actions as actions_module
import audioknigi.event_sounds as sounds_module
from audioknigi.actions import ActionsMixin
from audioknigi.event_sounds import EventSoundManager, EVENT_FILES
from audioknigi.models import Book, Track


class FakeSound:
    def __init__(self, path):
        self.path = path
        self.volume = None

    def set_volume(self, value):
        self.volume = value


class FakeChannel:
    def __init__(self, index):
        self.index = index
        self.volume = None
        self.stopped = 0
        self.played = []

    def set_volume(self, value):
        self.volume = value

    def stop(self):
        self.stopped += 1

    def play(self, sound):
        self.played.append(sound)


class FakeMixer:
    def __init__(self):
        self.initialized = False
        self.channels = 4
        self.channel = None
        self.Sound = FakeSound

    def get_init(self):
        return self.initialized

    def init(self):
        self.initialized = True

    def get_num_channels(self):
        return self.channels

    def set_num_channels(self, value):
        self.channels = int(value)

    def Channel(self, index):
        if self.channel is None or self.channel.index != index:
            self.channel = FakeChannel(index)
        return self.channel


def test_bundled_event_sound_files_exist():
    root = Path(__file__).resolve().parents[1]
    for filename in EVENT_FILES.values():
        path = root / "assets" / "sounds" / filename
        assert path.is_file()
        assert path.stat().st_size > 1000


def test_event_sound_manager_uses_separate_mixer_channel(monkeypatch):
    mixer = FakeMixer()
    monkeypatch.setattr(sounds_module, "pygame", SimpleNamespace(mixer=mixer))
    manager = EventSoundManager(enabled=True, volume=0.65)
    manager._play_worker("download_complete", False)

    assert mixer.initialized is True
    assert mixer.channels >= 8
    assert mixer.channel is not None
    assert mixer.channel.played
    assert mixer.channel.played[-1].volume == 0.65
    assert mixer.channel.volume == 0.65


def test_disabled_event_sounds_do_not_schedule_playback(monkeypatch):
    manager = EventSoundManager(enabled=False, volume=1.0)
    assert manager.play("error") is False
    assert manager.play("unknown") is False


def test_completion_and_error_workers_emit_expected_sounds(monkeypatch, tmp_path):
    monkeypatch.setattr(actions_module.messagebox, "showerror", lambda *args, **kwargs: None)

    book = Book(
        url="https://audioknigi.com.ua/test",
        title="Test",
        tracks=[Track(index=1, title="1", file="https://example.invalid/1.mp3")],
    )

    class Host(ActionsMixin):
        def __init__(self, fail=False):
            self.fail = fail
            self.current_book = book
            self.runtime_ui_mode = "easy"
            self.sounds = []
            self.statuses = []

        def _process_book(self, _book, _selected):
            if self.fail:
                raise RuntimeError("boom")
            return tmp_path

        def _play_event_sound(self, event, **_kwargs): self.sounds.append(event)
        def set_progress(self, *_args): pass
        def set_status(self, value): self.statuses.append(value)
        def set_stage(self, *_args): pass
        def _scan_book_files(self, *_args): return {}
        def ui(self, callback): callback()
        def _show_book(self, *_args): pass
        def _show_completion_actions(self, *_args): pass
        def log(self, *_args): pass
        def set_busy(self, *_args): pass
        def _refresh_unfinished_indicator(self): pass

    ok = Host(fail=False)
    ok._main_download_worker(book, [1])
    assert ok.sounds == ["download_complete"]

    failed = Host(fail=True)
    failed._main_download_worker(book, [1])
    assert failed.sounds == ["error"]
