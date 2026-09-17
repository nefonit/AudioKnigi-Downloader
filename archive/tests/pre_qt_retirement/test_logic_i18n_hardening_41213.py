from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace

from audioknigi.actions import ActionsMixin
from audioknigi.accessibility import AccessibilityManager
from audioknigi.core import extract_metadata_from_html
from audioknigi.dnd import DragDropMixin
from audioknigi.models import Book, QueueItem, Track
from audioknigi.queue_manager import QueueMixin
from audioknigi.templates import render_track_filename
from audioknigi.ui_state import (
    UI_MODE_ADVANCED,
    UI_MODE_EASY,
    normalize_ui_mode,
    ui_mode_label,
)


class _StatusHost(ActionsMixin):
    def __init__(self, language="ru"):
        self.language = language


def test_status_mapping_is_locale_aware_and_does_not_parse_book_titles_as_state():
    ru = _StatusHost("ru")
    assert ru._friendly_status_text("Ошибка резидента") == "Ошибка резидента"
    assert ru._friendly_status_text("Разделение") == "Разделение"
    assert ru._friendly_status_text("Открываем «Ошибка резидента»…") == "Открываем «Ошибка резидента»…"
    assert ru._friendly_status_info("Ошибка поиска")[1] == "error"

    en = _StatusHost("en")
    assert en._friendly_status_text("Анализ страницы") == "Getting book information"
    assert en._friendly_status_text("Проверка 12/48") == "Checking files — 12 of 48"
    assert en._friendly_status_text("Downloading 3/9") == "Downloading book"


def test_ui_mode_normalization_accepts_stable_keys_and_all_display_languages():
    for language in ("ru", "uk", "de", "en"):
        easy_label = ui_mode_label(language, UI_MODE_EASY)
        advanced_label = ui_mode_label(language, UI_MODE_ADVANCED)
        assert normalize_ui_mode(easy_label, language=language) == UI_MODE_EASY
        assert normalize_ui_mode(advanced_label, language=language) == UI_MODE_ADVANCED
    assert normalize_ui_mode("Advanced", language="ru") == UI_MODE_ADVANCED
    assert normalize_ui_mode("Einfach", language="en") == UI_MODE_EASY
    assert normalize_ui_mode("advanced") == UI_MODE_ADVANCED


def test_track_filenames_use_three_digits_for_books_with_100_plus_parts():
    tracks = [Track(index=i, title=f"Part {i}", file=f"https://example/{i}.mp3") for i in range(1, 131)]
    book = Book(url="u", title="Large", tracks=tracks)
    host = SimpleNamespace(runtime_use_templates=False, runtime_naming_mode="number")
    # Call the real mixin method without constructing Tk.
    from audioknigi.downloader import DownloaderMixin
    assert DownloaderMixin._track_filename(host, book, tracks[0]) == "001.mp3"
    assert DownloaderMixin._track_filename(host, book, tracks[99]) == "100.mp3"
    assert render_track_filename("{Track_Number}", book, tracks[0]) == "001.mp3"
    assert render_track_filename("{Track_Number} - {Track_Title}", book, tracks[129]) == "130 - Part 130.mp3"


def test_generic_javascript_name_is_not_used_as_book_title_fallback():
    html = '<script>window.controls={"name":"button_close"}</script>'
    title, author, cover = extract_metadata_from_html(html, fallback_title="")
    assert title == ""
    assert author == ""
    assert cover == ""

    structured = '''
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Audiobook","name":"Real Book","author":{"@type":"Person","name":"Real Author"}}
    </script>
    '''
    title, author, _cover = extract_metadata_from_html(structured, fallback_title="")
    assert title == "Real Book"
    assert author == "Real Author"


class _QueueHost(QueueMixin):
    def __init__(self):
        self.queue_items = [QueueItem(url="u")]
        self._queue_lock = threading.RLock()
    def ui(self, func):
        func()
    def _refresh_queue(self):
        pass


def test_queue_completion_logic_has_stable_status_code():
    host = _QueueHost()
    item = host.queue_items[0]
    host._queue_status(item, "Finished", status_code="done")
    assert item.status == "Finished"
    assert item.status_code == "done"
    host._queue_status(item, "Error", status_code="error")
    assert item.status_code == "error"


class _DropTarget:
    def __init__(self):
        self.text = "initial"
    def drop_target_register(self, *_args):
        pass
    def dnd_bind(self, *_args):
        pass
    def configure(self, **kwargs):
        self.text = kwargs.get("text", self.text)


class _DndHost(DragDropMixin):
    def __init__(self):
        self.dnd_available = True
        self.easy_drop_label = _DropTarget()
        self.logged = []
    def drop_target_register(self, *_args):
        pass
    def dnd_bind(self, *_args):
        pass
    def _on_drop_main(self, _event):
        return "copy"
    def _on_drop_root(self, _event):
        return "copy"
    def log(self, text):
        self.logged.append(text)


def test_successful_dnd_registration_updates_simple_mode_hint():
    host = _DndHost()
    host._register_drag_and_drop_targets()
    assert host.easy_drop_label.text == "Перетащи сюда ссылку на книгу из браузера"


def test_accessibility_schedule_from_worker_is_marshaled_without_calling_tk_after():
    posted = []
    after_calls = []
    app = SimpleNamespace(
        event_bus=SimpleNamespace(post=lambda callback: posted.append(callback)),
        after=lambda *_args: after_calls.append(threading.get_ident()),
    )
    manager = AccessibilityManager.__new__(AccessibilityManager)
    manager.app = app
    manager._ui_thread_id = threading.get_ident()
    manager._closed = False
    manager._after_ids = set()

    thread = threading.Thread(target=lambda: manager._schedule(10, lambda: None))
    thread.start(); thread.join()
    assert len(posted) == 1
    assert after_calls == []
    posted[0]()
    assert after_calls == [threading.get_ident()]
