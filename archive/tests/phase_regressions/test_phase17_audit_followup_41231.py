from __future__ import annotations

from pathlib import Path
import threading

import pytest

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_dump_mime_label_did_not_replace_real_service_filenames():
    assert (ROOT / "audioknigi/services/queue_service.py").is_file()
    assert (ROOT / "audioknigi/services/search_service.py").is_file()
    assert not list(ROOT.rglob("text/x-python"))


def test_legacy_needs_analysis_task_can_never_be_runnable():
    from audioknigi.services.queue_service import task_from_dict, next_runnable_index, task_requires_analysis

    task = task_from_dict({"url": "https://knigavuhe.org/book/example/", "title": "Legacy"})
    assert task.status_code == "needs_analysis"
    assert task_requires_analysis(task)
    # Even if a UI bug were to rewrite only the status/paused flag, the service gate protects the engine.
    task.status_code = "retry"
    task.paused = False
    assert task_requires_analysis(task)
    assert next_runnable_index([task]) is None


def test_search_dedupe_uses_canonical_supported_url(monkeypatch):
    from audioknigi.models import SearchResult
    import audioknigi.services.search_service as service

    monkeypatch.setattr(
        service,
        "search_audioknigi",
        lambda *_a, **_k: [
            SearchResult(title="A", url="https://audioknigi.com.ua/audio-123/"),
            SearchResult(title="A duplicate", url="https://audioknigi.com.ua/audio-123"),
        ],
    )
    monkeypatch.setattr(service, "search_knigavuhe", lambda *_a, **_k: [])
    monkeypatch.setattr(service, "enrich_knigavuhe_search_variants", lambda rows, **_k: rows)
    monkeypatch.setattr(service, "search_poleknig", lambda *_a, **_k: [])
    outcome = service.search_all_sources("abcd")
    assert len(outcome.results) == 1
    assert outcome.results[0].url == "https://audioknigi.com.ua/audio-123"


def test_audioknigi_known_author_is_not_duplicated_in_title(monkeypatch):
    import audioknigi.services.search_service as service
    from audioknigi.models import SearchResult

    class Response:
        text = "<html><title>Джордж Оруэлл - 1984 аудиокнига</title></html>"
        url = "https://audioknigi.com.ua/audio-123"
        def raise_for_status(self):
            return None

    class Session:
        def get(self, *a, **k):
            return Response()

    monkeypatch.setattr(service, "get_http_session", lambda: Session())
    monkeypatch.setattr(
        service,
        "extract_metadata_from_html",
        lambda *_a, **_k: ("Джордж Оруэлл - 1984", "Джордж Оруэлл", ""),
    )
    monkeypatch.setattr(service, "extract_extended_metadata_from_html", lambda *_a, **_k: ("", "", "", ""))
    row = service._audioknigi_page_metadata(SearchResult(title="1984", author="", url=Response.url))
    assert row.author == "Джордж Оруэлл"
    assert row.title == "1984"


def test_source_candidate_accepts_known_host_with_explicit_port():
    from audioknigi.sources import normalize_supported_url, source_key
    value = normalize_supported_url("audioknigi.com.ua:8080/audio-123/")
    assert value == "https://audioknigi.com.ua:8080/audio-123"
    assert source_key(value) == "audioknigi"


def test_mapping_dataclass_is_a_true_read_only_mapping():
    from collections.abc import Mapping, MutableMapping
    from audioknigi.models import Track
    track = Track(index=1, title="One", file="https://example.test/1.mp3")
    assert isinstance(track, Mapping)
    assert not isinstance(track, MutableMapping)
    assert track["title"] == "One"
    with pytest.raises(TypeError):
        track["title"] = "Two"  # type: ignore[index]


def test_knigavuhe_variant_hydration_has_explicit_cancel_contract():
    source = text("audioknigi/knigavuhe.py")
    assert "def _hydrate_narration_variant_readers(variants: list[NarrationVariant], current_url: str = \"\", cancel_event=None)" in source
    assert "fetch_book(url: str, cancel_event=None)" in source
    assert "cancel_event=cancel_event" in source


def test_book_analysis_passes_cancel_event_to_knigavuhe():
    source = text("audioknigi/services/book_analysis_service.py")
    assert "fetch_knigavuhe_book(normalized, cancel_event=self.cancel_event)" in source


def test_http_pool_is_non_blocking_on_pool_exhaustion():
    source = text("audioknigi/core.py")
    assert "pool_block=False" in source
    assert "pool_block=True" not in source


def test_segment_worker_cancel_does_not_raise_from_parked_daemon_thread():
    source = text("audioknigi/downloader.py")
    start = source.index("        def worker(worker_id):")
    end = source.index("        self.log(", start)
    worker = source[start:end]
    assert 'cancel_event = getattr(self, "cancel_event", None)' in worker
    assert "if cancel_event is not None and cancel_event.is_set():\n                    return" in worker
    assert "if cancel_event.wait(0.10):\n                            return" in worker
    assert "time.sleep(0.10)" in worker
    assert 'raise Cancelled("Операция отменена пользователем.")' not in worker


def test_stage_four_progress_uses_i18n_key():
    source = text("audioknigi/downloader.py")
    assert source.count('"status_checking_progress"') >= 2
    assert 'self.set_stage(4, f"Проверка' not in source


def test_invalid_focus_trace_argument_is_handled_before_qt_creation():
    source = text("audioknigi/qt/application.py")
    parse = source.index("clean_argv, trace_path = extract_focus_trace_argument")
    handler = source.rfind("try:", 0, parse)
    create = source.index("app = create_application(clean_argv, settings=settings)")
    assert handler < parse < create
    assert 'component="qt-arguments"' in source
    assert "return 2" in source[parse:create]


def test_event_sound_language_change_releases_old_players_and_system_beep_is_async():
    source = text("audioknigi/qt/event_sounds.py")
    assert "if new_language != self.language:" in source
    assert "self._stop_players()" in source
    assert "daemon=True" in source
    assert "self._system_sound_queue.put_nowait" in source
    assert "ThreadPoolExecutor" not in source


def test_theme_does_not_depend_on_fusion_object_name_for_reapply_guard():
    source = text("audioknigi/qt/theme.py")
    assert "_APPLIED_STYLE_KEY" in source
    dark = source[source.index('if mode in {"dark", "light"}'):source.index('if _SYSTEM_STYLE_NAME:')]
    assert 'app.style().objectName()' not in dark
    assert '_APPLIED_STYLE_KEY != "fusion"' in dark


def test_queue_ui_reanalyzes_legacy_task_but_blocks_unsafe_resume_pause_priority():
    source = text("audioknigi/qt/main_window.py")
    assert source.count("task_requires_analysis(task)") >= 4
    assert "self._queue_reanalyze_task_id = task.id" in source
    assert "Повторно анализирую импортированную задачу…" in source
    assert "нельзя возобновить без повторного анализа" in source


def test_queue_does_not_call_paused_or_error_remainder_completed():
    source = text("audioknigi/qt/main_window.py")
    start = source.index("    def _start_next_queue_task")
    end = source.index("    @Slot()\n    def pause_queue_current", start)
    body = source[start:end]
    assert "unresolved = [" in body
    assert "Очередь остановлена; остались задачи" in body
    assert "queue_complete" in body  # still used only for truly complete queue


def test_removing_last_queue_row_has_keyboard_focus_fallback():
    source = text("audioknigi/qt/main_window.py")
    start = source.index("    def remove_queue_selected")
    end = source.index("    @staticmethod\n    def _book_supports_full_mp3", start)
    body = source[start:end]
    assert "self.queue_add_url_button.setFocus" in body


def test_output_directory_fields_are_synchronized_for_manual_typing():
    source = text("audioknigi/qt/main_window.py")
    assert "def _wire_output_dir_sync" in source
    assert "edit.textChanged.connect" in source
    assert "for edit in (self.output_edit, self.book_output_edit, self.easy_output_edit)" in source


def test_accessible_announcer_preserves_first_polite_status_and_coalesces_followups():
    source = text("audioknigi/qt/accessibility.py")
    assert "self._latest_pending" in source
    assert "if not self._pending:" in source
    assert "latest = self._latest_pending" in source
    assert "self._timer.start(self.polite_delay_ms)" in source
    assert "max(self.polite_delay_ms, 400)" not in source
