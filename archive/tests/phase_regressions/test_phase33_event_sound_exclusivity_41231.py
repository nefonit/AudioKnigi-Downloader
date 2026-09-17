from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_event_sound_manager_uses_one_logical_playback_channel():
    source = text("audioknigi/qt/event_sounds.py")
    assert "def _stop_media_players(self, *, except_key: str | None = None) -> None:" in source
    assert "self._stop_media_players(except_key=key)" in source
    assert "player.stop()" in source
    assert "Re-triggering the same cue restarts it instead of layering it." in source


def test_retry_download_preempts_previous_error_cue():
    source = text("audioknigi/qt/main_window.py")
    event_source = text("audioknigi/qt/event_sounds.py")
    launch = source[source.index("def _launch_download"):source.index("@Slot()\n    def start_download")]
    finished = source[source.index("def _download_finished"):source.index("@Slot()\n    def _clear_download_thread")]
    assert 'self._play_event_sound("download_start")' in launch
    assert 'self._play_event_sound("error")' in finished
    # The event manager, not each caller, enforces exclusivity globally.
    assert "self._stop_media_players(except_key=key)" in event_source


def test_narration_change_emits_one_success_cue_for_automatic_reanalysis():
    source = text("audioknigi/qt/main_window.py")
    assert "self._suppress_next_book_found_sound = False" in source
    narration = source[source.index("def _narration_selected"):source.index("@Slot()\n    def select_first_available_narration")]
    assert "self._suppress_next_book_found_sound = True" in narration
    assert 'self._play_event_sound("narration_changed")' in narration

    analysis = source[source.index("def _analysis_finished"):source.index("@Slot()\n    def _clear_analysis_thread")]
    assert "suppress_book_found_sound = bool(self._suppress_next_book_found_sound)" in analysis
    assert "self._suppress_next_book_found_sound = False" in analysis
    assert 'if not suppress_book_found_sound:\n            self._play_event_sound("book_found")' in analysis
