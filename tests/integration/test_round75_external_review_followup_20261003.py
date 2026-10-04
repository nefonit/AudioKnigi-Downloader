from __future__ import annotations

from pathlib import Path

from audioknigi.config.settings import AppSettings
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.errors import SharedSourceTimelineError
from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, Track

ROOT = Path(__file__).resolve().parents[2]


def test_appsettings_unrelated_write_does_not_resurrect_deleted_default_key():
    settings = AppSettings({"theme": "dark", "scale": 100})
    del settings["theme"]
    settings["scale"] = 999
    assert "theme" not in settings
    assert settings["scale"] == 200


def test_book_fallback_skips_malformed_track_indices_instead_of_crashing():
    original = Book(url="https://audioknigi.com.ua/audio-1-demo", title="Original", tracks=[
        Track(index=1, title="One", file="https://cdn.invalid/shared.mp3"),
        Track(index=2, title="Broken", file="https://cdn.invalid/shared.mp3"),
    ])
    original.tracks[1].index = None
    fallback = Book(url="https://knigavuhe.org/book/demo/", title="Fallback", tracks=[
        Track(index=1, title="One", file="https://cdn.invalid/fallback.mp3"),
        Track(index=2, title="Broken", file="https://cdn.invalid/fallback.mp3"),
    ])
    fallback.tracks[1].index = "not-an-index"

    class Harness(BookFlowMixin):
        def __init__(self): self.calls = 0
        def _process_book_once(self, book, active_selected, status_callback):
            self.calls += 1
            if self.calls == 1:
                raise SharedSourceTimelineError({"reason":"invalid_last_boundary","expected_end":10.0,"actual_duration":5.0})
            return book, set(active_selected)
        def _clear_stale_source_downloads(self, _book): return 0
        def _knigavuhe_fallback_candidate(self, _book): return fallback
        def _remove_resume_manifest(self, _book): return None
        def _populate_missing_track_durations(self, _book): return 0
        def _log_book_flow(self, *args, **kwargs): return None
        def log(self, _message): return None

    result_book, selected = Harness()._process_book(original)
    assert result_book is fallback
    assert selected == {1}


def test_expired_source_mapping_uses_normalized_url_and_safe_indices():
    source = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    assert "if tr.file == url" not in source
    assert 'if str(getattr(tr, "file", "") or "") == url' in source
    assert 'safe_int(getattr(tr, "index", None), -1)' in source


def test_reviewed_runtime_localizations_are_consistent():
    player_message = ("У выбранной части пока нет доступного локального файла. "
                      "Сначала скачайте её или откройте готовый аудиофайл на вкладке «Плеер».")
    assert "Laden Sie ihn zuerst herunter" in localize_runtime_text("de", player_message)
    cancelled = "Скачивание отменено. Можно изменить выбор частей или снова нажать «Скачать книгу»."
    assert localize_runtime_text("en", cancelled).startswith("Download cancelled.")
    segmented = "Сегментированная загрузка: 4 поток(а/ов), 12 Range-задач."
    assert localize_runtime_text("uk", segmented) == "Сегментоване завантаження: 4 потік(ів), 12 Range-завдань."


def test_invalid_explicit_split_boundary_is_diagnosable_without_changing_fallback_behavior():
    source = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    block = source[source.index("def _split_track"):source.index("def _save_book_sidecars")]
    assert "event=split_invalid_explicit_boundary" in block
    assert "end <= start" in block
