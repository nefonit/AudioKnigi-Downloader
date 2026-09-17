from __future__ import annotations

import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase37_stage_marker_is_current():
    assert 'QT_MIGRATION_STAGE = "phase-39"' in text("audioknigi/qt/__init__.py")


def test_downloader_parallel_split_uses_checked_local_source_lookup_and_loudnorm_map_guard():
    source = text("audioknigi/downloader.py")
    assert "def local_source_for(source_url):" in source
    assert "src = local_map.get(source_url)" in source
    assert "Локальный исходник для нарезки не найден" in source
    assert 'if not str(map_label or "").strip():' in source
    assert "filter_complex требует явный map_label" in source


def test_active_response_cancel_snapshot_is_claimed_only_once_and_zero_progress_backs_off():
    source = text("audioknigi/downloader.py")
    cancel = source[source.index("def _cancel_active_network_io"):source.index("def _get_bandwidth_limiter", source.index("def _cancel_active_network_io"))]
    assert "responses.difference_update(active)" in cancel
    segment = source[source.index("def _download_segment"):source.index("def _download_segmented")]
    assert "def wait_before_retry()" in segment
    assert "cancel_event.wait(delay)" in segment
    assert "wait_before_retry()" in segment


def test_ffprobe_cleanup_explicitly_closes_subprocess_pipes():
    downloader = text("audioknigi/downloader.py")
    analysis = text("audioknigi/services/book_analysis_service.py")
    assert "def _close_subprocess_pipes(proc)" in downloader
    assert downloader.count("_close_subprocess_pipes(proc)") >= 2
    assert 'for stream_name in ("stdin", "stdout", "stderr")' in analysis


def test_poleknig_read_url_is_supported_and_canonicalized():
    from audioknigi.sources import is_supported_url, normalize_supported_url

    raw = "https://poleknig.com/books/12345-test-book/read"
    assert is_supported_url(raw)
    assert normalize_supported_url(raw) == "https://poleknig.com/books/12345"


def test_dns_bypasses_private_names_and_cache_is_bounded():
    from audioknigi import network_dns

    assert network_dns._bypass_cloudflare("nas")
    assert network_dns._bypass_cloudflare("audiobookshelf.lan")
    assert network_dns._bypass_cloudflare("server.internal")
    assert not network_dns._bypass_cloudflare("poleknig.com")
    assert network_dns._CACHE_MAX == 512
    source = text("audioknigi/network_dns.py")
    assert "while len(_CACHE) >= _CACHE_MAX" in source


def test_search_cancel_is_propagated_not_returned_as_partial_success():
    from audioknigi.core import Cancelled
    from audioknigi.services.search_service import search_all_sources

    event = threading.Event()
    event.set()
    with pytest.raises(Cancelled):
        search_all_sources("сталкер", cancel_event=event, sources=["poleknig.com"])


def test_knigavuhe_metadata_matching_includes_narrator_and_yo_normalization():
    from audioknigi.knigavuhe import _query_matches_metadata

    assert _query_matches_metadata("Клюквин", "Книга", "Автор", "Александр Клюквин")
    assert _query_matches_metadata("Фёдор", "Федор и море", "", "")


def test_queue_track_index_is_coerced_and_legacy_task_preserves_identity():
    from audioknigi.services.queue_service import _track_from_dict, task_from_dict

    track = _track_from_dict({"index": "7", "title": "Глава", "file": "https://example.test/a.mp3"})
    assert track.index == 7
    task = task_from_dict({
        "url": "https://poleknig.com/books/123",
        "title": "Книга",
        "author": "Автор",
        "narrator": "Чтец",
    })
    assert task.status_code == "needs_analysis"
    assert task.request.book.author == "Автор"
    assert task.request.book.narrator == "Чтец"
    assert "Повторить" in task.last_error


def test_legacy_queue_retry_starts_automatic_analysis_instead_of_dead_end():
    source = text("audioknigi/qt/main_window.py")
    retry = source[source.index("def retry_queue_selected"):source.index("def toggle_queue_priority")]
    assert "if task_requires_analysis(task):" in retry
    assert "self._queue_reanalyze_task_id = task.id" in retry
    assert "self.start_analysis()" in retry
    assert "Повторно анализирую импортированную задачу…" in retry


def test_player_store_treats_sub_three_second_position_as_start(tmp_path):
    from audioknigi.services.player_position_store import PlayerPositionStore

    media = tmp_path / "part.mp3"
    store = PlayerPositionStore(tmp_path / "positions.json")
    key = store.key(media)
    store._positions[key] = {"position": 2.5, "duration": 100.0}
    assert store.saved_seconds(media, duration=100.0) == 0.0


def test_player_resume_waits_until_backend_is_seekable():
    source = text("audioknigi/qt/player_controller.py")
    assert "if self._pending_resume_ms > 0 and not bool(self.player.isSeekable()):" in source
    assert "self.player.seekableChanged.connect(self._on_seekable_changed)" in source
    assert "if seekable and self.current_path is not None and not self._resume_applied:" in source


def test_exit_never_calls_qthread_terminate_and_uses_single_guarded_poll():
    source = text("audioknigi/qt/main_window.py")
    body = source[source.index("def _force_stop_workers_for_exit"):source.index("__all__")]
    assert "thread.terminate()" not in body
    assert "QTimer.singleShot(_EXIT_POLL_MS, self._poll_deferred_exit)" in body
    assert "if self._exit_poll_scheduled:" in body
    assert "os._exit(0)" in body


def test_native_ctrl_tab_is_not_double_registered():
    source = text("audioknigi/qt/main_window.py")
    shortcuts = source[source.index("def _install_shortcuts"):source.index("def _cycle_tab")]
    assert 'QKeySequence("Ctrl+Tab")' not in shortcuts
    assert 'QKeySequence("Ctrl+Shift+Tab")' not in shortcuts
    assert "QTabWidget already implements Ctrl+Tab" in shortcuts


def test_mass_queue_history_updates_block_signals_and_limit_resize_precision():
    source = text("audioknigi/qt/main_window.py")
    assert "QSignalBlocker(self.queue_table)" in source
    assert "QSignalBlocker(self.history_table)" in source
    assert source.count("setResizeContentsPrecision(60)") >= 4


def test_system_theme_uses_palette_sensitive_onboarding_contrast():
    source = text("audioknigi/qt/theme.py")
    assert "system_dark" in source
    assert 'onboarding_muted = "#aab2bf" if system_dark else "#566273"' in source
    assert 'border = "palette(mid)"' in source


def test_direct_accessibility_announcements_are_rate_limited():
    source = text("audioknigi/qt/accessibility.py")
    assert "_DIRECT_ANNOUNCE_LOCK" in source
    assert "now - _DIRECT_ANNOUNCE_LAST_AT < 0.06" in source
    assert "text == _DIRECT_ANNOUNCE_LAST_TEXT" in source


def test_event_sound_media_player_cache_is_bounded():
    source = text("audioknigi/qt/event_sounds.py")
    assert "_MAX_CACHED_MEDIA_PLAYERS = 3" in source
    assert "while len(self._players) >= _MAX_CACHED_MEDIA_PLAYERS" in source
    assert "def _retire_player" in source


def test_localized_context_menu_uses_weak_widget_reference():
    source = text("audioknigi/qt/localized_context_menu.py")
    assert "widget_ref = weakref.ref(widget)" in source
    assert "current = widget_ref()" in source
    assert "lambda pos, current=widget" not in source


def test_search_progress_timer_stops_when_hidden():
    source = text("audioknigi/qt/search_progress.py")
    assert "def hideEvent" in source
    assert "self._timer.stop()" in source
    assert "def showEvent" in source


def test_phase37_new_runtime_messages_are_localized():
    from audioknigi.i18n import localize_runtime_text

    values = [
        "Повторно анализирую импортированную задачу…",
        "Плейлист найден через Playwright fallback.",
        "Анализ выполнен через requests (Chromium не запускался).",
        "Ссылка полного аудиофайла устарела. Обновляю страницу и плейлист один раз…",
    ]
    for language in ("uk", "de", "en"):
        for value in values:
            assert localize_runtime_text(language, value) != value
