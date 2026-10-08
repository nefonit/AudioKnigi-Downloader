"""Consolidated integration tests for the privacy diagnostics domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


import ast
import importlib.util
import json
import threading
import zipfile
from pathlib import Path
import pytest
from audioknigi.core import Cancelled
from audioknigi.download.common import atomic_write_text
from audioknigi.models import Book, Track
from types import SimpleNamespace
from datetime import datetime
import socket
from audioknigi.diagnostics.support_bundle import _privacy_path, _sanitize_setting_value
from audioknigi.network_dns import _read_http_head
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata, _looks_like_author_prefix, _same_author_identity
from audioknigi.services.book_analysis_service import _playlist_track_title
from audioknigi.services.player_position_store import PlayerPositionStore
import requests
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.queue_service import _parse_selected_indices_payload
from tools.exception_audit import scan as exception_scan
from tools.qt_localization_audit import _ui_text_literals
from tools.unused_import_audit import unused_imports
import os
from audioknigi.diagnostics import support_bundle as support_bundle__recovery_diagnostics_hardening_20260912
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _hydrate_search_result_titles
from audioknigi.models import SearchResult
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.library_service import scan_unfinished
from audioknigi.core import extract_metadata_from_html
from audioknigi.logging_utils import sanitize_log_text
from audioknigi.models import Book, SearchResult, Track
from audioknigi.services.library_service import export_history
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict
from collections import UserDict
from audioknigi.core import Cancelled, _structured_book_nodes
from audioknigi.diagnostics import support_bundle as support_bundle__report_followup_round12_20260916
from audioknigi.download_engine import _DownloadEngine
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.download_request import build_download_request
import csv
from audioknigi.config.settings import migrate_settings
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.network import _segment_files
import audioknigi.poleknig as poleknig__report_followup_round14_20260916
from audioknigi.core import _walk_json
from audioknigi.download.common import replace_with_retry
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services import library_service
from audioknigi import core as core__report_followup_round21_20260917, knigavuhe, poleknig as poleknig__report_followup_round21_20260917
from audioknigi.diagnostics.support_bundle import create_support_bundle
from audioknigi.providers.audioknigi_search import _canonical_title
from audioknigi import core as core__report_followup_round2_20260915
from audioknigi.config.settings import save_app_settings
from audioknigi.core import load_json
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.core import Cancelled, load_json
from audioknigi.templates import template_values
from audioknigi import core as core__report_followup_round3_20260915
from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.download.probe import ProbeMixin
from audioknigi.download_engine import DownloadService, _DownloadEngine
from audioknigi.i18n import localize_runtime_text
from audioknigi.services.search_service import search_all_sources
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
from audioknigi.poleknig import _parse_playlist_objects
from audioknigi.providers.audioknigi_search import parse_audioknigi_results
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round47_20260923
from audioknigi.core import safe_int
from audioknigi.providers import audioknigi_search
import hashlib
import math
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round49_20260924
import audioknigi.download.source_analysis as source_analysis_module
from audioknigi.download.source_analysis import SourceAnalysisMixin
from audioknigi.models import Book, SearchResult
import sys
from types import ModuleType, SimpleNamespace
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round52_20260924
from audioknigi.services.download_request import DownloadRequest, build_download_request
from dataclasses import dataclass
from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, extract_extended_metadata_from_html
from audioknigi.diagnostics import support_bundle as support_bundle__round61_external_review_followup_20260929
from audioknigi.providers.audioknigi_search import _author_detail_score, _matches_query
from audioknigi.services.queue_service import _item_to_dict
from audioknigi.models import Book, Track, TRACK_STATUS_READY
from audioknigi.providers.audioknigi_search import _response_html_text
from audioknigi.config.settings import AppSettings, normalize_settings
from audioknigi.diagnostics import support_bundle as support_bundle__round63_followup_20260929
from audioknigi.services import library_service, source_health_service
from audioknigi import network_dns
from audioknigi.services.queue_service import _parse_created_at
import re
from audioknigi.diagnostics import support_bundle as support_bundle__round73_runtime_followup_20261002
from audioknigi.knigavuhe import _usable_search_title
from audioknigi.services.book_analysis_service import BookAnalysisService, _playlist_track_title
from audioknigi.services.library_service import _validated_backup_payloads
from audioknigi.services.queue_service import _optional_persisted_bool
from audioknigi.models import NarrationVariant, Track
from audioknigi.services.queue_service import _track_from_dict, _variant_from_dict
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
from threading import Event
from audioknigi.download_engine import DownloadService
from audioknigi.i18n import tr
from audioknigi.providers.audioknigi_search import search_audioknigi
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict
from audioknigi.diagnostics.support_bundle import _is_secret_key
from audioknigi.i18n import localize_runtime_text, tr, ui_text
from audioknigi.providers.adapters import KnigavuheProvider, PoleKnigProvider
import subprocess
from audioknigi.diagnostics import support_bundle as support_bundle__structured_hardening_20260912
from audioknigi.knigavuhe import _merge_narration_variants
from audioknigi.models import NarrationVariant, SearchResult, Track, TRACK_STATUS_MISSING
from audioknigi.services import search_service
from audioknigi.providers import provider_for_key


# Origin: test_acceptance_parser_diagnostics_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool__acceptance_parser_diagnostics_followup_20260915(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_support_bundle_includes_existing_empty_error_log(tmp_path: Path, monkeypatch):
    import audioknigi.diagnostics.support_bundle as support
    error_log = tmp_path / 'errors.log'
    error_log.write_bytes(b'')
    app_log = tmp_path / 'app.log'
    crash = tmp_path / 'crash.txt'
    queue = tmp_path / 'queue.json'
    queue.write_text('[]', encoding='utf-8')
    monkeypatch.setattr(support, 'ERROR_LOG_FILE', error_log)
    monkeypatch.setattr(support, 'APP_LOG_FILE', app_log)
    monkeypatch.setattr(support, 'CRASH_REPORT_FILE', crash)
    monkeypatch.setattr(support, 'QT_QUEUE_FILE', queue)
    target = support.create_support_bundle(tmp_path / 'support.zip', settings={})
    with zipfile.ZipFile(target) as archive:
        assert 'diagnostics/errors.log' in archive.namelist()
        assert archive.read('diagnostics/errors.log') == b''


# Origin: test_cancellation_cover_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_crash_report_survives_traceback_format_failure(monkeypatch, tmp_path):
    import audioknigi.crash_report as crash_report
    monkeypatch.setattr(crash_report, 'CRASH_REPORT_FILE', tmp_path / 'crash.txt')
    monkeypatch.setattr(crash_report.traceback, 'format_exception', lambda *args, **kwargs: (_ for _ in ()).throw(RecursionError('format failed')))
    exc = RecursionError('original')
    text = crash_report.build_report(RecursionError, exc, None, component='test')
    assert 'RecursionError: original' in text
    assert 'traceback formatting failed' in text
    assert (tmp_path / 'crash.txt').exists()


# Origin: test_external_review_hardening_20260928.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_redacts_posix_configured_and_embedded_paths():
    assert _privacy_path('/mnt/storage/Audiobooks') == '<configured-path>'
    assert _sanitize_setting_value('output_dir', '/media/user/Disk/Audiobooks') == '<configured-path>'
    text = _privacy_path('download failed at /mnt/storage/Audiobooks/Private Book/01.mp3; retrying', collapse_whole_path=False)
    assert '/mnt/storage' not in text
    assert '<configured-path>' in text
    assert _privacy_path('https://example.com/library/book.mp3', collapse_whole_path=False) == 'https://example.com/library/book.mp3'


# Origin: test_quality_runtime_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_ukrainian_catalog_has_search_period_variant_and_secret_field_translation():
    literals = json.loads((ROOT / 'audioknigi' / 'locales' / 'legacy_literals.json').read_text(encoding='utf-8'))
    assert literals['uk']['Введите минимум 3 символа для поиска.'] == 'Введіть мінімум 3 символи для пошуку.'
    for lang in ('uk', 'de', 'en'):
        assert literals[lang]['Секретное поле']


# Origin: test_recovery_diagnostics_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_absolute_posix_path_stays_private_even_when_home_is_root(monkeypatch):
    monkeypatch.setattr('pathlib.Path.home', lambda: Path('/'))
    assert support_bundle__recovery_diagnostics_hardening_20260912._privacy_path('/var/log/audio/app.log') == '<configured-path>'

def test_support_bundle_home_placeholder_matches_platform(monkeypatch, tmp_path):
    monkeypatch.setattr('pathlib.Path.home', lambda: tmp_path)
    value = str(tmp_path / 'Books')
    redacted = support_bundle__recovery_diagnostics_hardening_20260912._privacy_path(value)
    assert redacted == '<configured-path>'


# Origin: test_release_quality_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool__release_quality_followup_20260915(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_logging_sanitizer_does_not_hide_harmless_token_words():
    text = sanitize_log_text('folder_tokens: 5 tokenize_words=1 oauth_token=secret active_session_cookie=abc')
    assert 'folder_tokens: 5' in text
    assert 'tokenize_words=1' in text
    assert 'oauth_token=<hidden>' in text
    assert 'active_session_cookie=<hidden>' in text
    assert 'secret' not in text

def test_support_bundle_masks_only_private_configured_url():
    from audioknigi.diagnostics.support_bundle import sanitized_settings
    result = sanitized_settings({'abs_url': 'http://private.local', 'update_url': 'https://public.example/release'})
    assert result['abs_url'] == '<configured-url>'
    assert result['update_url'] == 'https://public.example/release'

def _request() -> DownloadRequest:
    book = Book(url='https://knigavuhe.org/book/1', title='Book', tracks=[Track(index=1, title='One', file='https://cdn.example/1.mp3')])
    return DownloadRequest(book=book, selected_indices=None, output_dir=Path('.'))


# Origin: test_report_followup_round12_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_masks_forward_slash_unc_paths():
    assert support_bundle__report_followup_round12_20260916._privacy_path('//server/private/audiobooks') == '<configured-path>'
    assert support_bundle__report_followup_round12_20260916._privacy_path('//?/UNC/server/private') == '<configured-path>'


# Origin: test_report_followup_round13_20260916.py
def test_support_bundle_preserves_dotted_name_and_masks_case_and_camel_secrets(tmp_path, monkeypatch):
    from audioknigi.diagnostics import support_bundle as support
    queue_path = tmp_path / 'qt_queue.json'
    queue_path.write_text(json.dumps([{'url': 'https://knigavuhe.org/book/example/', 'status': 'Ошибка', 'status_code': 'error', 'attempts': 2}], ensure_ascii=False), encoding='utf-8')
    monkeypatch.setattr(support, 'QT_QUEUE_FILE', queue_path)
    sanitized = support.sanitized_settings({'Geometry': 'private-geometry', 'apiKey': 'secret-a', 'authToken': 'secret-b', 'adminPassword': 'secret-c'})
    assert sanitized['Geometry'] == '<window-geometry>'
    assert sanitized['apiKey'] == '<redacted>'
    assert sanitized['authToken'] == '<redacted>'
    assert sanitized['adminPassword'] == '<redacted>'
    target = support.create_support_bundle(tmp_path / 'bundle_1.0', settings={})
    assert target.name == 'bundle_1.0.zip'
    with zipfile.ZipFile(target) as archive:
        summary = json.loads(archive.read('diagnostics/queue.summary.json').decode('utf-8'))
    assert summary[0]['status'] == 'Ошибка'
    assert summary[0]['status_code'] == 'error'

def test_support_bundle_directory_destination_creates_zip_inside_directory(tmp_path):
    from audioknigi.diagnostics.support_bundle import create_support_bundle
    target = create_support_bundle(tmp_path, settings={})
    assert target.parent == tmp_path
    assert target.suffix == '.zip'
    assert target.name.startswith('support_bundle_')


# Origin: test_report_followup_round14_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_masks_embedded_windows_paths_without_hiding_urls():
    assert _privacy_path('Cannot write to C:\\Users\\Ivan\\Music\\book.mp3') == 'Cannot write to <configured-path>'
    assert _privacy_path('Network \\\\server\\share\\book.mp3 failed') == 'Network <configured-path> failed'
    assert _privacy_path('https://example.test/audio.mp3') == 'https://example.test/audio.mp3'


# Origin: test_report_followup_round18_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_forward_slash_unc_redaction_requires_real_server_share_shape() -> None:
    assert _privacy_path('// TODO') == '// TODO'
    assert _privacy_path('//server/share/book.mp3') == '<configured-path>'
    assert _privacy_path('failure at //server/share/book.mp3 now') == 'failure at <configured-path> now'
    assert _privacy_path('https://example.test/audio.mp3') == 'https://example.test/audio.mp3'


# Origin: test_report_followup_round21_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_trailing_separator_means_explicit_missing_directory(tmp_path) -> None:
    folder = tmp_path / 'new-diagnostics'
    target = create_support_bundle(str(folder) + os.sep, settings={'language': 'en'})
    assert folder.is_dir()
    assert target.parent == folder
    assert target.name.startswith('support_bundle_')
    assert target.suffix == '.zip'


# Origin: test_report_followup_round24_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_tail_and_path_privacy_cover_reported_boundaries() -> None:
    support = (ROOT / 'audioknigi/diagnostics/support_bundle.py').read_text(encoding='utf-8')
    assert 'if newline >= 0:' in support
    assert '_EMBEDDED_DRIVE_PATH_RE = re.compile' in support
    assert '_EMBEDDED_UNC_PATH_RE = re.compile' in support
    assert '_WINDOWS_PATH_SEGMENT_RE =' in support and '_WINDOWS_PATH_FINAL_RE =' in support

def test_uncaught_worker_threads_are_captured_in_crash_reports() -> None:
    application = (ROOT / 'audioknigi/qt/application.py').read_text(encoding='utf-8')
    workers = (ROOT / 'audioknigi/qt/workers.py').read_text(encoding='utf-8')
    assert 'threading.excepthook = _thread_exception_hook' in application
    assert 'component=f"python-thread:{thread_name}"' in application
    assert 'app_logger.exception("Qt search worker failed")' in workers
    assert 'app_logger.exception("Qt analysis worker failed")' in workers


# Origin: test_report_followup_round2_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_windows_path_is_redacted_and_tail_is_valid_utf8(tmp_path):
    from audioknigi.diagnostics import support_bundle
    assert support_bundle._privacy_path('D:\\\\Audiobooks\\\\Private\\\\{Book_Title}') == '<configured-path>'
    path = tmp_path / 'application.log'
    path.write_bytes(b'valid line\ntruncated \xd0')
    tail = support_bundle._tail(path, max_bytes=512000)
    assert tail.decode('utf-8') == 'valid line\ntruncated '


# Origin: test_report_followup_round32_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round32_20260918(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

def test_support_bundle_sanitizes_path_objects() -> None:
    source = src__report_followup_round32_20260918('audioknigi/diagnostics/support_bundle.py')
    assert 'isinstance(value, (str, Path))' in source
    assert '_privacy_path(str(value))' in source


# Origin: test_report_followup_round3_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_redacts_two_slash_unc_path():
    from audioknigi.diagnostics.support_bundle import _privacy_path
    assert _privacy_path('\\\\server\\private\\books') == '<configured-path>'


# Origin: test_report_followup_round44_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round44_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_support_log_sanitizer_redacts_paths_and_common_credentials(monkeypatch) -> None:
    monkeypatch.setattr(support_bundle__report_followup_round44_20260920.os, 'name', 'nt', raising=False)
    monkeypatch.setattr(support_bundle__report_followup_round44_20260920.Path, 'home', classmethod(lambda cls: Path('C:\\\\Users\\\\Alice')))
    raw = b'open C:\\Users\\Alice\\Documents\\book.mp3\r\nAuthorization: Bearer TOP.SECRET-123\r\nhttps://example.test/file?token=URLSECRET&part=1\r\napi_key=KEYSECRET\r\n'
    cleaned = support_bundle__report_followup_round44_20260920._sanitize_log_bytes(raw).decode('utf-8')
    assert 'Alice' not in cleaned
    assert 'TOP.SECRET-123' not in cleaned
    assert 'URLSECRET' not in cleaned
    assert 'KEYSECRET' not in cleaned
    assert '<redacted>' in cleaned


# Origin: test_report_followup_round45_20260921.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round45_20260921(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_support_settings_sanitizer_recurses_into_nested_mappings_and_sequences(monkeypatch) -> None:
    monkeypatch.setattr(support_bundle__report_followup_round45_20260921.os, 'name', 'nt', raising=False)
    monkeypatch.setattr(support_bundle__report_followup_round45_20260921.Path, 'home', classmethod(lambda cls: Path('C:\\Users\\Alice')))
    payload = {'plugins': {'reader': {'api_key': 'nested-secret', 'download_dir': 'C:\\Users\\Alice\\Books', 'headers': [{'token': 'header-secret'}, 'Authorization: Bearer nested-bearer-secret']}}}
    cleaned = support_bundle__report_followup_round45_20260921.sanitized_settings(payload)
    reader = cleaned['plugins']['reader']
    assert reader['api_key'] == '<redacted>'
    assert reader['headers'][0]['token'] == '<redacted>'
    assert 'nested-bearer-secret' not in reader['headers'][1]
    assert 'Alice' not in reader['download_dir']

def test_support_log_sanitizer_redacts_entire_quoted_secret_values() -> None:
    raw = b'{"api_key": "abc def", "password": "p a s s"}\ntoken=\'quoted token with spaces\'\nhttps://example.test/?access_token=URLSECRET&part=1\n'
    cleaned = support_bundle__report_followup_round45_20260921._sanitize_log_bytes(raw).decode('utf-8')
    for secret in ('abc def', 'p a s s', 'quoted token with spaces', 'URLSECRET'):
        assert secret not in cleaned
    assert '"api_key": "<redacted>"' in cleaned
    assert '"password": "<redacted>"' in cleaned
    assert "token='<redacted>'" in cleaned

class _SplitDummy(MediaProcessingMixin):

    def __init__(self, target: Path):
        self.target = target

    def _track_path(self, _book, _track):
        return self.target

    def log(self, _message):
        pass


# Origin: test_report_followup_round47_20260923.py
def test_privacy_path_keeps_sanitizing_when_home_lookup_fails(monkeypatch):
    monkeypatch.setattr(support_bundle__report_followup_round47_20260923.Path, 'home', classmethod(lambda cls: (_ for _ in ()).throw(RuntimeError('no home'))))
    cleaned = support_bundle__report_followup_round47_20260923._privacy_path('error at D:\\\\Private\\\\book.mp3', collapse_whole_path=False)
    assert 'D:\\Private' not in cleaned
    assert '<configured-path>' in cleaned

def test_privacy_path_masks_drive_root_and_trailing_slash():
    root_only = support_bundle__report_followup_round47_20260923._privacy_path('free on D:\\\\ 20 GB', collapse_whole_path=False)
    trailing = support_bundle__report_followup_round47_20260923._privacy_path('folder D:\\\\Downloads\\\\', collapse_whole_path=False)
    assert 'D:\\' not in root_only
    assert 'D:\\Downloads' not in trailing


# Origin: test_report_followup_round49_20260924.py
def test_support_settings_redacts_string_windows_path_with_spaces() -> None:
    cleaned = support_bundle__report_followup_round49_20260924.sanitized_settings({'output_dir': 'D:\\Audio Books\\My Collection'})
    assert cleaned['output_dir'] == '<configured-path>'
    assert 'Audio Books' not in str(cleaned)
    assert 'My Collection' not in str(cleaned)

def test_support_bundle_hashes_modern_nested_queue_book_url(tmp_path, monkeypatch) -> None:
    queue_file = tmp_path / 'qt_queue.json'
    private_url = 'https://example.invalid/private-modern-book'
    queue_file.write_text(json.dumps([{'id': 'task-1', 'title': 'PRIVATE TITLE', 'status': 'Ожидает', 'status_code': 'pending', 'attempts': 2, 'request': {'book': {'url': private_url}}}]), encoding='utf-8')
    monkeypatch.setattr(support_bundle__report_followup_round49_20260924, 'QT_QUEUE_FILE', queue_file)
    target = support_bundle__report_followup_round49_20260924.create_support_bundle(tmp_path / 'bundle.zip', settings={'language': 'ru'})
    with zipfile.ZipFile(target) as archive:
        summary = json.loads(archive.read('diagnostics/queue.summary.json').decode('utf-8'))
        combined = b'\n'.join((archive.read(name) for name in archive.namelist()))
    expected = hashlib.sha256(private_url.encode('utf-8')).hexdigest()[:12]
    assert summary[0]['id'] == expected
    assert summary[0]['id'] != 'row-1'
    assert private_url.encode('utf-8') not in combined
    assert b'PRIVATE TITLE' not in combined

def test_support_bundle_accepts_versioned_queue_wrapper(tmp_path, monkeypatch) -> None:
    queue_file = tmp_path / 'qt_queue.json'
    queue_file.write_text(json.dumps({'version': 1, 'items': [{'status_code': 'pending', 'attempts': 1}]}), encoding='utf-8')
    monkeypatch.setattr(support_bundle__report_followup_round49_20260924, 'QT_QUEUE_FILE', queue_file)
    target = support_bundle__report_followup_round49_20260924.create_support_bundle(tmp_path / 'bundle.zip', settings={})
    with zipfile.ZipFile(target) as archive:
        summary = json.loads(archive.read('diagnostics/queue.summary.json').decode('utf-8'))
    assert summary == [{'id': 'row-1', 'status': '', 'status_code': 'pending', 'attempts': 1}]

class _FallbackHost(SourceAnalysisMixin):
    cancel_event = None
    _book_identity_hints = staticmethod(BookAnalysisService._book_identity_hints)
    _identity_tokens = staticmethod(BookAnalysisService._identity_tokens)

    def _check_cancel(self) -> None:
        return None


# Origin: test_report_followup_round52_20260924.py
def test_support_log_redacts_filename_with_spaces_without_eating_status_text() -> None:
    value = 'error at D:\\Audiobooks\\01. Введение.mp3 not found'
    cleaned = support_bundle__report_followup_round52_20260924._privacy_path(value, collapse_whole_path=False)
    assert cleaned == 'error at <configured-path> not found'
    assert 'Введение.mp3' not in cleaned

def test_support_log_redacts_unc_filename_with_spaces_and_accepts_path_objects() -> None:
    value = 'Network \\\\server\\share\\My Book.mp3 failed'
    assert support_bundle__report_followup_round52_20260924._privacy_path(value, collapse_whole_path=False) == 'Network <configured-path> failed'
    assert support_bundle__report_followup_round52_20260924._privacy_path(Path('D:\\Audio Books\\My Collection')) == '<configured-path>'


# Origin: test_round61_external_review_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_redacts_secret_key_and_preserves_text_after_drive_root(monkeypatch):
    monkeypatch.setattr(support_bundle__round61_external_review_followup_20260929.os, 'name', 'nt', raising=False)
    assert support_bundle__round61_external_review_followup_20260929.sanitized_settings({'secret_key': 'abc'})['secret_key'] == '<redacted>'
    text = 'Check C:\\ finished, starting download from https://site.com/file.mp3'
    sanitized = support_bundle__round61_external_review_followup_20260929._privacy_path(text, collapse_whole_path=False)
    assert sanitized == 'Check <configured-path> finished, starting download from https://site.com/file.mp3'
    assert support_bundle__round61_external_review_followup_20260929._privacy_path('C:\\Users\\Name\\Audiobooks\\Author\\Book') == '<configured-path>'


# Origin: test_round62_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_history_lock_contracts_and_dead_privacy_bookkeeping_removed():
    support = (ROOT / 'audioknigi/diagnostics/support_bundle.py').read_text(encoding='utf-8')
    library = (ROOT / 'audioknigi/services/library_service.py').read_text(encoding='utf-8')
    engine = (ROOT / 'audioknigi/download_engine.py').read_text(encoding='utf-8')
    assert 'original_was_absolute_path' in support
    assert 'if collapse_whole_path and original_was_absolute_path' in support
    assert 'if target == HISTORY_FILE:\n                        with HISTORY_LOCK:\n                            target.unlink' in library
    block = engine.split('def _history_metadata_matches_book', 1)[1].split('def _sidecar_metadata_matches_book', 1)[0]
    assert 'with HISTORY_LOCK:' in block
    assert 'history = load_json(HISTORY_FILE, [])' in block


# Origin: test_round63_followup_20260929.py
def test_support_bundle_collapses_absolute_home_path_after_username_masking():
    private_path = Path.home() / 'AudioBooks' / 'Author' / 'Book'
    assert support_bundle__round63_followup_20260929._privacy_path(str(private_path)) == '<configured-path>'

def test_support_bundle_can_keep_relative_home_structure_only_for_embedded_log_text():
    private_path = Path.home() / 'AudioBooks' / 'Author' / 'Book'
    text = f'Output path: {private_path}'
    sanitized = support_bundle__round63_followup_20260929._privacy_path(text, collapse_whole_path=False)
    assert str(Path.home()) not in sanitized
    assert 'AudioBooks' not in sanitized


# Origin: test_round66_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_privacy_path_runs_embedded_regex_redaction_once():
    source = (ROOT / 'audioknigi/diagnostics/support_bundle.py').read_text(encoding='utf-8')
    block = source[source.index('def _privacy_path'):source.index('def _sanitize_log_bytes')]
    for token in ('_EMBEDDED_DRIVE_FILE_RE.sub', '_EMBEDDED_UNC_FILE_RE.sub', '_EMBEDDED_DRIVE_PATH_RE.sub', '_EMBEDDED_UNC_PATH_RE.sub', '_EMBEDDED_POSIX_FILE_RE.sub', '_EMBEDDED_POSIX_PATH_RE.sub'):
        assert block.count(token) == 1


# Origin: test_round67_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_has_only_initial_whole_path_collapse_guard():
    source = (ROOT / 'audioknigi/diagnostics/support_bundle.py').read_text(encoding='utf-8')
    block = source[source.index('def _privacy_path'):source.index('def _sanitize_log_bytes')]
    assert block.count('collapse_whole_path and original_was_absolute_path') == 1
    assert block.count('return "<configured-path>"') == 1


# Origin: test_round73_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_directory_path_over_redaction_remains_privacy_first():
    value = 'Created directory C:\\Audiobooks\\Book 1 for narration by reader'
    cleaned = support_bundle__round73_runtime_followup_20261002._privacy_path(value, collapse_whole_path=False)
    assert cleaned == 'Created directory <configured-path>'
    assert 'Book 1' not in cleaned


# Origin: test_round76_external_review_followup_20261003.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_keeps_privacy_first_posix_redaction_contract():
    source = (ROOT / 'audioknigi/diagnostics/support_bundle.py').read_text(encoding='utf-8')
    assert 'Directory-like paths deliberately favor over-redaction' in source
    assert '_EMBEDDED_POSIX_PATH_RE' in source


# Origin: test_round77_external_review_followup_20261004.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_file_redaction_preserves_diagnostic_tail():
    from audioknigi.diagnostics.support_bundle import _privacy_path
    value = 'C:\\App\\test.mp3 finished with error code 500'
    cleaned = _privacy_path(value, collapse_whole_path=False)
    assert cleaned == '<configured-path> finished with error code 500'


# Origin: test_round78_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_mime_types_are_not_mistaken_for_posix_paths():
    from audioknigi.diagnostics.support_bundle import _privacy_path
    assert _privacy_path('Content-Type: application/json', collapse_whole_path=False) == 'Content-Type: application/json'
    assert _privacy_path('cover: image/jpeg', collapse_whole_path=False) == 'cover: image/jpeg'
    assert _privacy_path('path /secret', collapse_whole_path=False) == 'path <configured-path>'


# Origin: test_round79_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_posix_file_redaction_avoids_arithmetic_false_positive_but_keeps_real_paths_private():
    assert _privacy_path('math: 10 / 2 / calc.py', collapse_whole_path=False) == 'math: 10 / 2 / calc.py'
    assert _privacy_path('date: 2024 / 01 / file.mp3', collapse_whole_path=False) == 'date: 2024 / 01 / file.mp3'
    assert _privacy_path('file /home/user/My Book/file.mp3 done', collapse_whole_path=False) == 'file <configured-path> done'
    assert _privacy_path('path /secret', collapse_whole_path=False) == 'path <configured-path>'


# Origin: test_round80_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_windows_directory_redaction_stays_privacy_first_but_file_tail_is_preserved():
    assert _privacy_path('C:\\Audio\\My Book for Alice', collapse_whole_path=False) == '<configured-path>'
    assert _privacy_path('C:\\Audio\\Book\\chapter.mp3 failed to download because timeout', collapse_whole_path=False) == '<configured-path> failed to download because timeout'


# Origin: test_runtime_contract_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def _book() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3'), Track(index=2, title='Two', file='https://cdn.invalid/2.mp3')])

def test_cross_platform_log_home_placeholder_is_not_windows_only():
    source = (ROOT / 'audioknigi' / 'logging_utils.py').read_text(encoding='utf-8')
    assert 'placeholder = "%USERPROFILE%" if os.name == "nt" else "~"' in source


# Origin: test_stability_localization_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_secret_redaction_does_not_hide_unrelated_token_settings():
    assert _is_secret_key('token')
    assert _is_secret_key('oauth_token')
    assert _is_secret_key('abs_api_key')
    assert not _is_secret_key('folder_tokens')
    assert not _is_secret_key('tokenize_words')


# Origin: test_structured_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_bundle_path_privacy_handles_both_windows_slash_styles(monkeypatch):
    monkeypatch.setattr(support_bundle__structured_hardening_20260912.Path, 'home', classmethod(lambda cls: cls('C:/Users/Alice')))
    assert support_bundle__structured_hardening_20260912._privacy_path('C:\\Users\\Alice\\Books') == '<configured-path>'
    assert support_bundle__structured_hardening_20260912._privacy_path('C:/Users/Alice/Books') == '<configured-path>'

def test_support_bundle_tail_starts_at_clean_utf8_line_boundary(tmp_path):
    path = tmp_path / 'log.txt'
    text = 'строка один\nстрока два\nстрока три\n'
    path.write_text(text, encoding='utf-8')
    payload = support_bundle__structured_hardening_20260912._tail(path, max_bytes=20)
    decoded = payload.decode('utf-8')
    assert decoded
    normalized = decoded.replace('\r\n', '\n')
    assert normalized in text
    assert not normalized.startswith('ока')

def test_support_bundle_queue_uses_opaque_nonempty_ids_and_excludes_private_book_data(tmp_path, monkeypatch):
    queue_file = tmp_path / 'queue.json'
    private_url = 'https://example.invalid/private-book'
    queue_file.write_text(json.dumps([{'url': private_url, 'title': 'PRIVATE TITLE', 'status_code': 'pending', 'attempts': 2}]), encoding='utf-8')
    monkeypatch.setattr(support_bundle__structured_hardening_20260912, 'QT_QUEUE_FILE', queue_file)
    target = support_bundle__structured_hardening_20260912.create_support_bundle(tmp_path / 'bundle.zip', settings={'language': 'en'})
    with zipfile.ZipFile(target) as archive:
        payload = json.loads(archive.read('diagnostics/queue.summary.json').decode('utf-8'))
        combined = b'\n'.join((archive.read(name) for name in archive.namelist()))
    assert payload[0]['id'] and payload[0]['id'] != private_url
    assert payload[0]['status_code'] == 'pending'
    assert payload[0]['attempts'] == 2
    assert private_url.encode() not in combined
    assert b'PRIVATE TITLE' not in combined
