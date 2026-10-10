"""Consolidated integration tests for the queue history domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


import json
from pathlib import Path
import threading
import time
import pytest
from audioknigi.config import settings as settings_module__persistence_cancellation_hardening_20260929
from audioknigi.core import Cancelled
from audioknigi.models import Book, Track
from audioknigi.providers import audioknigi_search
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.library_service import scan_unfinished
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict
from audioknigi.services import search_service
import requests
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.services.queue_service import _parse_selected_indices_payload
from tools.exception_audit import scan as exception_scan
from tools.qt_localization_audit import _ui_text_literals
from tools.unused_import_audit import unused_imports
import os
from audioknigi.diagnostics import support_bundle as support_bundle__recovery_diagnostics_hardening_20260912
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _hydrate_search_result_titles
from audioknigi.models import SearchResult
import ast
from audioknigi.download.errors import MissingSelectedTracksError
from audioknigi.metadata import APP_VERSION
from audioknigi.services.queue_service import task_from_dict
from tools.exception_audit import audit as exception_audit
from tools.historical_regression_audit import _normalize_nodeid
from tools.qt_localization_audit import _assignment_value
from tools.undefined_global_audit import _SPECIAL_GLOBALS
import importlib.util
from audioknigi.core import extract_metadata_from_html
from audioknigi.logging_utils import sanitize_log_text
from audioknigi.models import Book, SearchResult, Track
from audioknigi.services.library_service import export_history
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict
from audioknigi.core import _first_json_ld
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from collections import UserDict
from audioknigi.core import Cancelled, _structured_book_nodes
from audioknigi.diagnostics import support_bundle as support_bundle__report_followup_round12_20260916
from audioknigi.download_engine import _DownloadEngine
from audioknigi.services.download_request import build_download_request
import base64
from types import SimpleNamespace
from audioknigi.download.common import atomic_write_text
from audioknigi.i18n import localize_runtime_text
import zipfile
from audioknigi.core import _walk_json
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.common import replace_with_retry
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services import library_service
from audioknigi import knigavuhe, poleknig
from audioknigi.core import fmt_eta, parse_time_seconds
from audioknigi.download.probe import ProbeMixin
from audioknigi.models import Book, SearchResult
from audioknigi.providers import audioknigi_search as search_module
from audioknigi import core as core__report_followup_round21_20260917, knigavuhe, poleknig
from audioknigi.diagnostics.support_bundle import create_support_bundle
from audioknigi.services.player_position_store import PlayerPositionStore
import inspect
import socket
from audioknigi import core as core__report_followup_round22_20260917, poleknig
from audioknigi.network_dns import _relay_bidirectional
from audioknigi import core as core__report_followup_round2_20260915
from audioknigi.config.settings import save_app_settings
from audioknigi.core import load_json
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.core import Cancelled, load_json
from audioknigi.templates import template_values
from audioknigi import core as core__report_followup_round33_20260918
from audioknigi.core import fmt_size
from audioknigi.templates import render_text_template
from audioknigi.config.settings import migrate_settings
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
import audioknigi.config.settings as settings_module__report_followup_round44_20260920
import audioknigi.core as core__report_followup_round44_20260920
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round44_20260920
import audioknigi.services.player_position_store as position_module
from audioknigi.models import Book
from audioknigi.providers.audioknigi_search import _matches_query, _response_html_text, parse_audioknigi_results
from audioknigi.services.queue_service import _book_to_dict
from audioknigi.knigavuhe import _extract_names
from audioknigi.services.queue_service import _normalize_queue_download_mode, _track_from_dict
import audioknigi.config.settings as settings_module__report_followup_round47_20260923
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round47_20260923
from audioknigi.core import safe_int
from audioknigi.core import load_browser_context_profile
from audioknigi.network_dns import _parse_proxy_authority
from audioknigi.providers.audioknigi_search import _split_audioknigi_title
from dataclasses import dataclass
from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, extract_extended_metadata_from_html
from audioknigi.diagnostics import support_bundle as support_bundle__round61_external_review_followup_20260929
from audioknigi.providers.audioknigi_search import _author_detail_score, _matches_query
from audioknigi.services.queue_service import _item_to_dict
from audioknigi.services import library_service, source_health_service
from audioknigi import network_dns
from audioknigi.services.queue_service import _parse_created_at
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, _DownloadEngine
import re
from audioknigi.diagnostics import support_bundle as support_bundle__round73_runtime_followup_20261002
from audioknigi.knigavuhe import _usable_search_title
from audioknigi.services.book_analysis_service import BookAnalysisService, _playlist_track_title
from audioknigi.services.library_service import _validated_backup_payloads
from audioknigi.services.queue_service import _optional_persisted_bool
from audioknigi.core import effective_track_duration
from audioknigi.models import Book, NarrationVariant, Track
from audioknigi.models import NarrationVariant, Track
from audioknigi.services.queue_service import _track_from_dict, _variant_from_dict
from audioknigi import cover_fetch
from audioknigi.core import display_track_timeline
from audioknigi.services.queue_service import _book_from_dict
from audioknigi.templates import _safe_track_index
from audioknigi.download.network import NetworkDownloadMixin
from threading import Event
from audioknigi.download_engine import DownloadService
from audioknigi.i18n import tr
from audioknigi.providers.audioknigi_search import search_audioknigi
from audioknigi.services.download_request import DownloadRequest, build_download_request
from audioknigi.download.network import SlidingSpeedMeter
from audioknigi.models import Book, SearchResult, TRACK_STATUS_DAMAGED, TRACK_STATUS_MISSING, TRACK_STATUS_PRESENT, TRACK_STATUS_READY, normalize_track_status
import types
from audioknigi.diagnostics import support_bundle as support_bundle__runtime_integrity_followup_20260912
from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.sources import normalize_supported_url
from audioknigi.config import normalize_settings
from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.diagnostics.support_bundle import _is_secret_key
from audioknigi.i18n import localize_runtime_text, tr, ui_text
from audioknigi.providers.adapters import KnigavuheProvider, PoleKnigProvider


# Origin: test_persistence_cancellation_hardening_20260929.py
def _book__persistence_cancellation_hardening_20260929() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1-test', title='Test', tracks=[Track(index=1, title='Part 1', file='https://example.com/1.mp3')])

def test_queue_roundtrip_preserves_optional_and_empty_template_values(tmp_path):
    request = DownloadRequest(book=_book__persistence_cancellation_hardening_20260929(), selected_indices=[1], output_dir=tmp_path, use_templates=None, folder_template='', track_template='')
    task = QueueTask(id='round60', request=request, title='Test')
    restored = task_from_dict(task_to_dict(task))
    assert restored.request.use_templates is None
    assert restored.request.folder_template == ''
    assert restored.request.track_template == ''

def test_scan_unfinished_preserves_explicit_empty_templates(tmp_path):
    folder = tmp_path / 'book'
    folder.mkdir()
    (folder / 'resume.json').write_text(json.dumps({'url': 'https://audioknigi.com.ua/audio-1-test', 'title': 'Test', 'selected_indices': [1], 'use_templates': False, 'folder_template': '', 'track_template': ''}), encoding='utf-8')
    record = scan_unfinished(tmp_path)[0]
    assert record.use_templates is False
    assert record.folder_template == ''
    assert record.track_template == ''


# Origin: test_quality_runtime_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_history_callback_failure_does_not_break_completed_download_bookkeeping(tmp_path, monkeypatch):
    import audioknigi.download_engine as engine_module
    book = Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[])
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    callbacks = DownloadCallbacks(history_changed=lambda: (_ for _ in ()).throw(RuntimeError('ui failed')))
    engine = _DownloadEngine(request, {}, threading.Event(), callbacks)
    monkeypatch.setattr(engine_module, 'HISTORY_FILE', tmp_path / 'history.json')
    engine._add_history(book, tmp_path, 0)
    assert (tmp_path / 'history.json').exists()

def test_queue_recovery_preserves_explicit_empty_selection():
    assert _parse_selected_indices_payload(None) is None
    assert _parse_selected_indices_payload([]) == []
    assert _parse_selected_indices_payload([None, 'bad', '']) == []


# Origin: test_recovery_diagnostics_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_whole_book_resume_manifest_null_or_empty_is_discoverable(tmp_path):
    for name, selected in (('null', None), ('legacy-empty', [])):
        folder = tmp_path / name
        folder.mkdir()
        (folder / 'resume.json').write_text(json.dumps({'url': 'https://example.test/book', 'title': name, 'selected_indices': selected}), encoding='utf-8')
    records = scan_unfinished(tmp_path)
    assert len(records) == 2
    assert all((record.selected_indices is None for record in records))


# Origin: test_release_integrity_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_legacy_queue_selected_indices_skip_invalid_values_without_losing_task(tmp_path):
    payload = {'url': 'https://audioknigi.com.ua/audio-1', 'title': 'Legacy', 'selected_indices': ['1', None, 'all', '2', 'bad', '2'], 'output_dir': str(tmp_path)}
    task = task_from_dict(payload)
    assert task.request.selected_indices == [1, 2]

def test_legacy_queue_all_marker_means_whole_book(tmp_path):
    payload = {'url': 'https://audioknigi.com.ua/audio-1', 'title': 'Legacy', 'selected_indices': 'all', 'output_dir': str(tmp_path)}
    task = task_from_dict(payload)
    assert task.request.selected_indices is None


# Origin: test_release_quality_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_history_export_does_not_silently_truncate_to_500(tmp_path: Path):
    rows = [{'title': f'Book {index}', 'date': str(index)} for index in range(650)]
    target = export_history(rows, tmp_path / 'history.json', 'json')
    exported = json.loads(target.read_text(encoding='utf-8'))
    assert len(exported) == 650

def _request() -> DownloadRequest:
    book = Book(url='https://knigavuhe.org/book/1', title='Book', tracks=[Track(index=1, title='One', file='https://cdn.example/1.mp3')])
    return DownloadRequest(book=book, selected_indices=None, output_dir=Path('.'))

def test_queue_persists_full_mp3_download_mode():
    task = QueueStore.new_task(_request(), download_mode='full_mp3')
    payload = task_to_dict(task)
    assert payload['download_mode'] == 'full_mp3'
    restored = task_from_dict(payload)
    assert restored.download_mode == 'full_mp3'

def test_queue_ui_launches_stored_mode_and_exposes_action():
    queue_source = (ROOT / 'audioknigi/qt/mixins/queue.py').read_text(encoding='utf-8')
    page_source = (ROOT / 'audioknigi/qt/main_window_pages.py').read_text(encoding='utf-8')
    assert 'mode=task.download_mode' in queue_source
    assert 'def add_current_full_mp3_to_queue' in queue_source
    assert 'self._l("Добавить одним MP3 в очередь")' in page_source


# Origin: test_report_followup_round11_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_scan_unfinished_accepts_scalar_selected_index_without_crashing(tmp_path):
    folder = tmp_path / 'Book'
    folder.mkdir()
    (folder / 'resume.json').write_text(json.dumps({'url': 'https://knigavuhe.org/book/1', 'title': 'Book', 'selected_indices': 1}, ensure_ascii=False), encoding='utf-8')
    rows = scan_unfinished(tmp_path)
    assert len(rows) == 1
    assert rows[0].selected_indices == [1]

def test_scan_unfinished_ignores_boolean_selected_payload(tmp_path):
    folder = tmp_path / 'Book'
    folder.mkdir()
    (folder / 'resume.json').write_text(json.dumps({'url': 'https://knigavuhe.org/book/1', 'title': 'Book', 'selected_indices': False}), encoding='utf-8')
    assert scan_unfinished(tmp_path) == []


# Origin: test_report_followup_round12_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_parallel_ffmpeg_failure_and_drop_queue_contracts_are_present():
    flow = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    split_start = flow.index('self.log("Параллельная нарезка одного исходника')
    split_end = flow.index('if want_mp3 and mp3_needs_creation:', split_start)
    split_block = flow[split_start:split_end]
    assert split_block.count('self._cancel_active_subprocesses()') >= 2
    analysis = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    start = analysis.index('if not isinstance(book, Book):')
    end = analysis.index('pending = self._pending_search_result', start)
    block = analysis[start:end]
    assert 'getattr(self, "_pending_queue_urls", None)' in block
    assert 'self._pending_queue_urls = []' in block
    assert 'QTimer.singleShot(0, self._queue_next_dropped_url)' not in block


# Origin: test_report_followup_round15_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_full_mp3_queue_parts_count_is_one_file():
    source = (ROOT / 'audioknigi/qt/mixins/queue.py').read_text(encoding='utf-8')
    block = source[source.index('def _queue_parts_count'):source.index('def _queue_row_summary')]
    assert 'download_mode", "selected"' in block
    assert '== "full_mp3"' in block
    assert 'return 1' in block


# Origin: test_report_followup_round18_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_restore_backup_rolls_back_already_written_members_on_late_failure(tmp_path, monkeypatch) -> None:
    first = tmp_path / 'settings.json'
    second = tmp_path / 'player_positions.json'
    first.write_text(json.dumps({'old': 1}), encoding='utf-8')
    second.write_text(json.dumps({'old': 2}), encoding='utf-8')
    backup = tmp_path / 'backup.zip'
    with zipfile.ZipFile(backup, 'w') as archive:
        archive.writestr('settings.json', json.dumps({'new': 1}))
        archive.writestr('player_positions.json', json.dumps({'new': 2}))
    monkeypatch.setattr(library_service, 'BACKUP_MEMBERS', {'settings.json': first, 'player_positions.json': second})
    real_save = library_service.save_json

    def flaky_save(path, data, *, raise_errors=False):
        if Path(path) == second and isinstance(data, dict) and (data.get('new') == 2):
            raise OSError('simulated disk failure')
        return real_save(path, data, raise_errors=raise_errors)
    monkeypatch.setattr(library_service, 'save_json', flaky_save)
    with pytest.raises(OSError, match='simulated disk failure'):
        library_service.restore_backup(backup)
    assert json.loads(first.read_text(encoding='utf-8')) == {'old': 1}
    assert json.loads(second.read_text(encoding='utf-8')) == {'old': 2}


# Origin: test_report_followup_round20_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_queue_legacy_string_selected_indices_support_common_separators() -> None:
    assert _parse_selected_indices_payload('1, 2; 3  4') == [1, 2, 3, 4]
    assert _parse_selected_indices_payload('') is None
    assert _parse_selected_indices_payload([]) == []


# Origin: test_report_followup_round21_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_round21_does_not_change_queue_empty_selection_or_proxy_drain_contracts() -> None:
    queue_source = (ROOT / 'audioknigi/services/queue_service.py').read_text(encoding='utf-8')
    assert 'An explicit empty' in queue_source
    assert 'return result' in queue_source
    proxy_source = (ROOT / 'audioknigi/network_dns.py').read_text(encoding='utf-8')
    assert 'half_close_deadline' in proxy_source
    assert 'return_when_right_closes=True' in proxy_source


# Origin: test_report_followup_round22_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_playwright_cookie_restore_is_fault_isolated_and_event_callback_does_not_raise_cancelled() -> None:
    pole_source = inspect.getsource(poleknig._fetch_book_playwright)
    analysis_source = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    assert 'context.add_cookies([cookie])' in pole_source
    assert 'Failed to restore PoleKnig cookie' in pole_source
    callback = pole_source[pole_source.index('def on_request(request):'):pole_source.index('page.on("request", on_request)')]
    assert 'raise Cancelled("Операция отменена пользователем")' not in callback
    assert 'return' in callback
    assert 'context.add_cookies([cookie])' in analysis_source
    assert 'Failed to restore audioknigi cookie' in analysis_source


# Origin: test_report_followup_round27_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_search_worker_gui_callbacks_are_explicitly_queued_to_main_qt_thread() -> None:
    source = _source('audioknigi/qt/mixins/search.py')
    assert 'worker.progress.connect(self._worker_ui_relay.search_progress, Qt.ConnectionType.QueuedConnection)' in source
    assert 'worker.finished.connect(self._worker_ui_relay.search_finished, Qt.ConnectionType.QueuedConnection)' in source
    assert 'thread.finished.connect(self._worker_ui_relay.search_thread_finished, Qt.ConnectionType.QueuedConnection)' in source

def test_analysis_worker_gui_callbacks_are_explicitly_queued() -> None:
    source = _source('audioknigi/qt/mixins/analysis_download.py')
    assert 'worker.progress.connect(self._worker_ui_relay.analysis_progress, Qt.ConnectionType.QueuedConnection)' in source
    assert 'worker.finished.connect(self._worker_ui_relay.analysis_finished, Qt.ConnectionType.QueuedConnection)' in source
    assert 'thread.finished.connect(self._worker_ui_relay.analysis_thread_finished, Qt.ConnectionType.QueuedConnection)' in source

def test_audiobookshelf_worker_gui_callbacks_are_explicitly_queued() -> None:
    source = _source('audioknigi/qt/mixins/settings.py')
    assert 'from PySide6.QtCore import QThread, QTimer, Slot, Qt' in source
    assert 'worker.finished.connect(self._worker_ui_relay.audiobookshelf_finished, Qt.ConnectionType.QueuedConnection)' in source
    assert 'thread.finished.connect(self._worker_ui_relay.audiobookshelf_thread_finished, Qt.ConnectionType.QueuedConnection)' in source


# Origin: test_report_followup_round2_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_scan_unfinished_accepts_utf8_bom_manifest(tmp_path):
    folder = tmp_path / 'Book'
    folder.mkdir()
    payload = {'url': 'https://knigavuhe.org/book/sample/', 'selected_indices': None}
    (folder / 'resume.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8-sig')
    found = scan_unfinished(tmp_path)
    assert len(found) == 1


# Origin: test_report_followup_round32_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round32_20260918(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

def test_queue_selected_indices_reject_json_booleans() -> None:
    assert _parse_selected_indices_payload([True, False, 2, '3']) == [2, 3]

def test_reported_save_json_and_queue_serialization_are_already_supported() -> None:
    core = src__report_followup_round32_20260918('audioknigi/core.py')
    models = src__report_followup_round32_20260918('audioknigi/models.py')
    assert 'def save_json(path, data, *, raise_errors=False):' in core
    assert 'class MappingDataclass' in models and 'def to_dict' in models


# Origin: test_report_followup_round33_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round33_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_root_library_recovery_depth_and_queue_drop_coordinate_are_hardened() -> None:
    library = src__report_followup_round33_20260918('audioknigi/services/library_service.py')
    workers = src__report_followup_round33_20260918('audioknigi/qt/workers.py')
    assert 'if depth >= 8:' in library
    assert 'target_row = self.rowAt(int(event.position().y()))' in workers
    assert 'mapFrom' not in workers[workers.index('def dropEvent'):workers.index('super().dropEvent', workers.index('def dropEvent'))]


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_shared_source_fallback_removes_old_resume_manifest_before_switch() -> None:
    source = src__report_followup_round34_20260919('audioknigi/download/book_flow.py')
    block = source[source.index('fallback_attempted = True'):source.index('book = fallback')]
    assert 'self._remove_resume_manifest(book)' in block

def test_queue_drop_uses_viewport_relative_event_position_directly() -> None:
    source = src__report_followup_round34_20260919('audioknigi/qt/workers.py')
    block = source[source.index('def dropEvent'):source.index('super().dropEvent', source.index('def dropEvent'))]
    assert 'self.rowAt(int(event.position().y()))' in block
    assert 'mapFrom' not in block


# Origin: test_report_followup_round41_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round41_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_history_folder_path_gets_remaining_width() -> None:
    history = src__report_followup_round41_20260920('audioknigi/qt/mixins/history.py')
    assert 'for column in (0, 1, 5):' in history
    assert 'history_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)' in history
    assert 'history_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)' in history
    assert 'history_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)' in history
    assert 'history_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)' in history
    assert 'self.history_table.setColumnWidth(2, 320)' in history
    assert 'self.history_table.setColumnWidth(3, 220)' in history
    assert 'self.history_table.setColumnWidth(4, 220)' in history


# Origin: test_report_followup_round44_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round44_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_large_queue_cover_is_not_embedded_but_small_thumbnail_is() -> None:
    large = Book(url='https://example.test/book', title='Book', cover_url='https://example.test/cover.jpg', cover_cache=(b'x' * (300 * 1024), 'image/jpeg'))
    large_data = _book_to_dict(large)
    assert large_data['cover_cache_b64'] == ''
    assert large_data['cover_cache_mime'] == ''
    assert large_data['cover_url'] == large.cover_url
    small_payload = b'small-cover'
    small = Book(url='https://example.test/small', title='Small', cover_cache=(small_payload, 'image/jpeg'))
    small_data = _book_to_dict(small)
    assert base64.b64decode(small_data['cover_cache_b64']) == small_payload
    assert small_data['cover_cache_mime'] == 'image/jpeg'


# Origin: test_report_followup_round46_20260922.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round46_20260922(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_queue_download_mode_normalizes_resume_parts_alias() -> None:
    assert _normalize_queue_download_mode('parts') == 'selected'
    assert _normalize_queue_download_mode('selected') == 'selected'
    assert _normalize_queue_download_mode('full_mp3') == 'full_mp3'
    assert _normalize_queue_download_mode('unknown-future-value') == 'selected'

def test_queue_track_selected_is_normalized_to_bool() -> None:
    assert _track_from_dict({'index': 1, 'title': 'A', 'file': 'x', 'selected': 'false'}).selected is False
    assert _track_from_dict({'index': 1, 'title': 'A', 'file': 'x', 'selected': '0'}).selected is False
    assert _track_from_dict({'index': 1, 'title': 'A', 'file': 'x', 'selected': None}).selected is False
    assert _track_from_dict({'index': 1, 'title': 'A', 'file': 'x', 'selected': 'true'}).selected is True

def test_queue_drag_reorder_is_disabled_while_any_task_is_active() -> None:
    source = src__report_followup_round46_20260922('audioknigi/qt/mixins/queue.py')
    start = source.index('def _queue_drag_reordered')
    end = source.index('def toggle_queue_item_pause', start)
    block = source[start:end]
    assert 'self._active_queue_task_id is not None' in block
    assert block.index('self._active_queue_task_id is not None') < block.index('self.queue_tasks.pop')

def test_all_queue_deserialization_paths_use_download_mode_normalizer() -> None:
    source = src__report_followup_round46_20260922('audioknigi/services/queue_service.py')
    assert source.count('download_mode=_normalize_queue_download_mode(data.get') >= 2
    assert 'mode = _normalize_queue_download_mode(download_mode)' in source


# Origin: test_report_followup_round47_20260923.py
def test_scan_unfinished_accepts_string_all_selection(tmp_path):
    folder = tmp_path / 'book'
    folder.mkdir()
    (folder / 'resume.json').write_text(json.dumps({'url': 'https://audioknigi.com.ua/audio-1', 'title': 'Book', 'selected_indices': 'all'}), encoding='utf-8')
    rows = scan_unfinished(tmp_path)
    assert len(rows) == 1
    assert rows[0].selected_indices is None


# Origin: test_report_followup_round9_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_legacy_queue_without_template_flag_preserves_global_inheritance():
    task = task_from_dict({'url': 'https://knigavuhe.org/book/1', 'title': 'Legacy'})
    assert task.request.use_templates is None
    assert task.request.folder_template is None
    assert task.request.track_template is None


# Origin: test_round61_external_review_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_queue_supports_plain_dataclass_without_bypassing_model_serializer_contract():

    @dataclass
    class Plain:
        one: int
        two: str
    assert _item_to_dict(Plain(1, 'x')) == {'one': 1, 'two': 'x'}
    source = (ROOT / 'audioknigi/services/queue_service.py').read_text(encoding='utf-8')
    assert 'asdict(' not in source


# Origin: test_round66_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_backup_restore_accepts_legacy_wrapped_queue(tmp_path):
    for wrapper_key in ('items', 'queue'):
        backup = tmp_path / f'legacy-{wrapper_key}.zip'
        with zipfile.ZipFile(backup, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('qt_queue.json', json.dumps({wrapper_key: [{'id': 'demo'}]}))
        payloads = library_service._validated_backup_payloads(backup)
        assert payloads['qt_queue.json'] == [{'id': 'demo'}]


# Origin: test_round67_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_parked_segment_worker_can_exit_after_active_workers_drain_queue():
    source = (ROOT / 'audioknigi/download/network.py').read_text(encoding='utf-8')
    start = source.index('def worker(worker_id)')
    end = source.index('self.log(', start)
    block = source[start:end]
    parked = block.split('if worker_id >= controller.current_workers():', 1)[1].split('try:', 1)[0]
    assert 'if jobs.empty():\n                        return' in parked
    assert parked.index('if jobs.empty():') < parked.index('cancel_event.wait(0.10)')

def test_scan_unfinished_splits_string_selected_indices(tmp_path):
    folder = tmp_path / 'Book'
    folder.mkdir()
    (folder / 'resume.json').write_text(json.dumps({'url': 'https://poleknig.com/books/123', 'title': 'Demo', 'selected_indices': '1, 2; 3'}), encoding='utf-8')
    rows = library_service.scan_unfinished(tmp_path)
    assert len(rows) == 1
    assert rows[0].selected_indices == [1, 2, 3]

def test_queue_created_at_preserves_explicit_zero():
    assert _parse_created_at(0.0) == 0.0
    assert _parse_created_at('0') == 0.0


# Origin: test_round70_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

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

def test_history_clear_is_blocked_during_active_long_operation_and_cover_icons_scale():
    history = (ROOT / 'audioknigi/qt/mixins/history.py').read_text(encoding='utf-8')
    start = history.index('def history_clear')
    block = history[start:history.index('@Slot()', start + 20)]
    assert 'if self._long_operation_active():' in block
    assert 'setIconSize(QSize(icon_px, icon_px))' in history
    assert 'setDefaultSectionSize(max(28, icon_px + 4))' in history
    queue = (ROOT / 'audioknigi/qt/mixins/queue.py').read_text(encoding='utf-8')
    assert 'setIconSize(QSize(icon_px, icon_px))' in queue
    assert 'setDefaultSectionSize(max(28, icon_px + 4))' in queue


# Origin: test_round73_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_backup_validation_preserves_all_history_rows(tmp_path):
    rows = [{'title': f'Book {index}'} for index in range(800)]
    archive = tmp_path / 'backup.zip'
    with zipfile.ZipFile(archive, 'w') as zf:
        zf.writestr('history.json', json.dumps(rows, ensure_ascii=False))
    payloads = _validated_backup_payloads(archive)
    assert len(payloads['history.json']) == 800

def test_queue_string_booleans_are_parsed_semantically():
    assert _optional_persisted_bool({'flag': 'false'}, 'flag') is False
    assert _optional_persisted_bool({'flag': '0'}, 'flag') is False
    assert _optional_persisted_bool({'flag': 'true'}, 'flag') is True
    assert _optional_persisted_bool({'flag': '1'}, 'flag') is True
    assert _optional_persisted_bool({'flag': 'unknown'}, 'flag') is False

def test_one_track_download_restores_selection_only_after_worker_finishes_without_announcement():
    clipboard = (ROOT / 'audioknigi/qt/mixins/clipboard.py').read_text(encoding='utf-8')
    block = clipboard[clipboard.index('def download_selected_track_only'):clipboard.index('__all__')]
    assert 'self._restore_track_selection_after_download = previous_selection' in block
    assert 'if not self.start_download():' in block
    analysis = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    assert 'restore_selection = getattr(self, "_restore_track_selection_after_download", None)' in analysis
    assert '_suppress_track_selection_announcement' in analysis

def test_history_reload_resizes_only_service_columns():
    source = (ROOT / 'audioknigi/qt/mixins/history.py').read_text(encoding='utf-8')
    block = source[source.index('def _load_history'):source.index('def _selected_history')]
    assert 'resizeColumnsToContents()' not in block
    assert 'for column in (0, 1, 5):' in block
    assert 'resizeColumnToContents(column)' in block


# Origin: test_round74_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_queue_deserializer_does_not_shadow_dataclasses_fields_function():
    source = (ROOT / 'audioknigi/services/queue_service.py').read_text(encoding='utf-8')
    block = source[source.index('def _book_from_dict'):source.index('def task_to_dict')]
    assert 'book_fields = {item.name for item in fields(Book)}' in block
    assert 'Book.__dataclass_fields__' not in block
    assert '\n    fields =' not in block

def test_analysis_requeue_and_delayed_actions_guard_state_and_indices():
    source = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    assert 'safe_int(getattr(track, "index", None), -1)) >= 0' in source
    assert 'safe_int(value, -1)) >= 0 and index in valid' in source
    assert 'self.current_book is not expected_book' in source
    assert 'if bool(getattr(self, "_exit_requested", False)):' in source


# Origin: test_round76_external_review_followup_20261003.py
ROOT = Path(__file__).resolve().parents[2]

def test_queue_track_and_variant_deserializers_use_public_dataclass_fields_api():
    source = (ROOT / 'audioknigi/services/queue_service.py').read_text(encoding='utf-8')
    track_block = source[source.index('def _track_from_dict'):source.index('def _variant_from_dict')]
    variant_block = source[source.index('def _variant_from_dict'):source.index('def _item_to_dict')]
    assert 'fields(Track)' in track_block
    assert 'Track.__dataclass_fields__' not in track_block
    assert 'fields(NarrationVariant)' in variant_block
    assert 'NarrationVariant.__dataclass_fields__' not in variant_block
    track = _track_from_dict({'index': '7', 'title': 'Seven', 'file': 'x', 'unknown': 1})
    assert isinstance(track, Track)
    assert track.index == 7
    assert track.title == 'Seven'
    variant = _variant_from_dict({'url': 'https://example.invalid/v', 'unknown': 1})
    assert isinstance(variant, NarrationVariant)
    assert variant.url == 'https://example.invalid/v'


# Origin: test_round77_external_review_followup_20261004.py
ROOT = Path(__file__).resolve().parents[2]

def test_queue_book_deserializer_uses_public_dataclass_fields_api():
    source = (ROOT / 'audioknigi/services/queue_service.py').read_text(encoding='utf-8')
    block = source[source.index('def _book_from_dict'):source.index('def task_to_dict')]
    assert 'fields(Book)' in block
    assert 'Book.__dataclass_fields__' not in block
    book = _book_from_dict({'url': 'https://example.invalid/book', 'title': 'Demo', 'unknown': 1})
    assert book.title == 'Demo'


# Origin: test_round80_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_queue_reanalysis_preserves_zero_index_in_source_contract():
    source = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    start = source.index('if self._queue_reanalyze_task_id and enabled:')
    block = source[start:source.index('def ', start + 10)]
    assert 'safe_int(getattr(track, "index", None), -1)) >= 0' in block
    assert 'safe_int(value, -1)) >= 0 and index in valid' in block
    assert 'safe_int(getattr(track, "index", None), 0)) > 0' not in block


# Origin: test_runtime_contract_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def _book__runtime_contract_hardening_20260912() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3'), Track(index=2, title='Two', file='https://cdn.invalid/2.mp3')])

def test_whole_book_none_selection_round_trips_queue(tmp_path):
    request = DownloadRequest(book=_book__runtime_contract_hardening_20260912(), selected_indices=None, output_dir=tmp_path)
    request.validate()
    task = QueueTask(id='whole', request=request, title='Demo')
    payload = task_to_dict(task)
    assert payload['request']['selected_indices'] is None
    restored = task_from_dict(payload)
    assert restored.request.selected_indices is None
    assert restored.request.resolved_selected_indices() == [1, 2]

def test_queue_and_download_ui_use_none_safe_part_counts():
    queue_source = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'queue.py').read_text(encoding='utf-8')
    analysis_source = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'analysis_download.py').read_text(encoding='utf-8')
    assert '_queue_parts_count' in queue_source
    assert 'len(task.request.selected_indices)' not in queue_source
    assert 'request.resolved_selected_indices()' in analysis_source
    assert 'for value in old.selected_indices' in analysis_source
    assert 'if old.selected_indices is None' in analysis_source


# Origin: test_runtime_followup_round7_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_queue_restore_preserves_explicit_empty_selection():
    assert _parse_selected_indices_payload(None) is None
    assert _parse_selected_indices_payload([]) == []
    assert _parse_selected_indices_payload([None, 'bad', '']) == []

def test_sliding_speed_meter_resets_history_when_counter_moves_backwards():
    meter = SlidingSpeedMeter(window_seconds=5.0)
    meter.update(1000)
    meter.update(2000)
    assert len(meter.samples) >= 2
    assert meter.update(50) == 0.0
    assert list(meter.samples)[-1][1] == 50
    assert len(meter.samples) == 1


# Origin: test_runtime_integrity_followup_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_unfinished_scan_preserves_zero_based_track_index(tmp_path):
    folder = tmp_path / 'book'
    folder.mkdir()
    (folder / 'resume.json').write_text(json.dumps({'url': 'https://knigavuhe.org/book/demo/', 'title': 'Demo', 'selected_indices': [0]}), encoding='utf-8')
    found = scan_unfinished(tmp_path)
    assert len(found) == 1
    assert found[0].selected_indices == [0]


# Origin: test_services.py
def test_queue_roundtrip_preserves_request(tmp_path):
    book = Book(url='https://example.invalid', title='Book', tracks=[Track(1, 'One', 'https://example.invalid/1.mp3')])
    request = build_download_request(book, {'output_dir': str(tmp_path)}, [1])
    task = QueueStore.new_task(request)
    restored = task_from_dict(task_to_dict(task))
    assert restored.request.book.title == 'Book'
    assert restored.request.selected_indices == [1]


# Origin: test_stability_localization_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_queue_model_dataclasses_are_serialized_with_tracks():
    book = Book(url='https://example.invalid/book', title='Book', tracks=[Track(index=1, title='One', file='https://example.invalid/1.mp3')])
    payload = _book_to_dict(book)
    assert payload['tracks'] and payload['tracks'][0]['index'] == 1

def test_history_lock_is_shared_by_engine_and_library_service():
    import audioknigi.download_engine as engine
    assert engine.HISTORY_LOCK is library_service.HISTORY_LOCK

def test_backup_uses_memory_snapshots_instead_of_zipfile_write(tmp_path, monkeypatch):
    source = tmp_path / 'settings.json'
    source.write_text('{"ok": true}', encoding='utf-8')
    monkeypatch.setattr(library_service, 'BACKUP_MEMBERS', {'settings.json': source})
    target = tmp_path / 'backup.zip'
    library_service.create_backup(target)
    import zipfile
    with zipfile.ZipFile(target) as archive:
        assert json.loads(archive.read('settings.json').decode('utf-8')) == {'ok': True}
        manifest = json.loads(archive.read('backup_manifest.json').decode('utf-8'))
        assert manifest['includes'] == ['settings.json']
    source_text = (ROOT / 'audioknigi' / 'services' / 'library_service.py').read_text(encoding='utf-8')
    assert 'archive.write(source' not in source_text

# Post-consolidation: Round 83 external audit follow-up.
def test_queue_deserialization_understands_german_boolean_values():
    from audioknigi.services.queue_service import _optional_persisted_bool, _track_from_dict

    assert _track_from_dict({'index': 1, 'selected': 'nein'}).selected is False
    assert _track_from_dict({'index': 1, 'selected': 'ja'}).selected is True
    assert _optional_persisted_bool({'flag': 'nein'}, 'flag') is False
    assert _optional_persisted_bool({'flag': 'ja'}, 'flag') is True


def test_queue_task_url_fails_closed_for_missing_legacy_book():
    from types import SimpleNamespace
    from audioknigi.services.queue_service import QueueTask

    task = QueueTask(id='legacy', request=SimpleNamespace(book=None), title='Legacy')
    assert task.url == ''


def test_restore_backup_snapshots_history_under_history_lock(monkeypatch, tmp_path):
    from audioknigi.services import library_service

    history = tmp_path / 'history.json'
    history.write_text('[]', encoding='utf-8')

    class LockProbe:
        def __init__(self):
            self.depth = 0

        def __enter__(self):
            self.depth += 1
            return self

        def __exit__(self, *_args):
            self.depth -= 1

    lock = LockProbe()
    monkeypatch.setattr(library_service, 'APP_DIR', tmp_path)
    monkeypatch.setattr(library_service, 'HISTORY_FILE', history)
    monkeypatch.setattr(library_service, 'HISTORY_LOCK', lock)
    monkeypatch.setattr(library_service, 'BACKUP_MEMBERS', {'history.json': history})
    monkeypatch.setattr(library_service, '_validated_backup_payloads', lambda _path: {'history.json': []})

    original_reader = library_service._read_backup_member

    def checked_reader(path):
        assert path == history
        assert lock.depth > 0
        return original_reader(path)

    monkeypatch.setattr(library_service, '_read_backup_member', checked_reader)
    monkeypatch.setattr(library_service, 'save_json', lambda *_args, **_kwargs: True)
    assert library_service.restore_backup(tmp_path / 'backup.zip') == ['history.json']


# Post-consolidation: Round 86 external audit follow-up.
def test_restore_backup_holds_history_lock_for_entire_transaction(monkeypatch, tmp_path):
    from audioknigi.services import library_service

    history = tmp_path / "history.json"
    settings = tmp_path / "settings.json"
    history.write_text("[]", encoding="utf-8")
    settings.write_text('{"before": true}', encoding="utf-8")

    class LockProbe:
        def __init__(self):
            self.depth = 0
            self.entries = 0
        def __enter__(self):
            self.depth += 1
            self.entries += 1
            return self
        def __exit__(self, *_args):
            self.depth -= 1

    lock = LockProbe()
    monkeypatch.setattr(library_service, "APP_DIR", tmp_path)
    monkeypatch.setattr(library_service, "HISTORY_FILE", history)
    monkeypatch.setattr(library_service, "HISTORY_LOCK", lock)
    monkeypatch.setattr(
        library_service,
        "BACKUP_MEMBERS",
        {"history.json": history, "settings.json": settings},
    )
    monkeypatch.setattr(
        library_service,
        "_validated_backup_payloads",
        lambda _path: {"history.json": [], "settings.json": {"after": True}},
    )

    original_reader = library_service._read_backup_member
    writes = []
    def checked_reader(path):
        assert lock.depth > 0
        return original_reader(path)
    def checked_save(path, data, **_kwargs):
        assert lock.depth > 0
        writes.append((Path(path).name, data))
        return True

    monkeypatch.setattr(library_service, "_read_backup_member", checked_reader)
    monkeypatch.setattr(library_service, "save_json", checked_save)
    assert library_service.restore_backup(tmp_path / "backup.zip") == ["history.json", "settings.json"]
    assert lock.entries == 1
    assert lock.depth == 0
    assert [name for name, _data in writes] == ["history.json", "settings.json"]


def test_queue_empty_selection_contract_remains_explicit_not_all_tracks():
    # Current snapshots serialize None for "all tracks". An explicit [] means
    # "nothing selected" and must not silently become a full-book download.
    assert _parse_selected_indices_payload(None) is None
    assert _parse_selected_indices_payload([]) == []
