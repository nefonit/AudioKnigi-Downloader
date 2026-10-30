"""Reproductions for the 2026-10-30 external audit: track naming and playback completion.

Playback completion is tested with a minimal Qt-independent signal harness because
PySide6/Windows Media Foundation are not available on Linux CI. Real-device
screen-reader and audio-backend acceptance remain separate release gates.
"""
import ast
import time
from pathlib import Path
from types import SimpleNamespace

from audioknigi.models import Book, Track
from audioknigi.templates import render_track_filename


def test_numeric_track_label_different_padding_does_not_duplicate_chapter_number():
    book = Book(
        title="Example", url="https://example.org/book",
        tracks=[Track(index=i, title=f"{i:02d}", file=f"https://example.org/{i}") for i in range(1, 151)],
    )
    assert render_track_filename("{Track_Number} - {Track_Title}", book, book.tracks[0]) == "001.mp3"
    # A meaningful title, in contrast, must not be suppressed.
    book.tracks[0].title = "Opening"
    assert render_track_filename("{Track_Number} - {Track_Title}", book, book.tracks[0]) == "001 - Opening.mp3"


def test_completed_signal_cannot_resurrect_playback_position_or_reset_next_track():
    """Exercise the actual controller method with substitute Qt interfaces.

    The callback represents the synchronous GUI completion slot loading the
    next chapter, before EndOfMedia returns.
    """
    controller_path = Path(__file__).resolve().parents[2] / "audioknigi/qt/player_controller.py"
    tree = ast.parse(controller_path.read_text(encoding="utf-8"))
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "QtPlayerController")
    method = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "_on_media_status_changed")
    method.decorator_list = []
    # Preserve the method body under test, avoid importing Qt in headless CI.
    mod = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    media_status = SimpleNamespace(LoadedMedia=1, BufferedMedia=2, EndOfMedia=3, InvalidMedia=4)
    qmedia = SimpleNamespace(MediaStatus=media_status)
    scope = {"QMediaPlayer": qmedia, "time": time}
    exec(compile(mod, str(controller_path), "exec"), scope)

    state = {"old.mp3": 70.0}
    cleared = []

    def clear(path):
        cleared.append(str(path))
        state.pop(str(path), None)

    obj = SimpleNamespace(
        _at_end=False, _source_loaded_at=time.monotonic() - 5,
        _pending_resume_ms=0, _pending_autoplay=True, _resume_applied=True,
        current_path="old.mp3", player=SimpleNamespace(duration=lambda: 75000, position=lambda: 75000),
        store=SimpleNamespace(clear=clear),
    )

    def listener(path):
        # In production controller.load() calls save_position(force=True)
        # while current_path still points to the completed file.
        if not obj._at_end:
            state[path] = 75.0
        obj.current_path = "new.mp3"
        obj._at_end = False
        obj._pending_autoplay = True
        obj._pending_resume_ms = 1200
        obj._resume_applied = False

    obj.completed = SimpleNamespace(emit=listener)
    scope["_on_media_status_changed"](obj, media_status.EndOfMedia)
    assert cleared == ["old.mp3"]
    assert "old.mp3" not in state
    assert obj.current_path == "new.mp3"
    assert obj._at_end is False
    assert obj._pending_autoplay is True
    assert obj._pending_resume_ms == 1200
    assert obj._resume_applied is False


def test_dynamic_id3_error_is_localized_without_changing_filename_or_reason():
    from audioknigi.i18n import localize_runtime_text
    source = "Не удалось записать ID3 в 01.mp3: permission denied"
    assert localize_runtime_text("en", source) == "Could not write ID3 tags to 01.mp3: permission denied"
    assert localize_runtime_text("de", source) == "ID3-Tags für 01.mp3 konnten nicht geschrieben werden: permission denied"
    assert localize_runtime_text("uk", source) == "Не вдалося записати ID3 у 01.mp3: permission denied"