"""Consolidated integration tests for the providers domain.

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
from audioknigi.models import NarrationVariant
import time
from audioknigi.config import settings as settings_module__persistence_cancellation_hardening_20260929
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
from audioknigi.download.errors import MissingSelectedTracksError
from audioknigi.metadata import APP_VERSION
from audioknigi.services.queue_service import task_from_dict
from tools.exception_audit import audit as exception_audit
from tools.historical_regression_audit import _normalize_nodeid
from tools.qt_localization_audit import _assignment_value
from tools.undefined_global_audit import _SPECIAL_GLOBALS
from audioknigi.core import extract_metadata_from_html
from audioknigi.logging_utils import sanitize_log_text
from audioknigi.models import Book, SearchResult, Track
from audioknigi.services.library_service import export_history
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict
from audioknigi.core import effective_track_duration, safe_float
from audioknigi.i18n import localize_runtime_text, tr
from audioknigi.knigavuhe import _extract_call_argument, _usable_search_title
from audioknigi.poleknig import _discover_narration_variants
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.core import _first_json_ld
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from collections import UserDict
from audioknigi.core import Cancelled, _structured_book_nodes
from audioknigi.diagnostics import support_bundle as support_bundle__report_followup_round12_20260916
from audioknigi.download_engine import _DownloadEngine
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
from audioknigi.sources import is_supported_url, normalize_supported_url
from audioknigi import poleknig as poleknig__report_followup_round19_20260917
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.services import book_analysis_service as analysis_module
from audioknigi.models import Book, SearchResult
from audioknigi import knigavuhe as knigavuhe__report_followup_round20_20260917, poleknig as poleknig__report_followup_round20_20260917
from audioknigi.core import fmt_eta, parse_time_seconds
from audioknigi.download.probe import ProbeMixin
from audioknigi.i18n import localize_runtime_text
from audioknigi.providers import audioknigi_search as search_module
from audioknigi import core as core__report_followup_round21_20260917, knigavuhe as knigavuhe__report_followup_round21_20260917, poleknig as poleknig__report_followup_round21_20260917
from audioknigi.diagnostics.support_bundle import create_support_bundle
import inspect
from audioknigi import core as core__report_followup_round22_20260917, poleknig as poleknig__report_followup_round22_20260917
from audioknigi.network_dns import _relay_bidirectional
from audioknigi.providers.audioknigi_search import _canonical_title
from audioknigi import core as core__report_followup_round2_20260915
from audioknigi.config.settings import save_app_settings
from audioknigi.core import load_json
from audioknigi.core import Cancelled, load_json
from audioknigi.templates import template_values
from audioknigi import core as core__report_followup_round33_20260918
from audioknigi.core import fmt_size
from audioknigi.templates import render_text_template
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi.knigavuhe import _description_from_html as knigavuhe_description
from audioknigi.poleknig import _book_page_metadata as poleknig_metadata
from audioknigi.knigavuhe import _hydrate_search_result_titles, _knigavuhe_matches_query
from audioknigi import core as core__report_followup_round3_20260915
from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.download_engine import DownloadService, _DownloadEngine
from audioknigi.services.search_service import search_all_sources
import audioknigi.config.settings as settings_module__report_followup_round43_20260920
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round43_20260920
import audioknigi.download.network as network_module
import audioknigi.knigavuhe as knigavuhe__report_followup_round43_20260920
import audioknigi.poleknig as poleknig__report_followup_round43_20260920
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata, _merge_author_names
import base64
import audioknigi.config.settings as settings_module__report_followup_round44_20260920
import audioknigi.core as core__report_followup_round44_20260920
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round44_20260920
import audioknigi.services.player_position_store as position_module
from audioknigi.models import Book
from audioknigi.providers.audioknigi_search import _matches_query, _response_html_text, parse_audioknigi_results
from audioknigi.services.queue_service import _book_to_dict
import audioknigi.config.settings as settings_module__report_followup_round45_20260921
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round45_20260921
from audioknigi.download.errors import SharedSourceTimelineError
from audioknigi.poleknig import _parse_playlist_objects
from audioknigi.providers.audioknigi_search import parse_audioknigi_results
from audioknigi.knigavuhe import _extract_names
from audioknigi.services.queue_service import _normalize_queue_download_mode, _track_from_dict
import audioknigi.config.settings as settings_module__report_followup_round47_20260923
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round47_20260923
from audioknigi.core import safe_int
import hashlib
import math
import audioknigi.config.settings as settings_module__report_followup_round49_20260924
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round49_20260924
import audioknigi.download.source_analysis as source_analysis_module
from audioknigi.download.source_analysis import SourceAnalysisMixin
from audioknigi.brand import version_label
from audioknigi.core import load_browser_context_profile
from audioknigi.network_dns import _parse_proxy_authority
from audioknigi.providers.audioknigi_search import _split_audioknigi_title
from dataclasses import dataclass
from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, extract_extended_metadata_from_html
from audioknigi.diagnostics import support_bundle as support_bundle__round61_external_review_followup_20260929
from audioknigi.providers.audioknigi_search import _author_detail_score, _matches_query
from audioknigi.services.queue_service import _item_to_dict
from audioknigi.config.settings import AppSettings, normalize_settings
from audioknigi.diagnostics import support_bundle as support_bundle__round63_followup_20260929
from audioknigi import poleknig as poleknig__round65_poleknig_search_relevance_20260929
from audioknigi.services import library_service, source_health_service
from audioknigi import poleknig as poleknig__round69_runtime_followup_20260930
from audioknigi.download.errors import MissingMediaSourceError
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, _DownloadEngine
from audioknigi.services.search_service import downloadable_search_results, search_result_sort_key
import re
from audioknigi.diagnostics import support_bundle as support_bundle__round73_runtime_followup_20261002
from audioknigi.knigavuhe import _usable_search_title
from audioknigi.services.book_analysis_service import BookAnalysisService, _playlist_track_title
from audioknigi.services.library_service import _validated_backup_payloads
from audioknigi.services.queue_service import _optional_persisted_bool
from audioknigi.core import effective_track_duration
from audioknigi.models import Book, NarrationVariant, Track
from audioknigi.core import safe_name
from audioknigi.knigavuhe import _extract_narration_variants
from audioknigi import cover_fetch
from audioknigi.core import SiteStructureChanged
from audioknigi.knigavuhe import parse_book_html
from threading import Event
from audioknigi.download_engine import DownloadService
from audioknigi.i18n import tr
from audioknigi.providers.audioknigi_search import search_audioknigi
from audioknigi.services.download_request import DownloadRequest, build_download_request
from audioknigi.download.network import SlidingSpeedMeter
from audioknigi.models import Book, SearchResult, TRACK_STATUS_DAMAGED, TRACK_STATUS_MISSING, TRACK_STATUS_PRESENT, TRACK_STATUS_READY, normalize_track_status
from audioknigi.diagnostics.support_bundle import _is_secret_key
from audioknigi.i18n import localize_runtime_text, tr, ui_text
from audioknigi.providers.adapters import KnigavuheProvider, PoleKnigProvider
import subprocess
import sys
from audioknigi.diagnostics import support_bundle as support_bundle__structured_hardening_20260912
from audioknigi.knigavuhe import _merge_narration_variants
from audioknigi.models import NarrationVariant, SearchResult, Track, TRACK_STATUS_MISSING
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

def test_poleknig_playwright_cancelled_before_browser_work():
    import audioknigi.poleknig as poleknig
    event = threading.Event()
    event.set()
    with pytest.raises(Cancelled):
        poleknig._fetch_book_playwright('https://poleknig.com/books/1', cancel_event=event)

def test_poleknig_author_catalog_future_does_not_swallow_cancelled():
    source = (ROOT / 'audioknigi/poleknig.py').read_text(encoding='utf-8')
    block = source[source.index('def _expand_matching_author_catalogs'):source.index('def search(', source.index('def _expand_matching_author_catalogs'))]
    assert 'except Cancelled:\n                raise' in block

def test_audioknigi_playwright_closes_browser_before_http_playlist_fetch():
    source = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    start = source.index('def _analyze_audioknigi_playwright')
    block = source[start:source.index('def _remote_size', start)]
    close_pos = block.index('browser.close()')
    request_pos = block.index('session.get(playlist_url')
    assert close_pos < request_pos


# Origin: test_cancellation_cover_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_poleknig_fetch_book_reraises_cancelled(monkeypatch):
    from audioknigi import poleknig
    from audioknigi.core import Cancelled
    from audioknigi.models import Book, Track

    class Response:
        url = 'https://poleknig.com/books/123'
        text = '<html></html>'
        content = b'<html></html>'

        def raise_for_status(self):
            return None

    class Session:

        def get(self, *args, **kwargs):
            return Response()
    monkeypatch.setattr(poleknig, 'get_http_session', lambda: Session())
    monkeypatch.setattr(poleknig, 'parse_book_html', lambda *args, **kwargs: Book(url=Response.url, title='Book', tracks=[Track(index=1, title='1', file='https://cdn/a.mp3')]))
    monkeypatch.setattr(poleknig, '_book_page_metadata', lambda *args, **kwargs: {'title': 'Book', 'author': '', 'narrator': ''})
    monkeypatch.setattr(poleknig, '_discover_narration_variants', lambda *args, **kwargs: (_ for _ in ()).throw(Cancelled('cancel')))
    with pytest.raises(Cancelled):
        poleknig.fetch_book(Response.url)

def test_poleknig_meta_url_preserves_trailing_punctuation():
    from audioknigi.poleknig import _book_page_metadata
    html = '<h1>Book</h1><meta property="og:image" content="https://cdn.example/cover?v=x-">'
    meta = _book_page_metadata(html, 'https://poleknig.com/books/1')
    assert meta['cover_url'] == 'https://cdn.example/cover?v=x-'

def test_playlist_null_title_uses_numeric_fallback():
    source = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    assert 'raw_track_title = html_lib.unescape(' in source
    assert 'title=raw_track_title or f"{track_index:02d}"' in source

def test_playlist_worker_cancelled_is_not_swallowed():
    source = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    parse_block = source[source.index('def _parse_playlist_data'):source.index('def _analyze_audioknigi_requests')]
    assert 'except Cancelled:' in parse_block
    assert 'except Cancelled:\n                    raise' in parse_block


# Origin: test_external_review_hardening_20260928.py
ROOT = Path(__file__).resolve().parents[2]

def test_audioknigi_partial_initial_expansion_and_long_initial_names():
    assert _same_author_identity('А. С. Пушкин', 'Александр Пушкин')
    assert _same_author_identity('А. С. Пушкин', 'Александр Сергеевич Пушкин')
    assert _looks_like_author_prefix('Дж. Р. Р. Толкин мл.')
    assert not _looks_like_author_prefix('S.T.A.L.K.E.R.')

def test_audioknigi_metadata_honors_pre_cancel_without_http():
    called = False

    def session_factory():
        nonlocal called
        called = True
        raise AssertionError('HTTP session must not be created after cancellation')
    event = threading.Event()
    event.set()
    with pytest.raises(Cancelled):
        _audioknigi_page_metadata(type('Result', (), {'url': 'https://audioknigi.com.ua/test'})(), cancel_event=event, session_factory=session_factory)
    assert called is False

@pytest.mark.parametrize('title', ['Chapter_01', 'Track-01', 'Part_1', 'CD1_01'])
def test_meaningful_numbered_playlist_titles_are_preserved(title):
    assert _playlist_track_title(title, 'https://example.com/raw_audio_01.mp3', 1, 'Book', 5) == title

def test_machine_playlist_slug_is_still_replaced():
    assert _playlist_track_title('audio_01_320kbps_final_1', 'https://example.com/different.mp3', 1, 'Book', 5) == 'Book — 01'


# Origin: test_network_parser_retention_round6_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_poleknig_title_fallback_extracts_only_quoted_book_name():
    from audioknigi.poleknig import _book_page_metadata
    html = '\n    <html><head><title>«Книга» Автор: слушать аудиокнигу онлайн</title></head>\n    <body><a href="/authors/123">Автор</a></body></html>\n    '
    meta = _book_page_metadata(html, 'https://poleknig.com/books/1')
    assert meta['title'] == 'Книга'
    assert meta['author'] == 'Автор'

def test_poleknig_meta_extractor_never_crosses_meta_tag_boundary():
    from audioknigi.poleknig import _extract_meta_content
    html = '<meta property="description"><meta property="og:image" content="https://example.test/cover.jpg">'
    assert _extract_meta_content(html, 'description') == ''

def test_knigavuhe_reader_hydration_does_not_mutate_input_variants(monkeypatch):
    import audioknigi.knigavuhe as knigavuhe
    variants = [NarrationVariant(url='https://knigavuhe.org/book/main/', narrator='Reader One', current=True), NarrationVariant(url='https://knigavuhe.org/book/alt/', narrator='', current=False)]

    class Response:
        text = '<title>Book — автор Author, читает Reader Two (слушать аудиокнигу)</title>'

        @staticmethod
        def raise_for_status():
            return None

    class Session:

        @staticmethod
        def get(*args, **kwargs):
            return Response()
    monkeypatch.setattr(knigavuhe, 'get_http_session', lambda: Session())
    hydrated = knigavuhe._hydrate_narration_variant_readers(variants, current_url='https://knigavuhe.org/book/main/')
    assert variants[1].narrator == ''
    assert hydrated[1].narrator == 'Reader Two'
    assert hydrated[1] is not variants[1]


# Origin: test_persistence_cancellation_hardening_20260929.py
def _book__persistence_cancellation_hardening_20260929() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1-test', title='Test', tracks=[Track(index=1, title='Part 1', file='https://example.com/1.mp3')])

def test_audioknigi_search_socket_wait_is_bounded():
    assert audioknigi_search.SEARCH_HTTP_TIMEOUT == (4.0, 8.0)


# Origin: test_quality_runtime_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_knigavuhe_call_argument_supports_backtick_template_strings():
    source = 'BookController.enter(`title: "A,B" (demo)`, secondArg)'
    assert _extract_call_argument(source) == '`title: "A,B" (demo)`'

def test_source_hosts_are_reused_by_provider_modules():
    knigavuhe = (ROOT / 'audioknigi' / 'knigavuhe.py').read_text(encoding='utf-8')
    poleknig = (ROOT / 'audioknigi' / 'poleknig.py').read_text(encoding='utf-8')
    adapters = (ROOT / 'audioknigi' / 'providers' / 'adapters.py').read_text(encoding='utf-8')
    assert 'KNIGAVUHE_HOST' in knigavuhe
    assert 'POLEKNIG_HOST' in poleknig
    assert 'AUDIOKNIGI_HOST' in adapters


# Origin: test_recovery_diagnostics_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_knigavuhe_hydration_propagates_cancelled(monkeypatch):
    import audioknigi.knigavuhe as kv
    result = SearchResult(title='Demo', url='https://knigavuhe.org/book/demo/', source='knigavuhe.org')

    def cancelled(_result):
        raise Cancelled('cancel')
    monkeypatch.setattr(kv, '_resolve_search_result_title', cancelled)
    with pytest.raises(Cancelled):
        _hydrate_search_result_titles([result])


# Origin: test_release_integrity_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_windows_acceptance_uses_metadata_and_reaps_killed_process():
    source = (ROOT / 'tools' / 'qt_windows_acceptance.py').read_text(encoding='utf-8')
    assert 'from audioknigi.metadata import APP_VERSION' in source
    assert 'from audioknigi.core import APP_VERSION' not in source
    kill_block = source[source.index('process.kill()'):source.index('block["app_exit_code"]')]
    assert 'process.wait()' in kill_block


# Origin: test_release_quality_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool__release_quality_followup_20260915(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_metadata_title_falls_back_to_og_title_then_html_title():
    title, author, cover = extract_metadata_from_html('<meta property="og:title" content="OG Book"><meta property="og:image" content="cover.jpg">', fallback_title='fallback')
    assert title == 'OG Book'
    title2, _, _ = extract_metadata_from_html('<title>  HTML   Book </title>', fallback_title='')
    assert title2 == 'HTML Book'

def _request() -> DownloadRequest:
    book = Book(url='https://knigavuhe.org/book/1', title='Book', tracks=[Track(index=1, title='One', file='https://cdn.example/1.mp3')])
    return DownloadRequest(book=book, selected_indices=None, output_dir=Path('.'))

def test_provider_analysis_prefetches_cover_for_knigavuhe_and_poleknig():
    source = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    assert source.count('normalize_cover_cache(self._fetch_cover_bytes(book.cover_url, book.url))') >= 2


# Origin: test_report_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_knigavuhe_fetch_normalizes_scheme_less_url(monkeypatch):
    import audioknigi.knigavuhe as knigavuhe
    requested = []

    class Response:
        url = 'https://knigavuhe.org/book/sample/'
        text = 'unused'

        @staticmethod
        def raise_for_status():
            return None

    class Session:

        def get(self, url, **kwargs):
            requested.append((url, kwargs))
            return Response()
    expected = Book(url='https://knigavuhe.org/book/sample/', title='Sample', tracks=[Track(index=1, title='1', file='https://cdn.test/1.mp3')])
    monkeypatch.setattr(knigavuhe, 'get_http_session', lambda: Session())
    monkeypatch.setattr(knigavuhe, 'parse_book_html', lambda text, url: expected)
    monkeypatch.setattr(knigavuhe, '_hydrate_narration_variant_readers', lambda variants, current_url, cancel_event=None: variants)
    result = knigavuhe.fetch_book('knigavuhe.org/book/sample/')
    assert result is expected
    assert requested[0][0] == 'https://knigavuhe.org/book/sample/'

def test_knigavuhe_fetch_rejects_other_host_before_request(monkeypatch):
    import audioknigi.knigavuhe as knigavuhe
    monkeypatch.setattr(knigavuhe, 'get_http_session', lambda: pytest.fail('unsupported host must be rejected before opening a session'))
    with pytest.raises(RuntimeError):
        knigavuhe.fetch_book('https://example.com/book/sample/')

def test_knigavuhe_invalid_bookcontroller_json_falls_back_to_direct_mp3():
    from audioknigi.knigavuhe import parse_book_html
    html = '\n    <html><head><title>Fallback Book</title></head><body>\n    <script>\n      BookController.enter({book: \'legacy\'}, secondArg);\n      window.audio = "https://cdn.example.test/audio/001.mp3";\n    </script>\n    </body></html>\n    '
    book = parse_book_html(html, 'https://knigavuhe.org/book/fallback/')
    assert book.title == 'Fallback Book'
    assert [track.file for track in book.tracks] == ['https://cdn.example.test/audio/001.mp3']


# Origin: test_report_followup_round10_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_knigavuhe_title_filter_does_not_hide_legitimate_comment_or_review_titles():
    assert _usable_search_title('Отзыв посла')
    assert _usable_search_title('Комментарии к Галльской войне')
    assert _usable_search_title('Отзыв')
    assert not _usable_search_title('Слушать онлайн')
    assert not _usable_search_title('Отзывы (12)')

def test_knigavuhe_extract_call_argument_tracks_nested_parentheses():
    source = 'BookController.enter((function(){return {id: 7};})(), {other: true});'
    assert _extract_call_argument(source) == '(function(){return {id: 7};})()'

def test_poleknig_variant_discovery_propagates_preexisting_cancel():
    event = threading.Event()
    event.set()
    with pytest.raises(Cancelled):
        _discover_narration_variants('', 'https://poleknig.com/books/1', {}, cancel_event=event)

class _Response__report_followup_round10_20260916:
    text = '<html><head><title>Тестовая книга</title></head><body>Исполнитель: Иван Иванов, Жанр: Фантастика</body></html>'

    def raise_for_status(self):
        return None

class _Session__report_followup_round10_20260916:

    def get(self, *args, **kwargs):
        return _Response__report_followup_round10_20260916()

def test_audioknigi_narrator_parser_stops_before_comma_metadata_field():
    result = SearchResult(title='Тестовая книга', url='https://audioknigi.com.ua/test', source='audioknigi.com.ua')
    hydrated = _audioknigi_page_metadata(result, session_factory=lambda: _Session__report_followup_round10_20260916(), metadata_extractor=lambda html, title: ('', '', ''), extended_metadata_extractor=lambda html: ('', '', '', ''))
    assert hydrated.narrator == 'Иван Иванов'


# Origin: test_report_followup_round11_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_playlist_track_title_decodes_html_entities():
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    book = service._parse_playlist_data(url='https://audioknigi.com.ua/demo', html_text='<title>Demo</title>', page_title='Demo', playlist_url='https://audioknigi.com.ua/demo.pl.txt', playlist_text=json.dumps([{'file': '1.mp3', 'title': '&quot;Глава 1&quot; &amp; 2'}], ensure_ascii=False))
    assert book.tracks[0].title == '"Глава 1" & 2'

def test_json_ld_parses_before_unescaping_entities():
    html = '<script type="application/ld+json">{"@type":"Book","name":"A &quot;quoted&quot; &amp; safe"}</script>'
    items = _first_json_ld(html)
    assert items == [{'@type': 'Book', 'name': 'A "quoted" & safe'}]


# Origin: test_report_followup_round12_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_structured_book_nodes_accept_schema_org_uri_and_prefix_types():
    html = '\n    <script type="application/ld+json">\n    [\n      {"@type":"https://schema.org/Book","name":"One"},\n      {"@type":"http://schema.org/Audiobook","name":"Two"},\n      {"@type":"schema:CreativeWork","name":"Three"},\n      {"@type":"WebSite","name":"Ignore"}\n    ]\n    </script>\n    '
    assert [row['name'] for row in _structured_book_nodes(html)] == ['One', 'Two', 'Three']

def test_knigavuhe_fetch_book_honors_already_cancelled_event(monkeypatch):
    import audioknigi.knigavuhe as knigavuhe
    event = threading.Event()
    event.set()

    def should_not_open_session():
        raise AssertionError('HTTP session must not be opened after cancellation')
    monkeypatch.setattr(knigavuhe, 'get_http_session', should_not_open_session)
    with pytest.raises(Cancelled):
        knigavuhe.fetch_book('https://knigavuhe.org/book/demo/', cancel_event=event)


# Origin: test_report_followup_round13_20260916.py
def test_audioknigi_query_filter_ignores_noise_and_accepts_initials():
    from audioknigi.providers.audioknigi_search import _matches_query
    assert _matches_query('Метель', 'Метель аудиокнига')
    assert _matches_query('Метель', 'аудиокнига')
    assert _matches_query('Война и мир', 'Лев Толстой', author='Л. Н. Толстой')
    assert not _matches_query('Дозор', 'Лев Толстой', author='С. Лукьяненко')


# Origin: test_report_followup_round14_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_poleknig_search_does_not_drop_site_ranked_result_for_extra_query_terms(monkeypatch):
    row = SearchResult(title='Гарри Поттер и философский камень', author='Джоан Роулинг', narrator='Иван Иванов', url='https://poleknig.com/books/1', source='poleknig.com')

    class Response:
        text = '<html></html>'
        url = 'https://poleknig.com/?s=test'
    monkeypatch.setattr(poleknig__report_followup_round14_20260916, '_fetch_search_page', lambda *_args, **_kwargs: Response())
    monkeypatch.setattr(poleknig__report_followup_round14_20260916, '_search_last_page', lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(poleknig__report_followup_round14_20260916, 'parse_search_results', lambda *_args, **_kwargs: [row])
    monkeypatch.setattr(poleknig__report_followup_round14_20260916, '_hydrate_search_result_info', lambda item: (item, []))
    monkeypatch.setattr(poleknig__report_followup_round14_20260916, '_book_page_author_links', lambda *_args, **_kwargs: [])
    monkeypatch.setattr(poleknig__report_followup_round14_20260916, '_expand_matching_author_catalogs', lambda *_args, **_kwargs: [])
    results = poleknig__report_followup_round14_20260916.search('гарри поттер аудиокнига росмэн')
    assert [item.url for item in results] == [row.url]

def test_poleknig_playwright_exposure_uses_circular_safe_json():
    source = (ROOT / 'audioknigi' / 'poleknig.py').read_text(encoding='utf-8')
    assert 'const safeJson = (value) =>' in source
    assert "if (seen.has(item)) return '[Circular]'" in source
    assert 'values.push(JSON.stringify(v))' not in source

def test_narration_switch_preserves_selected_chapters_contract():
    source = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'analysis_download.py').read_text(encoding='utf-8')
    assert 'self._pending_narration_selected_indices = list(self.track_model.selected_indices())' in source
    assert 'pending_narration_selection = getattr(self, "_pending_narration_selected_indices", None)' in source

def test_sidecar_metadata_uses_mapping_safe_track_fields():
    source = (ROOT / 'audioknigi' / 'download_engine.py').read_text(encoding='utf-8')
    block = source[source.index('def _sidecar_metadata_matches_book'):source.index('def _full_mp3_target')]
    assert 'self._book_field(track, "index", -1)' in block
    assert 'self._book_field(track, "title", "")' in block


# Origin: test_report_followup_round18_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_audioknigi_initial_matching_uses_person_fields_not_title_one_letter_words() -> None:
    assert _matches_query('Евгений Онегин', 'Александр Пушкин', author='А. С. Пушкин')
    assert not _matches_query('Море а ветер', 'Александр море', author='')


# Origin: test_report_followup_round19_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_poleknig_slash_slug_is_supported_and_canonicalized() -> None:
    raw = 'https://www.poleknig.com/books/12345/some-slug?utm_source=test#fragment'
    assert is_supported_url(raw)
    assert normalize_supported_url(raw) == 'https://poleknig.com/books/12345'
    assert poleknig__report_followup_round19_20260917._canonical_book_url('https://poleknig.com/', raw) == 'https://poleknig.com/books/12345'
    assert poleknig__report_followup_round19_20260917._canonical_book_url('https://poleknig.com/', '/books/12345/some-slug') == 'https://poleknig.com/books/12345'

def test_knigavuhe_fallback_prefers_known_matching_narrator(monkeypatch) -> None:
    original = Book(title='Book', author='Author', narrator='Exact Narrator', url='https://audioknigi.com.ua/audio-1')
    results = [SearchResult(title='Book', author='Author', narrator='', url='https://knigavuhe.org/book/unknown/', source='knigavuhe'), SearchResult(title='Book', author='Author', narrator='Exact Narrator', url='https://knigavuhe.org/book/exact/', source='knigavuhe')]
    monkeypatch.setattr(analysis_module, 'search_knigavuhe_books', lambda *_a, **_k: results)

    def fake_fetch(url, **_kwargs):
        narrator = '' if 'unknown' in url else 'Exact Narrator'
        return Book(title='Book', author='Author', narrator=narrator, url=url)
    monkeypatch.setattr(analysis_module, 'fetch_knigavuhe_book', fake_fetch)
    selected = BookAnalysisService()._knigavuhe_fallback_candidate(original)
    assert selected is not None
    assert selected.url.endswith('/exact/')

def test_round19_duplicate_metadata_uses_mapping_aware_book_fields() -> None:
    source = (ROOT / 'audioknigi/download_engine.py').read_text(encoding='utf-8')
    history = source.split('def _history_metadata_matches_book', 1)[1].split('def _sidecar_metadata_matches_book', 1)[0]
    sidecar = source.split('def _sidecar_metadata_matches_book', 1)[1].split('def _full_mp3_target', 1)[0]
    assert 'self._book_field(book, "url", "")' in history
    assert 'self._book_field(book, "tracks", [])' in history
    assert 'self._book_field(book, name, "")' in history
    assert 'self._book_field(book, "url", "")' in sidecar
    assert 'self._book_field(book, "tracks", [])' in sidecar


# Origin: test_report_followup_round20_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_knigavuhe_call_argument_balances_parentheses_inside_object() -> None:
    source = 'BookController.enter({title: "Book", value: fn(1, nested(2)), rows: [x(3)]}, true);'
    argument = knigavuhe__report_followup_round20_20260917._extract_call_argument(source)
    assert argument.startswith('{title: "Book"')
    assert 'fn(1, nested(2))' in argument
    assert argument.endswith('}')

def test_eta_float_string_and_nonfinite_playlist_times_are_safe() -> None:
    assert fmt_eta('120.5') == '00:02:00'
    assert parse_time_seconds(float('inf')) is None
    assert parse_time_seconds('Infinity') is None
    assert parse_time_seconds('1e308:00') is None

def test_poleknig_symbol_only_titles_do_not_merge_by_author(monkeypatch) -> None:
    response = SimpleNamespace(text='', url='https://poleknig.com/search/')
    rows = [SearchResult(title='!!!', author='Толстой', narrator='A', url='https://poleknig.com/books/1', source='poleknig'), SearchResult(title='???', author='Толстой', narrator='B', url='https://poleknig.com/books/2', source='poleknig')]
    monkeypatch.setattr(poleknig__report_followup_round20_20260917, '_fetch_search_page', lambda *_a, **_k: response)
    monkeypatch.setattr(poleknig__report_followup_round20_20260917, 'parse_search_results', lambda *_a, **_k: list(rows))
    monkeypatch.setattr(poleknig__report_followup_round20_20260917, '_search_last_page', lambda *_a, **_k: 1)
    monkeypatch.setattr(poleknig__report_followup_round20_20260917, '_hydrate_search_result_info', lambda item: (item, []))
    monkeypatch.setattr(poleknig__report_followup_round20_20260917, '_book_page_author_links', lambda *_a, **_k: [])
    monkeypatch.setattr(poleknig__report_followup_round20_20260917, '_expand_matching_author_catalogs', lambda *_a, **_k: [])
    results = poleknig__report_followup_round20_20260917.search('толстой')
    assert [item.url for item in results] == [rows[0].url, rows[1].url]

def test_audioknigi_search_prefers_utf8_response_bytes(monkeypatch) -> None:
    captured = {}
    html = '<a href="/audio-1">Война и мир</a>'
    mojibake = html.encode('utf-8').decode('latin-1')

    class Response:
        url = 'https://audioknigi.com.ua/search'
        content = html.encode('utf-8')
        text = mojibake

        def raise_for_status(self):
            return None

    class Session:

        def get(self, *_a, **_k):
            return Response()
    monkeypatch.setattr(search_module, 'get_http_session', lambda: Session())

    def fake_parse(text, *_a, **_k):
        captured['text'] = text
        return []
    monkeypatch.setattr(search_module, 'parse_audioknigi_results', fake_parse)
    search_module.search_audioknigi('война')
    assert captured['text'] == html


# Origin: test_report_followup_round21_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_knigavuhe_script_fallback_exposes_current_narration_variant() -> None:
    html = '\n        <html><head><title>Тестовая книга — автор Автор Тест</title></head>\n        <body><script>const audio = "https://cdn.example.test/book/001.mp3";</script></body></html>\n    '
    book = knigavuhe__report_followup_round21_20260917._fallback_script_book(html, 'https://knigavuhe.org/book/test/')
    assert book is not None
    assert len(book.narration_variants) == 1
    variant = book.narration_variants[0]
    assert variant.current is True
    assert variant.available is True
    assert variant.url == book.url
    assert variant.title == book.title

def test_poleknig_author_keys_accept_initials_but_reject_unrelated_people() -> None:
    full = poleknig__report_followup_round21_20260917._person_key('Илья Ильф, Евгений Петров')
    initials = poleknig__report_followup_round21_20260917._person_key('И. Ильф, Е. Петров')
    unrelated = poleknig__report_followup_round21_20260917._person_key('Иван Бунин')
    assert poleknig__report_followup_round21_20260917._person_keys_compatible(full, initials)
    assert poleknig__report_followup_round21_20260917._person_keys_compatible(initials, full)
    assert not poleknig__report_followup_round21_20260917._person_keys_compatible(full, unrelated)


# Origin: test_report_followup_round22_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_poleknig_book_title_preserves_meaningful_edge_punctuation() -> None:
    meta = poleknig__report_followup_round22_20260917._book_page_metadata('<html><body><h1>— Название книги —</h1></body></html>', 'https://poleknig.com/books/123')
    assert meta['title'] == '— Название книги —'


# Origin: test_report_followup_round24_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_canonical_audioknigi_title_removes_online_before_or_after_label() -> None:
    assert _canonical_title('Слушать онлайн аудиокнигу Крыса') == 'Крыса'
    assert _canonical_title('Слушать аудиокнигу онлайн: Крыса') == 'Крыса'
    assert _canonical_title('Аудиокнига онлайн — Крыса') == 'Крыса'

def test_playlist_machine_titles_do_not_leak_into_track_table_or_filenames() -> None:
    media = 'https://cdn.example/king_Rat_1.mp3'
    assert _playlist_track_title('king_Rat_1, king_Rat_1', media, 1, 'Крыса', 2) == 'Крыса — 01'
    assert _playlist_track_title('king_Rat_2', 'https://cdn.example/king_Rat_2.mp3', 2, 'Крыса', 2) == 'Крыса — 02'
    assert _playlist_track_title('Глава первая', media, 1, 'Крыса', 2) == 'Глава первая'

def test_knigavuhe_argument_parser_ignores_commented_out_calls_and_comment_brackets() -> None:
    source = '\n        // BookController.enter({"wrong": [)]});\n        /* BookController.enter({"also": "wrong"}); */\n        BookController.enter({"title": "ok", /* ) ] } */ "parts": [1, 2]}, true);\n    '
    value = _extract_call_argument(source)
    assert '"title": "ok"' in value
    assert '"parts": [1, 2]' in value
    assert 'wrong' not in value

def test_playwright_playlist_capture_wait_is_cancellable_and_not_fixed_1500ms() -> None:
    source = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    block_start = source.index('page.goto(url, wait_until="domcontentloaded"')
    block = source[block_start:block_start + 1800]
    assert 'for _attempt in range(32):' in block
    assert 'page.wait_for_timeout(250)' in block
    assert 'self._check_cancel()' in block
    assert 'page.wait_for_timeout(1500)' not in block


# Origin: test_report_followup_round2_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_ambiguous_dash_title_is_not_invented_as_author():

    class Response:
        text = '<html><title>Гарри Поттер — Философский камень</title></html>'

        def raise_for_status(self):
            return None

    class Session:

        def get(self, *_args, **_kwargs):
            return Response()
    result = SearchResult(title='Гарри Поттер — Философский камень', author='', url='https://audioknigi.com.ua/audio-1-test', source='audioknigi.com.ua')
    enriched = _audioknigi_page_metadata(result, session_factory=Session, metadata_extractor=lambda _html, fallback: (fallback, '', ''), extended_metadata_extractor=lambda _html: ('', '', '', ''))
    assert enriched.author == ''
    assert enriched.title == 'Гарри Поттер — Философский камень'


# Origin: test_report_followup_round30_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_easy_mode_exposes_narration_picker_for_multi_variant_results() -> None:
    main = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    search = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    assert 'self.easy_narration_combo = QComboBox()' in main
    assert 'identifier="easy_narration_variant"' in main
    assert 'easy_selection_model.selectionChanged.connect(self._easy_search_selection_changed)' in main
    assert 'def _refresh_easy_narration_variants' in search
    assert 'self.easy_narration_combo.addItem(self._l("Выберите озвучку…"), "")' in search
    assert 'for idx, item in enumerate(variants, start=1):' in search

def test_easy_mode_does_not_auto_choose_first_of_multiple_narrations() -> None:
    search = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    assert 'self.easy_narration_combo.setCurrentIndex(0)' in search
    assert 'narration_ready = len(variants) <= 1 or self._easy_selected_narration(easy_result) is not None' in search
    assert 'self.set_status(self._l("Выберите озвучку перед анализом книги."), assertive=True)' in search
    assert 'self.easy_narration_combo.setFocus(Qt.FocusReason.OtherFocusReason)' in search

def test_selected_easy_narration_url_is_used_for_analysis_and_preserves_variants() -> None:
    search = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    block = search[search.index('def use_selected_result'):search.index('def copy_selected_url')]
    assert 'selected_variant = self._easy_selected_narration(result)' in block
    assert 'selected_result = replace(result, url=selected_url, narrator=selected_narrator or result.narrator)' in block
    assert 'self._pending_search_result = selected_result' in block
    assert 'self.book_url_edit.setText(selected_result.url)' in block

def test_single_narration_keeps_one_click_flow() -> None:
    search = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    assert 'multiple = len(variants) > 1' in search
    assert 'self.easy_narration_label.setVisible(multiple and self.current_ui_mode() == "easy")' in search
    assert 'self.easy_narration_combo.setVisible(multiple and self.current_ui_mode() == "easy")' in search


# Origin: test_report_followup_round31_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_analysis_populates_easy_annotation_only_when_description_exists() -> None:
    source = _source('audioknigi/qt/mixins/analysis_download.py')
    assert 'easy_description = str(book.description or "").strip()' in source
    assert 'self.easy_description.setPlainText(easy_description)' in source
    assert 'self.easy_description_title.setVisible(bool(easy_description))' in source
    assert 'self.easy_description.setVisible(bool(easy_description))' in source
    assert 'self.easy_description.setAccessibleDescription(easy_description)' in source


# Origin: test_report_followup_round32_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round32_20260918(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

def test_missing_track_title_uses_unique_track_number_not_book_title() -> None:
    book = Book(url='https://example', title='Book', tracks=[Track(index=1, title='', file='a'), Track(index=2, title='', file='b')])
    assert template_values(book, book.tracks[0])['Track_Title'] == 'track-01'
    assert template_values(book, book.tracks[1])['Track_Title'] == 'track-02'

def test_audioknigi_html_paths_decode_content_as_utf8_sig() -> None:
    provider = src__report_followup_round32_20260918('audioknigi/providers/audioknigi_search.py')
    analysis = src__report_followup_round32_20260918('audioknigi/services/book_analysis_service.py')
    assert 'content.decode("utf-8-sig", errors="replace")' in provider
    assert 'content.decode("utf-8-sig", errors="replace")' in analysis

def test_knigavuhe_analysis_fallback_uses_clean_identity_hint() -> None:
    source = src__report_followup_round32_20260918('audioknigi/services/book_analysis_service.py')
    assert 'def _book_identity_hints' in source
    assert 'title_hint, author_hint, narrator_hint = self._book_identity_hints(book)' in source
    assert 'search_knigavuhe_books(title_hint' in source


# Origin: test_report_followup_round33_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round33_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_knigavuhe_grouped_search_collects_all_unique_narrators() -> None:
    source = src__report_followup_round33_20260918('audioknigi/knigavuhe.py')
    block = source[source.index('# Collapse separate recording pages'):source.index('__all__', source.index('# Collapse separate recording pages'))]
    assert 'narrators = []' in block
    assert 'if narrator and narrator not in narrators:' in block
    assert 'narrator=", ".join(narrators)' in block

def test_audioknigi_search_normalizes_query_and_decodes_bom() -> None:
    source = src__report_followup_round33_20260918('audioknigi/providers/audioknigi_search.py')
    block = source[source.index('def search_audioknigi'):source.index('__all__')]
    assert 'query_text = str(query or "").strip()' in block
    assert 'if not query_text:' in block
    assert 'params={"text": query_text}' in block
    assert '.decode("utf-8-sig", errors="replace")' in block

def test_round55_parallel_search_is_bounded_and_keeps_stable_provider_order() -> None:
    search = src__report_followup_round33_20260918('audioknigi/services/search_service.py')
    bootstrap = src__report_followup_round33_20260918('tools/pyinstaller_bootstrap.py')
    assert 'ThreadPoolExecutor(max_workers=min(4, len(providers))' in search
    assert 'provider_results_by_key' in search
    assert 'for provider in providers:' in search
    assert 'results.extend(provider_results_by_key.get(provider.key, []))' in search
    assert 'hasattr(platform, "_wmi")' in bootstrap


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_poleknig_prefers_real_visible_annotation_over_seo_meta_description() -> None:
    html = '\n    <html><head>\n      <title>«Крыса» Автор: слушать аудиокнигу</title>\n      <meta name="description" content="Скачать аудиокнигу Автор Крыса бесплатно и слушать аудиокнигу онлайн">\n      <meta property="og:image" content="/cover.jpg">\n    </head><body>\n      <h1>Крыса</h1>\n      <a href="/authors/12-author">Автор</a>\n      <div class="book-description">\n        Настоящая аннотация книги рассказывает о герое, который оказывается перед трудным выбором.\n        Это содержательное описание сюжета, а не служебный текст страницы для поисковых систем.\n      </div>\n    </body></html>\n    '
    meta = _book_page_metadata(html, 'https://poleknig.com/books/1')
    assert meta['description'].startswith('Настоящая аннотация книги')
    assert 'Скачать аудиокнигу' not in meta['description']

def test_poleknig_drops_seo_description_if_no_real_annotation_exists() -> None:
    html = '\n    <html><head><meta name="description" content="Скачать аудиокнигу Автор Крыса и слушать аудиокнигу онлайн"></head>\n    <body><h1>Крыса</h1><a href="/authors/12-author">Автор</a></body></html>\n    '
    assert _book_page_metadata(html, 'https://poleknig.com/books/1')['description'] == ''

def test_standalone_track_is_not_trimmed_by_rounded_metadata_duration() -> None:
    source = src__report_followup_round34_20260919('audioknigi/download/media.py')
    block = source[source.index('def _split_track'):source.index('def _save_book_sidecars')]
    assert 'elif start is None and end is None:' in block
    assert 'process the complete source to EOF' in block

def test_knigavuhe_js_call_parser_does_not_scan_past_assignment() -> None:
    assert _extract_call_argument('BookController.enter = function(x) {}; foo({"wrong": 1});') == ''
    assert '"ok": 1' in _extract_call_argument('BookController.enter   ({"ok": 1}, true);')

def test_audioknigi_author_prefix_handles_reordered_full_name() -> None:
    assert _strip_author_prefix_from_title('Лев Толстой - Война и мир', 'Толстой Лев Николаевич') == 'Война и мир'
    assert _strip_author_prefix_from_title('Метро 2033 — Тёмные туннели', 'Дмитрий Глуховский') == 'Метро 2033 — Тёмные туннели'

def test_search_status_distinguishes_provider_errors() -> None:
    source = src__report_followup_round34_20260919('audioknigi/services/search_service.py')
    assert 'provider_failed = False' in source
    assert 'f"Ошибка источника {provider.display_name}"' in source


# Origin: test_report_followup_round36_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round36_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_audioknigi_title_removes_seo_suffix_and_site_url() -> None:
    clean = audioknigi_search._canonical_title
    assert clean('Крыса аудиокнига слушать онлайн https://audioknigi.com.ua/') == 'Крыса'
    assert clean('Слушать онлайн аудиокнигу Крыса') == 'Крыса'
    assert clean('Аудиокнига онлайн — Крыса') == 'Крыса'

def test_audioknigi_author_prefix_without_dash_is_removed_from_title() -> None:
    strip = audioknigi_search._strip_author_prefix_from_title
    assert strip('Бурносов Юрий Тоннельная крыса', 'Юрий Бурносов') == 'Тоннельная крыса'
    assert strip('Лев Толстой - Война и мир', 'Толстой Лев Николаевич') == 'Война и мир'
    assert strip('Метро 2033 — Тёмные туннели', 'Дмитрий Глуховский') == 'Метро 2033 — Тёмные туннели'

def test_audioknigi_query_relevance_rejects_reported_unrelated_titles() -> None:
    matches = audioknigi_search._matches_query
    assert matches('Крыса', 'Крыса')
    assert matches('Тоннельная крыса', 'Крыса', author='Юрий Бурносов')
    assert not matches('Четыре всадника', 'Крыса', author='Докинз, Харрис, Хитченс, Деннет')
    assert not matches('Большие друзья. Музыкальные сказки', 'Крыса')
    assert not matches('Как удвоить объем памяти', 'Крыса')

def test_audioknigi_grouping_filters_unrelated_results_even_without_metadata(monkeypatch) -> None:
    items = [audioknigi_search.SearchResult(title='Крыса', url='https://audioknigi.com.ua/audio-1-krysa', source='audioknigi.com.ua'), audioknigi_search.SearchResult(title='Четыре всадника', url='https://audioknigi.com.ua/audio-2-four', source='audioknigi.com.ua'), audioknigi_search.SearchResult(title='Большие друзья. Музыкальные сказки', url='https://audioknigi.com.ua/audio-3-friends', source='audioknigi.com.ua')]
    monkeypatch.setattr(audioknigi_search, '_audioknigi_page_metadata', lambda item: item)
    result = audioknigi_search._group_audioknigi_recordings(items, query='Крыса')
    assert [item.title for item in result] == ['Крыса']

def test_audioknigi_real_annotation_beats_seo_description() -> None:
    html = '\n    <html><head>\n      <meta name="description" content="Крыса аудиокнига слушать онлайн https://audioknigi.com.ua/">\n    </head><body>\n      <div class="book-description">\n        Настоящая аннотация рассказывает о герое, его конфликте и событиях книги.\n      </div>\n    </body></html>\n    '
    value = audioknigi_search._audioknigi_description_from_html(html, title='Крыса', author='Автор')
    assert value.startswith('Настоящая аннотация')
    assert 'слушать онлайн' not in value.casefold()

def test_audioknigi_analysis_normalizes_title_author_and_description() -> None:
    html = '\n    <html><head>\n      <title>Бурносов Юрий Тоннельная крыса аудиокнига слушать онлайн https://audioknigi.com.ua/</title>\n      <script type="application/ld+json">\n      {"@context":"https://schema.org","@type":"AudioBook","name":"Бурносов Юрий Тоннельная крыса аудиокнига слушать онлайн","author":{"@type":"Person","name":"Юрий Бурносов"},"description":"Слушать аудиокнигу онлайн бесплатно"}\n      </script>\n    </head><body>\n      <div class="book-description">Содержательная аннотация о событиях романа и главных героях.</div>\n    </body></html>\n    '
    service = BookAnalysisService(cancel_event=threading.Event(), options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    book = service._parse_playlist_data(url='https://audioknigi.com.ua/audio-1-tonnelnaya-krysa', html_text=html, page_title='', playlist_url='https://audioknigi.com.ua/list.pl.txt', playlist_text='[{"file":"https://cdn.example/1.mp3","title":"Глава 1"}]')
    assert book.title == 'Тоннельная крыса'
    assert book.author == 'Юрий Бурносов'
    assert book.description.startswith('Содержательная аннотация')

def test_knigavuhe_annotation_prefers_visible_description_and_rejects_seo_meta() -> None:
    html = '\n    <meta name="description" content="Крыса слушать аудиокнигу бесплатно на knigavuhe.org">\n    <div class="book__description">Настоящая аннотация Knigavuhe с описанием сюжета книги.</div>\n    '
    assert knigavuhe_description(html).startswith('Настоящая аннотация Knigavuhe')
    seo_only = '<meta name="description" content="Крыса слушать аудиокнигу бесплатно на knigavuhe.org">'
    assert knigavuhe_description(seo_only) == ''

def test_poleknig_annotation_contract_still_prefers_visible_synopsis() -> None:
    html = '\n    <head><meta name="description" content="Скачать аудиокнигу Крыса бесплатно и слушать онлайн"></head>\n    <body><h1>Крыса</h1><a href="/authors/1">Автор</a>\n    <div class="book-description">Реальная аннотация с содержательным описанием сюжета и героя.</div></body>\n    '
    meta = poleknig_metadata(html, 'https://poleknig.com/books/1')
    assert meta['description'].startswith('Реальная аннотация')


# Origin: test_report_followup_round37_20260919.py
def test_knigavuhe_strict_relevance_rejects_reported_unrelated_books() -> None:
    query = 'Крыса'
    assert _knigavuhe_matches_query(SearchResult(title='Крысы в стенах', author='Говард Филлипс Лавкрафт', narrator='VartKes', url='https://knigavuhe.org/book/rats/', source='knigavuhe.org'), query)
    for title in ('Крауч Энд', 'Дворец грез', 'Кому жить на Руси хорошо'):
        assert not _knigavuhe_matches_query(SearchResult(title=title, author='Другой автор', narrator='Другой чтец', url=f'https://knigavuhe.org/book/{title}/', source='knigavuhe.org'), query)

def test_knigavuhe_hydration_applies_final_query_filter_without_network_when_metadata_complete() -> None:
    items = [SearchResult(title='Крысы в стенах', author='Лавкрафт', narrator='VartKes', url='https://knigavuhe.org/book/rats/', source='knigavuhe.org'), SearchResult(title='Крауч Энд', author='Стивен Кинг', narrator='Чтец', url='https://knigavuhe.org/book/crouch-end/', source='knigavuhe.org'), SearchResult(title='Дворец грез', author='Автор', narrator='Чтец', url='https://knigavuhe.org/book/palace/', source='knigavuhe.org'), SearchResult(title='Кому жить на Руси хорошо', author='Некрасов', narrator='Чтец', url='https://knigavuhe.org/book/rus/', source='knigavuhe.org')]
    filtered = _hydrate_search_result_titles(items, 'Крыса')
    assert [item.title for item in filtered] == ['Крысы в стенах']

class _Response__report_followup_round37_20260919:

    def __init__(self, html: str):
        self.content = html.encode('utf-8')
        self.text = html
        self.url = 'https://audioknigi.com.ua/audio-test'

    def raise_for_status(self):
        return None

class _Session__report_followup_round37_20260919:

    def __init__(self, html: str):
        self.html = html

    def get(self, *args, **kwargs):
        return _Response__report_followup_round37_20260919(self.html)

def test_audioknigi_page_metadata_keeps_coauthor_out_of_title_and_merges_authors() -> None:
    html = '<html><title>Бурносова Татьяна - Тоннельная крыса</title></html>'
    source = SearchResult(title='Тоннельная крыса', author='Бурносова Татьяна', url='https://audioknigi.com.ua/audio-test', source='audioknigi.com.ua')
    result = audioknigi_search._audioknigi_page_metadata(source, session_factory=lambda: _Session__report_followup_round37_20260919(html), metadata_extractor=lambda _html, _fallback: ('Бурносова Татьяна - Тоннельная крыса', 'Бурносов Юрий', ''), extended_metadata_extractor=lambda _html: ('', 'Чтец', '', ''))
    assert result.title == 'Тоннельная крыса'
    assert 'Бурносова Татьяна' in result.author
    assert 'Бурносов Юрий' in result.author

def test_audioknigi_author_merging_deduplicates_reordered_same_person() -> None:
    merged = audioknigi_search._merge_author_names('Юрий Бурносов', 'Бурносов Юрий', 'Татьяна Бурносова')
    assert merged.count('Юрий') == 1
    assert 'Татьяна Бурносова' in merged

def test_direct_audioknigi_analysis_does_not_invent_unverified_author_prefix() -> None:
    html = '\n    <title>Гарри Поттер — Философский камень</title>\n    <script type="application/ld+json">\n    {"@context":"https://schema.org","@type":"AudioBook",\n     "name":"Гарри Поттер — Философский камень",\n     "author":{"@type":"Person","name":"Джоан Роулинг"},\n     "description":"Настоящая аннотация книги."}\n    </script>\n    <div class="book-description">Настоящая аннотация книги о событиях романа.</div>\n    '
    service = BookAnalysisService(cancel_event=threading.Event(), options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    book = service._parse_playlist_data(url='https://audioknigi.com.ua/audio-test', html_text=html, page_title='', playlist_url='https://audioknigi.com.ua/list.pl.txt', playlist_text='[{"file":"https://cdn.example/1.mp3","title":"Глава 1"}]')
    assert book.title == 'Гарри Поттер — Философский камень'
    assert book.author == 'Джоан Роулинг'


# Origin: test_report_followup_round38_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round38_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_audioknigi_multi_author_prefix_is_removed_from_title() -> None:
    value = 'Бурносов Юрий, Бурносова Татьяна - Тоннельная крыса'
    title, authors = audioknigi_search._split_multi_author_prefix(value)
    assert title == 'Тоннельная крыса'
    assert authors == 'Бурносов Юрий, Бурносова Татьяна'
    assert audioknigi_search._split_audioknigi_title(value) == (title, authors)

def test_multi_author_split_does_not_treat_ordinary_dash_title_as_multi_author() -> None:
    value = 'Гарри Поттер — Философский камень'
    assert audioknigi_search._split_multi_author_prefix(value) == (value, '')

def test_audioknigi_page_hydration_merges_multi_author_prefix_with_structured_author() -> None:

    class Response:
        url = 'https://audioknigi.com.ua/audio-test'
        text = ''
        content = '<html><title>Бурносов Юрий, Бурносова Татьяна - Тоннельная крыса</title></html>'.encode('utf-8')

        def raise_for_status(self):
            return None

    class Session:

        def get(self, *args, **kwargs):
            return Response()
    result = audioknigi_search.SearchResult(title='Бурносов Юрий, Бурносова Татьяна - Тоннельная крыса', author='', url='https://audioknigi.com.ua/audio-test', source='audioknigi.com.ua')
    hydrated = audioknigi_search._audioknigi_page_metadata(result, session_factory=Session, metadata_extractor=lambda _html, _fallback: ('Бурносова Татьяна - Тоннельная крыса', 'Бурносов Юрий', ''), extended_metadata_extractor=lambda _html: ('', 'Чтец', '', ''))
    assert hydrated.title == 'Тоннельная крыса'
    assert 'Бурносов Юрий' in hydrated.author
    assert 'Бурносова Татьяна' in hydrated.author

def test_direct_audioknigi_analysis_imports_multi_author_normalizer() -> None:
    source = src__report_followup_round38_20260919('audioknigi/services/book_analysis_service.py')
    assert '_split_multi_author_prefix as _split_audioknigi_multi_author_prefix' in source
    assert '_merge_author_names as _merge_audioknigi_authors' in source
    assert 'visible_title, visible_authors = _split_audioknigi_multi_author_prefix(title)' in source
    assert 'metadata_book_title, metadata_prefix_authors = _split_audioknigi_multi_author_prefix(metadata_title)' in source


# Origin: test_report_followup_round3_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_playlist_url_and_track_numbering_are_hardened():
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    assert service._extract_playlist_url('<script>"//cdn.example/a.pl.txt"</script>') == 'https://cdn.example/a.pl.txt'
    assert service._extract_playlist_url('<script>"/media/a.pl.txt"</script>') == '/media/a.pl.txt'
    playlist = json.dumps([{'file': '1.mp3', 'title': 'One'}, {'title': 'ad'}, {'file': '3.mp3', 'title': 'Three'}])
    book = service._parse_playlist_data(url='https://audioknigi.com.ua/book/1', html_text='<title>Demo</title>', page_title='Demo', playlist_url='https://cdn.example/a.pl.txt', playlist_text=playlist)
    assert [track.index for track in book.tracks] == [1, 2]


# Origin: test_report_followup_round41_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round41_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_search_columns_prioritize_full_author_and_narrator_names() -> None:
    search = src__report_followup_round41_20260920('audioknigi/qt/mixins/search.py')
    assert 'for column in (0, 4, 5):' in search
    assert 'search_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)' in search
    assert 'search_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)' in search
    assert 'search_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)' in search
    assert 'self.search_table.setColumnWidth(2, 260)' in search
    assert 'self.search_table.setColumnWidth(3, 280)' in search


# Origin: test_report_followup_round43_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round43_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_knigavuhe_query_initials_match_in_both_directions_without_single_letter_false_positive() -> None:
    full = SearchResult(title='Война и мир', author='Лев Толстой', narrator='Иван Иванов', url='https://knigavuhe.org/book/1/', source='knigavuhe')
    abbreviated = SearchResult(title='Война и мир', author='Л. Толстой', narrator='И. Иванов', url='https://knigavuhe.org/book/1/', source='knigavuhe')
    assert knigavuhe__report_followup_round43_20260920._knigavuhe_matches_query(full, 'Л. Толстой')
    assert knigavuhe__report_followup_round43_20260920._knigavuhe_matches_query(abbreviated, 'Лев Толстой')
    assert not knigavuhe__report_followup_round43_20260920._knigavuhe_matches_query(full, 'Л.')
    assert not knigavuhe__report_followup_round43_20260920._knigavuhe_matches_query(full, 'А. Пушкин')

def test_knigavuhe_fallback_skips_zero_mp3_even_with_query_parameters() -> None:
    html = '\n    <title>Тестовая книга</title>\n    <script>\n    const a = "https://cdn.example/0.mp3?token=quiet";\n    const b = "https://cdn.example/1.mp3?token=real";\n    </script>\n    '
    book = knigavuhe__report_followup_round43_20260920._fallback_script_book(html, 'https://knigavuhe.org/book/test/')
    assert book is not None
    assert [track.file for track in book.tracks] == ['https://cdn.example/1.mp3?token=real']

def test_poleknig_js_literal_normalizer_ignores_backtick_template_text() -> None:
    raw = '[{title: `Chapter 1: true story`, enabled: true, extra: null}]'
    normalized = poleknig__report_followup_round43_20260920._normalize_js_literals_for_python(raw)
    assert '`Chapter 1: true story`' in normalized
    assert 'enabled: True' in normalized
    assert 'extra: None' in normalized

def test_author_merge_collapses_initial_and_full_name_but_keeps_different_initials() -> None:
    assert _merge_author_names('А. Пушкин', 'Александр Пушкин') == 'Александр Пушкин'
    assert _merge_author_names('Пушкин Александр', 'Александр Пушкин') == 'Пушкин Александр'
    assert _merge_author_names('А. Иванов', 'Б. Иванов') == 'А. Иванов, Б. Иванов'

def test_audioknigi_narrator_fallback_stops_at_duration_field() -> None:
    html = '<html><body>Исполнитель: Иван Иванов Время звучания: 12:34 Качество: 128 kbps</body></html>'

    class Response:
        content = html.encode('utf-8')
        text = html

        def raise_for_status(self):
            return None

    class Session:

        def get(self, *args, **kwargs):
            return Response()
    result = SearchResult(title='Книга', author='Автор', narrator='', url='https://audioknigi.com.ua/audio-1-test', source='audioknigi')
    hydrated = _audioknigi_page_metadata(result, session_factory=lambda: Session(), metadata_extractor=lambda _html, _title: ('', '', ''), extended_metadata_extractor=lambda _html: ('', '', '', ''))
    assert hydrated.narrator == 'Иван Иванов'


# Origin: test_report_followup_round44_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round44_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_audioknigi_initial_query_matches_full_person_name_but_not_unrelated_person() -> None:
    assert _matches_query('Война и мир', 'Л. Толстой Война', author='Лев Толстой')
    assert _matches_query('Война и мир', 'Лев Толстой Война', author='Л. Толстой')
    assert not _matches_query('Война и мир', 'А. Пушкин Война', author='Лев Толстой')
    assert not _matches_query('Война и мир', 'Л.', author='Лев Толстой')

def test_audioknigi_parser_accepts_relative_audio_href_without_leading_slash() -> None:
    html = '<a href="audio-12345-test-book">Тестовая книга</a>'
    results = parse_audioknigi_results(html, 'https://audioknigi.com.ua/search?q=test', 'Тестовая')
    assert len(results) == 1
    assert results[0].url == 'https://audioknigi.com.ua/audio-12345-test-book'

def test_audioknigi_response_decoder_uses_declared_legacy_encoding_after_utf8_fails() -> None:
    text = 'Александр Пушкин'
    response = SimpleNamespace(content=text.encode('cp1251'), encoding='windows-1251', apparent_encoding='windows-1251', text='')
    assert _response_html_text(response) == text


# Origin: test_report_followup_round45_20260921.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round45_20260921(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_audioknigi_relative_book_links_resolve_from_site_root_on_nested_search_pages() -> None:
    html = '<a href="audio-12345-test-book">Тестовая книга</a>'
    results = parse_audioknigi_results(html, 'https://audioknigi.com.ua/search/page/2/', 'Тестовая')
    assert len(results) == 1
    assert results[0].url == 'https://audioknigi.com.ua/audio-12345-test-book'

def test_poleknig_equal_zero_markers_do_not_create_zero_length_chapters() -> None:
    tracks = _parse_playlist_objects('[00:00]https://cdn.test/one.mp3,[00:00]https://cdn.test/two.mp3', 'https://poleknig.com/book/')
    assert len(tracks) == 2
    assert tracks[0].start == 0
    assert tracks[1].start == 0
    assert tracks[0].duration is None
    assert tracks[0].end is None

class _SplitDummy(MediaProcessingMixin):

    def __init__(self, target: Path):
        self.target = target

    def _track_path(self, _book, _track):
        return self.target

    def log(self, _message):
        pass


# Origin: test_report_followup_round46_20260922.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round46_20260922(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_knigavuhe_named_entity_is_terminal_for_nested_metadata_names() -> None:
    value = {'name': 'Александр Пушкин', 'genre': {'name': 'Классика'}, 'meta': {'category': {'name': 'Поэзия'}}}
    assert _extract_names(value) == ['Александр Пушкин']

def test_audioknigi_known_coauthor_prefixes_can_be_removed_consecutively() -> None:
    title = 'Александр Пушкин, Михаил Лермонтов - Стихи'
    for author in ('Александр Пушкин', 'Михаил Лермонтов'):
        candidate = _strip_author_prefix_from_title(title, author)
        if candidate != title:
            title = candidate.lstrip(' ,;')
    assert title == 'Стихи'

def test_full_mp3_playlist_refresh_resynchronizes_request_indices() -> None:
    source = src__report_followup_round46_20260922('audioknigi/download_engine.py')
    start = source.index('def run_full_mp3')
    end = source.find('\n    def ', start + len('def run_full_mp3'))
    block = source[start:] if end < 0 else source[start:end]
    assert 'req.book = book' in block
    assert 'req.selected_indices = [' in block
    assert 'req.track_index(track)' in block
    assert block.index('req.book = book') < block.index('req.selected_indices = [')


# Origin: test_report_followup_round47_20260923.py
def test_audioknigi_inferred_card_author_yields_to_structured_page_author():
    html = '<html><title>Гарри Поттер и Философский камень</title></html>'
    source = SearchResult(title='Философский камень', author='Гарри Поттер', author_inferred=True, url='https://audioknigi.com.ua/audio-1', source='audioknigi.com.ua')

    class Response:
        content = html.encode('utf-8')
        text = html

        def raise_for_status(self):
            return None

    class Session:

        def get(self, *args, **kwargs):
            return Response()
    result = audioknigi_search._audioknigi_page_metadata(source, session_factory=Session, metadata_extractor=lambda _html, _fallback: ('Гарри Поттер и Философский камень', 'Джоан Роулинг', ''), extended_metadata_extractor=lambda _html: ('', '', '', ''))
    assert result.author == 'Джоан Роулинг'
    assert result.title == 'Гарри Поттер и Философский камень'

def test_audioknigi_plain_narrator_is_reused_by_direct_analysis():
    html = '<div>Описание: текст книги. Читает: Иван Иванов Жанр: Фантастика</div>'
    assert audioknigi_search._audioknigi_plain_narrator(html) == 'Иван Иванов'

def test_direct_analysis_strips_all_coauthor_prefixes_and_plain_narrator():
    service = BookAnalysisService()
    html = '<html><body>Читает: Иван Иванов Жанр: Фантастика</body></html>'
    playlist = json.dumps([{'file': 'https://example.test/1.mp3', 'title': '1'}])
    import audioknigi.services.book_analysis_service as module
    old_meta = module.extract_metadata_from_html
    old_ext = module.extract_extended_metadata_from_html
    try:
        module.extract_metadata_from_html = lambda _html, _title: ('Андрей Уланов, Владимир Серебряков - Название', 'Андрей Уланов, Владимир Серебряков', '')
        module.extract_extended_metadata_from_html = lambda _html: ('', '', '', '')
        book = service._parse_playlist_data(url='https://audioknigi.com.ua/audio-1', html_text=html, page_title='Название', playlist_url='https://example.test/list.json', playlist_text=playlist)
    finally:
        module.extract_metadata_from_html = old_meta
        module.extract_extended_metadata_from_html = old_ext
    assert book.title == 'Название'
    assert book.narrator == 'Иван Иванов'


# Origin: test_report_followup_round48_20260923.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round48_20260923(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_advanced_narration_combo_does_not_grow_window_from_long_reader_names() -> None:
    pages = src__report_followup_round48_20260923('audioknigi/qt/main_window_pages.py')
    analysis = src__report_followup_round48_20260923('audioknigi/qt/mixins/analysis_download.py')
    assert 'QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon' in pages
    assert 'self.narration_combo.setMinimumContentsLength(22)' in pages
    assert 'self.narration_row_widget.setVisible(False)' in pages
    assert 'self.narration_row_widget.setVisible(visible)' in analysis


# Origin: test_report_followup_round49_20260924.py
class _FallbackHost(SourceAnalysisMixin):
    cancel_event = None
    _book_identity_hints = staticmethod(BookAnalysisService._book_identity_hints)
    _identity_tokens = staticmethod(BookAnalysisService._identity_tokens)

    def _check_cancel(self) -> None:
        return None

def test_download_fallback_continues_past_unknown_narrator_to_exact_match(monkeypatch) -> None:
    original = Book(title='Book', author='Author', narrator='Exact Narrator', url='https://audioknigi.com.ua/audio-1')
    results = [SearchResult(title='Book', author='Author', narrator='', url='https://knigavuhe.org/book/z-unknown/', source='knigavuhe'), SearchResult(title='Book', author='Author', narrator='', url='https://knigavuhe.org/book/a-exact/', source='knigavuhe')]
    monkeypatch.setattr(source_analysis_module, 'search_knigavuhe_books', lambda *_a, **_k: results)

    class Provider:

        def fetch_book(self, url, *, cancel_event=None):
            narrator = '' if 'z-unknown' in url else 'Exact Narrator'
            return Book(title='Book', author='Author', narrator=narrator, url=url)
    monkeypatch.setattr(source_analysis_module, 'provider_for_key', lambda _key: Provider())
    selected = _FallbackHost()._knigavuhe_fallback_candidate(original)
    assert selected is not None
    assert selected.url.endswith('/a-exact/')


# Origin: test_report_followup_round50_20260924.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round50_20260924(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_audioknigi_annotation_uses_real_synopsis_not_page_chrome() -> None:
    html = '\n    <html><body>\n      <div class="shortstory">\n        <p>Тут можно слушать бесплатно Демченко Антон - Боярич. Исполнитель: Карпов Дмитрий,\n        Жанр: Фантастика. Так же Вы можете слушать полную версию онлайн или прочесть\n        краткое содержание, предисловие (аннотацию), описание и ознакомиться с отзывами.</p>\n        <p>14 часов 32 минуты 26052</p>\n        <p>Слушать эту аудиокнигу в приложении</p>\n        <p>Добавляйте книги в android приложение Audiotales прямо с сайта.</p>\n        <p>Автор:</p><p>Демченко Антон</p>\n        <p>Исполнитель:</p><p>Карпов Дмитрий</p>\n        <p>Серия:</p><p>Воздушный стрелок (1)</p>\n        <p>Добавлено:</p><p>18.09.2019</p>\n        <p>Жанры</p><p>Фэнтези Технофэнтези</p>\n        <p>Характеристики</p><p>Приключенческое Психологическое</p>\n        <h2>Демченко Антон - Боярич краткое содержание</h2>\n        <p>Демченко Антон - Боярич - описание и краткое содержание,\n        исполнитель: Карпов Дмитрий, слушайте бесплатно онлайн на сайте электронной\n        библиотеки AudioKnigi.com.ua</p>\n        <p>Говорят, жить надо так, чтобы после смерти боги предложили тебе повторить.\n        Случай и воля древнего божества занесли героя в тело подростка.</p>\n        <h2>Демченко Антон - Боярич слушать онлайн бесплатно</h2>\n        <p>Плеер, скачать, отзывы и другая техническая информация.</p>\n      </div>\n    </body></html>\n    '
    value = audioknigi_search._audioknigi_description_from_html(html, title='Боярич', author='Демченко Антон')
    assert value.startswith('Говорят, жить надо так')
    assert 'Случай и воля' in value
    folded = value.casefold()
    assert 'audioknigi.com.ua' not in folded
    assert 'исполнитель:' not in folded
    assert 'добавлено:' not in folded
    assert 'audiotales' not in folded
    assert 'плеер' not in folded

def test_audioknigi_intro_phrase_does_not_start_annotation_capture() -> None:
    html = '\n    <article class="shortstory">\n      <p>Тут можно слушать бесплатно Книга. Также можно прочесть краткое содержание,\n      предисловие, описание и отзывы.</p>\n      <p>Автор: Автор Тестовый</p>\n      <p>Исполнитель: Чтец Тестовый</p>\n      <p>Добавлено: 24.09.2026</p>\n      <h2>Автор Тестовый - Книга краткое содержание</h2>\n      <p>Автор Тестовый - Книга - описание и краткое содержание, исполнитель:\n      Чтец Тестовый, слушайте бесплатно онлайн на сайте электронной библиотеки\n      AudioKnigi.com.ua</p>\n      <p>Это настоящая аннотация книги без сведений о плеере и каталоге.</p>\n      <h2>Автор Тестовый - Книга отзывы</h2>\n      <p>Комментарий пользователя.</p>\n    </article>\n    '
    value = audioknigi_search._audioknigi_description_from_html(html, title='Книга', author='Автор Тестовый')
    assert value == 'Это настоящая аннотация книги без сведений о плеере и каталоге.'

def test_audioknigi_semantic_fallback_still_accepts_clean_description() -> None:
    html = '\n    <div class="book-description">\n      Чистая аннотация о героях, конфликте и событиях произведения.\n    </div>\n    '
    value = audioknigi_search._audioknigi_description_from_html(html, title='Книга', author='Автор')
    assert value == 'Чистая аннотация о героях, конфликте и событиях произведения.'


# Origin: test_report_followup_round5_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_knigavuhe_variant_enrichment_propagates_cancelled(monkeypatch):
    import audioknigi.knigavuhe as module
    result = SearchResult(title='Demo', url='https://knigavuhe.org/book/demo/', source='knigavuhe.org')

    def cancelled(_item):
        raise Cancelled('cancel')
    monkeypatch.setattr(module, '_enrich_search_result_variants', cancelled)
    with pytest.raises(Cancelled):
        module.enrich_search_variants([result])

def test_knigavuhe_search_hydration_marks_restricted_book(monkeypatch):
    import audioknigi.knigavuhe as module
    result = SearchResult(title='Fallback', url='https://knigavuhe.org/book/demo/', source='knigavuhe.org')

    class Response:
        text = '<title>Demo — автор Author, читает Reader</title><p>Доступ к аудиокниге ограничен по просьбе правообладателя</p>'

        def raise_for_status(self):
            pass

    class Session:

        def get(self, *args, **kwargs):
            return Response()
    monkeypatch.setattr(module, 'get_http_session', Session)
    hydrated = module._resolve_search_result_title(result)
    assert hydrated.title == 'Demo'
    assert hydrated.availability == 'restricted'

def test_book_analysis_accepts_utf8_bom_playlist():
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    playlist = '\ufeff' + json.dumps([{'file': '1.mp3', 'title': 'One'}])
    book = service._parse_playlist_data(url='https://audioknigi.com.ua/book/1', html_text='<title>Demo</title>', page_title='Demo', playlist_url='https://cdn.example/demo.pl.txt', playlist_text=playlist)
    assert [track.index for track in book.tracks] == [1]


# Origin: test_report_followup_round9_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_proxy_authority_preserves_unbracketed_numeric_ipv6():
    assert _parse_proxy_authority('::1', 443) == ('::1', 443)
    assert _parse_proxy_authority('[2001:db8::1]:8443', 443) == ('2001:db8::1', 8443)
    assert _parse_proxy_authority('example.org:8080', 80) == ('example.org', 8080)
    with pytest.raises(ValueError):
        _parse_proxy_authority('[2001:db8::1', 443)

def test_full_mp3_default_template_without_literal_extension_uses_book_title(tmp_path):
    engine = _DownloadEngine.__new__(_DownloadEngine)
    engine.runtime_use_templates = True
    engine.runtime_track_template = '{Track_Number}'
    book = Book(url='https://example.test/book', title='My Book', tracks=[Track(index=1, title='One', file='x')])
    assert engine._full_mp3_target(book, tmp_path).name == 'My Book.mp3'

def test_audioknigi_dash_parser_rejects_series_and_numeric_prefixes():
    assert _split_audioknigi_title('Иван Автор — Тестовая книга') == ('Тестовая книга', 'Иван Автор')
    assert _split_audioknigi_title('S.T.A.L.K.E.R. — Тени Чернобыля') == ('S.T.A.L.K.E.R. — Тени Чернобыля', '')
    assert _split_audioknigi_title('1984 — Часть 1') == ('1984 — Часть 1', '')
    assert _split_audioknigi_title('Александр I — эпоха') == ('Александр I — эпоха', '')

def test_playlist_parser_accepts_whitespace_before_bom_and_prefers_precise_boundaries():
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    playlist = '  \n\ufeff' + json.dumps([{'file': 'one.mp3', 'title': 'One', 'start': 0, 'end': 60.45, 'duration': 60}, {'file': 'two.mp3', 'title': 'Two', 'start': 60.45, 'end': 120.9, 'duration': 60}])
    book = service._parse_playlist_data(url='https://audioknigi.com.ua/audio-1', html_text='<title>Demo</title>', page_title='Demo', playlist_url='https://audioknigi.com.ua/list.pl.txt', playlist_text=playlist)
    assert len(book.tracks) == 2
    assert book.tracks[0].duration == pytest.approx(60.45)
    assert book.tracks[1].duration == pytest.approx(60.45)


# Origin: test_round61_external_review_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_one_letter_book_title_queries_are_retained_and_author_detail_prefers_more_initials():
    assert _matches_query('Я, робот', 'я робот', author='Айзек Азимов') is True
    assert _author_detail_score('А. С. Пушкин') > _author_detail_score('А. Пушкин')

def test_core_narrator_parser_stops_before_duration_and_quality_metadata():
    _description, narrator, _genre, _year = extract_extended_metadata_from_html('Исполнитель: Илья Кривошеев, Время звучания: 12:45:00, Качество: 128 kbps')
    assert narrator == 'Илья Кривошеев'


# Origin: test_round63_followup_20260929.py
def test_audioknigi_detail_hydration_is_bounded(monkeypatch):
    items = [SearchResult(title=f'Book {index}', url=f'https://audioknigi.com.ua/audio-{index}', source='audioknigi.com.ua') for index in range(50)]
    seen = []
    lock = threading.Lock()

    def fake_metadata(item, cancel_event=None):
        with lock:
            seen.append(item.url)
        return item
    monkeypatch.setattr(audioknigi_search, '_audioknigi_page_metadata', fake_metadata)
    result = audioknigi_search._group_audioknigi_recordings(items)
    assert len(result) == 50
    assert len(seen) == audioknigi_search._MAX_HYDRATED_SEARCH_RESULTS == 30
    assert set(seen) == {item.url for item in items[:30]}


# Origin: test_round65_poleknig_search_relevance_20260929.py
def _run_search(monkeypatch, query: str, rows: list[SearchResult], *, author_expanded=None):
    response = SimpleNamespace(text='', url='https://poleknig.com/search/')
    monkeypatch.setattr(poleknig__round65_poleknig_search_relevance_20260929, '_fetch_search_page', lambda *_a, **_k: response)
    monkeypatch.setattr(poleknig__round65_poleknig_search_relevance_20260929, '_search_last_page', lambda *_a, **_k: 1)
    monkeypatch.setattr(poleknig__round65_poleknig_search_relevance_20260929, 'parse_search_results', lambda *_a, **_k: list(rows))
    monkeypatch.setattr(poleknig__round65_poleknig_search_relevance_20260929, '_hydrate_search_result_info', lambda item: (item, []))
    monkeypatch.setattr(poleknig__round65_poleknig_search_relevance_20260929, '_book_page_author_links', lambda *_a, **_k: [])
    monkeypatch.setattr(poleknig__round65_poleknig_search_relevance_20260929, '_expand_matching_author_catalogs', lambda *_a, **_k: list(author_expanded or []))
    return poleknig__round65_poleknig_search_relevance_20260929.search(query)

def test_multiword_title_search_filters_broad_poleknig_hits(monkeypatch):
    rows = [SearchResult(title='Аль Капоне. Порядок вне закона', author='Екатерина Глаголева', narrator='Reader', url='https://poleknig.com/books/1', source='poleknig.com'), SearchResult(title='Наемник Айвэн 3: Закон и порядок', author='Юрий Уленгов', narrator='Reader', url='https://poleknig.com/books/2', source='poleknig.com'), SearchResult(title='Кошачий закон и порядок. Как найти общий язык с кошкой', author='София Царегородцева', narrator='Reader', url='https://poleknig.com/books/3', source='poleknig.com'), SearchResult(title='Экономика без догм. Как США создают новый экономический порядок', author='Автор', narrator='Reader', url='https://poleknig.com/books/4', source='poleknig.com'), SearchResult(title='Закон насилия и закон любви', author='Лев Толстой', narrator='Reader', url='https://poleknig.com/books/5', source='poleknig.com')]
    results = _run_search(monkeypatch, 'Закон и порядок', rows)
    assert [item.title for item in results] == ['Наемник Айвэн 3: Закон и порядок', 'Кошачий закон и порядок. Как найти общий язык с кошкой']

def test_title_hit_suppresses_unrelated_author_name_hit(monkeypatch):
    rows = [SearchResult(title='Бесплатный тест-драйв материалов', author='Алекс Айвенго', url='https://poleknig.com/books/1', source='poleknig.com'), SearchResult(title='Айвенго', author='Вальтер Скотт', url='https://poleknig.com/books/2', source='poleknig.com')]
    results = _run_search(monkeypatch, 'Айвенго', rows)
    assert [item.url for item in results] == ['https://poleknig.com/books/2']

def test_author_search_keeps_author_catalog_when_no_title_hit(monkeypatch):
    rows = [SearchResult(title='Айвенго', author='Вальтер Скотт', url='https://poleknig.com/books/1', source='poleknig.com'), SearchResult(title='Квентин Дорвард', author='Вальтер Скотт', url='https://poleknig.com/books/2', source='poleknig.com'), SearchResult(title='Вальтер', author='Другой Автор', url='https://poleknig.com/books/3', source='poleknig.com')]
    expanded = [SearchResult(title='Роб Рой', author='Вальтер Скотт', url='https://poleknig.com/books/4', source='poleknig.com')]
    results = _run_search(monkeypatch, 'Вальтер Скотт', rows, author_expanded=expanded)
    assert [item.url for item in results] == ['https://poleknig.com/books/4', 'https://poleknig.com/books/1', 'https://poleknig.com/books/2']

def test_repeated_author_matches_beat_nonexact_one_word_title_hit(monkeypatch):
    rows = [SearchResult(title='Толстой о жизни', author='Другой Автор', url='https://poleknig.com/books/1', source='poleknig.com'), SearchResult(title='Война и мир', author='Лев Толстой', url='https://poleknig.com/books/2', source='poleknig.com'), SearchResult(title='Анна Каренина', author='Лев Толстой', url='https://poleknig.com/books/3', source='poleknig.com')]
    expanded = [SearchResult(title='Воскресение', author='Лев Толстой', url='https://poleknig.com/books/4', source='poleknig.com')]
    results = _run_search(monkeypatch, 'Толстой', rows, author_expanded=expanded)
    assert [item.url for item in results] == ['https://poleknig.com/books/4', 'https://poleknig.com/books/2', 'https://poleknig.com/books/3']


# Origin: test_round66_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_playwright_prefers_browser_playlist_body_before_http_fallback():
    source = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    start = source.index('def _analyze_audioknigi_playwright')
    block = source[start:source.index('def _remote_size', start)]
    assert 'captured_responses' in block
    assert 'browser_response.body()' in block
    assert 'if not playlist_text:' in block
    assert block.index('browser_response.body()') < block.index('browser.close()')
    assert block.index('browser.close()') < block.index('session.get(playlist_url')


# Origin: test_round69_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_audioknigi_hydration_propagates_cancelled(monkeypatch):
    source = SearchResult(title='Demo Book', author='Demo Author', narrator='', url='https://audioknigi.com.ua/demo', source='audioknigi.com.ua')

    def cancelled(*_args, **_kwargs):
        raise Cancelled('cancelled')
    monkeypatch.setattr(audioknigi_search, '_audioknigi_page_metadata', cancelled)
    with pytest.raises(Cancelled):
        audioknigi_search._group_audioknigi_recordings([source])

def test_poleknig_meta_parser_handles_multiline_attributes_without_dotall():
    html = '<html><head><meta property="og:description"\n content="Line one\nLine two"></head></html>'
    assert poleknig__round69_runtime_followup_20260930._extract_meta_content(html, 'og:description') == 'Line one Line two'


# Origin: test_round70_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_playwright_uses_only_successful_playlist_response_body_and_shorter_navigation_timeout():
    analysis = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    start = analysis.index('for browser_response in reversed(captured_responses):')
    block = analysis[start:analysis.index('try:\n                    browser_cookies', start)]
    assert 'status = int(getattr(browser_response, "status", 0) or 0)' in block
    assert 'if not 200 <= status < 300:' in block
    assert block.index('if not 200 <= status < 300:') < block.index('browser_response.body()')
    assert 'page.goto(url, wait_until="domcontentloaded", timeout=30000)' in analysis
    poleknig = (ROOT / 'audioknigi/poleknig.py').read_text(encoding='utf-8')
    assert 'page.goto(url, wait_until="domcontentloaded", timeout=30000)' in poleknig

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

def test_playlist_duration_zero_falls_through_to_positive_length():
    service = BookAnalysisService(cancel_event=threading.Event())
    playlist = json.dumps([{'file': 'https://cdn.invalid/a.mp3', 'title': 'Part 1', 'duration': '0', 'length': '12.5'}])
    book = service._parse_playlist_data(url='https://audioknigi.com.ua/audio-1-demo', html_text='<html><title>Demo</title></html>', page_title='Demo', playlist_url='https://cdn.invalid/book.pl.txt', playlist_text=playlist)
    assert len(book.tracks) == 1
    assert book.tracks[0].duration == pytest.approx(12.5)


# Origin: test_round72_search_sorting_availability_layout_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def _result(title: str, *, author: str='', narrator: str='', availability: str='') -> SearchResult:
    return SearchResult(title=title, author=author, narrator=narrator, availability=availability, url=f'https://example.invalid/{title}', source='demo')

def test_author_and_narrator_sort_alphabetically_with_missing_values_last():
    rows = [_result('C', author='', narrator=''), _result('B', author='Толстой', narrator='Петров'), _result('A', author='Булгаков', narrator='Алексеев')]
    by_author = sorted(rows, key=lambda item: search_result_sort_key(item, 'author'))
    by_narrator = sorted(rows, key=lambda item: search_result_sort_key(item, 'narrator'))
    assert [item.author for item in by_author] == ['Булгаков', 'Толстой', '']
    assert [item.narrator for item in by_narrator] == ['Алексеев', 'Петров', '']


# Origin: test_round73_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_short_shared_audioknigi_source_uses_start_markers_when_end_is_missing():
    fallback = Book(url='https://knigavuhe.org/book/demo/', title='Fallback', tracks=[Track(index=1, title='One', file='https://cdn.invalid/fallback.mp3')])

    class Service(BookAnalysisService):

        def _probe_remote_duration(self, _source, _referer):
            return 10.0

        def _knigavuhe_fallback_candidate(self, _book):
            return fallback

        def _populate_missing_track_durations(self, _book):
            return 0
    shared = 'https://cdn.invalid/shared.mp3'
    book = Book(url='https://audioknigi.com.ua/audio-1-demo', title='Demo', tracks=[Track(index=1, title='One', file=shared, start=0.0), Track(index=2, title='Two', file=shared, start=60.0)])
    assert Service(cancel_event=threading.Event())._recover_short_audioknigi_source(book) is fallback

def test_playlist_generated_title_width_tracks_total_chapter_count():
    title = _playlist_track_title('', 'https://cdn.invalid/track_001.mp3', 1, 'Book', 140)
    assert title == 'Book — 001'

def test_knigavuhe_title_validation_accepts_unicode_letters_beyond_handwritten_alphabet():
    assert _usable_search_title('Ґ') is True
    assert _usable_search_title('Ў') is True
    assert _usable_search_title('123 -_ …') is False


# Origin: test_round74_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_refresh_playlist_ignores_invalid_track_indices_instead_of_crashing(tmp_path):
    original = Book(url='https://example.invalid/book', title='Demo', tracks=[Track(index=1, title='One', file='old.mp3')])
    fresh = Book(url=original.url, title='Demo', tracks=[Track(index=None, title='Broken', file='broken.mp3'), Track(index=1, title='One', file='new.mp3')])

    class Harness(BookFlowMixin):
        runtime_language = 'ru'

        def _check_cancel(self):
            pass

        def set_status(self, _text):
            pass

        def set_stage(self, *_args):
            pass

        def log(self, _text):
            pass

        def _analyze_book(self, _url):
            return fresh

        def _clear_stale_source_downloads(self, _book):
            return 0
    changed = Harness()._refresh_book_media_playlist(original, [1, 'bad', None])
    assert changed == 1
    assert len(original.tracks) == 2
    assert original.tracks[1].file == 'new.mp3'

def test_provider_variant_availability_is_case_insensitive_and_current_is_explicit():
    poleknig = (ROOT / 'audioknigi/poleknig.py').read_text(encoding='utf-8')
    assert 'str(getattr(item, "availability", "") or "").casefold() == "restricted"' in poleknig
    assert 'str(getattr(item, "availability", "") or "").casefold() == "available"' in poleknig
    from audioknigi.knigavuhe import _extract_narration_variants
    available = _extract_narration_variants('', 'https://knigavuhe.org/book/demo', current_available=True)
    restricted = _extract_narration_variants('', 'https://knigavuhe.org/book/demo', current_available=False)
    assert available and available[0].available is True
    assert restricted and restricted[0].available is False


# Origin: test_round78_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_playlist_refresh_preserves_zero_index_and_local_state():
    original_track = Track(index=0, title='Prologue', file='old.mp3', selected=True, local_status='ready')
    original_track.actual_duration = 12.0
    original_track.local_path = 'saved.mp3'
    original = Book(url='https://example.invalid/book', title='Demo', tracks=[original_track])
    fresh = Book(url=original.url, title='Demo', tracks=[Track(index=0, title='Prologue', file='new.mp3')])

    class Harness(BookFlowMixin):
        runtime_language = 'ru'

        def _check_cancel(self):
            pass

        def set_status(self, _text):
            pass

        def set_stage(self, *_args):
            pass

        def log(self, _text):
            pass

        def _analyze_book(self, _url):
            return fresh

        def _clear_stale_source_downloads(self, _book):
            return 0
    assert Harness()._refresh_book_media_playlist(original, [0]) == 1
    assert original.tracks[0].index == 0
    assert original.tracks[0].selected is True
    assert original.tracks[0].actual_duration == pytest.approx(12.0)
    assert original.tracks[0].local_path == 'saved.mp3'

def test_safe_name_already_guards_invalid_book_titles():
    assert safe_name('???') == '___'
    assert safe_name('***') == '___'
    assert safe_name('   ') == 'audiobook'

def test_known_narrator_does_not_fall_back_to_unknown_after_explicit_conflict(monkeypatch):
    original = Book(title='Book', author='Author', narrator='Wanted Reader', url='https://audioknigi.com.ua/audio-1')
    results = [SearchResult(title='Book', author='Author', narrator='', url='https://knigavuhe.org/book/unknown/', source='knigavuhe'), SearchResult(title='Book', author='Author', narrator='Other Reader', url='https://knigavuhe.org/book/other/', source='knigavuhe')]
    monkeypatch.setattr(analysis_module, 'search_knigavuhe_books', lambda *_a, **_k: results)

    def fake_fetch(url, **_kwargs):
        narrator = '' if 'unknown' in url else 'Other Reader'
        return Book(title='Book', author='Author', narrator=narrator, url=url)
    monkeypatch.setattr(analysis_module, 'fetch_knigavuhe_book', fake_fetch)
    assert BookAnalysisService()._knigavuhe_fallback_candidate(original) is None
    source = (ROOT / 'audioknigi/download/source_analysis.py').read_text(encoding='utf-8')
    assert 'saw_conflicting_narrator = True' in source
    assert 'if narrator_tokens and saw_conflicting_narrator:' in source

def test_knigavuhe_generic_div_exact_other_narrations_heading_is_recognized():
    html = '<div class="title">Другие озвучки</div><a href="/book/alt/">Reader Name</a>'
    variants = _extract_narration_variants(html, 'https://knigavuhe.org/book/current/')
    assert any((item.url == 'https://knigavuhe.org/book/alt/' for item in variants))

def test_reported_knigavuhe_groups_nameerror_is_not_present():
    source = (ROOT / 'audioknigi/knigavuhe.py').read_text(encoding='utf-8')
    grouping = source[source.index('grouped: dict'):source.index('unique: list', source.index('grouped: dict'))]
    assert 'groups[key]' not in grouping
    assert 'grouped[key]' in grouping


# Origin: test_round79_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_optional_metadata_does_not_erase_existing_title(monkeypatch):
    service = BookAnalysisService()
    monkeypatch.setattr(analysis_module, 'extract_metadata_from_html', lambda _html, _title: ('', '', ''))
    book = service._parse_playlist_data(url='https://audioknigi.com.ua/demo', html_text='<script>new Playerjs({title:"Recovered Title"})</script>', page_title='Fallback Title', playlist_url='https://audioknigi.com.ua/list.pl.txt', playlist_text='[{"file":"track.mp3","title":"One"}]')
    assert book.title == 'Recovered Title'

def test_playlist_object_wrapper_is_supported_and_wrong_object_shape_is_explicit(monkeypatch):
    service = BookAnalysisService()
    monkeypatch.setattr(analysis_module, 'extract_metadata_from_html', lambda _html, title: (title, '', ''))
    kwargs = dict(url='https://audioknigi.com.ua/demo', html_text='<script>new Playerjs({title:"Demo"})</script>', page_title='Demo', playlist_url='https://audioknigi.com.ua/list.pl.txt')
    book = service._parse_playlist_data(**kwargs, playlist_text='{"playlist":[{"file":"track.mp3","title":"One"}]}')
    assert len(book.tracks) == 1
    with pytest.raises(SiteStructureChanged, match='ожидался список треков'):
        service._parse_playlist_data(**kwargs, playlist_text='{"error":"forbidden"}')

def test_knigavuhe_controller_uses_page_author_fallback():
    payload = {'book': {'name': 'Demo', 'authors': [], 'readers': []}, 'playlist': [{'url': 'https://cdn.invalid/1.mp3', 'title': 'One'}]}
    html = '<html><head><title>Demo — автор Иван Автор</title></head><body><script>BookController.enter(' + json.dumps(payload, ensure_ascii=False) + ');</script></body></html>'
    book = parse_book_html(html, 'https://knigavuhe.org/book/demo/')
    assert book.author == 'Иван Автор'


# Origin: test_runtime_contract_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def _book__runtime_contract_hardening_20260912() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3'), Track(index=2, title='Two', file='https://cdn.invalid/2.mp3')])

def test_audioknigi_search_cancellation_propagates():
    event = Event()
    event.set()
    with pytest.raises(Cancelled):
        search_audioknigi('demo', cancel_event=event)


# Origin: test_runtime_followup_round7_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_audioknigi_author_prefix_requires_explicit_separator():

    class Response:
        text = '<title>Fallback</title>'

        def raise_for_status(self):
            return None

    class Session:

        def get(self, *args, **kwargs):
            return Response()
    result = SearchResult(title='Fallback', url='https://audioknigi.com.ua/demo', source='audioknigi')
    ambiguous = _audioknigi_page_metadata(result, session_factory=Session, metadata_extractor=lambda _html, _fallback: ('Александр I', 'Александр', ''), extended_metadata_extractor=lambda _html: ('', '', '', ''))
    separated = _audioknigi_page_metadata(result, session_factory=Session, metadata_extractor=lambda _html, _fallback: ('Александр — Книга', 'Александр', ''), extended_metadata_extractor=lambda _html: ('', '', '', ''))
    assert ambiguous.title == 'Александр I'
    assert separated.title == 'Книга'


# Origin: test_stability_localization_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_provider_fetch_contract_delegates_to_analysis_service(monkeypatch):
    from audioknigi.services.book_analysis_service import BookAnalysisService
    seen = []
    expected = Book(url='https://knigavuhe.org/book/1', title='Book')

    def fake_analyze(self, url):
        seen.append(url)
        return expected
    monkeypatch.setattr(BookAnalysisService, 'analyze', fake_analyze)
    assert KnigavuheProvider().fetch_book('https://knigavuhe.org/book/1') is expected
    assert PoleKnigProvider().fetch_book('https://poleknig.com/book/1') is expected
    assert len(seen) == 2


# Origin: test_structured_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_knigavuhe_variant_merge_clones_inputs_before_enrichment():
    first = NarrationVariant(url='https://knigavuhe.org/book/demo/', narrator='', title='', current=False)
    second = NarrationVariant(url='https://knigavuhe.org/book/demo/', narrator='Reader', title='Book', current=True)
    merged = _merge_narration_variants([first], [second])
    assert len(merged) == 1
    assert merged[0] is not first
    assert merged[0].narrator == 'Reader'
    assert merged[0].title == 'Book'
    assert merged[0].current is True
    assert first.narrator == ''
    assert first.title == ''
    assert first.current is False

def test_search_source_filter_accepts_internal_provider_keys(monkeypatch):
    knigavuhe = provider_for_key('knigavuhe')
    poleknig = provider_for_key('poleknig')
    audioknigi = provider_for_key('audioknigi')
    monkeypatch.setattr(knigavuhe, 'search', lambda q, cancel_event=None: [SearchResult('K', 'https://knigavuhe.org/book/k/', source='knigavuhe.org')])
    monkeypatch.setattr(knigavuhe, 'enrich_search_results', lambda items, cancel_event=None: items)
    monkeypatch.setattr(poleknig, 'search', lambda q, cancel_event=None: [SearchResult('P', 'https://poleknig.com/books/1', source='poleknig.com')])
    monkeypatch.setattr(audioknigi, 'search', lambda q, cancel_event=None: pytest.fail('audioknigi provider must be filtered out'))
    outcome = search_service.search_all_sources('demo', sources=['knigavuhe', 'poleknig'])
    assert not outcome.errors
    assert {item.source for item in outcome.results} == {'knigavuhe.org', 'poleknig.com'}

def test_search_service_uses_registry_without_provider_search_cycle():
    service_source = (ROOT / 'audioknigi' / 'services' / 'search_service.py').read_text(encoding='utf-8')
    adapters_source = (ROOT / 'audioknigi' / 'providers' / 'adapters.py').read_text(encoding='utf-8')
    assert 'registered_providers' in service_source
    assert 'provider.search(' in service_source
    assert 'services.search_service' not in adapters_source

def test_book_analysis_service_has_real_knigavuhe_fetch_binding():
    source = (ROOT / 'audioknigi' / 'services' / 'book_analysis_service.py').read_text(encoding='utf-8')
    assert 'from ..knigavuhe import fetch_book as fetch_knigavuhe_book' in source
    assert 'fallback = fetch_knigavuhe_book(' in source
