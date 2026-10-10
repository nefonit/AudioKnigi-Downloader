"""Consolidated integration tests for the core services domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from datetime import datetime
import socket
import threading
from audioknigi.core import Cancelled
from audioknigi.diagnostics.support_bundle import _privacy_path, _sanitize_setting_value
from audioknigi.network_dns import _read_http_head
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata, _looks_like_author_prefix, _same_author_identity
from audioknigi.services.book_analysis_service import _playlist_track_title
from audioknigi.services.player_position_store import PlayerPositionStore
from audioknigi.models import NarrationVariant
import os
from audioknigi.diagnostics import support_bundle as support_bundle__recovery_diagnostics_hardening_20260912
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _hydrate_search_result_titles
from audioknigi.models import SearchResult
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.library_service import scan_unfinished
import ast
from audioknigi.download.errors import MissingSelectedTracksError
from audioknigi.metadata import APP_VERSION
from audioknigi.services.queue_service import task_from_dict
from tools.exception_audit import audit as exception_audit__release_integrity_followup_20260913
from tools.historical_regression_audit import _normalize_nodeid
from tools.qt_localization_audit import _assignment_value
from tools.undefined_global_audit import _SPECIAL_GLOBALS
from audioknigi.core import effective_track_duration, safe_float
from audioknigi.i18n import localize_runtime_text, tr
from audioknigi.models import Book, Track
from audioknigi.knigavuhe import _extract_call_argument, _usable_search_title
from audioknigi.models import Book, SearchResult, Track
from audioknigi.poleknig import _discover_narration_variants
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.services.download_request import DownloadRequest
from collections import UserDict
from audioknigi.core import Cancelled, _structured_book_nodes
from audioknigi.diagnostics import support_bundle as support_bundle__report_followup_round12_20260916
from audioknigi.download_engine import _DownloadEngine
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.download_request import build_download_request
import csv
import zipfile
from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, migrate_ui_scale_settings
from audioknigi.i18n import _normalize_runtime_regex_catalog
from audioknigi.services.search_service import search_all_sources
from audioknigi.core import _walk_json
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.common import replace_with_retry
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services import library_service
from audioknigi import core as core__report_followup_round21_20260917, knigavuhe, poleknig
from audioknigi.diagnostics.support_bundle import create_support_bundle
from audioknigi.core import Cancelled, load_json
from audioknigi.services.queue_service import _parse_selected_indices_payload
from audioknigi.templates import template_values
from audioknigi import core as core__report_followup_round33_20260918
from audioknigi.core import fmt_size
from audioknigi.templates import render_text_template
from audioknigi.config.settings import migrate_settings
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
import base64
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
from audioknigi.knigavuhe import _extract_names
from audioknigi.services.queue_service import _normalize_queue_download_mode, _track_from_dict
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round47_20260923
from audioknigi.core import safe_int
from audioknigi.providers import audioknigi_search
import hashlib
import math
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round49_20260924
import audioknigi.download.source_analysis as source_analysis_module__report_followup_round49_20260924
from audioknigi.download.source_analysis import SourceAnalysisMixin
from audioknigi.models import Book, SearchResult
import sys
from types import ModuleType, SimpleNamespace
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round52_20260924
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.services.download_request import DownloadRequest, build_download_request
from audioknigi.download import book_flow
from audioknigi.download.probe import ProbeMixin
from tools import exception_audit as exception_audit__report_followup_round53_20260926, package_source_release, qt_localization_audit
from tools import qt_windows_acceptance, undefined_global_audit
from audioknigi.diagnostics.support_bundle import _sanitize_log_bytes, _tail
from audioknigi.qt.acceptance_contract import ACCEPTANCE_SCHEMA, acceptance_issues
from tools import qt_localization_audit, qt_windows_acceptance
from audioknigi.brand import version_label
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.i18n import localize_runtime_text
from audioknigi.core import load_browser_context_profile
from audioknigi.network_dns import _parse_proxy_authority
from audioknigi.providers.audioknigi_search import _split_audioknigi_title
import subprocess
from audioknigi.services import search_service
from audioknigi.services.source_health_service import SourceHealthItem, SourceHealthOutcome
from audioknigi import network_dns
from audioknigi.config.settings import normalize_settings
from audioknigi.models import Book, Track, TRACK_STATUS_READY
from audioknigi.providers.audioknigi_search import _response_html_text
from audioknigi.config.settings import AppSettings, normalize_settings
from audioknigi.diagnostics import support_bundle as support_bundle__round63_followup_20260929
from audioknigi import poleknig
from audioknigi.services import library_service, source_health_service
from audioknigi.services.queue_service import _parse_created_at
from audioknigi.brand import AUTHOR_EMAIL, AUTHOR_GITHUB_URL, AUTHOR_NAME, COPYRIGHT_YEAR, PROJECT_URL
from tools.windows_version_info import render_version_info
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, _DownloadEngine
from audioknigi.services.search_service import downloadable_search_results, search_result_sort_key
from audioknigi.core import effective_track_duration
from audioknigi.models import Book, NarrationVariant, Track
from audioknigi import cover_fetch
from audioknigi.core import display_track_timeline
from audioknigi.services.queue_service import _book_from_dict
from audioknigi.templates import _safe_track_index
from audioknigi.core import safe_name
from audioknigi.knigavuhe import _extract_narration_variants
from audioknigi.services import book_analysis_service as analysis_module
from audioknigi.core import SiteStructureChanged
from audioknigi.download.errors import MissingMediaSourceError
from audioknigi.knigavuhe import parse_book_html
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.download.common import source_target_assignments
from audioknigi.services import source_health_service
from audioknigi.download import network as network_module
from audioknigi.download import source_analysis as source_analysis_module__round81_external_review_followup_20261006
from threading import Event
from audioknigi.download_engine import DownloadService
from audioknigi.i18n import tr
from audioknigi.providers.audioknigi_search import search_audioknigi
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict
from audioknigi.download.network import SlidingSpeedMeter
from audioknigi.models import Book, SearchResult, TRACK_STATUS_DAMAGED, TRACK_STATUS_MISSING, TRACK_STATUS_PRESENT, TRACK_STATUS_READY, normalize_track_status
import types
from audioknigi.diagnostics import support_bundle as support_bundle__runtime_integrity_followup_20260912
from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.sources import normalize_supported_url
import re
from audioknigi.diagnostics import support_bundle as support_bundle__structured_hardening_20260912
from audioknigi.knigavuhe import _merge_narration_variants
from audioknigi.models import NarrationVariant, SearchResult, Track, TRACK_STATUS_MISSING
from audioknigi.providers import provider_for_key


# Origin: test_cancellation_cover_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_missing_uk_literals_are_complete():
    from audioknigi.i18n import ui_text
    assert ui_text('uk', 'Нет активной операции для отмены.') == 'Немає активної операції для скасування.'
    assert ui_text('uk', 'Очередь очищена.') == 'Чергу очищено.'


# Origin: test_external_review_hardening_20260928.py
ROOT = Path(__file__).resolve().parents[2]

def test_round59_source_contracts():
    media = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    network = (ROOT / 'audioknigi/download/network.py').read_text(encoding='utf-8')
    book_flow = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    event_sounds = (ROOT / 'audioknigi/qt/event_sounds.py').read_text(encoding='utf-8')
    track_model = (ROOT / 'audioknigi/qt/track_model.py').read_text(encoding='utf-8')
    clipboard = (ROOT / 'audioknigi/qt/mixins/clipboard.py').read_text(encoding='utf-8')
    queue = (ROOT / 'audioknigi/qt/mixins/queue.py').read_text(encoding='utf-8')
    analysis = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    settings_sync = (ROOT / 'audioknigi/qt/settings_sync.py').read_text(encoding='utf-8')
    application = (ROOT / 'audioknigi/qt/application.py').read_text(encoding='utf-8')
    player = (ROOT / 'audioknigi/qt/player_controller.py').read_text(encoding='utf-8')
    entry = (ROOT / 'audioknigi_qt.py').read_text(encoding='utf-8')
    assert 'normalize_cover_cache(self._cover_bytes(book))' in media
    assert 'last_observe = [0.0]' in network
    assert 'tag_jobs = []' in book_flow
    assert '_queued_configure = Signal(object, object, object)' in event_sounds
    assert 'def set_selected_indices' in track_model
    assert 'Qt.ItemDataRole.CheckStateRole' in track_model and 'Qt.ItemDataRole.AccessibleTextRole' in track_model
    assert 'previous_selection = list(self.track_model.selected_indices())' in clipboard
    assert 'self.queue_table.clearSelection()' in queue
    assert '_pending_narration_selected_all' in analysis
    assert 'old_count == len(book.tracks)' in analysis
    assert 'blocker = getattr(self.quality_combo, "blockSignals", None)' in settings_sync
    assert 'blocker = getattr(self.easy_quality_combo, "blockSignals", None)' in settings_sync
    assert 'app_logger.debug("Failed to build Qt crash report"' in application
    assert 'zero-duration instant completion' in player
    assert 'QCoreApplication.sendPostedEvents()' in entry
    assert 'send_posted_events(None' not in entry


# Origin: test_network_parser_retention_round6_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_template_with_space_before_literal_extension_stays_single_extension():
    from audioknigi.models import Book, Track
    from audioknigi.templates import render_track_filename
    book = Book(url='', title='Book', tracks=[])
    track = Track(index=1, title='Part 01.mp3', file='')
    assert render_track_filename('{Track_Title} .mp3', book, track) == 'Part 01.mp3'


# Origin: test_recovery_diagnostics_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_playwright_private_entry_uses_runtime_error_not_assert(monkeypatch):
    import audioknigi.services.book_analysis_service as module
    monkeypatch.setattr(module, 'sync_playwright', None)
    service = BookAnalysisService()
    with pytest.raises(RuntimeError, match='Playwright'):
        service._analyze_audioknigi_playwright('https://example.test')

def test_qt_selftest_uses_binding_safe_posted_event_flush():
    source = (ROOT / 'audioknigi_qt.py').read_text(encoding='utf-8')
    assert 'QCoreApplication.sendPostedEvents()' in source
    assert 'send_posted_events(None' not in source
    assert 'event_type=QEvent.Type.DeferredDelete' not in source


# Origin: test_release_integrity_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_missing_selected_tracks_error_reports_truncated_count():
    error = MissingSelectedTracksError(range(1, 16))
    message = str(error)
    assert '12' in message
    assert '(и ещё 3)' in message


# Origin: test_report_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_safe_float_rejects_non_finite_values():
    assert safe_float(float('nan'), 1.25) == 1.25
    assert safe_float(float('inf'), 2.5) == 2.5
    assert safe_float(float('-inf'), 3.75) == 3.75

def test_reported_hardening_changes_are_present_in_sources():
    book_flow = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    assert 'owned = re.compile(' in book_flow
    assert 'candidate.is_file() or not owned.fullmatch(candidate.name)' in book_flow
    assert 'self._scan_book_files(book, create_folder=False)' in book_flow
    player = (ROOT / 'audioknigi/qt/player_mixin.py').read_text(encoding='utf-8')
    assert 'startswith(("_source", "_repair"))' in player
    engine = (ROOT / 'audioknigi/download_engine.py').read_text(encoding='utf-8')
    assert 'tags.save(str(target))' in engine
    media = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    assert 'author = str(getattr(book, "author", "") or "").strip()' in media
    analysis = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    invalid_result_block = analysis[analysis.index('if not isinstance(book, Book):'):analysis.index('pending = self._pending_search_result')]
    assert 'self._queue_after_analysis = False' in invalid_result_block
    assert 'self._download_after_analysis = False' in invalid_result_block
    assert 'self._queue_reanalyze_task_id = None' in invalid_result_block
    assert 'self._full_mp3_after_analysis = False' in invalid_result_block

def test_analysis_service_uses_shared_subprocess_pipe_cleanup():
    source = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    helper = source[source.index('def _probe_remote_duration'):source.index('def _populate_missing_track_durations')]
    assert 'close_subprocess_pipes(proc)' in helper
    assert 'for stream_name in ("stdin", "stdout", "stderr")' not in helper


# Origin: test_report_followup_round10_20260916.py
ROOT = Path(__file__).resolve().parents[2]

class _Response:
    text = '<html><head><title>Тестовая книга</title></head><body>Исполнитель: Иван Иванов, Жанр: Фантастика</body></html>'

    def raise_for_status(self):
        return None

class _Session:

    def get(self, *args, **kwargs):
        return _Response()

def test_round10_source_hardening_contracts_are_present():
    probe = (ROOT / 'audioknigi/download/probe.py').read_text(encoding='utf-8')
    media = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    book_flow = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    workers = (ROOT / 'audioknigi/qt/workers.py').read_text(encoding='utf-8')
    analysis = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    audit = (ROOT / 'tools/qt_localization_audit.py').read_text(encoding='utf-8')
    assert 'resolved_path = file_path.resolve()' in probe
    assert 'safe_int(getattr(item, "index", None), -1) == track_index' in media
    assert 'track_index = safe_int(raw_index, -1)' in book_flow
    assert 'isinstance(value, (str, int, float, bool))' in book_flow
    assert 'normalize_cover_cache(raw_cover)' in workers
    assert 'self._l("Озвучка {index}", index=idx + 1)' in analysis.replace('\n', ' ') or 'Озвучка {index}' in analysis
    assert '"addItem"' in audit
    assert '_leading_constant_text' in audit


# Origin: test_report_followup_round12_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_retained_full_source_path_never_aliases_processed_target(tmp_path):
    target = tmp_path / 'Book (исходник).mp3'
    retained = _DownloadEngine._retained_full_source_path(tmp_path, 'Book', '.mp3', target)
    assert retained != target
    assert retained.name == 'Book (исходник, оригинал).mp3'


# Origin: test_report_followup_round13_20260916.py
def test_csv_export_neutralizes_formula_cells(tmp_path):
    from audioknigi.services.library_service import export_history
    target = export_history([{'date': '2026-09-16', 'title': '=1+1', 'author': '@cmd', 'narrator': '+reader', 'genre': '-formula', 'year': '2026', 'parts': 1, 'folder': 'C:/Books', 'url': 'https://example.test/book'}], tmp_path / 'history.csv', 'csv')
    with target.open('r', encoding='utf-8-sig', newline='') as handle:
        row = next(csv.DictReader(handle))
    assert row['title'] == "'=1+1"
    assert row['author'] == "'@cmd"
    assert row['narrator'] == "'+reader"
    assert row['genre'] == "'-formula"
    assert row['url'] == 'https://example.test/book'


# Origin: test_report_followup_round17_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_round17_formatting_hygiene_for_reported_pep8_rough_edges() -> None:
    crash = (ROOT / 'audioknigi/crash_report.py').read_text(encoding='utf-8')
    knigavuhe = (ROOT / 'audioknigi/knigavuhe.py').read_text(encoding='utf-8')
    assert 'import platform, sys, time, traceback' not in crash
    assert 'availability="available"' not in knigavuhe
    assert 'availability = "available"' in knigavuhe


# Origin: test_report_followup_round18_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_json_walk_handles_extreme_programmatic_depth_without_recursion() -> None:
    root: object = {'leaf': 1}
    for _ in range(2500):
        root = [root]
    nodes = list(_walk_json(root))
    assert nodes == [{'leaf': 1}]

def test_round18_explicit_cancel_stops_dropped_url_batch() -> None:
    source = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    cancelled = source.split('if kind == "cancelled":', 1)[1].split('if kind == "error":', 1)[0]
    assert 'self._pending_queue_urls = []' in cancelled
    assert 'self._queue_next_dropped_url' not in cancelled


# Origin: test_report_followup_round21_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_save_json_retries_transient_replace_lock(tmp_path, monkeypatch) -> None:
    target = tmp_path / 'settings.json'
    real_replace = core__report_followup_round21_20260917.os.replace
    attempts = {'count': 0}

    def flaky_replace(source, destination):
        if Path(destination) == target and attempts['count'] < 2:
            attempts['count'] += 1
            raise PermissionError('sharing violation')
        return real_replace(source, destination)
    monkeypatch.setattr(core__report_followup_round21_20260917.os, 'replace', flaky_replace)
    assert core__report_followup_round21_20260917.save_json(target, {'round': 21}, raise_errors=True)
    assert target.read_text(encoding='utf-8').strip().endswith('}')
    assert attempts['count'] == 2


# Origin: test_report_followup_round23_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def lifecycle_source() -> str:
    return (ROOT / 'audioknigi/qt/mixins/lifecycle.py').read_text(encoding='utf-8')

def test_exit_action_does_not_prearm_or_cancel_active_work_before_close_event_confirmation() -> None:
    source = lifecycle_source()
    start = source.index('def request_exit')
    end = source.index('def _notify_tray_if_hidden', start)
    body = source[start:end]
    assert 'self.close()' in body
    assert 'self._exit_requested = True' not in body
    assert 'self._cancel_all_workers_for_exit()' not in body
    assert 'UI LIFECYCLE | event=request_exit' in body

def test_deferred_exit_timeout_never_hard_kills_process() -> None:
    source = lifecycle_source()
    start = source.index('def closeEvent')
    end = source.index('__all__', start)
    body = source[start:end]
    assert 'os._exit' not in source
    assert 'event=deferred_exit_timeout' in body
    assert 'action=abort_close' in body
    assert 'self._exit_requested = False' in body
    assert 'event.ignore()' in body
    assert 'Закрытие отменено' in body

def test_confirmed_active_operation_still_uses_bounded_deferred_exit() -> None:
    source = lifecycle_source()
    assert '_EXIT_GRACE_SECONDS = 5.0' in source
    assert 'self._begin_deferred_exit()' in source
    assert 'self._cancel_all_workers_for_exit()' in source
    assert 'QTimer.singleShot(_EXIT_POLL_MS, self._poll_deferred_exit)' in source


# Origin: test_report_followup_round32_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round32_20260918(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

def test_cancelled_is_not_runtimeerror_and_stream_copy_fallback_cannot_swallow_it() -> None:
    assert not issubclass(Cancelled, RuntimeError)

def test_load_json_accepts_utf8_bom(tmp_path: Path) -> None:
    path = tmp_path / 'settings.json'
    path.write_bytes(b'\xef\xbb\xbf' + json.dumps({'ok': True}).encode('utf-8'))
    assert load_json(path, {}) == {'ok': True}


# Origin: test_report_followup_round33_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round33_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_zero_bytes_are_formatted_as_real_size() -> None:
    assert fmt_size(0) == '0.0 B'
    assert fmt_size(-1) == '—'

def test_template_tokens_are_case_insensitive() -> None:
    values = {'Author': 'Author', 'Book_Title': 'Book'}
    assert render_text_template('{author} - {BOOK_TITLE}', values) == 'Author - Book'

def test_track_filename_extension_handling_is_already_space_safe() -> None:
    core_source = src__report_followup_round33_20260918('audioknigi/core.py')
    templates = src__report_followup_round33_20260918('audioknigi/templates.py')
    assert 'name = re.sub(r"\\s+", " ", name).strip(". ")' in core_source
    assert '".ogg"' in templates and '".opus"' in templates

def test_fallback_log_labels_non_primary_failure_correctly() -> None:
    source = src__report_followup_round33_20260918('audioknigi/download/network.py')
    assert 'source_label = (' in source
    assert 'if pos == 1' in source
    assert 'f"Резервный источник ({source_name(url)})"' in source

def test_middle_shared_track_without_end_boundary_is_diagnosed() -> None:
    source = src__report_followup_round33_20260918('audioknigi/download/media.py')
    assert 'event=split_missing_middle_boundary' in source
    assert 'raise SharedSourceTimelineError' in source

def test_runtime_catalog_static_literal_duplicate_is_removed_but_prefix_fallback_is_retained() -> None:
    exact = json.loads((ROOT / 'audioknigi/locales/runtime_exact.json').read_text(encoding='utf-8'))
    prefixes = json.loads((ROOT / 'audioknigi/locales/runtime_prefixes.json').read_text(encoding='utf-8'))
    assert 'ID библиотеки Audiobookshelf' not in exact
    assert 'Скачивание завершено. Пропущены недоступные части: ' in prefixes


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_retry_all_failed_skips_tasks_requiring_analysis() -> None:
    source = src__report_followup_round34_20260919('audioknigi/qt/mixins/queue.py')
    block = source[source.index('def retry_all_failed'):source.index('def clear_queue')]
    assert 'if task.status_code == "error" and not task_requires_analysis(task):' in block


# Origin: test_report_followup_round44_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round44_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_atomic_temp_names_include_per_call_monotonic_token() -> None:
    common = src__report_followup_round44_20260920('audioknigi/download/common.py')
    assert common.count('time.monotonic_ns()') >= 2

def test_system_sound_worker_observes_shutdown_even_without_sentinel() -> None:
    source = src__report_followup_round44_20260920('audioknigi/qt/event_sounds.py')
    worker_start = source.index('def _system_sound_worker')
    worker_end = source.index('def play_system', worker_start)
    worker = source[worker_start:worker_end]
    assert 'if self._system_shutdown.is_set():' in worker
    assert 'if flag is None:' in worker
    assert worker.count('if self._system_shutdown.is_set():') >= 2


# Origin: test_report_followup_round45_20260921.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round45_20260921(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

class _SplitDummy(MediaProcessingMixin):

    def __init__(self, target: Path):
        self.target = target

    def _track_path(self, _book, _track):
        return self.target

    def log(self, _message):
        pass

def test_shared_source_middle_track_requires_strictly_increasing_boundary(tmp_path) -> None:
    first = Track(index=1, title='One', file='https://cdn.test/book.mp3', start=0)
    second = Track(index=2, title='Two', file='https://cdn.test/book.mp3', start=0)
    book = Book(url='https://example.test/book', title='Book', tracks=[first, second])
    with pytest.raises(SharedSourceTimelineError) as exc:
        _SplitDummy(tmp_path / '1.mp3')._split_track(book, first, tmp_path / 'source.mp3')
    assert exc.value.issue['reason'] == 'non_increasing_middle_boundary'


# Origin: test_report_followup_round46_20260922.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round46_20260922(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_native_event_filter_rejects_null_message_pointer_before_from_address() -> None:
    source = src__report_followup_round46_20260922('audioknigi/qt/media_keys.py')
    start = source.index('def nativeEventFilter')
    block = source[start:]
    assert 'address = int(message)' in block
    assert 'if not address:' in block
    assert 'wintypes.MSG.from_address(address)' in block
    assert block.index('if not address:') < block.index('wintypes.MSG.from_address(address)')


# Origin: test_report_followup_round47_20260923.py
def test_support_log_multiline_path_does_not_collapse_whole_log(monkeypatch):
    monkeypatch.setattr(support_bundle__report_followup_round47_20260923.os, 'name', 'nt', raising=False)
    monkeypatch.setattr(support_bundle__report_followup_round47_20260923.Path, 'home', classmethod(lambda cls: Path('C:\\\\Users\\\\Alice')))
    raw = b'D:\\Books\\broken.mp3\r\nsecond diagnostic line\r\n'
    cleaned = support_bundle__report_followup_round47_20260923._sanitize_log_bytes(raw).decode('utf-8')
    assert cleaned != '<configured-path>'
    assert 'second diagnostic line' in cleaned
    assert 'D:\\' not in cleaned

def test_safe_int_accepts_integer_like_decimal_but_not_fractional():
    assert safe_int('12.0', 7) == 12
    assert safe_int('12.5', 7) == 7


# Origin: test_report_followup_round49_20260924.py
class _FallbackHost(SourceAnalysisMixin):
    cancel_event = None
    _book_identity_hints = staticmethod(BookAnalysisService._book_identity_hints)
    _identity_tokens = staticmethod(BookAnalysisService._identity_tokens)

    def _check_cancel(self) -> None:
        return None

def test_smart_format_log_explains_no_lossy_upsampling() -> None:

    class Dummy(MediaProcessingMixin):
        runtime_audio_preset = '128k_stereo'
        runtime_normalization_mode = 'off'

        def __init__(self):
            self.messages: list[str] = []

        def _cached_probe_audio_info(self, _source):
            return {'codec': 'mp3', 'bit_rate': 64000, 'channels': 1}

        def log(self, message):
            self.messages.append(str(message))
    dummy = Dummy()
    copy_mode, bitrate, channels = dummy._effective_mp3_profile('source.mp3')
    assert (copy_mode, bitrate, channels) == (True, None, None)
    message = ' '.join(dummy.messages)
    assert 'не хуже' not in message
    assert 'повышать' in message
    assert 'без потери качества' in message


# Origin: test_report_followup_round52_20260924.py
def test_qt_entrypoint_normalizes_none_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    import audioknigi_qt
    fake = ModuleType('audioknigi.qt.application')
    fake.run_qt = lambda _argv: None
    monkeypatch.setitem(sys.modules, 'audioknigi.qt.application', fake)
    monkeypatch.setattr(sys, 'argv', ['audioknigi_qt.py'])
    assert audioknigi_qt.main() == 0


# Origin: test_report_followup_round53_20260926.py
def test_source_package_keeps_fixtures_but_not_nested_private_state_or_binaries(tmp_path):
    root = tmp_path / 'project'
    names = ['tests/fixtures/settings.json', 'tests/fixtures/nested/history.json', 'settings.json', 'profile/cookies.json', 'plugins/module.pyd', 'native/lib.so', 'native/LIB.DLL', 'app.py']
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'fixture')
    output = package_source_release.build_source_zip(root, tmp_path / 'source.zip', root_name='src')
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == {'src/tests/fixtures/settings.json', 'src/tests/fixtures/nested/history.json', 'src/app.py'}

def test_missing_audio_message_preserves_zero_index(tmp_path, monkeypatch):
    monkeypatch.setattr(book_flow, 'resolve_executable', lambda name: 'ffmpeg')

    class Flow(book_flow.BookFlowMixin):

        def _check_cancel(self):
            pass

        def _scan_book_files(self, *args, **kwargs):
            pass

        def _check_disk_space(self, *args, **kwargs):
            return True

        def _write_resume_manifest(self, *args):
            pass

        def _book_folder(self, *args):
            return tmp_path

        def _log_book_flow(self, *args, **kwargs):
            pass
    book = Book(url='https://example.invalid/book', title='Book', tracks=[Track(index=0, title='Prologue', file='', local_status='missing')])
    with pytest.raises(RuntimeError, match='частей: 0\\.'):
        Flow()._process_book_once(book, [0])

@pytest.mark.parametrize('selection', ['all', '*', ['all'], ['*'], [0, 'all']])
def test_space_estimation_all_markers_include_entire_book(tmp_path, selection):

    class Probe(ProbeMixin):

        def _book_folder(self, *args, **kwargs):
            return tmp_path
    book = Book(url='https://example.invalid/book', title='Book', tracks=[Track(index=0, title='Zero', file='https://example.invalid/0.mp3', duration=10, local_status='missing'), Track(index=1, title='One', file='https://example.invalid/1.mp3', duration=20, local_status='missing')])
    probe = Probe()
    assert probe._estimate_required_space(book, selection) == probe._estimate_required_space(book)
    assert probe._estimate_required_space(book) > probe._estimate_required_space(book, [0]) > 0

@pytest.mark.parametrize('selection', [[True], ['bad'], [-1], ['1.5']])
def test_space_estimation_rejects_invalid_selection_instead_of_underestimating(selection):
    book = Book(url='https://example.invalid/book', title='Book')
    with pytest.raises(ValueError, match='Invalid selected track index'):
        ProbeMixin()._estimate_required_space(book, selection)

@pytest.mark.parametrize('candidate_valid', [False, True])
def test_acceptance_status_displays_existing_report_without_rewriting(tmp_path, monkeypatch, capsys, candidate_valid):
    exe = tmp_path / 'app.exe'
    exe.write_bytes(b'current binary')
    report_path = tmp_path / 'report.json'
    report = qt_windows_acceptance._new_report(exe)
    report['exe_sha256'] = '0' * 64
    raw = json.dumps(report).encode('utf-8')
    report_path.write_bytes(raw)
    if candidate_valid:
        monkeypatch.setattr(qt_windows_acceptance, 'validate_candidate_manifest', lambda *a, **kw: {})
    result = qt_windows_acceptance.main(['--exe', str(exe), '--report', str(report_path), '--candidate-manifest', str(tmp_path / 'missing.json'), '--status', '--allow-non-windows'])
    out = capsys.readouterr().out
    assert result == (1 if candidate_valid else 43)
    assert 'INCOMPLETE' in out
    assert '0' * 64 in out
    assert ('Release-candidate manifest rejected' in out) is not candidate_valid
    assert report_path.read_bytes() == raw

@pytest.mark.parametrize('newline', ['\n', '\r\n'])
def test_support_tail_keeps_short_utf8_content_for_both_line_endings(tmp_path, newline):
    from audioknigi.diagnostics.support_bundle import _tail
    text = newline.join(['строка один', 'строка два', 'строка три', ''])
    path = tmp_path / 'app.log'
    path.write_bytes(text.encode('utf-8'))
    payload = _tail(path, max_bytes=20)
    assert 0 < len(payload) <= 20
    assert payload.decode('utf-8') in text
    assert not payload.decode('utf-8').startswith('ока')


# Origin: test_report_followup_round54_20260926.py
def test_support_tail_keeps_complete_following_line_after_truncated_prefix(tmp_path):
    path = tmp_path / 'app.log'
    path.write_bytes(('X' * 80 + '\r\n' + 'safe final diagnostic\r\n').encode('utf-8'))
    payload = _tail(path, max_bytes=30)
    assert payload.decode('utf-8') == 'safe final diagnostic\r\n'

@pytest.mark.parametrize('selection', [[1.5], [float('nan')], [float('inf')], 1.5, True])
def test_space_estimation_rejects_fractional_nonfinite_and_boolean_indices(selection):
    book = Book(url='https://example.invalid/book', title='Book')
    with pytest.raises(ValueError, match='Invalid selected track index'):
        ProbeMixin()._estimate_required_space(book, selection)

def test_space_estimation_accepts_scalar_integer_index(tmp_path):

    class Probe(ProbeMixin):

        def _book_folder(self, *args, **kwargs):
            return tmp_path
    book = Book(url='https://example.invalid/book', title='Book', tracks=[Track(index=0, title='Zero', file='https://example.invalid/0.mp3', duration=10), Track(index=1, title='One', file='https://example.invalid/1.mp3', duration=20)])
    probe = Probe()
    assert probe._estimate_required_space(book, 1) == probe._estimate_required_space(book, [1])

def test_acceptance_issues_treat_malformed_schema_as_incomplete():
    report = {'schema': [], 'app_version': '', 'platform': 'windows', 'automated': {}, 'screen_readers': {}}
    issues = acceptance_issues(report, app_version='', require_windows=True)
    assert 'unsupported acceptance schema' in issues

def test_acceptance_main_returns_43_for_malformed_candidate_schema(tmp_path, monkeypatch):
    exe = tmp_path / 'app.exe'
    exe.write_bytes(b'binary')
    manifest = tmp_path / 'candidate.json'
    manifest.write_text(json.dumps({'schema': []}), encoding='utf-8')
    report = tmp_path / 'report.json'
    result = qt_windows_acceptance.main(['--exe', str(exe), '--report', str(report), '--candidate-manifest', str(manifest), '--allow-non-windows', '--automated-only'])
    assert result == 43


# Origin: test_report_followup_round5_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_round5_static_hardening_contracts_are_present():
    book_flow = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    assert 'getattr(self, "runtime_delete_source", True)' in book_flow
    assert 'getattr(self, "runtime_delete_source", False)' not in book_flow
    network = (ROOT / 'audioknigi/download/network.py').read_text(encoding='utf-8')
    report_block = network[network.index('def report(delta, force=False):'):network.index('jobs = queue.Queue()')]
    assert 'with progress_lock:' in report_block
    assert 'last_target[0] = target_workers' in report_block
    probe = (ROOT / 'audioknigi/download/probe.py').read_text(encoding='utf-8')
    assert '"packet=pts_time,dts_time"' in probe
    queue_ui = (ROOT / 'audioknigi/qt/mixins/queue.py').read_text(encoding='utf-8')
    assert 'def _same_supported_url' in queue_ui
    assert 'normalize_supported_url' in queue_ui
    assert 'task.url.rstrip("/") == url.rstrip("/")' not in queue_ui
    analysis = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    assert 'pending_url = normalize_supported_url' in analysis
    assert 'force_redownload' in analysis
    main_window = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    easy = main_window[main_window.index('def easy_add_another_book'):main_window.index('def _play_event_sound')]
    assert 'self.book_url_edit.clear()' in easy
    prefixes = json.loads((ROOT / 'audioknigi/locales/runtime_prefixes.json').read_text(encoding='utf-8'))
    assert 'Обрабатываю полный файл' not in prefixes


# Origin: test_report_followup_round9_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_round9_source_hardening_contracts():
    network = (ROOT / 'audioknigi' / 'download' / 'network.py').read_text(encoding='utf-8')
    assert 'part.name + ".segments.json"' in network
    assert '"url": str(url or "")' in network
    assert '"total_size": int(total_size)' in network
    player = (ROOT / 'audioknigi' / 'qt' / 'player_controller.py').read_text(encoding='utf-8')
    assert 'self._resume_after_stop_ms > 0' in player
    assert 'PlaybackState.StoppedState' in player
    pages = (ROOT / 'audioknigi' / 'qt' / 'main_window.py').read_text(encoding='utf-8')
    assert 'self._easy_input_is_stale = easy_stale' in pages
    access = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'accessibility_ui.py').read_text(encoding='utf-8')
    assert 'window_ref = weakref.ref(self)' in access
    media = (ROOT / 'audioknigi' / 'download' / 'media.py').read_text(encoding='utf-8')
    assert 'clean_graph = str(filter_complex).strip().rstrip(";").rstrip()' in media
    accessibility_audit = (ROOT / 'audioknigi' / 'qt' / 'accessibility_audit.py').read_text(encoding='utf-8')
    required_block = accessibility_audit.split('REQUIRED_ACCESSIBLE_IDS = (', 1)[1].split(')\n\n', 1)[0]
    focusable_block = accessibility_audit.split('FOCUSABLE_ACCESSIBLE_IDS = (', 1)[1].split(')\n', 1)[0]
    for identifier in ('cancel_search', 'easy_cancel_search', 'toggle_session_log'):
        assert f'"{identifier}"' in required_block
        assert f'"{identifier}"' in focusable_block
    for identifier in ('download_book', 'download_full_mp3', 'add_book_to_queue'):
        assert f'"{identifier}"' in required_block
        assert f'"{identifier}"' not in focusable_block


# Origin: test_round4_circular_import_20260915.py
def test_book_analysis_service_can_be_imported_from_clean_interpreter():
    root = Path(__file__).resolve().parents[2]
    code = 'from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService; from audioknigi.services.queue_service import QueueStore, QueueTask; print(AnalysisOptions.__name__, BookAnalysisService.__name__, QueueStore.__name__, QueueTask.__name__)'
    proc = subprocess.run([sys.executable, '-c', code], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
    assert proc.returncode == 0, proc.stderr
    assert 'AnalysisOptions BookAnalysisService QueueStore QueueTask' in proc.stdout


# Origin: test_round55_accessibility_guidance_20260926.py
ROOT = Path(__file__).resolve().parents[2]

class _FakeProvider:

    def __init__(self, key: str, display_name: str, barrier: threading.Barrier, delay: float=0.0):
        self.key = key
        self.display_name = display_name
        self._barrier = barrier
        self._delay = delay

    def search(self, query: str, *, cancel_event=None):
        self._barrier.wait(timeout=1.5)
        if self._delay:
            time.sleep(self._delay)
        return [SearchResult(title=f'{self.display_name} {query}', url=f'https://example.invalid/{self.key}', source=self.display_name)]

    def enrich_search_results(self, results, *, cancel_event=None):
        return list(results)

def test_all_sources_unavailable_message_includes_vpn_and_warp_guidance():
    source = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'Proton VPN' in source
    assert 'Mullvad VPN' in source
    assert 'Cloudflare WARP' in source
    assert 'не позволяет выбрать другую страну' in source
    assert 'self._show_message(QMessageBox.Icon.Warning' in source
    assert 'announce_now=True' in source


# Origin: test_round57_selftest_finally_20260926.py
ROOT = Path(__file__).resolve().parents[2]

ENTRYPOINT = ROOT / 'audioknigi_qt.py'

def test_qt_entrypoint_compiles_with_syntaxwarnings_as_errors():
    result = subprocess.run([sys.executable, '-W', 'error::SyntaxWarning', '-m', 'py_compile', str(ENTRYPOINT)], cwd=ROOT, text=True, capture_output=True, timeout=30, check=False)
    combined = (result.stdout or '') + '\n' + (result.stderr or '')
    assert result.returncode == 0, combined
    assert 'SyntaxWarning' not in combined

def test_async_callback_failure_check_runs_after_finally():
    source = ENTRYPOINT.read_text(encoding='utf-8')
    finally_pos = source.index('    finally:\n', source.index('def _qt_accessibility_selftest'))
    async_check_pos = source.index('    if async_callback_errors:', finally_pos)
    playwright_pos = source.index('\ndef _playwright_edge_selftest', async_check_pos)
    assert finally_pos < async_check_pos < playwright_pos
    finally_tail = source[finally_pos:async_check_pos]
    assert 'return 26' not in finally_tail
    assert 'return 0' not in finally_tail


# Origin: test_round58_dns_resilience_20260928.py
ROOT = Path(__file__).resolve().parents[2]

def _system_fake(host, port, family=0, type=0, proto=0, flags=0):
    host = str(host)
    if host == 'example.com' or host.endswith('.example'):
        address = '203.0.113.44'
    else:
        address = host
    fam = socket.AF_INET6 if ':' in address else socket.AF_INET
    return [(fam, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (address, port))]

def setup_function(_function):
    network_dns.configure_dns_mode('auto')
    network_dns._reset_dns_runtime_state()

def teardown_function(_function):
    network_dns.configure_dns_mode('auto')
    network_dns._reset_dns_runtime_state()

def test_round58_timeout_and_circuit_are_bounded():
    assert 0.5 <= network_dns.CLOUDFLARE_DOH_TIMEOUT <= 2.0
    assert network_dns.CLOUDFLARE_FAILURE_THRESHOLD == 3
    assert network_dns.CLOUDFLARE_CIRCUIT_COOLDOWN_SECONDS == 300.0


# Origin: test_round62_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_audio_info_cache_refreshes_hits_before_eviction(tmp_path, monkeypatch):
    from audioknigi.download import media as media_module
    monkeypatch.setattr(media_module, '_AUDIO_INFO_CACHE_MAX', 2)

    class Harness(MediaProcessingMixin):

        def __init__(self):
            self.calls = []

        def _probe_audio_info(self, path):
            self.calls.append(Path(path).name)
            return {'codec': 'mp3', 'channels': 2, 'bit_rate': 128000}
    files = [tmp_path / name for name in ('one.mp3', 'two.mp3', 'three.mp3')]
    for index, path in enumerate(files):
        path.write_bytes(bytes([index + 1]))
    harness = Harness()
    harness._cached_probe_audio_info(files[0])
    harness._cached_probe_audio_info(files[1])
    harness._cached_probe_audio_info(files[0])
    harness._cached_probe_audio_info(files[2])
    cached_paths = {key[0] for key in harness._audio_info_cache}
    assert str(files[0].resolve()) in cached_paths
    assert str(files[2].resolve()) in cached_paths
    assert str(files[1].resolve()) not in cached_paths


# Origin: test_round63_followup_20260929.py
def test_blank_folder_template_is_intentionally_normalized_to_default():
    assert normalize_settings({'folder_template': ''})['folder_template'] == '{Book_Title}'


# Origin: test_round64_qt_fontdir_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_round64_does_not_bundle_font_files():
    build_bat = (ROOT / 'build_qt_exe.bat').read_text(encoding='utf-8').casefold()
    build_ps1 = (ROOT / 'build_qt_ci.ps1').read_text(encoding='utf-8').casefold()
    assert 'dejavu' not in build_bat + build_ps1
    assert 'copy' not in '\n'.join((line for line in (build_bat + '\n' + build_ps1).splitlines() if 'font' in line))


# Origin: test_round65_poleknig_search_relevance_20260929.py
def _run_search(monkeypatch, query: str, rows: list[SearchResult], *, author_expanded=None):
    response = SimpleNamespace(text='', url='https://poleknig.com/search/')
    monkeypatch.setattr(poleknig, '_fetch_search_page', lambda *_a, **_k: response)
    monkeypatch.setattr(poleknig, '_search_last_page', lambda *_a, **_k: 1)
    monkeypatch.setattr(poleknig, 'parse_search_results', lambda *_a, **_k: list(rows))
    monkeypatch.setattr(poleknig, '_hydrate_search_result_info', lambda item: (item, []))
    monkeypatch.setattr(poleknig, '_book_page_author_links', lambda *_a, **_k: [])
    monkeypatch.setattr(poleknig, '_expand_matching_author_catalogs', lambda *_a, **_k: list(author_expanded or []))
    return poleknig.search(query)

def test_exact_title_is_ranked_before_partial_title(monkeypatch):
    rows = [SearchResult(title='Кошачий закон и порядок', author='Автор 1', url='https://poleknig.com/books/1', source='poleknig.com'), SearchResult(title='Закон и порядок', author='Автор 2', url='https://poleknig.com/books/2', source='poleknig.com'), SearchResult(title='Наемник: Закон и порядок', author='Автор 3', url='https://poleknig.com/books/3', source='poleknig.com')]
    results = _run_search(monkeypatch, 'Закон и порядок', rows)
    assert results[0].title == 'Закон и порядок'
    assert {item.title for item in results[1:]} == {'Кошачий закон и порядок', 'Наемник: Закон и порядок'}


# Origin: test_round66_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_transient_message_boxes_are_scheduled_for_cleanup():
    source = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    start = source.index('def _show_message')
    end = source.index('@Slot(bool)', start)
    block = source[start:end]
    assert block.count('box.deleteLater()') >= 2
    assert block.count('result = box.standardButton(box.clickedButton())') >= 2


# Origin: test_round67_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_zero_next_start_is_preserved_in_shared_source_error_payload():
    source = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    assert '"expected_end": float(next_start if next_start is not None else start)' in source
    assert 'float(next_start or start)' not in source


# Origin: test_round68_creator_metadata_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_creator_identity_constants_are_canonical():
    assert AUTHOR_NAME == 'Едуард Саратовцев'
    assert AUTHOR_EMAIL == 'serioussem39@gmail.com'
    assert AUTHOR_GITHUB_URL == 'https://github.com/nefonit'
    assert PROJECT_URL == 'https://github.com/nefonit/AudioKnigi-Downloader'
    assert COPYRIGHT_YEAR == 2026


# Origin: test_round70_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_retained_repair_promotes_fresh_source_to_canonical_path():
    source = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    assert 'not bool(getattr(self, "runtime_delete_source", True))' in source
    assert 'replace_with_retry(src, original_source)' in source
    assert 'src = Path(original_source)' in source

def test_manifest_boundary_error_does_not_trigger_wrong_source_fallback():
    source = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    start = source.index('except SharedSourceTimelineError as exc:')
    block = source[start:source.index('if source_key(', start) + 120]
    assert 'issue.get("reason") == "non_increasing_middle_boundary"' in block
    assert 'Повторите анализ книги или выберите другой источник.' in block

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


# Origin: test_round71_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_zero_hydration_limit_does_not_construct_zero_worker_pool(monkeypatch):
    source = SearchResult(title='Demo', author='Author', narrator='', url='https://audioknigi.com.ua/audio-1-demo', source='audioknigi.com.ua')
    monkeypatch.setattr(audioknigi_search, '_MAX_HYDRATED_SEARCH_RESULTS', 0)
    rows = audioknigi_search._group_audioknigi_recordings([source])
    assert rows

def test_missing_next_boundary_remains_a_shared_source_integrity_error(tmp_path):

    class Harness(MediaProcessingMixin):

        def _track_path(self, _book, track):
            return tmp_path / f'{track.index}.mp3'
    tracks = [Track(index=1, title='One', file='shared.mp3', start=0.0), Track(index=2, title='Two', file='shared.mp3', start=None)]
    book = Book(url='https://example.invalid/book', title='Book', tracks=tracks)
    with pytest.raises(SharedSourceTimelineError):
        Harness()._split_track(book, tracks[0], tmp_path / 'shared.mp3')

def test_round70_fixes_remain_present():
    player = (ROOT / 'audioknigi/qt/player_mixin.py').read_text(encoding='utf-8')
    engine = (ROOT / 'audioknigi/download_engine.py').read_text(encoding='utf-8')
    progress = (ROOT / 'audioknigi/qt/search_progress.py').read_text(encoding='utf-8')
    settings = (ROOT / 'audioknigi/qt/mixins/settings.py').read_text(encoding='utf-8')
    assert '"cover.webp"' in player
    assert 'selected_indices=list(getattr(self.request, "selected_indices", None) or full_indices)' in engine
    assert 'except OSError:' in engine[engine.index('def duplicate_preflight'):engine.index('def delete_existing_outputs')]
    assert 'if side < 16:' in progress
    assert 'replace_all(updated)' in settings


# Origin: test_round72_search_sorting_availability_layout_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def _result(title: str, *, author: str='', narrator: str='', availability: str='') -> SearchResult:
    return SearchResult(title=title, author=author, narrator=narrator, availability=availability, url=f'https://example.invalid/{title}', source='demo')

def test_restricted_and_unavailable_results_are_filtered_but_unknown_is_preserved():
    rows = [_result('Available', availability='available'), _result('Restricted', availability='restricted'), _result('Unavailable', availability='unavailable'), _result('Unknown', availability='')]
    kept = downloadable_search_results(rows)
    assert [item.title for item in kept] == ['Available', 'Unknown']


# Origin: test_round74_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_runtime_template_with_named_count_is_already_exact_format_safe():
    from audioknigi.i18n import ui_text
    assert ui_text('en', 'Найдено вариантов озвучки: {count}. Выберите чтеца.', count=3) == 'Narration options found: 3. Choose a narrator.'

def test_round73_high_value_fixes_remain_present():
    library = (ROOT / 'audioknigi/services/library_service.py').read_text(encoding='utf-8')
    assert '_history_rows(data, strict=True, limit=None)' in library
    engine = (ROOT / 'audioknigi/download_engine.py').read_text(encoding='utf-8')
    full = engine[engine.index('def run_full_mp3'):engine.index('def run(self)')]
    assert 'if source_ready:' in full
    assert 'tags.delall("TRCK")' in full
    media = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    split = media[media.index('def _split_track'):media.index('def _save_book_sidecars')]
    assert 'unlink_with_retry(out, missing_ok=True)' in split


# Origin: test_round75_external_review_followup_20261003.py
ROOT = Path(__file__).resolve().parents[2]

def test_book_fallback_skips_malformed_track_indices_instead_of_crashing():
    original = Book(url='https://audioknigi.com.ua/audio-1-demo', title='Original', tracks=[Track(index=1, title='One', file='https://cdn.invalid/shared.mp3'), Track(index=2, title='Broken', file='https://cdn.invalid/shared.mp3')])
    original.tracks[1].index = None
    fallback = Book(url='https://knigavuhe.org/book/demo/', title='Fallback', tracks=[Track(index=1, title='One', file='https://cdn.invalid/fallback.mp3'), Track(index=2, title='Broken', file='https://cdn.invalid/fallback.mp3')])
    fallback.tracks[1].index = 'not-an-index'

    class Harness(BookFlowMixin):

        def __init__(self):
            self.calls = 0

        def _process_book_once(self, book, active_selected, status_callback):
            self.calls += 1
            if self.calls == 1:
                raise SharedSourceTimelineError({'reason': 'invalid_last_boundary', 'expected_end': 10.0, 'actual_duration': 5.0})
            return (book, set(active_selected))

        def _clear_stale_source_downloads(self, _book):
            return 0

        def _knigavuhe_fallback_candidate(self, _book):
            return fallback

        def _remove_resume_manifest(self, _book):
            return None

        def _populate_missing_track_durations(self, _book):
            return 0

        def _log_book_flow(self, *args, **kwargs):
            return None

        def log(self, _message):
            return None
    result_book, selected = Harness()._process_book(original)
    assert result_book is fallback
    assert selected == {1}

def test_expired_source_mapping_uses_normalized_url_and_safe_indices():
    source = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    assert 'if tr.file == url' not in source
    assert 'if str(getattr(tr, "file", "") or "") == url' in source
    assert 'safe_int(getattr(tr, "index", None), -1)' in source


# Origin: test_round77_external_review_followup_20261004.py
ROOT = Path(__file__).resolve().parents[2]

def test_integrations_json_decode_error_uses_old_requests_safe_fallback():
    source = (ROOT / 'audioknigi/integrations.py').read_text(encoding='utf-8')
    assert '_JSONDecodeError = getattr(requests.exceptions, "JSONDecodeError", ValueError)' in source
    assert 'except (ValueError, _JSONDecodeError) as exc:' in source

def test_template_track_index_rejects_bool_field_values():
    assert _safe_track_index({'index': True}) == 0
    assert _safe_track_index({'index': False}) == 0
    assert _safe_track_index({'index': '7'}) == 7

def test_locale_catalog_has_no_reported_duplicate_or_prefix_regex_conflict():
    exact_path = ROOT / 'audioknigi/locales/runtime_exact.json'
    raw = exact_path.read_text(encoding='utf-8')
    assert raw.count('"Проверить системный звук"') == 1
    prefixes = json.loads((ROOT / 'audioknigi/locales/runtime_prefixes.json').read_text(encoding='utf-8'))
    regex_rows = json.loads((ROOT / 'audioknigi/locales/runtime_regex.json').read_text(encoding='utf-8'))
    prefix = 'Скачивание завершено. Пропущены недоступные части: '
    assert prefix in prefixes
    assert any(('Пропущены недоступные части' in row[0] for row in regex_rows))
    i18n_source = (ROOT / 'audioknigi/i18n.py').read_text(encoding='utf-8')
    assert i18n_source.index('for pattern, variants in _PHASE29_RUNTIME_REGEX') < i18n_source.index('for prefix, variants in _PHASE29_RUNTIME_PREFIXES.items()')

def test_reviewed_locale_wording_is_consistent():
    legacy = json.loads((ROOT / 'audioknigi/locales/legacy_literals.json').read_text(encoding='utf-8'))
    assert legacy['en']['Выделить всё'] == 'Select all'
    assert all(('озвучк' not in value.casefold() for value in legacy['uk'].values()))
    exact = json.loads((ROOT / 'audioknigi/locales/runtime_exact.json').read_text(encoding='utf-8'))
    assert exact['Аннотация выбранной книги']['de'] == 'Beschreibung des ausgewählten Buchs'


# Origin: test_round78_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_blank_track_titles_keep_unique_template_fallbacks():
    book = Book(url='https://example.invalid/book', title='Book', tracks=[Track(index=1, title=' ', file='x'), Track(index=2, title='\t', file='y')])
    assert template_values(book, book.tracks[0])['Track_Title'] == 'track-01'
    assert template_values(book, book.tracks[1])['Track_Title'] == 'track-02'

def test_speed_graph_reserves_label_area_using_font_metrics():
    source = (ROOT / 'audioknigi/qt/speed_graph.py').read_text(encoding='utf-8')
    assert 'metrics = painter.fontMetrics()' in source
    assert 'label_baseline = min(max(2, metrics.ascent() + 2), max(2, self.height() - 2))' in source
    assert 'graph_top = min(max(7, metrics.height() + 4), max(1, self.height() - 3))' in source
    assert 'painter.drawText(7, label_baseline' in source


# Origin: test_round79_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_process_book_accepts_primitive_string_indices():

    class Harness(BookFlowMixin):

        def _process_book_once(self, book, active_selected, status_callback=None):
            return (book, set(active_selected))

        def log(self, _text):
            pass
    book = Book(url='https://example.invalid/book', title='Demo', tracks=[Track(index=0, title='Prologue', file='x'), Track(index=1, title='Chapter', file='y')])
    _book, selected = Harness()._process_book(book, ['0', '1'])
    assert selected == {0, 1}

def test_process_book_once_accepts_mapping_tracks_and_string_selection(monkeypatch):

    class Harness(BookFlowMixin):

        def _check_cancel(self):
            pass

        def _scan_book_files(self, *_args, **_kwargs):
            pass

        def _estimate_required_space(self, *_args, **_kwargs):
            return 0

        def _disk_free_for_path(self, *_args, **_kwargs):
            return 10 ** 9

        def _book_folder(self, *_args, **_kwargs):
            return ROOT

        def set_status(self, *_args, **_kwargs):
            pass

        def set_progress(self, *_args, **_kwargs):
            pass

        def set_stage(self, *_args, **_kwargs):
            pass

        def log(self, *_args, **_kwargs):
            pass
    monkeypatch.setattr('audioknigi.download.book_flow.resolve_executable', lambda _name: '/ffmpeg')
    harness = Harness()
    harness._scan_book_files = lambda book, create_folder=False: (_ for _ in ()).throw(RuntimeError('selection-ok'))
    book = SimpleNamespace(tracks=[{'index': '0', 'title': 'P', 'file': 'x'}])
    with pytest.raises(RuntimeError, match='selection-ok'):
        harness._process_book_once(book, ['0'])

def test_reported_already_fixed_round78_items_remain_fixed():
    source = (ROOT / 'audioknigi/knigavuhe.py').read_text(encoding='utf-8')
    grouping = source[source.index('grouped: dict'):source.index('unique: list', source.index('grouped: dict'))]
    assert 'groups[key]' not in grouping
    assert 'grouped[key]' in grouping
    speed = (ROOT / 'audioknigi/qt/speed_graph.py').read_text(encoding='utf-8')
    assert 'fontMetrics()' in speed and 'label_baseline' in speed


# Origin: test_round80_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_missing_source_diagnostic_survives_malformed_index(monkeypatch, tmp_path):
    track = Track(index=0, title='Prologue', file='', local_status='missing')
    book = Book(url='https://example.invalid/book', title='Demo', tracks=[track])

    class Harness(BookFlowMixin):
        runtime_audio_preset = 'copy'
        runtime_normalization_mode = 'off'
        runtime_embed_tags = False
        runtime_save_sidecars = True
        runtime_delete_source = True

        def _check_cancel(self):
            pass

        def _scan_book_files(self, current, create_folder=False):
            current.tracks[0].index = None

        def _check_disk_space(self, *_args, **_kwargs):
            return True

        def _write_resume_manifest(self, *_args, **_kwargs):
            pass

        def _book_folder(self, *_args, **_kwargs):
            return tmp_path

        def _log_book_flow(self, *_args, **_kwargs):
            pass

        def log(self, *_args, **_kwargs):
            pass
    monkeypatch.setattr('audioknigi.download.book_flow.resolve_executable', lambda _name: '/ffmpeg')
    with pytest.raises(RuntimeError, match='отсутствует адрес аудиофайла для частей: 1'):
        Harness()._process_book_once(book, [0])

def test_i18n_exact_precedes_regex_and_regex_precedes_prefix():
    exact = 'Анализирую audioknigi.com.ua быстрым HTTP-способом…'
    assert localize_runtime_text('en', exact) == 'Analyzing audioknigi.com.ua using the fast HTTP method…'
    assert localize_runtime_text('en', 'История обновлена: 12 записей.') == 'History refreshed: 12 entries.'
    assert localize_runtime_text('en', 'Скачано 15 MB из 100 MB') == 'Downloaded 15 MB of 100 MB'


# Origin: test_round81_external_review_followup_20261006.py
ROOT = Path(__file__).resolve().parents[2]

def test_source_analysis_candidate_unpacking_uses_url_key(monkeypatch):
    seen = []
    result = SimpleNamespace(title='Demo Book', author='Author Name', narrator='Reader Name', url='https://knigavuhe.org/book/demo/', narration_variants=[])
    fallback = SimpleNamespace(title='Demo Book', author='Author Name', narrator='Reader Name', url=result.url)
    monkeypatch.setattr(source_analysis_module__round81_external_review_followup_20261006, 'search_knigavuhe_books', lambda *_a, **_k: [result])

    class Provider:

        def fetch_book(self, url, cancel_event=None):
            seen.append(url)
            return fallback
    monkeypatch.setattr(source_analysis_module__round81_external_review_followup_20261006, 'provider_for_key', lambda _key: Provider())

    class Harness(SourceAnalysisMixin):
        cancel_event = None

        def _check_cancel(self):
            pass

        @staticmethod
        def _identity_tokens(value):
            return [token for token in str(value or '').casefold().split() if token]

        @staticmethod
        def _book_identity_hints(book):
            return (book.title, book.author, book.narrator)
    book = SimpleNamespace(title='Demo Book', author='Author Name', narrator='Reader Name')
    assert Harness()._knigavuhe_fallback_candidate(book) is fallback
    assert seen == ['https://knigavuhe.org/book/demo/']

def test_single_stream_does_not_promote_truncated_response(monkeypatch, tmp_path):

    class Response:
        status_code = 200
        headers = {'content-length': '10'}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=0):
            yield b'abc'

    class Session:

        def get(self, *_args, **_kwargs):
            return Response()
    monkeypatch.setattr(network_module, 'get_http_session', lambda: Session())

    class Limiter:

        def consume(self, *_args, **_kwargs):
            pass

    class Harness(NetworkDownloadMixin):
        cancel_event = None
        _suppress_source_transfer_ui = True

        def _check_cancel(self):
            pass

        def _get_bandwidth_limiter(self):
            return Limiter()

        def record_transfer_metrics(self, *_args):
            pass

        def set_progress(self, *_args):
            pass

        def set_status(self, *_args):
            pass
    target = tmp_path / 'source.mp3'
    with pytest.raises(RuntimeError, match='Загрузка оборвалась'):
        Harness()._download_single('https://cdn.invalid/source.mp3', target, 'https://example.invalid/')
    assert not target.exists()
    assert target.with_name(target.name + '.part').read_bytes() == b'abc'


# Origin: test_runtime_contract_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def _book() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3'), Track(index=2, title='Two', file='https://cdn.invalid/2.mp3')])

def test_explicit_empty_selection_is_still_rejected(tmp_path):
    request = DownloadRequest(book=_book(), selected_indices=[], output_dir=tmp_path)
    with pytest.raises(ValueError, match='Не выбрана ни одна часть'):
        request.validate()

def test_tr_does_not_format_template_braces_without_arguments(monkeypatch):
    import audioknigi.i18n as i18n
    monkeypatch.setitem(i18n.STRINGS.setdefault('ru', {}), 'template_contract', '{Book_Title} / {Track_Number}')
    assert tr('ru', 'template_contract') == '{Book_Title} / {Track_Number}'

def test_selftests_print_failure_traceback_and_cleanup_after_close_failure():
    source = (ROOT / 'audioknigi_qt.py').read_text(encoding='utf-8')
    assert source.count('print(details, file=sys.stderr') >= 3
    assert 'try:\n                    window.close()\n                except Exception:' in source
    assert 'window.event_sound_manager.shutdown()' in source

def test_source_analysis_indentation_is_normalized():
    source = (ROOT / 'audioknigi' / 'download' / 'source_analysis.py').read_text(encoding='utf-8')
    assert '    def _knigavuhe_fallback_candidate(self, book):\n        """' in source


# Origin: test_runtime_followup_round7_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_explicit_empty_selection_is_rejected_instead_of_becoming_full_book(tmp_path):
    from audioknigi.models import Track
    request = DownloadRequest(book=Book(url='https://example.test/book', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.test/1.mp3')]), selected_indices=[], output_dir=tmp_path)
    with pytest.raises(ValueError, match='Не выбрана ни одна часть'):
        request.validate()

def test_short_track_resume_uses_proportional_edge_guard(tmp_path):
    store = PlayerPositionStore(tmp_path / 'positions.json')
    media = tmp_path / 'short.mp3'
    assert store.update(media, 2.5, 5.0)
    assert store.saved_seconds(media, duration=5.0) == pytest.approx(2.5)
    assert store.update(media, 4.8, 5.0)
    assert store.saved_seconds(media, duration=5.0) == 0.0


# Origin: test_runtime_integrity_followup_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_mapping_base_has_real_docstring_and_safe_to_dict():
    assert MappingDataclass.__doc__
    assert 'mapping adapter' in MappingDataclass.__doc__.casefold()
    assert MappingDataclass().to_dict() == {}

def test_malformed_explicit_port_is_rejected_without_value_error():
    assert normalize_supported_url('https://poleknig.com:abc/books/1') == ''


# Origin: test_static_quality_gates.py
ROOT = Path(__file__).resolve().parents[2]

def run_tool(name, *args, timeout=60):
    return subprocess.run([sys.executable, str(ROOT / 'tools' / name), *args], cwd=ROOT, text=True, capture_output=True, timeout=timeout)

def test_archived_behavioral_regressions_have_no_new_failures():
    proc = run_tool('historical_regression_audit.py', timeout=300)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert 'HISTORICAL REGRESSION: PASS' in proc.stdout


# Origin: test_structured_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_retry_constructor_does_not_require_urllib3_2_only_other_keyword():
    source = (ROOT / 'audioknigi' / 'core.py').read_text(encoding='utf-8')
    block = source[source.index('retry = Retry('):source.index('adapter = HTTPAdapter', source.index('retry = Retry('))]
    assert 'other=' not in block

def test_qt_refactor_contracts_are_present_without_importing_pyside():
    main_source = (ROOT / 'audioknigi' / 'qt' / 'main_window.py').read_text(encoding='utf-8')
    accessibility_source = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'accessibility_ui.py').read_text(encoding='utf-8')
    audit_source = (ROOT / 'audioknigi' / 'qt' / 'accessibility_audit.py').read_text(encoding='utf-8')
    assert 'from .player_controller import QtPlayerController' in main_source
    assert 'self._l("Неподдерживаемая ссылка")' in main_source
    assert 'from ..accessibility_audit import audit_accessibility_window' in accessibility_source
    assert audit_source.count('"download_options"') >= 2

# Post-consolidation: Round 85 external audit follow-up.
def test_shared_source_timeline_error_exposes_normalized_track_indices():
    exc = SharedSourceTimelineError({
        "reason": "non_increasing_middle_boundary",
        "track_index": "7",
        "expected_end": 10.0,
        "actual_duration": 0.0,
    })
    assert exc.issue["track_indices"] == [7]
    assert exc.issue["reason"] == "non_increasing_middle_boundary"


# Post-consolidation: Round 86 external audit follow-up.
def test_analysis_duration_probe_reaps_process_killed_by_cancel_coordinator(monkeypatch):
    import subprocess as _subprocess
    from audioknigi.services import book_analysis_service as module

    service = BookAnalysisService()
    communicate_calls = []

    class FakeProc:
        def __init__(self):
            self.returncode = None
            self.stdout = None
            self.stderr = None
        def poll(self):
            return self.returncode
        def kill(self):
            self.returncode = -9
        def communicate(self, timeout=None):
            communicate_calls.append(timeout)
            if len(communicate_calls) == 1:
                service.cancel_event.set()
                raise _subprocess.TimeoutExpired(cmd="ffprobe", timeout=timeout)
            return ("", "")
    fake = FakeProc()

    monkeypatch.setattr(module, "resolve_executable", lambda _name: "ffprobe")
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_args, **_kwargs: fake)

    with pytest.raises(Cancelled):
        service._probe_remote_duration("https://example.invalid/audio.mp3")

    # First communicate times out, cancellation kills the process, and finally
    # still communicates/reaps the already-dead child.
    assert fake.returncode == -9
    assert len(communicate_calls) >= 2
    assert fake not in service._duration_probe_processes


def test_blank_track_title_does_not_duplicate_number_when_template_already_has_number():
    from audioknigi.templates import render_track_filename
    book = Book(
        url="https://example.invalid/book",
        title="Book",
        tracks=[Track(index=1, title="", file="x")],
    )
    assert render_track_filename(
        "{Track_Number} - {Track_Title}.mp3", book, book.tracks[0]
    ) == "01.mp3"
    # Track_Title-only still needs a unique fallback.
    assert render_track_filename("{Track_Title}.mp3", book, book.tracks[0]) == "track-01.mp3"
