from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path
from tkinter import ttk

import pytest

from audioknigi import AudioKnigiApp
from audioknigi.logging_utils import app_logger
from audioknigi.models import Book, NarrationVariant, Track


@pytest.fixture
def app():
    instance = AudioKnigiApp()
    instance.update_idletasks()
    instance.ui_mode_var.set("Простой")
    instance._apply_ui_mode()
    instance.runtime_ui_mode = "easy"
    yield instance
    try:
        instance.destroy()
    except Exception:
        pass


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


def test_simple_mode_exposes_same_narration_choices_as_advanced(app, tmp_path):
    app.runtime_output_dir = str(tmp_path)
    app.runtime_use_templates = False
    book = Book(
        url="https://knigavuhe.org/book/current/",
        title="Книга с озвучками",
        author="Автор",
        narrator="Чтец А",
        narration_variants=[
            NarrationVariant(url="https://knigavuhe.org/book/current/", narrator="Чтец А", current=True, available=True),
            NarrationVariant(url="https://knigavuhe.org/book/other/", narrator="Чтец Б", available=True),
        ],
        tracks=[Track(index=1, title="01", file="https://example/1.mp3")],
    )
    app.current_book = book

    app._update_narration_selector(book)
    app._show_easy_download_confirmation(book)
    app.update_idletasks()

    advanced_values = tuple(app.narration_combo.cget("values"))
    easy_values = tuple(app.easy_narration_combo.cget("values"))
    assert easy_values == advanced_values == ("Чтец А — доступно", "Чтец Б — доступно")
    assert app.easy_narration_row.winfo_manager() == "pack"
    assert app.narration_var.get() == "Чтец А — доступно"


def test_simple_narration_choice_reanalyzes_selected_recording(app, monkeypatch):
    current = "https://knigavuhe.org/book/current/"
    other = "https://knigavuhe.org/book/other/"
    book = Book(
        url=current,
        title="Книга с озвучками",
        narrator="Чтец А",
        narration_variants=[
            NarrationVariant(url=current, narrator="Чтец А", current=True, available=True),
            NarrationVariant(url=other, narrator="Чтец Б", available=True),
        ],
        tracks=[Track(index=1, title="01", file="https://example/1.mp3")],
    )
    app.current_book = book
    app._update_narration_selector(book)
    app.narration_var.set("Чтец Б — доступно")
    scheduled = []
    sounds = []
    monkeypatch.setattr(app, "after", lambda delay, callback, *args: scheduled.append((delay, callback)))
    monkeypatch.setattr(app, "_play_event_sound", lambda event, **_kwargs: sounds.append(event))

    app.select_narration_variant()

    assert app.url_var.get() == other
    assert sounds == ["narration_changed"]
    assert scheduled and scheduled[0][0] == 50


def test_simple_narration_selector_is_hidden_for_single_recording(app):
    book = Book(
        url="https://knigavuhe.org/book/only/",
        title="Одна озвучка",
        narrator="Один чтец",
        narration_variants=[NarrationVariant(url="https://knigavuhe.org/book/only/", narrator="Один чтец", current=True)],
        tracks=[Track(index=1, title="01", file="https://example/1.mp3")],
    )
    app._update_narration_selector(book)
    app.update_idletasks()
    assert app.easy_narration_row.winfo_manager() == ""


def test_treeview_scrollbars_use_explicit_audioknigi_styles(app):
    styles = {
        str(widget.cget("style"))
        for widget in _walk(app)
        if isinstance(widget, ttk.Scrollbar)
    }
    assert "AudioKnigi.Vertical.TScrollbar" in styles
    assert "AudioKnigi.Horizontal.TScrollbar" in styles


def test_slider_values_are_visible_and_numeric(app):
    app.bandwidth_limit_var.set(0)
    app.on_bandwidth_slider(0)
    assert app.bandwidth_label_var.get() == "0 МБ/с — без лимита"
    app.bandwidth_limit_var.set(25)
    app.on_bandwidth_slider(25)
    assert app.bandwidth_label_var.get() == "25 МБ/с"

    app.event_sound_volume_var.set(65)
    app.on_event_sound_volume(65)
    assert app.event_sound_volume_label_var.get() == "65%"


def test_shortcut_hints_have_dynamic_wrap_support(app):
    app.update_idletasks()
    assert int(float(app.easy_search_shortcut_hint.cget("wraplength"))) >= 160
    assert int(float(app.search_shortcut_hint.cget("wraplength"))) >= 180


def test_error_log_is_detailed_and_rotated_more_generously(app):
    handlers = [h for h in app_logger.handlers if hasattr(h, "maxBytes")]
    assert handlers
    handler = handlers[0]
    assert handler.maxBytes >= 5_000_000
    assert handler.backupCount >= 5
    fmt = str(handler.formatter._fmt)
    for field in ("%(threadName)s", "%(module)s", "%(funcName)s", "%(lineno)d"):
        assert field in fmt
    assert app_logger.level <= logging.DEBUG
    assert sys.excepthook == app._main_exception_handler


def test_all_python_modules_parse_and_have_no_bare_except():
    root = Path(__file__).resolve().parents[1] / "audioknigi"
    files = sorted(root.rglob("*.py"))
    assert len(files) >= 40
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        bare = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler) and n.type is None]
        assert not bare, f"bare except in {path}"
