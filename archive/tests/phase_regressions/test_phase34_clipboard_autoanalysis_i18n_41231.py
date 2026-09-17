from __future__ import annotations

from pathlib import Path

from audioknigi.core import display_track_timeline
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.models import Book, Track
from audioknigi.services import book_analysis_service
from audioknigi.services.book_analysis_service import BookAnalysisService

ROOT = Path(__file__).resolve().parents[1]


def source(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_poleknig_analysis_populates_missing_durations_and_cumulative_timeline(monkeypatch):
    book = Book(
        url="https://poleknig.com/books/266948",
        title="Test",
        tracks=[
            Track(index=1, title="01", file="https://s.example/01.mp3"),
            Track(index=2, title="02", file="https://s.example/02.mp3"),
            Track(index=3, title="03", file="https://s.example/03.mp3"),
        ],
    )
    monkeypatch.setattr(book_analysis_service, "fetch_poleknig_book", lambda *_a, **_k: book)
    durations = {
        "https://s.example/01.mp3": 100.0,
        "https://s.example/02.mp3": 125.5,
        "https://s.example/03.mp3": 90.0,
    }
    monkeypatch.setattr(
        BookAnalysisService,
        "_probe_remote_duration",
        lambda self, url, referer="": durations[url],
    )
    progress = []
    result = BookAnalysisService(progress=progress.append).analyze(book.url)

    assert [track.duration for track in result.tracks] == [100.0, 125.5, 90.0]
    assert display_track_timeline(result.tracks) == [
        (0.0, 100.0, 100.0),
        (100.0, 225.5, 125.5),
        (225.5, 315.5, 90.0),
    ]
    assert any("Определяю длительность частей" in item for item in progress)


def test_analysis_duration_probe_does_not_treat_one_shared_source_as_each_chapter(monkeypatch):
    shared = "https://s.example/full.mp3"
    book = Book(
        url="https://poleknig.com/books/266948",
        title="Shared",
        tracks=[
            Track(index=1, title="01", file=shared, start=0, end=100, duration=100),
            Track(index=2, title="02", file=shared, start=100, end=200, duration=100),
        ],
    )
    service = BookAnalysisService()
    calls = []
    monkeypatch.setattr(service, "_probe_remote_duration", lambda *args, **kwargs: calls.append(args) or 999.0)
    assert service._populate_missing_track_durations(book) == 0
    assert calls == []


def test_track_table_uses_display_timeline_for_start_end_and_duration():
    text = source("audioknigi/qt/track_model.py")
    assert "display_track_timeline" in text
    assert "self._timeline_rows = display_track_timeline(self._tracks)" in text
    assert "if column in (3, 4, 5):" in text


def test_clipboard_watcher_is_immediate_and_yes_updates_both_modes():
    text = source("audioknigi/qt/main_window.py")
    assert "clipboard.dataChanged.connect(self._clipboard_data_changed)" in text
    assert "def _insert_clipboard_book_link" in text
    assert "self.book_url_edit.setText(value)" in text
    assert "self.easy_input.setText(value)" in text
    assert "self._suppress_clipboard_prompt_text = value.strip()" in text
    assert "self._set_clipboard_text(result.url)" in text


def test_search_choice_automatically_starts_analysis_in_advanced_and_easy_modes():
    text = source("audioknigi/qt/main_window.py")
    start = text.index("def use_selected_result(self):")
    end = text.index("def copy_selected_url(self):", start)
    block = text[start:end]
    assert 'self.tabs.setCurrentIndex(self.TAB_BOOK)' in block
    assert 'QTimer.singleShot(0, self.start_analysis)' in block
    assert 'Выбрать и проанализировать' in text


def test_phase34_runtime_and_accessibility_strings_translate_for_all_supported_languages():
    runtime_samples = (
        "Ссылка в буфере обмена",
        "В буфере найдена поддерживаемая ссылка аудиокниги. Вставить её в поле книги?",
        "Определяю длительность частей: 2/5",
        "Ожидает",
        "Скачивается",
        "Требуется повторный анализ",
    )
    literal_samples = (
        "Выбрать и проанализировать",
        "Текущая позиция {seconds} секунд. Диапазон до {maximum} секунд",
        "Книга: {title}. Статус: {status}. Пауза: {paused}. Приоритет: {priority}. Попытки: {attempts}. Частей: {parts}. Ошибка: {error}. URL: {url}.",
        "Загрузчик аудиокниг с поиском, очередью, историей, встроенным плеером и поддержкой экранных дикторов.",
    )
    for language in ("uk", "de", "en"):
        for value in runtime_samples:
            translated = localize_runtime_text(language, value)
            assert translated != value or (language == "uk" and value == "Ожидает") is False
        for value in literal_samples:
            assert ui_text(language, value) != value


def test_extended_qt_localization_audit_covers_runtime_tooltips_and_ui_text():
    from tools.qt_localization_audit import audit

    assert audit() == []
