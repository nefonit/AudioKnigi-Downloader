from __future__ import annotations

from pathlib import Path
import threading

import pytest

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_negative_fmt_time_is_clamped_to_zero():
    from audioknigi.core import fmt_time

    assert fmt_time(-5) == "00:00:00"
    assert fmt_time(-3601) == "00:00:00"


def test_shared_source_fallback_clears_stale_source_and_uses_safe_cancel_event():
    source = text("audioknigi/downloader.py")
    start = source.index("except SharedSourceTimelineError as exc:")
    block = source[start:start + 5000]
    assert "self._clear_stale_source_downloads(book)" in block
    assert block.index("self._clear_stale_source_downloads(book)") < block.index("self._knigavuhe_fallback_candidate(book)")
    fallback = source[source.index("def _knigavuhe_fallback_candidate"):source.index("def _recover_short_audioknigi_source", source.index("def _knigavuhe_fallback_candidate"))]
    assert 'cancel_event = getattr(self, "cancel_event", None)' in fallback
    assert "cancel_event=self.cancel_event" not in fallback


def test_full_mp3_preserves_sidecars_abs_history_and_duplicate_contracts():
    source = text("audioknigi/download_engine.py")
    full = source[source.index("def run_full_mp3"):source.index("def run(self)", source.index("def run_full_mp3"))]
    assert "self._save_book_sidecars(" in full
    assert "self._scan_audiobookshelf_after_book()" in full
    assert "self._add_history(book, folder, 1)" in full
    assert "def duplicate_preflight(self, *, full_mp3: bool = False, probe_durations: bool = True)" in source
    assert "def delete_existing_outputs(self, *, full_mp3: bool = False)" in source
    assert "create_folder=False" in source[source.index("def delete_existing_outputs"):source.index("def run_full_mp3")]


def test_duration_error_uses_effective_track_duration():
    source = text("audioknigi/downloader.py")
    assert "fmt_time(effective_track_duration(tr))" in source


def test_knigavuhe_query_matching_normalizes_yo():
    from audioknigi.knigavuhe import _query_matches_metadata

    assert _query_matches_metadata("Фёдор", "Федор и море", "Автор")
    assert _query_matches_metadata("Федор", "Фёдор и море", "Автор")


def test_poleknig_playwright_logger_and_thread_local_sessions_are_present():
    source = text("audioknigi/poleknig.py")
    assert "from .logging_utils import app_logger" in source
    detail = source[source.index("def _candidate_detail_variant"):source.index("def _discover_narration_variants", source.index("def _candidate_detail_variant"))]
    assert "session = get_http_session()" in detail
    assert "def _candidate_detail_variant(_session" not in source
    assert "pool.submit(_candidate_detail_variant, session," not in source
    assert "worker_session = get_http_session()" in source


def test_http_proxy_removes_blank_header_lines_before_connection_close():
    source = text("audioknigi/network_dns.py")
    forward = source[source.index("filtered = []"):source.index("upstream.sendall", source.index("filtered = []"))]
    assert "if not line.strip():" in forward
    assert 'filtered.append(b"Connection: close")' in forward


def test_application_migrates_scale_reuses_qapplication_and_reapplies_onboarding_theme():
    source = text("audioknigi/qt/application.py")
    assert "QApplication.instance()" in source
    assert "migrate_ui_scale_settings(settings)" in source
    assert "base_font.pixelSize()" in source
    wizard_tail = source[source.index("settings = onboarding.result_settings()") : source.index("window = AudioKnigiQtWindow()")]
    assert "apply_theme(app" in wizard_tail


def test_player_does_not_erase_resume_before_resume_is_applied_and_message_localizes():
    source = text("audioknigi/qt/player_controller.py")
    save = source[source.index("def save_position"):source.index("def shutdown", source.index("def save_position"))]
    assert "not self._resume_applied" in save
    assert "localize_runtime_text(" in source
    assert "Файл загружен. Продолжение с сохранённой позиции" in source


def test_context_menu_cleanup_onboarding_accessibility_queue_defaults_and_hidden_dir_prune():
    assert "WA_DeleteOnClose" in text("audioknigi/qt/localized_context_menu.py")
    assert 'self.browse_button.setAccessibleName(ui_text(self._language, "Выбрать папку для аудиокниг"))' in text("audioknigi/qt/onboarding.py")
    queue = text("audioknigi/services/queue_service.py")
    assert 'kwargs.setdefault("url", "")' in queue
    assert 'kwargs.setdefault("title", "—")' in queue
    library = text("audioknigi/services/library_service.py")
    assert 'dirs[:] = [name for name in dirs if not name.startswith(".")]' in library


def test_book_analysis_preflight_recovers_short_shared_source(monkeypatch):
    from audioknigi.models import Book, Track
    from audioknigi.services.book_analysis_service import BookAnalysisService

    service = BookAnalysisService(cancel_event=threading.Event())
    original = Book(
        url="https://audioknigi.com.ua/audio-1-test",
        title="Test",
        tracks=[Track(index=1, title="One", file="https://cdn.example/book.mp3", start=0, end=100)],
    )
    fallback = Book(
        url="https://knigavuhe.org/book/test/",
        title="Test",
        tracks=[Track(index=1, title="One", file="https://cdn.example/one.mp3", duration=100)],
    )
    monkeypatch.setattr(service, "_probe_remote_duration", lambda *_a, **_k: 50.0)
    monkeypatch.setattr(service, "_knigavuhe_fallback_candidate", lambda _book: fallback)
    monkeypatch.setattr(service, "_populate_missing_track_durations", lambda _book: 0)
    assert service._recover_short_audioknigi_source(original) is fallback
    source = text("audioknigi/services/book_analysis_service.py")
    playwright_tail = source[source.index("book = self._analyze_audioknigi_playwright"):source.index("@staticmethod", source.index("book = self._analyze_audioknigi_playwright"))]
    assert "book = self._recover_short_audioknigi_source(book)" in playwright_tail


def test_search_service_honors_explicit_source_filter_and_empty_selection(monkeypatch):
    import audioknigi.services.search_service as service
    from audioknigi.models import SearchResult

    calls = []
    monkeypatch.setattr(service, "search_audioknigi", lambda *_a, **_k: calls.append("a") or [SearchResult("A", "https://audioknigi.com.ua/audio-1-a")])
    monkeypatch.setattr(service, "search_knigavuhe", lambda *_a, **_k: calls.append("k") or [])
    monkeypatch.setattr(service, "enrich_knigavuhe_search_variants", lambda rows, **_k: rows)
    monkeypatch.setattr(service, "search_poleknig", lambda *_a, **_k: calls.append("p") or [])

    outcome = service.search_all_sources("test", sources=["poleknig.com"])
    assert calls == ["p"]
    assert outcome.errors == []

    calls.clear()
    empty = service.search_all_sources("test", sources=[])
    assert calls == []
    assert empty.results == []
    assert empty.errors == ["Не выбран ни один источник поиска"]


def test_search_filters_main_ui_and_quality_localization_hardening_are_wired():
    main = text("audioknigi/qt/main_window.py")
    assert 'self.search_filter_button = QToolButton(page)' in main
    for provider in ("audioknigi.com.ua", "knigavuhe.org", "poleknig.com"):
        assert provider in main
    assert 'self.search_only_available_action = self.search_filter_menu.addAction(self._l("Только доступные"))' in main
    assert 'self.speed_graph.add_speed(0.0)' in main
    assert 'self._l("Папка для аудиокниг")' in main
    assert 'self._l("Остановить загрузку")' in main
    assert 'self._l("Пропустить часть и продолжить")' in main
    assert "self.easy_search_table.setVisible(False)" in main
    assert "def _easy_quality_preset_changed" in main
    assert 'QKeySequence("Shift+F10"), self.history_table' in main
    assert 'QKeySequence("Shift+F10"), self.queue_table' in main


def test_windows_global_media_key_contract_is_background_capable():
    source = text("audioknigi/qt/media_keys.py")
    assert "WM_APPCOMMAND = 0x0319" in source
    assert "WM_HOTKEY = 0x0312" in source
    assert "RegisterHotKey" in source
    assert "UnregisterHotKey" in source
    assert "VK_MEDIA_PLAY_PAUSE" in source
    assert "VK_MEDIA_NEXT_TRACK" in source
    assert "VK_MEDIA_PREV_TRACK" in source
    assert "time.monotonic()" in source
    assert "now - self._last_dispatch_at < 0.18" in source
    main = text("audioknigi/qt/main_window.py")
    player = text("audioknigi/qt/player_mixin.py")
    assert "media_filter.set_global_enabled" in player
    assert "media_filter.shutdown()" in main
    for callback in ("media_play_pause", "media_next_track", "media_previous_track"):
        assert f"def {callback}" in player


def test_main_window_worker_classes_are_extracted_to_dedicated_module():
    main = text("audioknigi/qt/main_window.py")
    workers = text("audioknigi/qt/workers.py")
    assert "class _DownloadWorker" not in main
    assert "class _SearchWorker" not in main
    assert "class DownloadWorker(QObject)" in workers
    assert "class SearchWorker(QObject)" in workers
    assert "class QueueTableWidget(QTableWidget)" in workers
    assert len(main.splitlines()) < 4600
    assert "class PlayerUiMixin" in text("audioknigi/qt/player_mixin.py")


def test_declared_runtime_minimums_make_python38_and_qt65_fallbacks_unnecessary():
    pyproject = text("pyproject.toml")
    assert 'requires-python = ">=3.11"' in pyproject
    assert '"PySide6>=6.8,<7"' in pyproject
