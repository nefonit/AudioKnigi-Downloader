from __future__ import annotations

import json
import re
import threading
import zipfile
from pathlib import Path

from audioknigi.config.settings import AppSettings
from audioknigi.diagnostics import support_bundle
from audioknigi.download.probe import ProbeMixin
from audioknigi.i18n import localize_runtime_text
from audioknigi.knigavuhe import _usable_search_title
from audioknigi.models import Book, Track
from audioknigi.services.book_analysis_service import BookAnalysisService, _playlist_track_title
from audioknigi.services.library_service import _validated_backup_payloads
from audioknigi.services.queue_service import _optional_persisted_bool

ROOT = Path(__file__).resolve().parents[2]


def test_replace_all_partial_mapping_keeps_first_run_semantics_consistent():
    settings = AppSettings({"theme": "dark"})
    settings.replace_all({"theme": "light"})
    assert settings["theme"] == "light"
    assert settings["first_run_complete"] is False


def test_shared_source_timeline_remote_probe_runs_when_local_map_misses_source():
    calls = []

    class Probe(ProbeMixin):
        def _probe_remote_duration(self, source, referer):
            calls.append((source, referer))
            return 120.0

    source = "https://cdn.invalid/shared.mp3"
    book = Book(
        url="https://audioknigi.com.ua/audio-1-demo",
        title="Demo",
        tracks=[
            Track(index=1, title="One", file=source, start=0.0),
            Track(index=2, title="Two", file=source, start=60.0),
        ],
    )
    assert Probe()._shared_source_timeline_issue(book, local_map={}) is None
    assert calls == [(source, book.url)]


def test_split_track_uses_retrying_unlink_before_ffmpeg_overwrite():
    source = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    start = source.index("def _split_track")
    block = source[start:source.index("def _save_book_sidecars", start)]
    assert "unlink_with_retry(out, missing_ok=True)" in block
    assert "out.unlink()" not in block


def test_backup_validation_preserves_all_history_rows(tmp_path):
    rows = [{"title": f"Book {index}"} for index in range(800)]
    archive = tmp_path / "backup.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("history.json", json.dumps(rows, ensure_ascii=False))
    payloads = _validated_backup_payloads(archive)
    assert len(payloads["history.json"]) == 800


def test_short_shared_audioknigi_source_uses_start_markers_when_end_is_missing():
    fallback = Book(
        url="https://knigavuhe.org/book/demo/",
        title="Fallback",
        tracks=[Track(index=1, title="One", file="https://cdn.invalid/fallback.mp3")],
    )

    class Service(BookAnalysisService):
        def _probe_remote_duration(self, _source, _referer):
            return 10.0

        def _knigavuhe_fallback_candidate(self, _book):
            return fallback

        def _populate_missing_track_durations(self, _book):
            return 0

    shared = "https://cdn.invalid/shared.mp3"
    book = Book(
        url="https://audioknigi.com.ua/audio-1-demo",
        title="Demo",
        tracks=[
            Track(index=1, title="One", file=shared, start=0.0),
            Track(index=2, title="Two", file=shared, start=60.0),
        ],
    )
    assert Service(cancel_event=threading.Event())._recover_short_audioknigi_source(book) is fallback


def test_search_parallel_source_status_is_localized():
    source = "Ищу одновременно на источниках: 3"
    assert "Searching across sources simultaneously: 3" == localize_runtime_text("en", source)
    assert "Suche gleichzeitig auf Quellen: 3" == localize_runtime_text("de", source)
    assert "Шукаю одночасно на джерелах: 3" == localize_runtime_text("uk", source)


def test_queue_string_booleans_are_parsed_semantically():
    assert _optional_persisted_bool({"flag": "false"}, "flag") is False
    assert _optional_persisted_bool({"flag": "0"}, "flag") is False
    assert _optional_persisted_bool({"flag": "true"}, "flag") is True
    assert _optional_persisted_bool({"flag": "1"}, "flag") is True
    assert _optional_persisted_bool({"flag": "unknown"}, "flag") is False


def test_playlist_generated_title_width_tracks_total_chapter_count():
    title = _playlist_track_title("", "https://cdn.invalid/track_001.mp3", 1, "Book", 140)
    assert title == "Book — 001"


def test_full_mp3_resume_and_id3_hardening_are_present():
    source = (ROOT / "audioknigi/download_engine.py").read_text(encoding="utf-8")
    run = source[source.index("def run_full_mp3"):source.index("def run(self)")]
    assert "source_ready = source_target.is_file() and source_target.stat().st_size > 0" in run
    assert "Использую уже полностью скачанный исходный аудиофайл книги." in run
    assert 'tags.delall("TRCK")' in run
    assert "duration_tolerance = max(5.0, min(15.0, float(current_duration) * 0.015))" in source


def test_runtime_exact_lookup_precedes_regex_and_static_entries_moved_to_exact():
    source = (ROOT / "audioknigi/i18n.py").read_text(encoding="utf-8")
    assert source.index("exact_entry = _PHASE29_RUNTIME_EXACT.get(raw)") < source.index(
        "for pattern, variants in _PHASE29_RUNTIME_REGEX"
    )
    exact = json.loads((ROOT / "audioknigi/locales/runtime_exact.json").read_text(encoding="utf-8"))
    regex_rows = json.loads((ROOT / "audioknigi/locales/runtime_regex.json").read_text(encoding="utf-8"))
    assert "Анализирую audioknigi.com.ua быстрым HTTP-способом…" in exact
    assert "HTTP-анализ не сработал. Пробую Playwright fallback…" in exact
    patterns = {row[0] for row in regex_rows}
    assert r"^Анализирую audioknigi\.com\.ua быстрым HTTP-способом…$" not in patterns
    assert r"^HTTP-анализ не сработал\. Пробую Playwright fallback…$" not in patterns


def test_knigavuhe_title_validation_accepts_unicode_letters_beyond_handwritten_alphabet():
    assert _usable_search_title("Ґ") is True
    assert _usable_search_title("Ў") is True
    assert _usable_search_title("123 -_ …") is False


def test_easy_mode_recognizes_supported_schemeless_urls_and_reset_clears_focus_flag():
    source = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    update = source[source.index("def _update_easy_action_text"):source.index("def _set_operation_ui_blocked")]
    reset = source[source.index("def _easy_reset_to_initial_state"):source.index("def _easy_user_input_edited")]
    assert 'or valid_site_url(value)' in update
    assert "self._focus_download_after_analysis = False" in reset


def test_player_load_has_single_status_announcement_path_and_menu_has_no_text_arrow():
    player = (ROOT / "audioknigi/qt/player_mixin.py").read_text(encoding="utf-8")
    block = player[player.index("def _load_player_file"):player.index("def _player_path_identity")]
    assert "controller.load(path, autoplay=autoplay)" in block
    assert "self.set_status(" not in block
    pages = (ROOT / "audioknigi/qt/main_window_pages.py").read_text(encoding="utf-8")
    assert 'self.download_menu_button = QPushButton("")' in pages


def test_batch_analysis_errors_continue_and_missing_media_dialog_is_deleted():
    source = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    error_start = source.index('if kind == "error":')
    error_end = source.index("book = payload", error_start)
    error_block = source[error_start:error_end]
    assert "QTimer.singleShot(0, self._queue_next_dropped_url)" in error_block
    assert "self._pending_queue_urls = []" not in error_block
    prompt_start = source.index("def _resolve_missing_media")
    prompt_end = source.index("def _download_request_changed", prompt_start)
    assert "box.deleteLater()" in source[prompt_start:prompt_end]


def test_one_track_download_restores_selection_only_after_worker_finishes_without_announcement():
    clipboard = (ROOT / "audioknigi/qt/mixins/clipboard.py").read_text(encoding="utf-8")
    block = clipboard[clipboard.index("def download_selected_track_only"):clipboard.index("__all__")]
    assert "self._restore_track_selection_after_download = previous_selection" in block
    assert "if not self.start_download():" in block
    analysis = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    assert "restore_selection = getattr(self, \"_restore_track_selection_after_download\", None)" in analysis
    assert "_suppress_track_selection_announcement" in analysis


def test_history_reload_resizes_only_service_columns():
    source = (ROOT / "audioknigi/qt/mixins/history.py").read_text(encoding="utf-8")
    block = source[source.index("def _load_history"):source.index("def _selected_history")]
    assert "resizeColumnsToContents()" not in block
    assert "for column in (0, 1, 5):" in block
    assert "resizeColumnToContents(column)" in block


def test_help_details_are_present_for_all_supported_languages_and_german_style_is_consistent():
    source = (ROOT / "audioknigi/qt/help_center.py").read_text(encoding="utf-8")
    for name in (
        "ROUND55_TOPIC_DETAILS_RU",
        "ROUND55_TOPIC_DETAILS_EN",
        "ROUND55_TOPIC_DETAILS_DE",
        "ROUND55_TOPIC_DETAILS_UK",
    ):
        assert name in source
    assert 'ROUND55_TOPIC_DETAILS.get(self.language, {}).get(key, "")' in source

    messages = json.loads((ROOT / "audioknigi/locales/messages.json").read_text(encoding="utf-8"))
    german = "\n".join(str(value) for value in messages["de"].values())
    assert not re.search(r"\b(?:Du|du|Gib|Füge|Wähle|Klicke|Kopiere|Nutze|Prüfe)\b", german)
    for name in ("runtime_exact.json", "runtime_regex.json", "legacy_literals.json"):
        assert "Wiedergabeliste" not in (ROOT / "audioknigi/locales" / name).read_text(encoding="utf-8")


def test_support_bundle_directory_path_over_redaction_remains_privacy_first():
    value = r"Created directory C:\Audiobooks\Book 1 for narration by reader"
    cleaned = support_bundle._privacy_path(value, collapse_whole_path=False)
    assert cleaned == "Created directory <configured-path>"
    assert "Book 1" not in cleaned
