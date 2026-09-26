from __future__ import annotations

import json
from pathlib import Path

from audioknigi.config.settings import migrate_settings
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.providers.audioknigi_search import _canonical_title
from audioknigi.services.book_analysis_service import _playlist_track_title


ROOT = Path(__file__).resolve().parents[2]


def test_canonical_audioknigi_title_removes_online_before_or_after_label() -> None:
    assert _canonical_title("Слушать онлайн аудиокнигу Крыса") == "Крыса"
    assert _canonical_title("Слушать аудиокнигу онлайн: Крыса") == "Крыса"
    assert _canonical_title("Аудиокнига онлайн — Крыса") == "Крыса"


def test_playlist_machine_titles_do_not_leak_into_track_table_or_filenames() -> None:
    media = "https://cdn.example/king_Rat_1.mp3"
    assert _playlist_track_title("king_Rat_1, king_Rat_1", media, 1, "Крыса", 2) == "Крыса — 01"
    assert _playlist_track_title("king_Rat_2", "https://cdn.example/king_Rat_2.mp3", 2, "Крыса", 2) == "Крыса — 02"
    assert _playlist_track_title("Глава первая", media, 1, "Крыса", 2) == "Глава первая"


def test_knigavuhe_argument_parser_ignores_commented_out_calls_and_comment_brackets() -> None:
    source = r'''
        // BookController.enter({"wrong": [)]});
        /* BookController.enter({"also": "wrong"}); */
        BookController.enter({"title": "ok", /* ) ] } */ "parts": [1, 2]}, true);
    '''
    value = _extract_call_argument(source)
    assert '"title": "ok"' in value
    assert '"parts": [1, 2]' in value
    assert "wrong" not in value


def test_legacy_normalize_audio_is_migrated_then_removed() -> None:
    settings, changed = migrate_settings({"normalize_audio": True})
    assert changed is True
    assert settings["normalization_mode"] == "single"
    assert "normalize_audio" not in settings


def test_round24_runtime_localization_covers_tray_variants_and_placeholder_style() -> None:
    catalog = json.loads((ROOT / "audioknigi/locales/runtime_exact.json").read_text(encoding="utf-8"))
    assert "Системный трей активен." in catalog
    assert "Системный трей недоступен." in catalog
    placeholder = catalog["Введите название/автора для поиска или вставьте ссылку на поддерживаемый сайт"]
    assert all(not value.endswith(".") for value in placeholder.values())


def test_easy_mode_has_blocking_progress_for_search_analysis_and_download() -> None:
    main = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    dialog = (ROOT / "audioknigi/qt/operation_dialog.py").read_text(encoding="utf-8")
    search = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    analysis = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    assert 'self.current_ui_mode() != "easy"' in main
    assert "Qt.WindowModality.NonModal" in dialog
    assert "central.setEnabled(not blocked)" in main
    assert '_show_blocking_operation(\n            "search"' in search
    assert '_show_blocking_operation(\n            "analysis"' in analysis
    assert '_show_blocking_operation(\n                "download"' in analysis
    assert "cancelRequested" in dialog


def test_missing_media_wait_and_dialog_have_bounded_failure_paths() -> None:
    workers = (ROOT / "audioknigi/qt/workers.py").read_text(encoding="utf-8")
    analysis = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    assert "MISSING_MEDIA_DECISION_TIMEOUT_SECONDS" in workers
    assert 'prompt.resolve("stop")' in workers
    assert "box.finished.connect" in analysis
    assert "box.destroyed.connect" in analysis


def test_network_proxy_and_media_edge_cases_are_hardened() -> None:
    network = (ROOT / "audioknigi/network_dns.py").read_text(encoding="utf-8")
    media = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    assert 'path = quote(path, safe="/:?#[]@!$&\'()*+,;=%")' in network
    assert "except (OSError, ValueError):" in network
    assert "start = int(float(start))" in media
    assert "duration = int(float(duration))" in media


def test_support_bundle_tail_and_path_privacy_cover_reported_boundaries() -> None:
    support = (ROOT / "audioknigi/diagnostics/support_bundle.py").read_text(encoding="utf-8")
    assert "if newline >= 0:" in support
    assert "_EMBEDDED_DRIVE_PATH_RE = re.compile" in support
    assert "_EMBEDDED_UNC_PATH_RE = re.compile" in support
    assert "_WINDOWS_PATH_SEGMENT_RE =" in support and "_WINDOWS_PATH_FINAL_RE =" in support


def test_player_queue_clipboard_and_root_scan_followup_contracts() -> None:
    player_ui = (ROOT / "audioknigi/qt/player_mixin.py").read_text(encoding="utf-8")
    player = (ROOT / "audioknigi/qt/player_controller.py").read_text(encoding="utf-8")
    queue = (ROOT / "audioknigi/qt/mixins/queue.py").read_text(encoding="utf-8")
    clipboard = (ROOT / "audioknigi/qt/mixins/clipboard.py").read_text(encoding="utf-8")
    library = (ROOT / "audioknigi/services/library_service.py").read_text(encoding="utf-8")
    assert "player_chapter_list.itemClicked.connect(self._player_chapter_activated)" in player_ui
    assert "_last_player_chapter_activation" in player_ui
    shutdown = player[player.index("def shutdown"):player.index("@Slot(int)", player.index("def shutdown"))]
    assert shutdown.index("self._save_timer.stop()") < shutdown.index("self.save_position(force=True)") < shutdown.index("self.player.stop()")
    assert 'self._notify_tray_if_hidden(self._l("Очередь завершена."))' in queue
    assert 'value.lower().startswith(("http://", "https://"))' in clipboard
    assert "base_is_filesystem_root" in library and "if depth >= 8:" in library


def test_uncaught_worker_threads_are_captured_in_crash_reports() -> None:
    application = (ROOT / "audioknigi/qt/application.py").read_text(encoding="utf-8")
    workers = (ROOT / "audioknigi/qt/workers.py").read_text(encoding="utf-8")
    assert "threading.excepthook = _thread_exception_hook" in application
    assert 'component=f"python-thread:{thread_name}"' in application
    assert 'app_logger.exception("Qt search worker failed")' in workers
    assert 'app_logger.exception("Qt analysis worker failed")' in workers


def test_playwright_playlist_capture_wait_is_cancellable_and_not_fixed_1500ms() -> None:
    source = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    block_start = source.index("page.goto(url, wait_until=\"domcontentloaded\"")
    block = source[block_start:block_start + 1800]
    assert "for _attempt in range(32):" in block
    assert "page.wait_for_timeout(250)" in block
    assert "self._check_cancel()" in block
    assert "page.wait_for_timeout(1500)" not in block
