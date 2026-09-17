from __future__ import annotations

import csv
from pathlib import Path

from audioknigi.models import Book
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.library_service import export_history
from audioknigi.services.player_position_store import PlayerPositionStore
from audioknigi.services.queue_service import QueueTask, _track_from_dict, task_to_dict
from audioknigi.services.search_service import _matches_query, parse_audioknigi_results
from audioknigi.poleknig import _tracks_from_playerjs


ROOT = Path(__file__).resolve().parents[1]


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_queue_track_time_fields_are_normalized_from_legacy_strings():
    track = _track_from_dict({
        "index": "7",
        "title": "Chapter",
        "file": "https://example.test/a.mp3",
        "start": "00:01:02.5",
        "end": "",
        "duration": "63.25",
        "actual_duration": None,
    })
    assert track.index == 7
    assert track.start == 62.5
    assert track.end is None
    assert track.duration == 63.25
    assert track.actual_duration is None


def test_queue_serialization_tolerates_mapping_tracks_from_legacy_adapter(tmp_path):
    book = Book(
        url="https://example.test/book",
        title="Book",
        tracks=[{"index": 1, "title": "One", "file": "https://example.test/1.mp3"}],  # type: ignore[list-item]
    )
    task = QueueTask(
        id="x",
        request=DownloadRequest(book=book, selected_indices=[1], output_dir=tmp_path),
        title="Book",
    )
    payload = task_to_dict(task)
    assert payload["request"]["book"]["tracks"][0]["title"] == "One"


def test_audioknigi_query_matching_includes_author_metadata():
    assert _matches_query("Азазель", "Акунин Азазель", author="Борис Акунин")
    assert not _matches_query("Азазель", "Лукьяненко Дозор", author="Борис Акунин")


def test_audioknigi_title_only_search_card_is_not_dropped_by_author_plus_title_query():
    html = '<a href="/audio-123-azazel">Азазель</a>'
    results = parse_audioknigi_results(html, "https://audioknigi.com.ua/", query="Акунин Азазель")
    assert len(results) == 1
    assert results[0].title == "Азазель"


def test_csv_export_quotes_multiline_and_quote_content(tmp_path):
    target = tmp_path / "history.csv"
    export_history([
        {
            "date": "2026-09-10",
            "title": 'Книга "Тест"\nВторая строка',
            "author": "Автор",
            "narrator": "Чтец",
            "genre": "",
            "year": "",
            "parts": 1,
            "folder": "C:/Books/Test",
            "url": "https://example.test/book",
        }
    ], target, "csv")
    raw = target.read_text(encoding="utf-8-sig")
    assert raw.startswith('"date","title"')
    with target.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["title"] == 'Книга "Тест"\nВторая строка'


def test_player_position_store_can_reload_after_backup_replacement(tmp_path):
    state = tmp_path / "positions.json"
    media = tmp_path / "book.mp3"
    media.write_bytes(b"x")
    store = PlayerPositionStore(state)
    store.update(media, 12.0, 100.0)
    state.write_text(
        '{"%s": {"position": 45.0, "duration": 100.0}}' % PlayerPositionStore.key(media).replace('\\', '\\\\'),
        encoding="utf-8",
    )
    store.reload()
    assert store.saved_seconds(media, duration=100.0) == 45.0


def test_poleknig_playerjs_fallback_ignores_non_script_file_text():
    html = '<!-- file: "fake.mp3" --><script>var cfg={file:"real.mp3"};</script>'
    tracks = _tracks_from_playerjs(html, "https://poleknig.com/books/1")
    assert len(tracks) == 1
    assert tracks[0].file.endswith("/books/real.mp3")


def test_windows_media_hotkeys_declare_pointer_sized_ctypes_signatures_and_fallback():
    source = text("audioknigi/qt/media_keys.py")
    assert "RegisterHotKey.argtypes" in source
    assert "UnregisterHotKey.argtypes" in source
    assert "wintypes.HWND" in source
    assert "RegisterHotKey(hwnd, hotkey_id, 0, virtual_key)" in source


def test_accessibility_preserves_explicit_untranslated_dynamic_names():
    source = text("audioknigi/qt/accessibility.py")
    body = source[source.index("def configure_accessible"):source.index("def ensure_accessibility_tree")]
    assert "widget.setAccessibleName(ui_text(language, str(name)))" in body
    assert "localized_name == str(name)" not in body


def test_player_chapter_activation_is_single_and_background_transitions_do_not_steal_focus():
    source = text("audioknigi/qt/player_mixin.py")
    assert "itemActivated.connect(self._player_chapter_activated)" in source
    assert "itemDoubleClicked.connect" not in source
    completed = source[source.index("def _player_completed"):source.index("__all__")]
    assert "activate_ui=False" in completed
    media_switch = source[source.index("def _player_switch_chapter"):source.index("def media_play_pause")]
    assert "activate_ui=False" in media_switch


def test_player_volume_and_rate_update_live_settings_snapshot():
    source = text("audioknigi/qt/player_mixin.py")
    assert 'self.settings["player_volume"] = percent' in source
    assert 'self.settings["player_rate"] = rate' in source


def test_track_model_implements_accessible_description_role_for_rows():
    source = text("audioknigi/qt/track_model.py")
    assert "if role == Qt.ItemDataRole.AccessibleDescriptionRole:" in source
    assert "return self._accessible_row_summary(index.row(), track)" in source
    assert "return str(section + 1)" in source


def test_search_source_filter_is_validated_before_controls_are_disabled():
    source = text("audioknigi/qt/main_window.py")
    body = source[source.index("def start_search"):source.index("def _search_finished")]
    assert body.index("if not sources:") < body.index("self.search_button.setEnabled(False)")
    assert body.index("if not sources:") < body.index("self._set_search_progress(5")


def test_empty_analysis_clears_deferred_download_and_queue_actions():
    source = text("audioknigi/qt/main_window.py")
    body = source[source.index("def _analysis_finished"):source.index("def _clear_analysis_thread")]
    assert "if not enabled:" in body
    empty = body[body.index("if not enabled:"):]
    assert "self._queue_after_analysis = False" in empty
    assert "self._download_after_analysis = False" in empty
    assert "self._queue_reanalyze_task_id = None" in empty


def test_easy_quality_save_maps_to_runtime_codec_preset():
    source = text("audioknigi/qt/main_window.py")
    body = source[source.index("def _settings_from_ui"):source.index("def _save_settings")]
    assert 'if quality_preset == "phone":' in body
    assert 'audio_preset, normalization_mode = "64k_mono", "off"' in body
    assert 'elif quality_preset == "normalize":' in body


def test_queue_and_history_cells_do_not_duplicate_whole_row_summary_as_accessible_text():
    source = text("audioknigi/qt/main_window.py")
    queue = source[source.index("def _refresh_queue"):source.index("def add_current_to_queue")]
    history = source[source.index("def _load_history"):source.index("def _selected_history")]
    assert "accessible_text = row_summary if" not in queue
    assert "accessible_text = row_summary if" not in history
    assert "AccessibleDescriptionRole, row_summary" in queue
    assert "AccessibleDescriptionRole, row_summary" in history


def test_qapplication_selftest_does_not_force_shiboken_singleton_destruction():
    source = text("audioknigi_qt.py")
    body = source[source.index("def _qt_accessibility_selftest"):source.index("def _playwright_edge_selftest")]
    assert "shiboken_delete(app)" not in body
    assert "app.quit()" in body


def test_full_mp3_non_mp3_conversion_requires_resolved_ffmpeg():
    source = text("audioknigi/download_engine.py")
    body = source[source.index("def run_full_mp3"):source.index("__all__")]
    assert 'ffmpeg = resolve_executable("ffmpeg")' in body
    assert 'if ffmpeg is None:' in body
    assert 'FFmpeg не найден. Он необходим для обработки полного файла MP3.' in body


def test_thread_finished_state_is_cleared_before_delete_later_and_shutdown_checks_are_guarded():
    source = text("audioknigi/qt/main_window.py")
    for clear in ("_clear_analysis_thread", "_clear_download_thread", "_clear_search_thread", "_clear_abs_thread"):
        marker = f"thread.finished.connect(self.{clear})"
        pos = source.index(marker)
        delete_pos = source.index("thread.finished.connect(thread.deleteLater)", pos)
        assert pos < delete_pos
    assert "def _thread_is_running(thread) -> bool:" in source
    assert "except RuntimeError:" in source[source.index("def _thread_is_running"):source.index("def _running_exit_threads")]


def test_profile_restore_pauses_and_reloads_player_position_store():
    source = text("audioknigi/qt/main_window.py")
    body = source[source.index("def restore_backup"):source.index("def _wire_output_dir_sync")]
    assert "controller.suspend_position_persistence()" in body
    assert "controller.reload_position_store()" in body
    assert "controller.resume_position_persistence()" in body


def test_application_font_scale_has_native_effective_size_fallback():
    source = text("audioknigi/qt/application.py")
    assert "QFontInfo" in source
    assert "QFontInfo(base_font).pointSizeF()" in source


def test_tray_shutdown_releases_menu_and_action_references():
    source = text("audioknigi/qt/tray_controller.py")
    body = source[source.index("def shutdown"):source.index("__all__")]
    assert "self.icon.setContextMenu(None)" in body
    assert "self.menu.deleteLater()" in body
    assert "self.exit_action = None" in body
