from __future__ import annotations

import ast
from pathlib import Path

import audioknigi.downloader as downloader_module
from audioknigi.downloader import DownloaderMixin
from audioknigi.i18n import ui_text
from audioknigi.models import Book, Track

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_downloader_translation_function_cannot_be_shadowed_by_track_objects(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader_module, "resolve_executable", lambda _name: "ffmpeg")

    source_path = tmp_path / "_source.mp3"
    source_path.write_bytes(b"source")

    class FakeDownloader(DownloaderMixin):
        runtime_language = "ru"
        runtime_audio_preset = "copy"
        runtime_normalization_mode = "off"
        runtime_embed_tags = False
        runtime_save_sidecars = False
        runtime_delete_source = False
        runtime_parallel_single_source = False
        _last_process_skipped_indices = []

        def _check_cancel(self):
            return None

        def _scan_book_files(self, book, *, create_folder=True):
            return None

        def _check_disk_space(self, book, selected_indices=None, show_warning=True):
            return True

        def _write_resume_manifest(self, book, selected_indices):
            return None

        def _book_folder(self, book, *, create=True):
            return tmp_path

        def _log_book_flow(self, *args, **kwargs):
            return None

        def log(self, _message):
            return None

        def _track_filename(self, book, track, mode=None):
            return f"{int(track.index):02d}.mp3"

        def _track_path(self, book, track, mode=None, *, create_folder=True):
            return tmp_path / self._track_filename(book, track, mode)

        def _source_target_assignments(self, book, source_urls, folder):
            return [(1, source_urls[0], source_path)]

        def _shared_source_timeline_issue(self, book, local_map=None):
            return None

        def set_stage(self, number, message):
            self.last_stage = (number, message)

        def set_status(self, message):
            self.last_status = message

        def set_progress(self, value):
            self.last_progress = value

        def _split_track(self, book, track, source_path):
            self._track_path(book, track).write_bytes(b"mp3")

        def _verify_track_file(self, book, track, *, create_folder=True):
            return "готово", float(track.duration or 1.0), self._track_path(book, track)

        def _cover_bytes(self, book):
            return None

        def _save_book_sidecars(self, book, folder, tracks):
            return None

        def _scan_audiobookshelf_after_book(self):
            return None

        def _remove_resume_manifest(self, book):
            return None

        def _add_history(self, book, folder, count):
            return None

    book = Book(
        url="https://example.test/book",
        title="Test",
        tracks=[Track(index=1, title="001", file="https://example.test/audio.mp3", duration=1.0)],
    )
    engine = FakeDownloader()
    result = engine._process_book_once(book, [1])

    assert result == tmp_path
    assert (tmp_path / "01.mp3").is_file()
    assert engine.last_stage == (5, "Готово")

    source = text("audioknigi/downloader.py")
    assert "from .i18n import tr as i18n_tr" in source
    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "tr"
        for node in ast.walk(tree)
    )


def test_search_availability_codes_have_human_localized_labels():
    model = text("audioknigi/qt/search_model.py")
    assert '"available": "Доступно"' in model
    assert '"restricted": "Ограничено"' in model
    assert '"unavailable": "Недоступно"' in model
    assert '"Статус не определён"' in model

    assert ui_text("ru", "Доступно") == "Доступно"
    assert ui_text("ru", "Ограничено") == "Ограничено"
    assert ui_text("de", "Доступно") == "Verfügbar"
    assert ui_text("en", "Ограничено") == "Restricted"
    assert ui_text("uk", "Статус не определён") == "Статус не визначено"


def test_knigavuhe_successful_hydration_marks_result_available():
    source = text("audioknigi/knigavuhe.py")
    assert source.count('availability="available"') >= 2
    assert 'if any(str(getattr(item, "availability", "") or "").casefold() == "available" for item in members)' in source


def test_text_editor_context_menu_uses_selected_application_language():
    helper = text("audioknigi/qt/localized_context_menu.py")
    main = text("audioknigi/qt/main_window.py")
    onboarding = text("audioknigi/qt/onboarding.py")

    for label in ("Отменить", "Повторить", "Вырезать", "Копировать", "Вставить", "Удалить текст", "Выделить всё"):
        assert f'ui_text(language, "{label}")' in helper
    assert "self._install_localized_text_context_menus()" in main
    assert "install_localized_text_context_menu(self.folder_edit, lambda: self._language)" in onboarding

    assert ui_text("en", "Отменить") == "Undo"
    assert ui_text("de", "Вырезать") == "Ausschneiden"
    assert ui_text("uk", "Выделить всё") == "Виділити все"


def test_download_worker_logs_full_traceback_before_showing_error():
    workers = text("audioknigi/qt/workers.py")
    block = workers[workers.index("class DownloadWorker"):workers.index("class QueueTableWidget")]
    assert 'app_logger.exception("Qt download worker failed")' in block
    assert 'self.finished.emit(("error", str(exc)))' in block
