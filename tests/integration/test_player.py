"""Consolidated integration tests for the player domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


from datetime import datetime
import json
from pathlib import Path
import socket
import threading
import pytest
from audioknigi.core import Cancelled
from audioknigi.diagnostics.support_bundle import _privacy_path, _sanitize_setting_value
from audioknigi.network_dns import _read_http_head
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata, _looks_like_author_prefix, _same_author_identity
from audioknigi.services.book_analysis_service import _playlist_track_title
from audioknigi.services.player_position_store import PlayerPositionStore
import os
from audioknigi.diagnostics import support_bundle as support_bundle__recovery_diagnostics_hardening_20260912
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _hydrate_search_result_titles
from audioknigi.models import SearchResult
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.library_service import scan_unfinished
from audioknigi.core import _first_json_ld
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
import csv
import zipfile
from types import SimpleNamespace
from audioknigi.config.settings import migrate_settings
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.network import _segment_files
import audioknigi.poleknig as poleknig__report_followup_round14_20260916
import base64
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.common import atomic_write_text
from audioknigi.i18n import localize_runtime_text
from audioknigi.services.queue_service import task_from_dict
from audioknigi.core import _walk_json
from audioknigi.download.common import replace_with_retry
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services import library_service
from audioknigi import knigavuhe, poleknig as poleknig__report_followup_round20_20260917
from audioknigi.core import fmt_eta, parse_time_seconds
from audioknigi.download.probe import ProbeMixin
from audioknigi.models import Book, SearchResult
from audioknigi.providers import audioknigi_search as search_module
from audioknigi.services.queue_service import _parse_selected_indices_payload
from audioknigi import core as core__report_followup_round21_20260917, knigavuhe, poleknig as poleknig__report_followup_round21_20260917
from audioknigi.diagnostics.support_bundle import create_support_bundle
from audioknigi.download_engine import _DownloadEngine
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.providers.audioknigi_search import _canonical_title
from audioknigi.core import Cancelled, load_json
from audioknigi.templates import template_values
from audioknigi.models import Book, Track
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi.services.download_request import DownloadRequest
import time
import audioknigi.config.settings as settings_module
import audioknigi.core as core__report_followup_round44_20260920
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round44_20260920
import audioknigi.services.player_position_store as position_module
from audioknigi.models import Book
from audioknigi.providers.audioknigi_search import _matches_query, _response_html_text, parse_audioknigi_results
from audioknigi.services.queue_service import _book_to_dict
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round45_20260921
from audioknigi.download.errors import SharedSourceTimelineError
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.poleknig import _parse_playlist_objects
from audioknigi.providers.audioknigi_search import parse_audioknigi_results
from audioknigi.models import Book, Track, TRACK_STATUS_READY
from audioknigi.providers.audioknigi_search import _response_html_text
from audioknigi.config.settings import AppSettings
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, _DownloadEngine
from audioknigi.models import Book, SearchResult, Track
from audioknigi.providers import audioknigi_search
import re
from audioknigi.diagnostics import support_bundle as support_bundle__round73_runtime_followup_20261002
from audioknigi.knigavuhe import _usable_search_title
from audioknigi.services.book_analysis_service import BookAnalysisService, _playlist_track_title
from audioknigi.services.library_service import _validated_backup_payloads
from audioknigi.services.queue_service import _optional_persisted_bool
from audioknigi.core import safe_name
from audioknigi.knigavuhe import _extract_narration_variants
from audioknigi.services import book_analysis_service as analysis_module
from threading import Event
from audioknigi.download_engine import DownloadService
from audioknigi.i18n import tr
from audioknigi.providers.audioknigi_search import search_audioknigi
from audioknigi.services.download_request import DownloadRequest, build_download_request
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict
from audioknigi.download.network import SlidingSpeedMeter
from audioknigi.models import Book, SearchResult, TRACK_STATUS_DAMAGED, TRACK_STATUS_MISSING, TRACK_STATUS_PRESENT, TRACK_STATUS_READY, normalize_track_status
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
import types
from audioknigi.diagnostics import support_bundle as support_bundle__runtime_integrity_followup_20260912
from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.sources import normalize_supported_url
from audioknigi.config import normalize_settings
from audioknigi.services.download_request import build_download_request
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict


# Origin: test_external_review_hardening_20260928.py
ROOT = Path(__file__).resolve().parents[2]

def test_player_position_timestamp_is_timezone_aware(tmp_path):
    store = PlayerPositionStore(tmp_path / 'positions.json')
    audio = tmp_path / 'chapter.mp3'
    audio.write_bytes(b'x')
    assert store.update(audio, 10.0, 100.0, persist=False)
    record = next(iter(store.snapshot().values()))
    parsed = datetime.fromisoformat(str(record['updated']))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() is not None


# Origin: test_recovery_diagnostics_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_refactored_network_and_playerjs_hot_paths_are_not_semicolon_compressed():
    network = (ROOT / 'audioknigi' / 'download' / 'network.py').read_text(encoding='utf-8')
    pole = (ROOT / 'audioknigi' / 'poleknig.py').read_text(encoding='utf-8')
    network_head = network[:network.index('class NetworkDownloadMixin:')]
    playerjs = pole[pole.index('def _iter_js_object_literals'):pole.index('def _normalize_js_literals_for_python')]
    assert ';' not in network_head
    assert ';' not in playerjs


# Origin: test_report_followup_round11_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_round11_clipboard_guards_is_file_inside_try():
    source = (ROOT / 'audioknigi/qt/mixins/clipboard.py').read_text(encoding='utf-8')
    block = source[source.index('if path.suffix.lower() == ".url":'):source.index('if value and value not in out:')]
    assert 'try:' in block
    assert 'if not path.is_file():' in block
    assert 'except (OSError, ValueError):' in block


# Origin: test_report_followup_round13_20260916.py
def test_player_position_uses_saved_duration_when_runtime_duration_unknown(tmp_path):
    from audioknigi.services.player_position_store import PlayerPositionStore
    media = tmp_path / 'chapter.mp3'
    media.write_bytes(b'x')
    store_path = tmp_path / 'positions.json'
    key = PlayerPositionStore.key(media)
    store_path.write_text(json.dumps({key: {'position': 99.5, 'duration': 100.0, 'file': media.name}}), encoding='utf-8')
    store = PlayerPositionStore(store_path)
    assert store.saved_seconds(media) == 0.0


# Origin: test_report_followup_round14_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_invalid_event_sound_player_is_retired_before_fallback():
    source = (ROOT / 'audioknigi' / 'qt' / 'event_sounds.py').read_text(encoding='utf-8')
    block = source[source.index('if status == QMediaPlayer.MediaStatus.InvalidMedia'):]
    assert 'self._retire_player(media_key)' in block.split('return', 1)[0]

def test_media_key_unregister_keeps_pointer_sized_hwnd_conversion():
    source = (ROOT / 'audioknigi' / 'qt' / 'media_keys.py').read_text(encoding='utf-8')
    block = source[source.index('def unregister_global_hotkeys'):source.index('def shutdown')]
    assert 'ctypes.c_void_p(self._hwnd or 0).value' in block


# Origin: test_report_followup_round15_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_clipboard_suppression_compares_canonical_supported_urls():
    source = (ROOT / 'audioknigi/qt/mixins/clipboard.py').read_text(encoding='utf-8')
    block = source[source.index('suppress = str(self._suppress_clipboard_prompt_text'):]
    assert 'same_clipboard_url = text == suppress' in block
    assert 'normalize_supported_url(text) == normalize_supported_url(suppress)' in block


# Origin: test_report_followup_round18_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_round18_full_mp3_history_and_event_sound_hardening_contracts() -> None:
    engine = (ROOT / 'audioknigi/download_engine.py').read_text(encoding='utf-8')
    sounds = (ROOT / 'audioknigi/qt/event_sounds.py').read_text(encoding='utf-8')
    assert 'history_saved = bool(save_json(HISTORY_FILE' in engine
    assert 'replace_with_retry(source_target, target)' in engine
    assert 'replace_with_retry(source_target, retained)' in engine
    assert sounds.count('player.setAudioOutput(None)') >= 2

def test_round18_media_key_registration_rechecks_native_window_handle() -> None:
    source = (ROOT / 'audioknigi/qt/media_keys.py').read_text(encoding='utf-8')
    assert 'new_hwnd = int(pointer_value)' in source
    assert 'self._hwnd == new_hwnd' in source
    assert 'self._hwnd != new_hwnd' in source


# Origin: test_report_followup_round20_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_history_player_and_parallel_progress_contracts_are_stable() -> None:
    history = (ROOT / 'audioknigi/qt/mixins/history.py').read_text(encoding='utf-8')
    listen = history.split('def history_listen', 1)[1].split('def history_open_folder', 1)[0]
    assert 'self.set_ui_mode("advanced", persist=False)' in listen
    flow = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    assert 'self._suppress_source_transfer_ui = True' in flow
    assert 'self.set_progress(pos * 100 / max(1, len(download_jobs)))' in flow
    network = (ROOT / 'audioknigi/download/network.py').read_text(encoding='utf-8')
    assert network.count('_suppress_source_transfer_ui') >= 4


# Origin: test_report_followup_round21_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_player_position_store_rejects_empty_media_path(tmp_path) -> None:
    store_path = tmp_path / 'positions.json'
    store = PlayerPositionStore(store_path)
    assert PlayerPositionStore.key('') == ''
    assert store.saved_seconds('') == 0.0
    assert store.update('', 120.0, 600.0) is False
    assert store.clear('') is False
    assert store.snapshot() == {}
    assert not store_path.exists()


# Origin: test_report_followup_round24_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_player_queue_clipboard_and_root_scan_followup_contracts() -> None:
    player_ui = (ROOT / 'audioknigi/qt/player_mixin.py').read_text(encoding='utf-8')
    player = (ROOT / 'audioknigi/qt/player_controller.py').read_text(encoding='utf-8')
    queue = (ROOT / 'audioknigi/qt/mixins/queue.py').read_text(encoding='utf-8')
    clipboard = (ROOT / 'audioknigi/qt/mixins/clipboard.py').read_text(encoding='utf-8')
    library = (ROOT / 'audioknigi/services/library_service.py').read_text(encoding='utf-8')
    assert 'player_chapter_list.itemClicked.connect(self._player_chapter_activated)' in player_ui
    assert '_last_player_chapter_activation' in player_ui
    shutdown = player[player.index('def shutdown'):player.index('@Slot(int)', player.index('def shutdown'))]
    assert shutdown.index('self._save_timer.stop()') < shutdown.index('self.save_position(force=True)') < shutdown.index('self.player.stop()')
    assert 'self._notify_tray_if_hidden(self._l("Очередь завершена."))' in queue
    assert 'value.lower().startswith(("http://", "https://"))' in clipboard
    assert 'base_is_filesystem_root' in library and 'if depth >= 8:' in library


# Origin: test_report_followup_round32_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round32_20260918(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

def test_analysis_refreshes_player_button_after_model_reset() -> None:
    source = src__report_followup_round32_20260918('audioknigi/qt/mixins/analysis_download.py')
    assert 'self.track_model.set_book(book)\n        self._update_selected_track_player_button()' in source
    finish = source[source.index('def _download_finished'):source.index('def _clear_download_thread')]
    assert 'self.track_model.set_book(self.current_book)' in finish
    assert 'self._update_selected_track_player_button()' in finish
    assert finish.index('self.track_model.set_book(self.current_book)') < finish.index('self._update_selected_track_player_button()')


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_opening_player_from_easy_mode_reveals_advanced_player_tab() -> None:
    source = src__report_followup_round34_20260919('audioknigi/qt/player_mixin.py')
    block = source[source.index('def _load_player_file'):source.index('@staticmethod', source.index('def _load_player_file'))]
    assert 'if self.current_ui_mode() == "easy":' in block
    assert 'self.set_ui_mode("advanced")' in block


# Origin: test_report_followup_round39_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round39_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_player_card_is_wider_and_more_comfortable_for_production_layout() -> None:
    source = src__report_followup_round39_20260919('audioknigi/qt/player_mixin.py')
    assert 'card.setMaximumWidth(1180)' in source
    assert 'card_layout.setContentsMargins(24, 24, 24, 24)' in source
    assert 'self.player_chapter_list.setMinimumHeight(150)' in source


# Origin: test_report_followup_round41_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round41_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_settings_and_player_remain_centered_form_cards() -> None:
    pages = src__report_followup_round41_20260920('audioknigi/qt/main_window_pages.py')
    player = src__report_followup_round41_20260920('audioknigi/qt/player_mixin.py')
    theme = src__report_followup_round41_20260920('audioknigi/qt/theme.py')
    assert 'settings_card.setObjectName("settingsCard")' in pages
    assert 'settings_card.setMaximumWidth(1180)' in pages
    assert 'center.addStretch(1)' in pages
    assert 'card.setObjectName("playerCard")' in player
    assert 'card.setMaximumWidth(1180)' in player
    assert 'QWidget#easyCard, QWidget#playerCard, QWidget#settingsCard' in theme


# Origin: test_report_followup_round44_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round44_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_player_position_store_preserves_write_order_without_blocking_state_reads(monkeypatch, tmp_path) -> None:
    writes: list[float] = []
    first_started = threading.Event()
    release_first = threading.Event()

    def fake_load_json(_path, default):
        return dict(default)

    def fake_save_json(_path, payload):
        position = float(next(iter(payload.values()))['position'])
        if position == 10.0:
            first_started.set()
            assert release_first.wait(timeout=2.0)
        writes.append(position)
        return True
    monkeypatch.setattr(position_module, 'load_json', fake_load_json)
    monkeypatch.setattr(position_module, 'save_json', fake_save_json)
    store = PlayerPositionStore(tmp_path / 'positions.json')
    media = tmp_path / 'book.mp3'
    first = threading.Thread(target=lambda: store.update(media, 10.0, 100.0))
    second = threading.Thread(target=lambda: store.update(media, 20.0, 100.0))
    first.start()
    assert first_started.wait(timeout=2.0)
    second.start()
    deadline = time.monotonic() + 1.0
    while store.saved_seconds(media, duration=100.0) != 20.0 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert store.saved_seconds(media, duration=100.0) == 20.0
    release_first.set()
    first.join(timeout=2.0)
    second.join(timeout=2.0)
    assert not first.is_alive() and (not second.is_alive())
    assert writes[-1] == 20.0

def test_player_persists_recent_seek_target_when_backend_position_is_stale() -> None:
    source = src__report_followup_round44_20260920('audioknigi/qt/player_controller.py')
    assert 'def _position_for_persistence_ms' in source
    assert 'self._last_seek_target_ms = target' in source
    stop_start = source.index('def stop(self)')
    stop_end = source.index('def seek(self', stop_start)
    stop_block = source[stop_start:stop_end]
    assert 'position = self._position_for_persistence_ms()' in stop_block
    assert 'explicit_seconds=position / 1000.0' in stop_block


# Origin: test_report_followup_round45_20260921.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round45_20260921(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_player_position_store_keeps_state_reads_live_while_disk_write_is_blocked(monkeypatch, tmp_path) -> None:
    writes: list[float] = []
    first_started = threading.Event()
    release_first = threading.Event()
    monkeypatch.setattr(position_module, 'load_json', lambda _path, default: dict(default))

    def fake_save_json(_path, payload):
        position = float(next(iter(payload.values()))['position'])
        if position == 10.0:
            first_started.set()
            assert release_first.wait(timeout=2.0)
        writes.append(position)
        return True
    monkeypatch.setattr(position_module, 'save_json', fake_save_json)
    media = tmp_path / 'book.mp3'
    store = PlayerPositionStore(tmp_path / 'positions.json')
    first = threading.Thread(target=lambda: store.update(media, 10.0, 100.0))
    second = threading.Thread(target=lambda: store.update(media, 20.0, 100.0))
    first.start()
    assert first_started.wait(timeout=2.0)
    second.start()
    deadline = time.monotonic() + 1.0
    while store.saved_seconds(media, duration=100.0) != 20.0 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert store.saved_seconds(media, duration=100.0) == 20.0
    assert first.is_alive()
    release_first.set()
    first.join(timeout=2.0)
    second.join(timeout=2.0)
    assert not first.is_alive() and (not second.is_alive())
    assert writes[-1] == 20.0

class _SplitDummy(MediaProcessingMixin):

    def __init__(self, target: Path):
        self.target = target

    def _track_path(self, _book, _track):
        return self.target

    def log(self, _message):
        pass

def test_media_key_shutdown_guards_zero_hwnd_before_ctypes_conversion() -> None:
    source = src__report_followup_round45_20260921('audioknigi/qt/media_keys.py')
    start = source.index('def unregister_global_hotkeys')
    end = source.index('def shutdown', start)
    block = source[start:end]
    assert 'if not self._hwnd:' in block
    assert block.index('if not self._hwnd:') < block.index('ctypes.c_void_p(self._hwnd or 0).value')

def test_player_controller_can_unload_current_windows_file_and_ui_handles_empty_source() -> None:
    controller = src__report_followup_round45_20260921('audioknigi/qt/player_controller.py')
    assert 'def unload(self, *, save_position: bool = True)' in controller
    assert 'self.player.setSource(QUrl())' in controller
    assert 'self.sourceChanged.emit("")' in controller
    assert 'def unload_if_path' in controller
    mixin = src__report_followup_round45_20260921('audioknigi/qt/player_mixin.py')
    start = mixin.index('def _player_source_changed')
    end = mixin.index('def _player_position_changed', start)
    block = mixin[start:end]
    assert 'if not source_text:' in block
    assert 'button.setEnabled(False)' in block
    assert 'self.player_seek_slider.setEnabled(False)' in block


# Origin: test_round62_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_player_position_keys_preserve_case_on_posix(tmp_path):
    upper = tmp_path / 'Track.mp3'
    lower = tmp_path / 'track.mp3'
    upper.write_bytes(b'A')
    lower.write_bytes(b'B')
    if os.name == 'nt':
        pytest.skip('Windows intentionally normalizes case')
    assert PlayerPositionStore.key(upper) != PlayerPositionStore.key(lower)


# Origin: test_round70_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_player_position_reload_serializes_against_disk_persistence(tmp_path):
    path = tmp_path / 'positions.json'
    path.write_text(json.dumps({'a': {'position': 10.0}}), encoding='utf-8')
    store = PlayerPositionStore(path)
    events = []

    class TrackingLock:

        def __enter__(self):
            events.append('persist-enter')
            return self

        def __exit__(self, *_args):
            events.append('persist-exit')
            return False
    store._persist_lock = TrackingLock()
    store.reload()
    assert events == ['persist-enter', 'persist-exit']

def _full_mp3_engine(tmp_path, *, selected):
    tracks = [Track(index=1, title='One', file='https://cdn.invalid/book.mp3', duration=60.0), Track(index=2, title='Two', file='https://cdn.invalid/book.mp3', duration=60.0)]
    book = Book(url='https://audioknigi.com.ua/audio-1-demo', title='Demo', tracks=tracks, remote_size=7)
    request = DownloadRequest(book=book, selected_indices=list(selected), output_dir=tmp_path)
    engine = _DownloadEngine(request, {'delete_source': True, 'embed_tags': False, 'save_sidecars': False, 'audio_preset': 'copy'}, threading.Event(), DownloadCallbacks())
    engine._write_resume_manifest = lambda *_args, **_kwargs: None
    engine._disk_free_for_path = lambda _path: 10 ** 9
    engine._download_source_with_fallback = lambda _url, _fallback, target, _referer: Path(target).write_bytes(b'mp3data')
    engine._cached_probe_audio_info = lambda _path: {'codec': 'mp3', 'bit_rate': 128000}
    engine._effective_mp3_profile = lambda _path: (True, None, None)
    engine._save_book_sidecars = lambda *_args, **_kwargs: None
    engine._scan_audiobookshelf_after_book = lambda *_args, **_kwargs: None
    engine._add_history = lambda *_args, **_kwargs: None
    engine._remove_resume_manifest = lambda *_args, **_kwargs: None
    return engine

def test_player_accepts_webp_sidecar_cover_and_search_progress_rejects_tiny_rects():
    player = (ROOT / 'audioknigi/qt/player_mixin.py').read_text(encoding='utf-8')
    assert '"cover.webp"' in player
    assert '"folder.webp"' in player
    assert '"front.webp"' in player
    progress = (ROOT / 'audioknigi/qt/search_progress.py').read_text(encoding='utf-8')
    start = progress.index('def paintEvent')
    block = progress[start:progress.index('__all__', start)]
    assert 'if side < 16:' in block
    assert block.index('if side < 16:') < block.index('QPainter(self)')


# Origin: test_round71_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_clipboard_prompt_compares_canonical_supported_urls():
    source = (ROOT / 'audioknigi/qt/mixins/clipboard.py').read_text(encoding='utf-8')
    start = source.index('def _check_clipboard_for_book_link')
    end = source.index('def _insert_clipboard_book_link', start) if 'def _insert_clipboard_book_link' in source[start + 1:] else len(source)
    block = source[start:end]
    assert 'normalized_clipboard = normalize_supported_url(text)' in block
    assert 'normalize_supported_url(value) if valid_site_url(value) else value' in block
    assert 'if normalized_clipboard in normalized_current_values:' in block


# Origin: test_round73_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_player_load_has_single_status_announcement_path_and_menu_has_no_text_arrow():
    player = (ROOT / 'audioknigi/qt/player_mixin.py').read_text(encoding='utf-8')
    block = player[player.index('def _load_player_file'):player.index('def _player_path_identity')]
    assert 'controller.load(path, autoplay=autoplay)' in block
    assert 'self.set_status(' not in block
    pages = (ROOT / 'audioknigi/qt/main_window_pages.py').read_text(encoding='utf-8')
    assert 'self.download_menu_button = QPushButton("")' in pages


# Origin: test_round78_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_existing_proxy_media_filter_folder_and_volume_guards_remain_present():
    core = (ROOT / 'audioknigi/core.py').read_text(encoding='utf-8')
    health = (ROOT / 'audioknigi/services/source_health_service.py').read_text(encoding='utf-8')
    lifecycle = (ROOT / 'audioknigi/qt/mixins/lifecycle.py').read_text(encoding='utf-8')
    settings = (ROOT / 'audioknigi/qt/mixins/settings.py').read_text(encoding='utf-8')
    accessibility = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'session.trust_env = False' in core
    assert 'session.trust_env = False' in health
    assert 'app.removeNativeEventFilter(media_filter)' in lifecycle
    assert 'def _choose_output_dir(self, _checked=False, *, target=None):' in settings
    assert 'self.event_sound_manager.configure(volume=percent / 100.0)' in accessibility


# Origin: test_runtime_contract_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def _book() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3'), Track(index=2, title='Two', file='https://cdn.invalid/2.mp3')])

def test_player_persistence_accepts_mutable_mapping_settings():
    source = (ROOT / 'audioknigi' / 'qt' / 'player_mixin.py').read_text(encoding='utf-8')
    assert 'MutableMapping' in source
    assert 'isinstance(getattr(self, "settings", None), MutableMapping)' in source


# Origin: test_runtime_followup_round7_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_clipboard_prompt_waits_for_active_application_and_narration_switch_suppresses_stale_warning():
    source = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'clipboard.py').read_text(encoding='utf-8')
    assert 'app.applicationState() != Qt.ApplicationState.ApplicationActive' in source
    assert 'narration_switch = bool(getattr(self, "_pending_narration_switch", False))' in source


# Origin: test_runtime_integrity_followup_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_downloader_source_analysis_delegates_playerjs_to_shared_service():
    source = (ROOT / 'audioknigi' / 'download' / 'source_analysis.py').read_text(encoding='utf-8')
    assert 'BookAnalysisService' in source
    assert 'def _parse_playlist_data' not in source
    assert 'def _extract_playlist_url' not in source


# Origin: test_services.py
def test_player_position_store_prunes_completed_position(tmp_path):
    store = PlayerPositionStore(tmp_path / 'positions.json')
    media = tmp_path / 'chapter.mp3'
    store.update(media, 99.0, 100.0)
    assert store.saved_seconds(media, duration=100.0) == 0.0
