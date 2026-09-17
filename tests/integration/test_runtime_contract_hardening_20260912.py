from __future__ import annotations

from pathlib import Path
from threading import Event

import pytest

from audioknigi.config.settings import AppSettings
from audioknigi.core import Cancelled
from audioknigi.download_engine import DownloadService
from audioknigi.i18n import tr
from audioknigi.models import Book, Track
from audioknigi.providers.audioknigi_search import search_audioknigi
from audioknigi.services.download_request import DownloadRequest, build_download_request
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict

ROOT = Path(__file__).resolve().parents[2]


def _book() -> Book:
    return Book(
        url="https://audioknigi.com.ua/audio-1",
        title="Demo",
        tracks=[
            Track(index=1, title="One", file="https://cdn.invalid/1.mp3"),
            Track(index=2, title="Two", file="https://cdn.invalid/2.mp3"),
        ],
    )


def test_whole_book_none_selection_round_trips_queue(tmp_path):
    request = DownloadRequest(book=_book(), selected_indices=None, output_dir=tmp_path)
    request.validate()
    task = QueueTask(id="whole", request=request, title="Demo")
    payload = task_to_dict(task)
    assert payload["request"]["selected_indices"] is None
    restored = task_from_dict(payload)
    assert restored.request.selected_indices is None
    assert restored.request.resolved_selected_indices() == [1, 2]


def test_explicit_empty_selection_is_still_rejected(tmp_path):
    request = DownloadRequest(book=_book(), selected_indices=[], output_dir=tmp_path)
    with pytest.raises(ValueError, match="Не выбрана ни одна часть"):
        request.validate()


def test_build_request_accepts_none_as_whole_book(tmp_path):
    request = build_download_request(_book(), {"output_dir": str(tmp_path)}, None)
    assert request.selected_indices is None
    assert request.resolved_selected_indices() == [1, 2]


def test_duplicate_preflight_treats_none_as_full_selection(tmp_path):
    request = DownloadRequest(book=_book(), selected_indices=None, output_dir=tmp_path)
    result = DownloadService().duplicate_preflight(request, probe_durations=False)
    assert result.evidence == "files-incomplete"


def test_audioknigi_search_cancellation_propagates():
    event = Event()
    event.set()
    with pytest.raises(Cancelled):
        search_audioknigi("demo", cancel_event=event)


def test_tr_does_not_format_template_braces_without_arguments(monkeypatch):
    import audioknigi.i18n as i18n
    monkeypatch.setitem(i18n.STRINGS.setdefault("ru", {}), "template_contract", "{Book_Title} / {Track_Number}")
    assert tr("ru", "template_contract") == "{Book_Title} / {Track_Number}"


def test_appsettings_is_used_by_qt_settings_sync_contract():
    source = (ROOT / "audioknigi" / "qt" / "settings_sync.py").read_text(encoding="utf-8")
    assert "from collections.abc import Mapping" in source
    assert "isinstance(self.settings, Mapping)" in source
    assert "isinstance(self.settings, dict)" not in source


def test_player_persistence_accepts_mutable_mapping_settings():
    source = (ROOT / "audioknigi" / "qt" / "player_mixin.py").read_text(encoding="utf-8")
    assert "MutableMapping" in source
    assert 'isinstance(getattr(self, "settings", None), MutableMapping)' in source


def test_backup_restore_reloads_typed_settings():
    source = (ROOT / "audioknigi" / "qt" / "mixins" / "history.py").read_text(encoding="utf-8")
    assert "load_app_settings" in source
    assert "self.settings = load_app_settings()" in source
    assert "self.settings = load_json" not in source


def test_queue_and_download_ui_use_none_safe_part_counts():
    queue_source = (ROOT / "audioknigi" / "qt" / "mixins" / "queue.py").read_text(encoding="utf-8")
    analysis_source = (ROOT / "audioknigi" / "qt" / "mixins" / "analysis_download.py").read_text(encoding="utf-8")
    assert "_queue_parts_count" in queue_source
    assert "len(task.request.selected_indices)" not in queue_source
    assert "request.resolved_selected_indices()" in analysis_source
    assert "for value in old.selected_indices" in analysis_source
    assert "if old.selected_indices is None" in analysis_source


def test_first_run_cancel_is_skip_not_process_exit():
    source = (ROOT / "audioknigi" / "qt" / "application.py").read_text(encoding="utf-8")
    block = source[source.index('if not bool(settings.get("first_run_complete"'):source.index('app.setProperty("audioknigi_language"')]
    assert 'settings["first_run_complete"] = True' in block
    assert "save_app_settings(settings)" in block
    assert "return 0" not in block


def test_selftests_print_failure_traceback_and_cleanup_after_close_failure():
    source = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")
    assert source.count('print(details, file=sys.stderr') >= 3
    assert 'try:\n                    window.close()\n                except Exception:' in source
    assert 'window.event_sound_manager.shutdown()' in source


def test_release_dependency_pins_are_documented_as_verified_current_releases():
    release = (ROOT / "requirements-release.txt").read_text(encoding="utf-8")
    for pin in (
        "PySide6==6.11.2",
        "requests==2.32.5",
        "playwright==1.62.0",
        "Pillow==12.3.0",
        "mutagen==1.47.0",
        "pyinstaller==6.22.2",
    ):
        assert pin in release


def test_third_party_notice_mentions_packaged_media_and_qt_runtime():
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "PySide6 / Qt for Python" in notices
    assert "FFmpeg / FFprobe" in notices
    assert "Playwright for Python" in notices


def test_search_service_private_compatibility_wrappers_are_not_dead_imports():
    source = (ROOT / "audioknigi" / "services" / "search_service.py").read_text(encoding="utf-8")
    assert "def _iter_completed_cancellable" in source
    assert "def _matches_query" in source
    imported_block = source.split("from ..providers.audioknigi_search import (", 1)[1].split(")", 1)[0]
    assert "_iter_completed_cancellable" not in imported_block
    assert "_matches_query" not in imported_block


def test_source_analysis_indentation_is_normalized():
    source = (ROOT / "audioknigi" / "download" / "source_analysis.py").read_text(encoding="utf-8")
    assert '    def _knigavuhe_fallback_candidate(self, book):\n        """' in source


def test_cross_platform_log_home_placeholder_is_not_windows_only():
    source = (ROOT / "audioknigi" / "logging_utils.py").read_text(encoding="utf-8")
    assert 'placeholder = "%USERPROFILE%" if os.name == "nt" else "~"' in source
