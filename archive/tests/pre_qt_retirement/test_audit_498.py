from pathlib import Path
from types import SimpleNamespace

import audioknigi.library_visuals as library_visuals_module
import audioknigi.queue_manager as queue_module
import audioknigi.storage as storage_module
from audioknigi.library_visuals import LibraryVisualMixin
from audioknigi.models import Book
from audioknigi.queue_manager import QueueMixin
from audioknigi.search import _title_score
from audioknigi.storage import StorageMixin


def test_unicode_dash_gets_same_search_shape_bonus_as_ascii_dash():
    plain = _title_score("Филатов Валерий Лабиринт искажений", "филатов")
    ascii_dash = _title_score("Филатов Валерий - Лабиринт искажений", "филатов")
    en_dash = _title_score("Филатов Валерий – Лабиринт искажений", "филатов")
    em_dash = _title_score("Филатов Валерий — Лабиринт искажений", "филатов")
    assert ascii_dash[1] == en_dash[1] == em_dash[1] == plain[1] + 1


def test_history_normalizes_none_metadata_to_empty_strings(monkeypatch, tmp_path):
    saved = {}
    monkeypatch.setattr(storage_module, "save_json", lambda _path, data: saved.setdefault("data", data))

    class Dummy(StorageMixin):
        def __init__(self):
            self.history = []
        def ui(self, callback):
            callback()
        def _refresh_history(self):
            pass

    book = Book(
        url="https://example.test/book",
        title="Demo",
        author=None,
        narrator=None,
        genre=None,
        year=None,
        description=None,
    )
    dummy = Dummy()
    dummy._add_history(book, tmp_path / "book", 1)
    entry = dummy.history[0]
    for key in ("author", "narrator", "genre", "year", "description"):
        assert entry[key] == ""
    assert saved["data"][0]["author"] == ""


def test_photo_payload_accepts_already_decoded_pillow_image(monkeypatch):
    if library_visuals_module.Image is None:
        return
    source = library_visuals_module.Image.new("RGB", (10, 10), "white")
    monkeypatch.setattr(library_visuals_module.ImageTk, "PhotoImage", lambda image, master=None: (image.size, master))
    dummy = LibraryVisualMixin()
    cache = {}
    photo = dummy._photo_from_payload(source, cache, "img", (8, 8))
    assert photo[0] == (8, 8)
    assert cache["img"] == photo


def test_queue_worker_restores_pause_button_label(monkeypatch):
    class Button:
        def __init__(self):
            self.text = "ПРОДОЛЖИТЬ"
        def configure(self, **kwargs):
            self.text = kwargs.get("text", self.text)

    class Dummy(QueueMixin):
        def __init__(self):
            self.queue_items = []
            self.queue_running = True
            self.queue_resume_event = SimpleNamespace(set=lambda: None)
            self.queue_pause_btn = Button()
            self._queue_run_token = 7
        def _queue_state_lock(self):
            class Lock:
                def __enter__(self): return self
                def __exit__(self, *args): return False
            return Lock()
        def set_status(self, *_): pass
        def set_stage(self, *_): pass
        def set_progress(self, *_): pass
        def set_busy(self, *_): pass
        def _notify_queue_complete(self, *_): pass
        def _refresh_unfinished_indicator(self): pass
        def ui(self, callback): callback()

    monkeypatch.setattr(queue_module.messagebox, "showinfo", lambda *a, **k: None)
    dummy = Dummy()
    dummy._queue_worker(run_token=7)
    assert dummy.queue_pause_btn.text == "ПАУЗА"


def test_easy_home_visible_drag_hint_is_the_actual_dnd_target():
    source = (Path(__file__).resolve().parents[1] / "audioknigi" / "ui" / "easy_home.py").read_text(encoding="utf-8")
    assert 'app.easy_drop_label = CTkLabel(' in source
    assert 'app.easy_drop_label.pack(' in source
    assert 'app.easy_drop_label = CTkLabel(main, text="", height=1' not in source


def test_reported_source_truncations_are_not_present():
    root = Path(__file__).resolve().parents[1] / "audioknigi"
    actions = (root / "actions.py").read_text(encoding="utf-8")
    onboarding = (root / "onboarding.py").read_text(encoding="utf-8")
    tray = (root / "tray.py").read_text(encoding="utf-8")
    assert "track = self._current_tree_track()" in actions
    assert 'entry = getattr(app, "easy_url_entry", None)' in onboarding
    assert "self._lock = threading.RLock()" in tray
    assert "def notify(self, title, message):" in tray
