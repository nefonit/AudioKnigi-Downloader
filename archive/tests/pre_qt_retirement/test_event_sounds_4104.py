from pathlib import Path

from audioknigi.event_sounds import EVENT_FILES, EventSoundManager


def test_complete_english_sound_pack_covers_every_registered_event():
    root = Path(__file__).resolve().parents[1]
    english_dir = root / "assets" / "sounds" / "en"
    manager = EventSoundManager(language="en-US")

    assert len(EVENT_FILES) == 17
    for event, filename in EVENT_FILES.items():
        path = manager._sound_path(event)
        assert path == english_dir / filename
        assert path.is_file() and path.stat().st_size > 1000
