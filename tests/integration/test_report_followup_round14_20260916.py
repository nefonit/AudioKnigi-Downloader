from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.config.settings import migrate_settings
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.network import _segment_files
from audioknigi.models import SearchResult
import audioknigi.poleknig as poleknig


ROOT = Path(__file__).resolve().parents[2]


def test_legacy_normalize_audio_true_migrates_to_single_pass():
    migrated, changed = migrate_settings({"normalize_audio": True})
    assert changed is True
    assert migrated["normalization_mode"] == "single"


def test_support_bundle_masks_embedded_windows_paths_without_hiding_urls():
    assert _privacy_path(r"Cannot write to C:\Users\Ivan\Music\book.mp3") == "Cannot write to <configured-path>"
    assert _privacy_path(r"Network \\server\share\book.mp3 failed") == "Network <configured-path> failed"
    assert _privacy_path("https://example.test/audio.mp3") == "https://example.test/audio.mp3"


def test_segment_file_discovery_is_literal_for_bracketed_names(tmp_path):
    part = tmp_path / "_source [Reader].mp3.part"
    wanted = [tmp_path / f"{part.name}.seg{i:03d}" for i in range(2)]
    for item in wanted:
        item.write_bytes(b"x")
    (tmp_path / "_source R.mp3.part.seg000").write_bytes(b"x")
    assert sorted(_segment_files(part)) == sorted(wanted)


def test_poleknig_search_does_not_drop_site_ranked_result_for_extra_query_terms(monkeypatch):
    row = SearchResult(
        title="Гарри Поттер и философский камень",
        author="Джоан Роулинг",
        narrator="Иван Иванов",
        url="https://poleknig.com/books/1",
        source="poleknig.com",
    )

    class Response:
        text = "<html></html>"
        url = "https://poleknig.com/?s=test"

    monkeypatch.setattr(poleknig, "_fetch_search_page", lambda *_args, **_kwargs: Response())
    monkeypatch.setattr(poleknig, "_search_last_page", lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(poleknig, "parse_search_results", lambda *_args, **_kwargs: [row])
    monkeypatch.setattr(poleknig, "_hydrate_search_result_info", lambda item: (item, []))
    monkeypatch.setattr(poleknig, "_book_page_author_links", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(poleknig, "_expand_matching_author_catalogs", lambda *_args, **_kwargs: [])

    results = poleknig.search("гарри поттер аудиокнига росмэн")
    assert [item.url for item in results] == [row.url]


def test_poleknig_playwright_exposure_uses_circular_safe_json():
    source = (ROOT / "audioknigi" / "poleknig.py").read_text(encoding="utf-8")
    assert "const safeJson = (value) =>" in source
    assert "if (seen.has(item)) return '[Circular]'" in source
    assert "values.push(JSON.stringify(v))" not in source


def test_probe_cache_retry_is_iterative_not_recursive():
    source = (ROOT / "audioknigi" / "download" / "media.py").read_text(encoding="utf-8")
    block = source[source.index("def _cached_probe_audio_info"):source.index("@staticmethod\n    def _preset_target")]
    assert "while True:" in block
    assert "return self._cached_probe_audio_info(path)" not in block


def test_narration_switch_preserves_selected_chapters_contract():
    source = (ROOT / "audioknigi" / "qt" / "mixins" / "analysis_download.py").read_text(encoding="utf-8")
    assert "self._pending_narration_selected_indices = list(self.track_model.selected_indices())" in source
    assert 'pending_narration_selection = getattr(self, "_pending_narration_selected_indices", None)' in source


def test_player_chapter_activation_does_not_steal_focus_to_play_button():
    source = (ROOT / "audioknigi" / "qt" / "player_mixin.py").read_text(encoding="utf-8")
    block = source[source.index("def _player_chapter_activated"):source.index("def _refresh_player_context")]
    assert "activate_ui=False" in block


def test_invalid_event_sound_player_is_retired_before_fallback():
    source = (ROOT / "audioknigi" / "qt" / "event_sounds.py").read_text(encoding="utf-8")
    block = source[source.index("if status == QMediaPlayer.MediaStatus.InvalidMedia"):]
    assert "self._retire_player(media_key)" in block.split("return", 1)[0]


def test_choose_output_dir_relies_on_debounced_refresh_only():
    source = (ROOT / "audioknigi" / "qt" / "mixins" / "settings.py").read_text(encoding="utf-8")
    block = source[source.index("def _choose_output_dir"):source.index("def _preview_theme")]
    assert "edit.setText(selected)" in block
    assert "self._refresh_unfinished()" not in block


def test_queue_and_history_rows_do_not_duplicate_native_screen_reader_speech():
    queue = (ROOT / "audioknigi" / "qt" / "mixins" / "queue.py").read_text(encoding="utf-8")
    history = (ROOT / "audioknigi" / "qt" / "mixins" / "history.py").read_text(encoding="utf-8")
    qblock = queue[queue.index("def _queue_current_cell_changed"):queue.index("def _update_queue_action_states")]
    hblock = history[history.index("def _history_current_cell_changed"):history.index("def _update_history_action_states")]
    assert "announce(" not in qblock
    assert "announce(" not in hblock
    assert "AccessibleDescriptionRole" in queue
    assert "AccessibleDescriptionRole" in history


def test_media_key_unregister_keeps_pointer_sized_hwnd_conversion():
    source = (ROOT / "audioknigi" / "qt" / "media_keys.py").read_text(encoding="utf-8")
    block = source[source.index("def unregister_global_hotkeys"):source.index("def shutdown")]
    assert "ctypes.c_void_p(self._hwnd or 0).value" in block


def test_sidecar_metadata_uses_mapping_safe_track_fields():
    source = (ROOT / "audioknigi" / "download_engine.py").read_text(encoding="utf-8")
    block = source[source.index("def _sidecar_metadata_matches_book"):source.index("def _full_mp3_target")]
    assert 'self._book_field(track, "index", -1)' in block
    assert 'self._book_field(track, "title", "")' in block
