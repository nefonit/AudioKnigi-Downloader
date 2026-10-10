"""Consolidated integration tests for the network domain.

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
import requests
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.models import Book, Track
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.queue_service import _parse_selected_indices_payload
from tools.exception_audit import scan as exception_scan
from tools.qt_localization_audit import _ui_text_literals
from tools.unused_import_audit import unused_imports
from audioknigi.core import _first_json_ld
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.library_service import scan_unfinished
from collections import UserDict
from audioknigi.core import Cancelled, _structured_book_nodes
from audioknigi.diagnostics import support_bundle as support_bundle__report_followup_round12_20260916
from audioknigi.download_engine import _DownloadEngine
from audioknigi.services.download_request import build_download_request
import csv
import zipfile
from audioknigi.config.settings import migrate_settings
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.network import _segment_files
from audioknigi.models import SearchResult
import audioknigi.poleknig as poleknig__report_followup_round14_20260916
from audioknigi.core import _walk_json
from audioknigi.download.common import replace_with_retry
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services import library_service
import inspect
from audioknigi import core as core__report_followup_round22_20260917, poleknig as poleknig__report_followup_round22_20260917
from audioknigi.network_dns import _relay_bidirectional
from audioknigi.providers.audioknigi_search import _canonical_title
from audioknigi import core as core__report_followup_round2_20260915
from audioknigi.config.settings import save_app_settings
from audioknigi.core import load_json
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.models import Book, SearchResult, Track
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.core import Cancelled, load_json
from audioknigi.templates import template_values
from audioknigi import core as core__report_followup_round33_20260918
from audioknigi.core import fmt_size
from audioknigi.templates import render_text_template
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi import core as core__report_followup_round3_20260915
from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.download.probe import ProbeMixin
from audioknigi.download_engine import DownloadService, _DownloadEngine
from audioknigi.i18n import localize_runtime_text
from audioknigi.services.search_service import search_all_sources
import audioknigi.config.settings as settings_module
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round43_20260920
import audioknigi.download.network as network_module__report_followup_round43_20260920
import audioknigi.knigavuhe as knigavuhe
import audioknigi.poleknig as poleknig__report_followup_round43_20260920
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata, _merge_author_names
import base64
import time
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
import sys
from types import ModuleType, SimpleNamespace
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round52_20260924
from audioknigi.services.download_request import DownloadRequest, build_download_request
import ast
from audioknigi.services import search_service
from audioknigi.services.source_health_service import SourceHealthItem, SourceHealthOutcome
from audioknigi import network_dns
from audioknigi.config.settings import normalize_settings
import os
from audioknigi.models import Book, Track, TRACK_STATUS_READY
from audioknigi.providers.audioknigi_search import _response_html_text
from audioknigi.services import library_service, source_health_service
from audioknigi.services.queue_service import _parse_created_at
from audioknigi import poleknig as poleknig__round69_runtime_followup_20260930
from audioknigi.download.errors import MissingMediaSourceError
from audioknigi.providers import audioknigi_search
from audioknigi.config.settings import AppSettings
from audioknigi.download.common import source_target_assignments
from audioknigi.services import source_health_service
from audioknigi.download import network as network_module__round81_external_review_followup_20261006
from audioknigi.download import source_analysis as source_analysis_module
from audioknigi.download.source_analysis import SourceAnalysisMixin
import types
from audioknigi.diagnostics import support_bundle as support_bundle__runtime_integrity_followup_20260912
from audioknigi.download_engine import DownloadService
from audioknigi.downloader import DownloaderMixin
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.sources import normalize_supported_url
from audioknigi.diagnostics.support_bundle import _is_secret_key
from audioknigi.i18n import localize_runtime_text, tr, ui_text
from audioknigi.providers.adapters import KnigavuheProvider, PoleKnigProvider


# Origin: test_cancellation_cover_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_connect_proxy_preserves_full_duplex_after_upstream_half_close():
    source = (ROOT / 'audioknigi/network_dns.py').read_text(encoding='utf-8')
    connect_block = source[source.index('if method.upper() == "CONNECT"'):source.index('parsed = urlsplit(target)')]
    assert '_relay_bidirectional(client, upstream)' in connect_block
    assert 'return_when_right_closes=True' not in connect_block


# Origin: test_external_review_hardening_20260928.py
ROOT = Path(__file__).resolve().parents[2]

def test_proxy_header_reader_accepts_lf_only_headers():
    left, right = socket.socketpair()
    try:
        right.sendall(b'CONNECT example.com:443 HTTP/1.1\nHost: example.com\n\nTAIL')
        head, remainder = _read_http_head(left, deadline_seconds=1.0)
    finally:
        left.close()
        right.close()
    assert b'CONNECT example.com:443' in head
    assert remainder == b'TAIL'


# Origin: test_network_parser_retention_round6_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_connect_relay_forwards_payload_before_returning_on_upstream_eof():
    from audioknigi.network_dns import _relay_bidirectional
    client_side, relay_left = socket.socketpair()
    relay_right, upstream_side = socket.socketpair()
    thread = threading.Thread(target=_relay_bidirectional, args=(relay_left, relay_right), kwargs={'return_when_right_closes': True}, daemon=True)
    thread.start()
    try:
        payload = b'payload-before-fin'
        upstream_side.sendall(payload)
        upstream_side.shutdown(socket.SHUT_WR)
        assert client_side.recv(len(payload)) == payload
        thread.join(timeout=2.0)
        assert not thread.is_alive()
    finally:
        for sock in (client_side, relay_left, relay_right, upstream_side):
            try:
                sock.close()
            except OSError:
                pass

def test_connect_handler_keeps_full_duplex_half_close_contract():
    source = (ROOT / 'audioknigi' / 'network_dns.py').read_text(encoding='utf-8')
    connect_start = source.index('if method.upper() == "CONNECT":')
    plain_start = source.index('parsed = urlsplit(target)', connect_start)
    connect_block = source[connect_start:plain_start]
    assert '_relay_bidirectional(client, upstream)' in connect_block
    assert 'return_when_right_closes=True' not in connect_block

def test_remote_ffprobe_paths_use_cloudflare_proxy_args():
    probe = (ROOT / 'audioknigi' / 'download' / 'probe.py').read_text(encoding='utf-8')
    analysis = (ROOT / 'audioknigi' / 'services' / 'book_analysis_service.py').read_text(encoding='utf-8')
    assert '*cloudflare_ffmpeg_input_args()' in probe[probe.index('def _probe_remote_duration'):]
    assert '*cloudflare_ffmpeg_input_args()' in analysis[analysis.index('def _probe_remote_duration'):]


# Origin: test_quality_runtime_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_expired_media_indices_can_be_inferred_from_http_response_url():
    book = Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/one.mp3'), Track(index=2, title='Two', file='https://cdn.invalid/two.mp3')])
    response = requests.Response()
    response.status_code = 404
    response.url = 'https://cdn.invalid/two.mp3'
    error = requests.HTTPError('404', response=response)
    assert BookFlowMixin._expired_media_track_indices(error, book, {1, 2}) == [2]


# Origin: test_report_followup_round11_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_round11_network_peer_abort_contract_present():
    source = (ROOT / 'audioknigi/download/network.py').read_text(encoding='utf-8')
    assert 'peer_abort_event=None' in source
    assert 'peer_abort_event = threading.Event()' in source
    assert 'peer_abort_event=peer_abort_event' in source
    assert 'peer_abort_event.set()' in source
    assert 'if peer_aborted():' in source


# Origin: test_report_followup_round12_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_remote_size_requests_identity_encoding(monkeypatch):
    import audioknigi.services.book_analysis_service as module
    captured = {}

    class Response:
        status_code = 206
        headers = {'content-range': 'bytes 0-0/12345'}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @staticmethod
        def raise_for_status():
            return None

    class Session:

        def get(self, url, **kwargs):
            captured.update(kwargs)
            return Response()
    monkeypatch.setattr(module, 'get_http_session', lambda: Session())
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    assert service._remote_size('https://cdn.example/audio.mp3', 'https://example.test/book') == 12345
    assert captured['headers']['Accept-Encoding'] == 'identity'


# Origin: test_report_followup_round13_20260916.py
def test_cloudflare_just_a_moment_is_only_strong_in_page_title():
    from audioknigi.services.book_analysis_service import BookAnalysisService
    normal = '<html><head><title>Real book</title></head><body>Wait just a moment, he said.</body></html>'
    challenge = '<html><head><title>Just a moment...</title></head><body>Checking</body></html>'
    assert BookAnalysisService._looks_like_protection(normal, 200) is False
    assert BookAnalysisService._looks_like_protection(challenge, 200) is True


# Origin: test_report_followup_round14_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_segment_file_discovery_is_literal_for_bracketed_names(tmp_path):
    part = tmp_path / '_source [Reader].mp3.part'
    wanted = [tmp_path / f'{part.name}.seg{i:03d}' for i in range(2)]
    for item in wanted:
        item.write_bytes(b'x')
    (tmp_path / '_source R.mp3.part.seg000').write_bytes(b'x')
    assert sorted(_segment_files(part)) == sorted(wanted)


# Origin: test_report_followup_round18_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_round18_network_and_probe_cancellation_contracts_are_present() -> None:
    network = (ROOT / 'audioknigi/download/network.py').read_text(encoding='utf-8')
    probe = (ROOT / 'audioknigi/download/probe.py').read_text(encoding='utf-8')
    assert 'unlink_with_retry(part.with_name(part.name + ".assembling"), missing_ok=True)' in network
    assert 'replace_with_retry(assembling, target)' in network
    assert 'wait(pending, timeout=0.10, return_when=FIRST_COMPLETED)' in probe
    assert 'cancel_active = getattr(self, "_cancel_active_subprocesses", None)' in probe


# Origin: test_report_followup_round22_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_connect_relay_preserves_reverse_direction_after_upstream_half_close() -> None:
    client, left = socket.socketpair()
    right, upstream = socket.socketpair()
    worker = threading.Thread(target=_relay_bidirectional, args=(left, right), daemon=True)
    worker.start()
    try:
        upstream.sendall(b'response')
        upstream.shutdown(socket.SHUT_WR)
        client.settimeout(2.0)
        assert client.recv(8) == b'response'
        client.sendall(b'late-client')
        upstream.settimeout(2.0)
        assert upstream.recv(11) == b'late-client'
        client.shutdown(socket.SHUT_WR)
        worker.join(2.0)
        assert not worker.is_alive()
    finally:
        for sock in (client, left, right, upstream):
            try:
                sock.close()
            except OSError:
                pass

def test_connect_handler_uses_full_duplex_relay_but_plain_http_can_end_on_upstream_eof() -> None:
    source = (ROOT / 'audioknigi/network_dns.py').read_text(encoding='utf-8')
    connect_block = source[source.index('if method.upper() == "CONNECT":'):source.index('parsed = urlsplit(target)')]
    assert '_relay_bidirectional(client, upstream)' in connect_block
    assert 'return_when_right_closes=True' not in connect_block
    assert source.count('return_when_right_closes=True') == 1

def test_round22_removes_only_confirmed_dead_checks_and_redundant_range_noop() -> None:
    analysis_source = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    network_source = (ROOT / 'audioknigi/download/network.py').read_text(encoding='utf-8')
    settings_source = (ROOT / 'audioknigi/config/settings.py').read_text(encoding='utf-8')
    assert 'if playlist_response is None:' not in analysis_source
    range_block = network_source[network_source.index('if status == 200:'):network_source.index('cr = response.headers.get("content-range", "")')]
    assert range_block.count('response.raise_for_status()') == 1
    assert 'raw["auto_chunk_min_kbytes_per_sec"] = max(1, safe_int(' in settings_source


# Origin: test_report_followup_round24_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_network_proxy_and_media_edge_cases_are_hardened() -> None:
    network = (ROOT / 'audioknigi/network_dns.py').read_text(encoding='utf-8')
    media = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    assert 'path = quote(path, safe="/:?#[]@!$&\'()*+,;=%")' in network
    assert 'except (OSError, ValueError):' in network
    assert 'start = int(float(start))' in media
    assert 'duration = int(float(duration))' in media


# Origin: test_report_followup_round2_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_persist_browser_cookies_accepts_legacy_headers(monkeypatch):
    captured = {}

    def fake(cookies, headers=None):
        captured['cookies'] = cookies
        captured['headers'] = headers
    monkeypatch.setattr(core__report_followup_round2_20260915, 'persist_browser_session', fake)
    core__report_followup_round2_20260915.persist_browser_cookies([{'name': 'a', 'value': 'b'}], {'User-Agent': 'UA'})
    assert captured['headers'] == {'User-Agent': 'UA'}


# Origin: test_report_followup_round32_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round32_20260918(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

def test_segmented_wait_closes_active_io_on_cancel_path() -> None:
    source = src__report_followup_round32_20260918('audioknigi/download/network.py')
    start = source.index('cancelled_peers_for_error = False')
    block = source[start:start + 1200]
    assert 'try:' in block and 'finally:' in block
    assert 'if any(thread.is_alive() for thread in threads):' in block
    assert 'self._cancel_active_network_io()' in block


# Origin: test_report_followup_round33_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round33_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_empty_playwright_cookie_list_preserves_existing_cookie_file(monkeypatch) -> None:
    writes = []
    monkeypatch.setattr(core__report_followup_round33_20260918, '_load_persisted_profile', lambda: {'headers': {}, 'cookies_saved': 4})
    monkeypatch.setattr(core__report_followup_round33_20260918, 'save_json', lambda path, payload: writes.append((path, payload)) or True)
    monkeypatch.setattr(core__report_followup_round33_20260918, 'refresh_http_session_profile', lambda: None)
    core__report_followup_round33_20260918.persist_browser_session([], {'User-Agent': 'UA'})
    assert not any((path == core__report_followup_round33_20260918.COOKIE_FILE for path, _payload in writes))
    profile = [payload for path, payload in writes if path == core__report_followup_round33_20260918.SESSION_PROFILE_FILE][-1]
    assert profile['cookies_saved'] == 4


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_segmented_cancel_closes_sockets_then_waits_for_file_handles() -> None:
    source = src__report_followup_round34_20260919('audioknigi/download/network.py')
    block = source[source.index('cancelled_peers_for_error = False'):source.index('if errors:', source.index('cancelled_peers_for_error = False'))]
    assert 'self._cancel_active_network_io()' in block
    assert 'thread.join(timeout=min(1.0, remaining))' in block
    assert 'event=segmented_cancel_workers_lingering' in block


# Origin: test_report_followup_round3_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_unknown_remote_size_still_estimates_nonzero_disk_space(tmp_path):

    class Dummy(ProbeMixin):
        runtime_audio_preset = 'copy'

        def _book_folder(self, book, create=False):
            return tmp_path / 'book'
    track = Track(index=1, title='One', file='https://cdn.invalid/1.mp3', duration=60.0)
    book = Book(url='https://example.invalid', title='Book', tracks=[track], remote_size=0)
    assert Dummy()._estimate_required_space(book) > 0


# Origin: test_report_followup_round40_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round40_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_mode_switch_is_a_real_segmented_control_holder() -> None:
    theme = src__report_followup_round40_20260920('audioknigi/qt/theme.py')
    window = src__report_followup_round40_20260920('audioknigi/qt/main_window.py')
    assert 'QWidget#modeSegmentHolder' in theme
    assert 'mode_segment_holder.setObjectName("modeSegmentHolder")' in window
    assert 'mode_segment_layout.setContentsMargins(2, 2, 2, 2)' in window
    assert 'mode_segment_layout.setSpacing(0)' in window


# Origin: test_report_followup_round43_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round43_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_range_probe_accepts_whitespace_around_content_range_slash(monkeypatch) -> None:

    class Response:
        status_code = 206
        headers = {'content-range': 'bytes 0-0 / 1234567'}

        def raise_for_status(self):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class Session:

        def get(self, *args, **kwargs):
            return Response()
    monkeypatch.setattr(network_module__report_followup_round43_20260920, 'get_http_session', lambda: Session())
    assert NetworkDownloadMixin()._range_info('https://cdn.example/book.mp3', 'https://example/') == (True, 1234567)


# Origin: test_report_followup_round44_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round44_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_persist_browser_session_does_not_refresh_requests_pool_for_identical_material(monkeypatch) -> None:
    cookies = [{'name': 'cf_clearance', 'value': 'abc', 'domain': '.example.test', 'path': '/', 'expires': -1, 'secure': True}]
    profile = {'headers': {'User-Agent': 'UA'}, 'cookies_saved': 1, 'saved_at': 1}
    saves = []
    refreshes = []
    monkeypatch.setattr(core__report_followup_round44_20260920, '_load_persisted_profile', lambda: dict(profile))
    monkeypatch.setattr(core__report_followup_round44_20260920, 'load_json', lambda path, default=None: list(cookies) if path == core__report_followup_round44_20260920.COOKIE_FILE else default)
    monkeypatch.setattr(core__report_followup_round44_20260920, 'save_json', lambda path, payload: saves.append((path, payload)) or True)
    monkeypatch.setattr(core__report_followup_round44_20260920, 'refresh_http_session_profile', lambda: refreshes.append(True))
    core__report_followup_round44_20260920.persist_browser_session(cookies, {'User-Agent': 'UA'})
    assert saves == []
    assert refreshes == []
    core__report_followup_round44_20260920.persist_browser_session(cookies, {'User-Agent': 'UA-2'})
    assert any((path == core__report_followup_round44_20260920.SESSION_PROFILE_FILE for path, _payload in saves))
    assert refreshes == [True]


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

def test_segmented_download_rejects_nonpositive_size_before_division() -> None:
    source = src__report_followup_round45_20260921('audioknigi/download/network.py')
    start = source.index('def _download_segmented')
    block = source[start:]
    guard = 'if total_size <= 0:'
    assert guard in block
    assert block.index(guard) < block.index('total_size // min_chunk')
    assert 'raise RangeUnsupported' in block[block.index(guard):block.index('target = Path(target)')]


# Origin: test_report_followup_round52_20260924.py
def test_segment_count_normalizes_zero_and_out_of_range_values() -> None:
    assert settings_module.normalize_settings({'segment_count': '0'})['segment_count'] == 'auto'
    assert settings_module.normalize_settings({'segment_count': 0})['segment_count'] == 'auto'
    assert settings_module.normalize_settings({'segment_count': '9'})['segment_count'] == 'auto'
    assert settings_module.normalize_settings({'segment_count': '3'})['segment_count'] == '3'


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

def test_source_health_outcome_reports_blocked_and_unavailable_counts():
    outcome = SourceHealthOutcome([SourceHealthItem('one', 'https://one/', True, status_code=200), SourceHealthItem('two', 'https://two/', False, blocked=True, status_code=451), SourceHealthItem('three', 'https://three/', False, error='timeout')])
    assert outcome.reachable_count == 1
    assert outcome.unavailable_count == 2
    assert outcome.blocked_count == 1
    assert outcome.all_unavailable is False

def test_hidden_window_skips_startup_source_health_check():
    source = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'if not self.isVisible()' in source
    assert 'threading.Thread(' in source
    assert 'daemon=True' in source
    assert 'relay.source_health_result.emit(outcome)' in source


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

def test_dns_setting_defaults_to_auto_and_invalid_value_is_normalized():
    assert normalize_settings({})['dns_mode'] == 'auto'
    assert normalize_settings({'dns_mode': 'garbage'})['dns_mode'] == 'auto'
    assert normalize_settings({'dns_mode': 'cloudflare'})['dns_mode'] == 'cloudflare'
    assert normalize_settings({'dns_mode': 'system'})['dns_mode'] == 'system'

def test_auto_mode_falls_back_to_system_on_cloudflare_transport_failure(monkeypatch):

    def fail_cloudflare(host, family):
        raise socket.gaierror(socket.EAI_AGAIN, 'Cloudflare TLS handshake timed out')
    monkeypatch.setattr(network_dns, '_resolve', fail_cloudflare)
    monkeypatch.setattr(network_dns, '_ORIGINAL_GETADDRINFO', _system_fake)
    network_dns.configure_dns_mode('auto')
    rows = network_dns.cloudflare_getaddrinfo('example.com', 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
    assert rows[0][4] == ('203.0.113.44', 443)
    status = network_dns.dns_runtime_status()
    assert status['fallback_active'] is True
    assert status['fallback_event'] >= 1
    assert status['failures'] == 1

def test_auto_mode_opens_circuit_and_skips_cloudflare_until_cooldown(monkeypatch):
    calls = []

    def fail_cloudflare(host, family):
        calls.append(host)
        raise socket.gaierror(socket.EAI_AGAIN, 'DoH unavailable')
    monkeypatch.setattr(network_dns, '_resolve', fail_cloudflare)
    monkeypatch.setattr(network_dns, '_ORIGINAL_GETADDRINFO', _system_fake)
    network_dns.configure_dns_mode('auto')
    for host in ('one.example', 'two.example', 'three.example'):
        network_dns.cloudflare_getaddrinfo(host, 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
    status = network_dns.dns_runtime_status()
    assert status['circuit_open'] is True
    assert status['retry_after_seconds'] > 0
    assert len(calls) == network_dns.CLOUDFLARE_FAILURE_THRESHOLD
    network_dns.cloudflare_getaddrinfo('four.example', 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
    assert len(calls) == network_dns.CLOUDFLARE_FAILURE_THRESHOLD

def test_cloudflare_only_mode_never_uses_system_fallback(monkeypatch):
    original_calls = []

    def fail_cloudflare(host, family):
        raise socket.gaierror(socket.EAI_AGAIN, 'DoH unavailable')

    def original(*args, **kwargs):
        original_calls.append(args[0])
        return _system_fake(*args, **kwargs)
    monkeypatch.setattr(network_dns, '_resolve', fail_cloudflare)
    monkeypatch.setattr(network_dns, '_ORIGINAL_GETADDRINFO', original)
    network_dns.configure_dns_mode('cloudflare')
    with pytest.raises(socket.gaierror):
        network_dns.cloudflare_getaddrinfo('example.com', 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
    assert original_calls == []

def test_system_mode_bypasses_cloudflare_for_python_playwright_and_ffmpeg(monkeypatch):
    monkeypatch.setattr(network_dns, '_ORIGINAL_GETADDRINFO', _system_fake)
    monkeypatch.setattr(network_dns, '_resolve', lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('DoH must not run')))
    monkeypatch.setattr(network_dns, 'ensure_cloudflare_playwright_proxy', lambda: (_ for _ in ()).throw(AssertionError('proxy must not run')))
    network_dns.configure_dns_mode('system')
    assert network_dns.cloudflare_getaddrinfo('example.com', 443)[0][4][0] == '203.0.113.44'
    assert network_dns.cloudflare_ffmpeg_input_args() == []
    options = network_dns.cloudflare_playwright_launch_kwargs()
    assert 'proxy' not in options
    assert '--dns-over-https-mode=off' in options['args']

def test_auto_mode_keeps_shared_proxy_for_playwright_and_ffmpeg(monkeypatch):
    monkeypatch.setattr(network_dns, 'ensure_cloudflare_playwright_proxy', lambda: 'http://127.0.0.1:45555')
    network_dns.configure_dns_mode('auto')
    assert network_dns.cloudflare_ffmpeg_input_args() == ['-http_proxy', 'http://127.0.0.1:45555']
    options = network_dns.cloudflare_playwright_launch_kwargs()
    assert options['proxy']['server'] == 'http://127.0.0.1:45555'
    assert '--disable-quic' in options['args']
    assert any(('dns-over-https-mode=secure' in arg for arg in options['args']))

def test_cached_cloudflare_answer_does_not_fake_recovery(monkeypatch):
    network_dns.configure_dns_mode('auto')
    network_dns._record_cloudflare_failure(socket.gaierror(socket.EAI_AGAIN, 'DoH unavailable'))
    key = ('cached.example', 1)
    with network_dns._CACHE_LOCK:
        network_dns._CACHE[key] = (network_dns.time.monotonic() + 60.0, ('203.0.113.8',))
    monkeypatch.setattr(network_dns, '_query_cloudflare_json', lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('live DoH must not run')))
    assert network_dns._resolve_with_policy('cached.example', socket.AF_INET) == ('203.0.113.8',)
    assert network_dns.dns_runtime_status()['fallback_active'] is True

def test_live_cloudflare_success_announces_recovery(monkeypatch):
    network_dns.configure_dns_mode('auto')
    network_dns._record_cloudflare_failure(socket.gaierror(socket.EAI_AGAIN, 'DoH unavailable'))
    before = int(network_dns.dns_runtime_status()['recovery_event'])
    with network_dns._CACHE_LOCK:
        network_dns._CACHE.pop(('fresh.example', 1), None)
    monkeypatch.setattr(network_dns, '_query_cloudflare_json', lambda *args, **kwargs: (('203.0.113.9',), 60, '1.1.1.1'))
    assert network_dns._resolve_with_policy('fresh.example', socket.AF_INET) == ('203.0.113.9',)
    status = network_dns.dns_runtime_status()
    assert status['fallback_active'] is False
    assert int(status['recovery_event']) == before + 1


# Origin: test_round62_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_response_html_prefers_detected_encoding_before_http_default_latin1():
    original = 'Исполнитель: Илья Кривошеев'

    class Response:
        content = original.encode('cp1251')
        encoding = 'ISO-8859-1'
        apparent_encoding = 'windows-1251'
        text = ''
    assert _response_html_text(Response()) == original

def test_loudnorm_filter_complex_keeps_requested_range(monkeypatch):
    from audioknigi.download import media as media_module
    captured = {}
    monkeypatch.setattr(media_module, 'resolve_executable', lambda _name: 'ffmpeg')

    class Harness(MediaProcessingMixin):

        def _run_ffmpeg_capture(self, cmd, timeout):
            captured['cmd'] = list(cmd)
            return '{"input_i":"-20","input_lra":"4","input_tp":"-2","input_thresh":"-30","target_offset":"1"}'
    Harness()._measure_loudnorm('source.mp3', start=12.5, duration=30, filter_complex='[0:a]anull[a]', map_label='a')
    cmd = captured['cmd']
    assert cmd[cmd.index('-ss') + 1] == '12.5'
    assert cmd[cmd.index('-t') + 1] == '30'


# Origin: test_round66_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_segmented_workers_use_atomic_get_and_only_check_empty_when_parked():
    source = (ROOT / 'audioknigi/download/network.py').read_text(encoding='utf-8')
    block = source[source.index('def worker(worker_id)'):source.index('self.log(', source.index('def worker(worker_id)'))]
    parked_marker = 'if worker_id >= controller.current_workers():'
    before_parked, parked_and_after = block.split(parked_marker, 1)
    parked_block = parked_and_after.split('try:', 1)[0]
    assert 'jobs.empty()' not in before_parked
    assert 'if jobs.empty():' in parked_block
    assert 'jobs.get_nowait()' in block
    assert 'except queue.Empty:' in block

def test_source_health_403_is_reachable_but_blocked(monkeypatch):

    class Response:
        status_code = 403

        def close(self):
            pass

    class Session:

        def __init__(self):
            self.headers = {}
            self.trust_env = True

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, *_args, **_kwargs):
            return Response()
    monkeypatch.setattr(source_health_service.requests, 'Session', Session)
    item = source_health_service._probe_source('example.invalid', timeout=1.0)
    assert item.reachable is True
    assert item.blocked is True
    assert item.status_code == 403
    assert item.error == ''


# Origin: test_round67_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_empty_dns_resolution_raises_clear_gaierror(monkeypatch):
    monkeypatch.setattr(network_dns, '_bypass_cloudflare', lambda _host: False)
    monkeypatch.setattr(network_dns, 'current_dns_mode', lambda: network_dns.DNS_MODE_CLOUDFLARE)
    monkeypatch.setattr(network_dns, '_is_numeric_host', lambda _host: False)
    monkeypatch.setattr(network_dns, '_resolve_with_policy', lambda _host, _family: ())
    with pytest.raises(socket.gaierror) as exc_info:
        network_dns._connect_target('no-records.invalid', 443, timeout=0.01)
    assert 'No DNS records for no-records.invalid' in str(exc_info.value)


# Origin: test_round69_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_health_and_main_http_sessions_share_proxy_isolation_policy():
    core_source = (ROOT / 'audioknigi/core.py').read_text(encoding='utf-8')
    health_source = (ROOT / 'audioknigi/services/source_health_service.py').read_text(encoding='utf-8')
    build_block = core_source[core_source.index('def build_http_session'):core_source.index('def get_http_session')]
    assert 'session.trust_env = False' in build_block
    assert 'session.trust_env = False' in health_source


# Origin: test_round80_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_segmented_tiny_payload_never_creates_negative_or_empty_ranges(tmp_path):
    seen = []

    class Harness(NetworkDownloadMixin):
        runtime_segment_count = '2'
        runtime_bandwidth_limit = 0.0
        runtime_auto_chunk_min_kbytes_per_sec = 256
        cancel_event = None

        def _check_cancel(self):
            pass

        def _download_segment(self, _url, seg_path, start, end, _referer, progress_cb, peer_abort_event=None):
            seen.append((start, end))
            assert 0 <= start <= end
            payload = b'x' * (end - start + 1)
            Path(seg_path).write_bytes(payload)
            progress_cb(len(payload), force=True)
            return len(payload)

        def _cancel_active_network_io(self):
            pass

        def set_progress(self, *_args):
            pass

        def set_status(self, *_args):
            pass

        def log(self, *_args):
            pass

        def record_transfer_metrics(self, *_args):
            pass
    target = tmp_path / 'tiny.bin'
    result = Harness()._download_segmented('https://example.invalid/tiny', target, '', 1, 8)
    assert Path(result).read_bytes() == b'x'
    assert seen == [(0, 0)]

def test_source_health_proxy_policy_matches_global_http_policy():
    core = (ROOT / 'audioknigi/core.py').read_text(encoding='utf-8')
    health = (ROOT / 'audioknigi/services/source_health_service.py').read_text(encoding='utf-8')
    assert 'session.trust_env = False' in core
    assert 'session.trust_env = False' in health


# Origin: test_round81_external_review_followup_20261006.py
ROOT = Path(__file__).resolve().parents[2]

def test_source_health_503_is_reachable_but_blocked(monkeypatch):

    class Response:
        status_code = 503

        def close(self):
            pass

    class Session:

        def __init__(self):
            self.headers = {}
            self.trust_env = True

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, *_args, **_kwargs):
            return Response()
    monkeypatch.setattr(source_health_service.requests, 'Session', Session)
    item = source_health_service._probe_source('example.invalid', timeout=1.0)
    assert item.reachable is True
    assert item.blocked is True
    assert item.status_code == 503
    assert item.error == ''

def test_reviewed_i18n_and_proxy_contracts_remain_intentional():
    assert localize_runtime_text('en', 'Анализирую audioknigi.com.ua быстрым HTTP-способом…') == 'Analyzing audioknigi.com.ua using the fast HTTP method…'
    assert localize_runtime_text('en', 'История обновлена: 12 записей.') == 'History refreshed: 12 entries.'
    core = (ROOT / 'audioknigi/core.py').read_text(encoding='utf-8')
    health = (ROOT / 'audioknigi/services/source_health_service.py').read_text(encoding='utf-8')
    assert 'session.trust_env = False' in core
    assert 'session.trust_env = False' in health


# Origin: test_runtime_integrity_followup_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_cloudflare_http_200_interstitial_detection_is_shared():
    assert BookAnalysisService._looks_like_protection("<title>Just a moment...</title><div class='cf-chl-x'>", 200)
    assert not BookAnalysisService._looks_like_protection('An article mentioning Cloudflare and captcha.', 200)


# Origin: test_stability_localization_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_cover_fetch_rejects_non_http_schemes_without_network(monkeypatch):
    import audioknigi.cover_fetch as module

    def explode():
        raise AssertionError('network session must not be created for data/file URLs')
    monkeypatch.setattr(module, 'get_http_session', explode)
    assert fetch_cover_bytes('data:image/png;base64,AAAA') is None
    assert fetch_cover_bytes('file:///tmp/cover.jpg') is None

# Round 82: post-consolidation audit follow-up

def test_single_stream_416_discards_stale_part_and_restarts_only_once(monkeypatch, tmp_path):
    calls = []

    class Response:
        def __init__(self, status_code, headers, chunks=()):
            self.status_code = status_code
            self.headers = headers
            self._chunks = list(chunks)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"HTTP {self.status_code}")

        def iter_content(self, chunk_size=0):
            yield from self._chunks

    responses = [
        Response(416, {"content-range": "bytes */10"}),
        Response(200, {"content-length": "5"}, [b"fresh"]),
    ]

    class Session:
        def get(self, _url, *, headers, **_kwargs):
            calls.append(dict(headers))
            return responses.pop(0)

    monkeypatch.setattr(network_module__report_followup_round43_20260920, "get_http_session", lambda: Session())

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

    target = tmp_path / "source.mp3"
    part = target.with_name(target.name + ".part")
    part.write_bytes(b"stale")

    assert Harness()._download_single("https://cdn.invalid/source.mp3", target, "https://example.invalid/") == target
    assert target.read_bytes() == b"fresh"
    assert len(calls) == 2
    assert calls[0]["Range"] == "bytes=5-"
    assert "Range" not in calls[1]


def test_single_stream_416_on_zero_offset_retry_surfaces_error_without_recursing(monkeypatch, tmp_path):
    calls = []

    class Response:
        status_code = 416
        headers = {"content-range": "bytes */10"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def raise_for_status(self):
            raise requests.HTTPError("HTTP 416")

        def iter_content(self, chunk_size=0):
            return iter(())

    class Session:
        def get(self, _url, *, headers, **_kwargs):
            calls.append(dict(headers))
            return Response()

    monkeypatch.setattr(network_module__report_followup_round43_20260920, "get_http_session", lambda: Session())

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

    target = tmp_path / "source.mp3"
    target.with_name(target.name + ".part").write_bytes(b"stale")

    with pytest.raises(RuntimeError, match="Сетевая ошибка"):
        Harness()._download_single("https://cdn.invalid/source.mp3", target, "https://example.invalid/")

    assert len(calls) == 2
    assert "Range" in calls[0]
    assert "Range" not in calls[1]

# Post-consolidation: Round 85 external audit follow-up.
def test_range_unsupported_fallback_discards_stale_single_stream_part(tmp_path):
    from audioknigi.download.errors import RangeUnsupported

    class Harness(NetworkDownloadMixin):
        runtime_segment_count = "2"
        runtime_segment_threshold_mb = 1

        def _range_info(self, _url, _referer):
            return True, 20 * 1024 * 1024

        def _download_segmented(self, *_args, **_kwargs):
            raise RangeUnsupported("server rejected ranges")

        def _download_single(self, _url, target, _referer):
            part = Path(target).with_name(Path(target).name + ".part")
            assert not part.exists()
            return Path(target)

        def log(self, *_args, **_kwargs):
            pass

    target = tmp_path / "book.mp3"
    part = target.with_name(target.name + ".part")
    part.write_bytes(b"stale-old-stream")
    Path(str(part) + ".seg000").write_bytes(b"range-state")

    assert Harness()._download_with_resume("https://example.invalid/book.mp3", target, "") == target
    assert not part.exists()


def test_segment_worker_accounts_dequeued_job_even_when_download_fails():
    source = (ROOT / "audioknigi/download/network.py").read_text(encoding="utf-8")
    start = source.index("def worker(worker_id):")
    end = source.index("self.log(\n            f\"Сегментированная загрузка", start)
    block = source[start:end]
    assert "finally:\n                    jobs.task_done()" in block


# Post-consolidation: Round 86 external audit follow-up.
@pytest.mark.parametrize("status", [401, 451])
def test_source_health_blocked_http_status_is_still_network_reachable(monkeypatch, status):
    class Response:
        status_code = status
        def close(self):
            pass

    class Session:
        def __init__(self):
            self.headers = {}
            self.trust_env = True
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def get(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr(source_health_service.requests, "Session", Session)
    item = source_health_service._probe_source("example.invalid", timeout=1.0)
    assert item.reachable is True
    assert item.blocked is True
    assert item.status_code == status
    assert item.error == ""


def test_parallel_cancel_claims_subprocess_snapshot_once():
    import weakref

    class Proc:
        def __init__(self):
            self.kills = 0
        def poll(self):
            return None
        def kill(self):
            self.kills += 1

    harness = NetworkDownloadMixin()
    harness._active_subprocess_lock = threading.RLock()
    harness._active_subprocesses = weakref.WeakSet()
    proc = Proc()
    harness._active_subprocesses.add(proc)

    assert harness._cancel_active_subprocesses() == 1
    assert harness._cancel_active_subprocesses() == 0
    assert proc.kills == 1
