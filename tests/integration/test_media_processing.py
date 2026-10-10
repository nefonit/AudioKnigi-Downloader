"""Consolidated integration tests for the media processing domain.

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
from audioknigi.core import _first_json_ld
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
import csv
from audioknigi.config.settings import migrate_settings
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.network import _segment_files
from audioknigi.models import SearchResult
import audioknigi.poleknig as poleknig__report_followup_round14_20260916
import base64
from audioknigi.i18n import localize_runtime_text
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
from audioknigi.providers import audioknigi_search as search_module
from audioknigi.providers.audioknigi_search import _canonical_title
from audioknigi.services.book_analysis_service import _playlist_track_title
from audioknigi import core
from audioknigi.config.settings import save_app_settings
from audioknigi.core import load_json
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.core import fmt_size
from audioknigi.templates import render_text_template
from audioknigi.download_engine import _DownloadEngine
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.download_engine import DownloadService, _DownloadEngine
from audioknigi.services.search_service import search_all_sources
import audioknigi.config.settings as settings_module__report_followup_round43_20260920
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round43_20260920
import audioknigi.download.network as network_module__report_followup_round43_20260920
import audioknigi.knigavuhe as knigavuhe__report_followup_round43_20260920
import audioknigi.poleknig as poleknig__report_followup_round43_20260920
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata, _merge_author_names
import audioknigi.config.settings as settings_module__report_followup_round45_20260921
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round45_20260921
import audioknigi.services.player_position_store as position_module
from audioknigi.download.errors import SharedSourceTimelineError
from audioknigi.poleknig import _parse_playlist_objects
from audioknigi.providers.audioknigi_search import parse_audioknigi_results
from audioknigi.services.player_position_store import PlayerPositionStore
from audioknigi.knigavuhe import _extract_names
from audioknigi.services.queue_service import _normalize_queue_download_mode, _track_from_dict
import audioknigi.config.settings as settings_module__report_followup_round47_20260923
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round47_20260923
from audioknigi.core import safe_int
import hashlib
import math
import audioknigi.config.settings as settings_module__report_followup_round49_20260924
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round49_20260924
import audioknigi.download.source_analysis as source_analysis_module__report_followup_round49_20260924
from audioknigi.download.source_analysis import SourceAnalysisMixin
from audioknigi.brand import version_label
from audioknigi.core import load_browser_context_profile
from audioknigi.network_dns import _parse_proxy_authority
from audioknigi.providers.audioknigi_search import _split_audioknigi_title
from audioknigi.services.source_health_service import SourceHealthItem, SourceHealthOutcome
from dataclasses import dataclass
from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, extract_extended_metadata_from_html
from audioknigi.diagnostics import support_bundle as support_bundle__round61_external_review_followup_20260929
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.providers.audioknigi_search import _author_detail_score, _matches_query
from audioknigi.services.queue_service import _item_to_dict
import os
from audioknigi.models import Book, Track, TRACK_STATUS_READY
from audioknigi.providers.audioknigi_search import _response_html_text
from audioknigi.services import library_service, source_health_service
from audioknigi import poleknig as poleknig__round69_runtime_followup_20260930
from audioknigi.download.errors import MissingMediaSourceError
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, _DownloadEngine
import re
from audioknigi.diagnostics import support_bundle as support_bundle__round73_runtime_followup_20261002
from audioknigi.knigavuhe import _usable_search_title
from audioknigi.services.book_analysis_service import BookAnalysisService, _playlist_track_title
from audioknigi.services.library_service import _validated_backup_payloads
from audioknigi.services.queue_service import _optional_persisted_bool
from audioknigi.core import effective_track_duration
from audioknigi.models import Book, NarrationVariant, Track
from audioknigi import cover_fetch
from audioknigi.core import display_track_timeline
from audioknigi.services.queue_service import _book_from_dict
from audioknigi.templates import _safe_track_index
from audioknigi.core import safe_name
from audioknigi.knigavuhe import _extract_narration_variants
from audioknigi.templates import template_values
from audioknigi.core import SiteStructureChanged
from audioknigi.knigavuhe import parse_book_html
from audioknigi.download.common import source_target_assignments
from audioknigi.models import Book
from audioknigi.services import source_health_service
from audioknigi.download import network as network_module__round81_external_review_followup_20261006
from audioknigi.download import source_analysis as source_analysis_module__round81_external_review_followup_20261006
from audioknigi.download.network import SlidingSpeedMeter
from audioknigi.models import Book, SearchResult, TRACK_STATUS_DAMAGED, TRACK_STATUS_MISSING, TRACK_STATUS_PRESENT, TRACK_STATUS_READY, normalize_track_status
import types
from audioknigi.diagnostics import support_bundle as support_bundle__runtime_integrity_followup_20260912
from audioknigi.download_engine import DownloadService
from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.sources import normalize_supported_url
from audioknigi.diagnostics.support_bundle import _is_secret_key
from audioknigi.i18n import localize_runtime_text, tr, ui_text
from audioknigi.providers.adapters import KnigavuheProvider, PoleKnigProvider
from audioknigi.services.queue_service import _book_to_dict


# Origin: test_acceptance_parser_diagnostics_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool__acceptance_parser_diagnostics_followup_20260915(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_atomic_write_text_creates_missing_parent_directory(tmp_path: Path):
    target = tmp_path / 'nested' / 'more' / 'file.txt'
    atomic_write_text(target, 'hello')
    assert target.read_text(encoding='utf-8') == 'hello'

def test_split_track_uses_effective_duration_when_end_is_missing():
    source = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    block = source[source.index('def _split_track'):source.index('def _save_book_sidecars')]
    assert 'measured = effective_track_duration(track)' in block
    assert 'cmd += ["-t", str(duration)]' in block


# Origin: test_cancellation_cover_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_download_engine_has_shared_cover_fetch_method():
    from audioknigi.download_engine import _DownloadEngine
    assert callable(getattr(_DownloadEngine, '_fetch_cover_bytes', None))

def test_shared_cover_fetch_preserves_cancelled(monkeypatch):
    from audioknigi import cover_fetch
    from audioknigi.core import Cancelled
    event = SimpleNamespace(is_set=lambda: True)
    with pytest.raises(Cancelled):
        cover_fetch.fetch_cover_bytes('https://example.test/cover.jpg', cancel_event=event)

def test_media_sidecar_supports_webp_and_central_json_writer():
    source = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    assert 'elif "webp" in mime_text:' in source
    assert 'save_json(folder / "metadata.json", payload, raise_errors=True)' in source
    assert '_atomic_write_text(' not in source

def test_worker_snapshot_drops_native_cover_before_deepcopy():
    source = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    assert 'normalized_cover = normalize_cover_cache(raw_cover)' in source
    assert 'snapshot_source.book.cover_cache = None' in source
    assert 'worker_request = copy.deepcopy(snapshot_source)' in source


# Origin: test_persistence_cancellation_hardening_20260929.py
def _book() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1-test', title='Test', tracks=[Track(index=1, title='Part 1', file='https://example.com/1.mp3')])

def test_ffprobe_stop_request_is_single_owner_across_threads():

    class FakeProcess:

        def __init__(self):
            self.kill_count = 0
            self._lock = threading.Lock()

        def poll(self):
            return None

        def kill(self):
            with self._lock:
                self.kill_count += 1
    service = BookAnalysisService()
    proc = FakeProcess()
    service._register_duration_probe_process(proc)
    threads = [threading.Thread(target=service._request_duration_probe_stop, args=(proc,)) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=1)
    assert proc.kill_count == 1
    service._unregister_duration_probe_process(proc)


# Origin: test_quality_runtime_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_sidecar_duplicate_check_fails_closed_on_invalid_current_track_index(tmp_path):
    book = Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index='bad', title='Part', file='https://cdn.invalid/1.mp3')])
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    engine = _DownloadEngine(request, {}, threading.Event(), DownloadCallbacks())
    (tmp_path / 'metadata.json').write_text(json.dumps({'source_url': book.url, 'title': 'Demo', 'author': '', 'narrator': '', 'tracks': [{'index': 1, 'title': 'Part'}]}), encoding='utf-8')
    assert engine._sidecar_metadata_matches_book(book, tmp_path) is False

def test_media_probe_defensively_validates_stream_list_shape():
    source = (ROOT / 'audioknigi' / 'download' / 'media.py').read_text(encoding='utf-8')
    assert 'isinstance(streams, list)' in source
    assert 'isinstance(streams[0], dict)' in source


# Origin: test_release_integrity_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_split_module_style_regressions_are_cleaned():
    source_analysis = (ROOT / 'audioknigi' / 'download' / 'source_analysis.py').read_text(encoding='utf-8')
    book_flow = (ROOT / 'audioknigi' / 'download' / 'book_flow.py').read_text(encoding='utf-8')
    lifecycle = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'lifecycle.py').read_text(encoding='utf-8')
    clipboard = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'clipboard.py').read_text(encoding='utf-8')
    search = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'search.py').read_text(encoding='utf-8')
    assert 'return unknown_narrator_choice\n\n    def _service' in source_analysis
    assert 'reason="disabled")\n\n        self._save_book_sidecars' in book_flow
    assert 'try: self.tray_controller.shutdown()' not in lifecycle
    assert '; self.track_table.selectRow' not in clipboard
    assert '; table.selectRow' not in search


# Origin: test_release_quality_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool__release_quality_followup_20260915(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_text_sidecars_use_atomic_writer():
    source = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    assert 'atomic_write_text(folder / "book_info.txt"' in source
    assert 'atomic_write_text(folder / "book.nfo"' in source
    assert 'atomic_write_text(folder / "desc.txt"' in source
    assert 'atomic_write_text(folder / "reader.txt"' in source

def _request() -> DownloadRequest:
    book = Book(url='https://knigavuhe.org/book/1', title='Book', tracks=[Track(index=1, title='One', file='https://cdn.example/1.mp3')])
    return DownloadRequest(book=book, selected_indices=None, output_dir=Path('.'))


# Origin: test_report_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_effective_track_duration_rejects_zero_length_span():
    track = Track(index=1, title='One', file='https://example.test/1.mp3', start=10, end=10)
    assert effective_track_duration(track) is None


# Origin: test_report_followup_round11_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_round11_skip_preserves_completed_sources_and_split_cancels_pending():
    source = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    marker = 'if action == "skip" and available_after_skip:'
    first = source.index(marker)
    window = source[first:first + 900]
    assert '_clear_stale_source_downloads(book)' not in window
    assert 'Keep already completed fresh source downloads' in window
    assert source.count('pending.cancel()') >= 4


# Origin: test_report_followup_round13_20260916.py
def test_media_id3_accepts_string_track_index(monkeypatch, tmp_path):
    from audioknigi.download import media
    saved = {}

    class FakeTags:

        def delall(self, _name):
            pass

        def add(self, frame):
            text = frame.get('text') if isinstance(frame, dict) else None
            if text:
                saved.setdefault('texts', []).append(text)

        def save(self, _path):
            saved['saved'] = True
    monkeypatch.setattr(media, 'ID3', lambda *_args, **_kwargs: FakeTags())
    monkeypatch.setattr(media, 'TIT2', lambda **kwargs: kwargs)
    monkeypatch.setattr(media, 'TALB', lambda **kwargs: kwargs)
    monkeypatch.setattr(media, 'TRCK', lambda **kwargs: kwargs)
    monkeypatch.setattr(media, 'TPE1', lambda **kwargs: kwargs)
    monkeypatch.setattr(media, 'APIC', lambda **kwargs: kwargs)
    host = SimpleNamespace(runtime_embed_tags=True, log=lambda *_args, **_kwargs: None)
    book = SimpleNamespace(title='Book', author='')
    track = SimpleNamespace(title='')
    media.MediaProcessingMixin._write_id3(host, tmp_path / 'part.mp3', book, '2', '10', None, track)
    assert saved.get('saved') is True
    assert any(('часть 02' in str(text) for text in saved.get('texts', [])))
    assert '2/10' in saved.get('texts', [])

def test_split_track_parses_clock_start_end(monkeypatch, tmp_path):
    from audioknigi.download.media import MediaProcessingMixin
    source = tmp_path / 'source.mp3'
    source.write_bytes(b'source')
    output = tmp_path / 'out.mp3'
    commands = []

    class Host(MediaProcessingMixin):
        runtime_normalization_mode = 'off'

        def _track_path(self, _book, _track):
            return output

        def _effective_mp3_profile(self, _source):
            return (True, None, None)

        def _run_ffmpeg(self, cmd, timeout=7200):
            commands.append(list(cmd))
            output.write_bytes(b'done')
    host = Host()
    book = SimpleNamespace(tracks=[])
    track = SimpleNamespace(index=1, start='00:01:00', end='00:01:30', duration=None)
    book.tracks = [track]
    host._split_track(book, track, source)
    cmd = commands[0]
    assert cmd[cmd.index('-ss') + 1] == '60'
    assert cmd[cmd.index('-t') + 1] == '30'

def test_audio_probe_cache_does_not_hold_lock_during_ffprobe(tmp_path):
    from audioknigi.download.media import MediaProcessingMixin
    first = tmp_path / 'one.mp3'
    second = tmp_path / 'two.mp3'
    first.write_bytes(b'1')
    second.write_bytes(b'2')
    first_entered = threading.Event()
    second_entered = threading.Event()
    release = threading.Event()

    class Host(MediaProcessingMixin):

        def _probe_audio_info(self, path):
            if Path(path) == first:
                first_entered.set()
                release.wait(2.0)
            else:
                second_entered.set()
            return {'codec': 'mp3'}
    host = Host()
    results = []
    t1 = threading.Thread(target=lambda: results.append(host._cached_probe_audio_info(first)))
    t2 = threading.Thread(target=lambda: results.append(host._cached_probe_audio_info(second)))
    t1.start()
    assert first_entered.wait(1.0)
    t2.start()
    try:
        assert second_entered.wait(0.5), 'second probe was blocked behind the cache lock'
    finally:
        release.set()
        t1.join(2.0)
        t2.join(2.0)
    assert len(results) == 2


# Origin: test_report_followup_round14_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_probe_cache_retry_is_iterative_not_recursive():
    source = (ROOT / 'audioknigi' / 'download' / 'media.py').read_text(encoding='utf-8')
    block = source[source.index('def _cached_probe_audio_info'):source.index('@staticmethod\n    def _preset_target')]
    assert 'while True:' in block
    assert 'return self._cached_probe_audio_info(path)' not in block


# Origin: test_report_followup_round15_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_atomic_write_text_retries_transient_permission_error(monkeypatch, tmp_path):
    import audioknigi.download.common as common
    target = tmp_path / 'book_info.txt'
    real_replace = common.os.replace
    calls = {'count': 0}

    def flaky_replace(src, dst):
        calls['count'] += 1
        if calls['count'] < 3:
            raise PermissionError('sharing violation')
        return real_replace(src, dst)
    monkeypatch.setattr(common.os, 'replace', flaky_replace)
    monkeypatch.setattr(common.time, 'sleep', lambda _seconds: None)
    atomic_write_text(target, 'ok')
    assert target.read_text(encoding='utf-8') == 'ok'
    assert calls['count'] == 3

def test_incomplete_loudnorm_stats_fall_back_instead_of_raising():
    source = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    assert '"Неполная статистика loudnorm первого прохода."' not in source
    assert 'использую безопасную однопроходную нормализацию' in source
    block = source[source.index('required = ('):source.index('def _normalization_filter_for_track')]
    assert 'return base' in block

def test_duration_probe_cancel_kills_registered_children_before_pool_wait():
    source = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    assert 'def _cancel_duration_probe_processes' in source
    block = source[source.index('def _populate_missing_track_durations'):source.index('@staticmethod', source.index('def _populate_missing_track_durations'))]
    assert 'self._cancel_duration_probe_processes()' in block
    assert block.index('self._cancel_duration_probe_processes()') < block.index('pool.shutdown(wait=False')

def test_duration_probe_registry_kills_live_processes():
    service = BookAnalysisService()

    class FakeProc:

        def __init__(self):
            self.killed = False

        def poll(self):
            return None

        def kill(self):
            self.killed = True
    proc = FakeProc()
    service._register_duration_probe_process(proc)
    service._cancel_duration_probe_processes()
    assert proc.killed is True
    service._unregister_duration_probe_process(proc)


# Origin: test_report_followup_round18_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_replace_with_retry_recovers_from_transient_permission_error(tmp_path, monkeypatch) -> None:
    source = tmp_path / 'source.bin'
    target = tmp_path / 'target.bin'
    source.write_bytes(b'new')
    target.write_bytes(b'old')
    original = Path.replace
    attempts = {'count': 0}

    def flaky_replace(self, other):
        if self == source and attempts['count'] < 2:
            attempts['count'] += 1
            raise PermissionError('sharing violation')
        return original(self, other)
    monkeypatch.setattr(Path, 'replace', flaky_replace)
    assert replace_with_retry(source, target) == target
    assert target.read_bytes() == b'new'
    assert attempts['count'] == 2


# Origin: test_report_followup_round19_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_split_track_does_not_infer_duration_from_next_different_source(tmp_path) -> None:

    class Dummy(MediaProcessingMixin):

        def _track_path(self, _book, _track):
            return tmp_path / 'out.mp3'

        def _effective_mp3_profile(self, _source):
            return (True, None, None)

        def _run_ffmpeg(self, cmd):
            self.cmd = list(cmd)

        def _normalization_filter_for_track(self, *_args):
            return ''

        def log(self, *_args, **_kwargs):
            pass
    current = SimpleNamespace(index=1, start=10, end=None, duration=None, actual_duration=None, file='part1.mp3')
    following = SimpleNamespace(index=2, start=20, end=None, duration=None, actual_duration=None, file='part2.mp3')
    book = SimpleNamespace(tracks=[current, following])
    dummy = Dummy()
    dummy._split_track(book, current, tmp_path / 'part1.mp3')
    assert '-ss' in dummy.cmd
    assert '-t' not in dummy.cmd


# Origin: test_report_followup_round20_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_partial_download_sidecars_use_full_book_track_list_contract() -> None:
    source = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    assert 'self._save_book_sidecars(book, folder, list(getattr(book, "tracks", None) or []))' in source
    assert 'self._save_book_sidecars(book, folder, chosen)' not in source

def test_probe_filename_accepts_mapping_track() -> None:

    class Dummy(ProbeMixin):
        runtime_use_templates = False
        runtime_naming_mode = 'number_title'
    book = Book(url='https://example.invalid/book', title='Book', tracks=[])
    name = Dummy()._track_filename(book, {'index': '4', 'title': 'Chapter'})
    assert name == '04 - Chapter.mp3'


# Origin: test_report_followup_round24_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_missing_media_wait_and_dialog_have_bounded_failure_paths() -> None:
    workers = (ROOT / 'audioknigi/qt/workers.py').read_text(encoding='utf-8')
    analysis = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    assert 'MISSING_MEDIA_DECISION_TIMEOUT_SECONDS' in workers
    assert 'prompt.resolve("stop")' in workers
    assert 'box.finished.connect' not in analysis
    assert 'box.destroyed.connect' in analysis
    assert 'clicked_button = box.clickedButton()' in analysis


# Origin: test_report_followup_round2_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_loudnorm_nonfinite_statistics_fall_back_to_single_pass(monkeypatch):

    class Dummy(MediaProcessingMixin):
        pass
    dummy = Dummy()
    monkeypatch.setattr('audioknigi.download.media.resolve_executable', lambda _name: 'ffmpeg')
    monkeypatch.setattr(dummy, '_run_ffmpeg_capture', lambda *_args, **_kwargs: '{"input_i":"-inf","input_lra":"0.0","input_tp":"-inf","input_thresh":"-70.0","target_offset":"0.0"}')
    value = dummy._measure_loudnorm('silent.wav')
    assert value == 'loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json'


# Origin: test_report_followup_round33_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round33_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_loudnorm_scan_window_is_large_enough_for_noisy_inputs() -> None:
    source = src__report_followup_round33_20260918('audioknigi/download/media.py')
    assert 'loudnorm_tail = str(stderr or "")[-524_288:]' in source

def test_cover_format_switch_removes_stale_alternate_sidecars() -> None:
    source = src__report_followup_round33_20260918('audioknigi/download/media.py')
    assert 'for old_ext in (".jpg", ".jpeg", ".png", ".webp"):' in source
    assert '(folder / ("cover" + old_ext)).unlink(missing_ok=True)' in source

def test_book_analysis_bounds_fallback_and_always_cancels_probe_children() -> None:
    source = src__report_followup_round33_20260918('audioknigi/services/book_analysis_service.py')
    assert 'best_by_url: dict[str, float] = {}' in source
    assert 'sorted(best_by_url.items(), key=lambda item: item[1], reverse=True)[:8]' in source
    finally_block = source[source.index('finally:', source.index('def _populate_missing_track_durations')):source.index('@staticmethod', source.index('def _populate_missing_track_durations'))]
    assert 'self._cancel_duration_probe_processes()' in finally_block
    assert 'pool.shutdown(wait=False, cancel_futures=True)' in finally_block


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_cover_sidecar_is_written_atomically() -> None:
    common = src__report_followup_round34_20260919('audioknigi/download/common.py')
    media = src__report_followup_round34_20260919('audioknigi/download/media.py')
    assert 'def atomic_write_bytes' in common
    assert 'atomic_write_bytes(folder / ("cover" + ext), data)' in media


# Origin: test_report_followup_round3_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_duplicate_preflight_requires_ready_when_duration_probe_enabled(monkeypatch, tmp_path):
    book = Book(url='https://knigavuhe.org/book/demo/', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3')])
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    monkeypatch.setattr(_DownloadEngine, '_scan_book_files', lambda self, _book, create_folder=False: {'ready': 0, 'existing': 1, 'damaged': 0, 'total': 1})
    result = DownloadService().duplicate_preflight(request, probe_durations=True)
    assert result.exact_duplicate is False
    assert result.evidence == 'files-incomplete'

def test_protocol_relative_cover_is_normalized_without_referer(monkeypatch):
    import audioknigi.cover_fetch as module
    seen = {}

    class Response:
        headers = {'content-type': 'image/jpeg'}

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=0):
            return iter([b'image'])

        def close(self):
            pass

    class Session:

        def get(self, url, **kwargs):
            seen['url'] = url
            return Response()
    monkeypatch.setattr(module, 'get_http_session', Session)
    assert fetch_cover_bytes('//poleknig.com/cover.jpg') == (b'image', 'image/jpeg')
    assert seen['url'] == 'https://poleknig.com/cover.jpg'

def test_probe_filename_does_not_duplicate_audio_extension(tmp_path):

    class Dummy(ProbeMixin):
        runtime_use_templates = False
        runtime_naming_mode = 'number_title'
    book = Book(url='https://example.invalid', title='Book', tracks=[])
    track = Track(index=1, title='01_intro.mp3', file='x')
    assert Dummy()._track_filename(book, track) == '01 - 01_intro.mp3'

def test_ffmpeg_capture_timeout_cleanup_is_guarded():
    source = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    block = source[source.index('def _run_ffmpeg_capture'):source.index('def _probe_audio_info')]
    marker = 'if remaining <= 0:'
    timeout_block = block[block.index(marker):block.index('try:', block.index(marker) + len(marker)) + 120]
    assert 'proc.communicate(timeout=5)' in timeout_block
    assert 'except Exception' in timeout_block


# Origin: test_report_followup_round41_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round41_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_book_chapter_title_stretches_and_source_remains_readable() -> None:
    pages = src__report_followup_round41_20260920('audioknigi/qt/main_window_pages.py')
    assert 'for column in (0, 1, 2, 3, 4, 5):' in pages
    assert 'track_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)' in pages
    assert 'track_header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)' in pages
    assert 'self.track_table.setColumnWidth(7, 280)' in pages


# Origin: test_report_followup_round43_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round43_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_probe_identity_accepts_ascii_en_and_em_dashes() -> None:
    probe = ProbeMixin()
    for separator in (' - ', ' – ', ' — '):
        book = SimpleNamespace(title=f'Лев Толстой{separator}Война и мир', author='', narrator='')
        title, author, narrator = probe._book_identity_hints(book)
        assert title == 'Война и мир'
        assert author == 'Лев Толстой'
        assert narrator == ''


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

def test_audiobookshelf_ui_probe_timeout_fits_exit_grace_window() -> None:
    source = src__report_followup_round45_20260921('audioknigi/qt/workers.py')
    start = source.index('class AudiobookshelfWorker')
    end = source.index('class AnalysisWorker', start)
    block = source[start:end]
    assert 'timeout: float = 4.0' in block
    assert 'timeout=self.timeout' in block


# Origin: test_report_followup_round46_20260922.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round46_20260922(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_missing_media_decision_dialog_has_stable_main_window_parent() -> None:
    source = src__report_followup_round46_20260922('audioknigi/qt/mixins/analysis_download.py')
    start = source.index('def _resolve_missing_media')
    end = source.index('def ', start + 8)
    block = source[start:end]
    assert 'box = QMessageBox(self)' in block
    assert 'dialog_parent' not in block


# Origin: test_report_followup_round47_20260923.py
def test_probe_space_estimator_accepts_string_track_indices(tmp_path):
    from audioknigi.download.probe import ProbeMixin

    class Probe(ProbeMixin):
        runtime_audio_preset = 'copy'
        runtime_normalization_mode = 'off'
        runtime_delete_source = True

        def _book_folder(self, _book, create=False):
            return tmp_path

        def _source_target_assignments(self, _book, source_urls, folder):
            return [(index, url, Path(folder) / f'source-{index}.mp3') for index, url in enumerate(source_urls)]
    track = Track(index=1, title='x', file='https://example/x.mp3', local_status='missing', duration=10)
    track.index = '1'
    book = Book(url='https://example/book', title='book', tracks=[track], remote_size=1000000)
    assert Probe()._estimate_required_space(book, [1]) > 0


# Origin: test_report_followup_round49_20260924.py
class _FallbackHost(SourceAnalysisMixin):
    cancel_event = None
    _book_identity_hints = staticmethod(BookAnalysisService._book_identity_hints)
    _identity_tokens = staticmethod(BookAnalysisService._identity_tokens)

    def _check_cancel(self) -> None:
        return None

def test_resume_guard_rejects_nan_duration() -> None:
    guard = PlayerPositionStore._resume_guard_seconds(float('nan'))
    assert math.isfinite(guard)
    assert guard == 3.0


# Origin: test_report_followup_round5_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_probe_audio_info_uses_container_bitrate_when_stream_bitrate_is_na(monkeypatch, tmp_path):
    import audioknigi.download.media as module
    payload = json.dumps({'streams': [{'codec_name': 'mp3', 'bit_rate': 'N/A', 'sample_rate': '44100', 'channels': 2}], 'format': {'bit_rate': '128000'}})

    class FakeProc:
        returncode = 0
        stdin = stdout = stderr = None

        def communicate(self, timeout=None):
            return (payload, '')

        def poll(self):
            return 0

        def kill(self):
            pass

    class Dummy(MediaProcessingMixin):
        cancel_event = threading.Event()

        def _check_cancel(self):
            pass

        def _register_active_subprocess(self, proc):
            pass

        def _unregister_active_subprocess(self, proc):
            pass
    seen = {}
    monkeypatch.setattr(module, 'resolve_executable', lambda _name: 'ffprobe')

    def fake_popen(cmd, **kwargs):
        seen['cmd'] = cmd
        return FakeProc()
    monkeypatch.setattr(module.subprocess, 'Popen', fake_popen)
    info = Dummy()._probe_audio_info(tmp_path / 'demo.mp3')
    assert info['bit_rate'] == 128000
    assert 'stream=codec_name,bit_rate,sample_rate,channels:format=bit_rate,format_name' in seen['cmd']


# Origin: test_report_followup_round9_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_split_track_infers_next_start_when_current_duration_missing(tmp_path):
    commands = []

    class Dummy(MediaProcessingMixin):
        runtime_normalization_mode = 'off'
        runtime_embed_tags = False

        def _track_path(self, _book, track):
            return tmp_path / f'{track.index}.mp3'

        def _effective_mp3_profile(self, _source):
            return (True, None, None)

        def _run_ffmpeg(self, cmd, timeout=0):
            commands.append(list(cmd))

        def _write_id3(self, *args, **kwargs):
            return None

        def _cached_probe_audio_info(self, _source):
            return {}
    first = Track(index=1, title='One', file='source', start=10, end=None, duration=None)
    second = Track(index=2, title='Two', file='source', start=25, end=None, duration=None)
    book = Book(url='https://example.test', title='Demo', tracks=[first, second])
    source = tmp_path / 'source.mp3'
    source.write_bytes(b'x')
    Dummy()._split_track(book, first, source)
    assert commands
    cmd = commands[0]
    assert '-ss' in cmd and cmd[cmd.index('-ss') + 1] == '10'
    assert '-t' in cmd and float(cmd[cmd.index('-t') + 1]) == pytest.approx(15.0)


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

def test_global_hotkeys_use_window_context_and_cover_all_six_tabs():
    source = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'Qt.ShortcutContext.WindowShortcut' in source
    for sequence in ('Ctrl+L', 'Ctrl+F', 'Ctrl+D', 'Ctrl+Q', 'Ctrl+H', 'Escape'):
        assert f'_add_window_shortcut("{sequence}"' in source
    assert 'f"Alt+{number}"' in source
    assert 'f"Ctrl+{number}"' in source
    assert 'self.TAB_PLAYER' in source


# Origin: test_round61_external_review_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_round61_static_contracts_cover_reported_runtime_regressions():
    source_analysis = (ROOT / 'audioknigi/download/source_analysis.py').read_text(encoding='utf-8')
    book_analysis = (ROOT / 'audioknigi/services/book_analysis_service.py').read_text(encoding='utf-8')
    book_flow = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    probe = (ROOT / 'audioknigi/download/probe.py').read_text(encoding='utf-8')
    player = (ROOT / 'audioknigi/qt/player_mixin.py').read_text(encoding='utf-8')
    analysis_ui = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    assert 'best_by_url' in source_analysis
    assert 'best_by_url' in book_analysis
    assert book_flow.count('req.selected_indices = sorted(active_selected)') >= 3
    assert 'for segment_path in _segment_files(part_target)' in probe
    assert 'starts = [' in probe and 'expected_end = max(starts)' in probe
    assert 'save_app_settings(self.settings)' in player
    assert 'known_paths = {Path(candidate).expanduser().resolve() for candidate in files}' in player
    assert 'self._pending_queue_urls = []' in analysis_ui


# Origin: test_round62_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_probe_accepts_track_objects_as_selected_indices(tmp_path):

    class Harness(ProbeMixin):
        runtime_audio_preset = 'copy'

        def _book_folder(self, _book, *, create=True):
            return tmp_path
    track = Track(index=1, title='One', file='https://example.invalid/1.mp3', local_status=TRACK_STATUS_READY)
    book = Book(url='https://example.invalid/book', title='Book', tracks=[track])
    assert Harness()._estimate_required_space(book, [track]) == 0


# Origin: test_round66_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_unknown_size_and_duration_still_reserve_disk_space(tmp_path):

    class Harness(ProbeMixin):
        runtime_audio_preset = 'copy'

        def _book_folder(self, _book, *, create=True):
            return tmp_path
    track = Track(index=1, title='Unknown', file='https://example.invalid/a.mp3')
    book = Book(url='https://example.invalid/book', title='Book', tracks=[track], remote_size=0)
    required = Harness()._estimate_required_space(book)
    assert required >= 30 * 1024 * 1024


# Origin: test_round69_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_missing_media_source_is_expired_even_without_cause_chain():
    exc = MissingMediaSourceError('media disappeared', source_url='https://cdn.invalid/a.mp3', track_indices=[1])
    assert exc.__cause__ is None
    assert BookFlowMixin._is_expired_media_error(exc) is True


# Origin: test_round70_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_multisource_disk_preflight_scales_to_selected_chapters_without_bookflow_mixin(tmp_path):

    class ProbeOnly(ProbeMixin):
        runtime_audio_preset = 'copy'

        def _book_folder(self, _book, *, create=False):
            return tmp_path
    tracks = [Track(index=index, title=f'Part {index}', file=f'https://cdn.invalid/{index}.mp3', duration=60.0) for index in range(1, 51)]
    book = Book(url='https://example.invalid/book', title='Book', tracks=tracks, remote_size=2000000000)
    required = ProbeOnly()._estimate_required_space(book, [1])
    assert 1000000 < required < 150000000

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


# Origin: test_round73_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_shared_source_timeline_remote_probe_runs_when_local_map_misses_source():
    calls = []

    class Probe(ProbeMixin):

        def _probe_remote_duration(self, source, referer):
            calls.append((source, referer))
            return 120.0
    source = 'https://cdn.invalid/shared.mp3'
    book = Book(url='https://audioknigi.com.ua/audio-1-demo', title='Demo', tracks=[Track(index=1, title='One', file=source, start=0.0), Track(index=2, title='Two', file=source, start=60.0)])
    assert Probe()._shared_source_timeline_issue(book, local_map={}) is None
    assert calls == [(source, book.url)]

def test_split_track_uses_retrying_unlink_before_ffmpeg_overwrite():
    source = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    start = source.index('def _split_track')
    block = source[start:source.index('def _save_book_sidecars', start)]
    assert 'unlink_with_retry(out, missing_ok=True)' in block
    assert 'out.unlink()' not in block

def test_full_mp3_resume_and_id3_hardening_are_present():
    source = (ROOT / 'audioknigi/download_engine.py').read_text(encoding='utf-8')
    run = source[source.index('def run_full_mp3'):source.index('def run(self)')]
    assert 'source_ready = source_target.is_file() and source_target.stat().st_size > 0' in run
    assert 'Использую уже полностью скачанный исходный аудиофайл книги.' in run
    assert 'tags.delall("TRCK")' in run
    assert 'duration_tolerance = max(5.0, min(15.0, float(current_duration) * 0.015))' in source

def test_batch_analysis_errors_continue_and_missing_media_dialog_is_deleted():
    source = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    error_start = source.index('if kind == "error":')
    error_end = source.index('book = payload', error_start)
    error_block = source[error_start:error_end]
    assert 'QTimer.singleShot(0, self._queue_next_dropped_url)' in error_block
    assert 'self._pending_queue_urls = []' not in error_block
    prompt_start = source.index('def _resolve_missing_media')
    prompt_end = source.index('def _download_request_changed', prompt_start)
    assert 'box.deleteLater()' in source[prompt_start:prompt_end]


# Origin: test_round74_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_effective_track_duration_accepts_mapping_tracks():
    assert effective_track_duration({'duration': '12.5'}) == pytest.approx(12.5)
    assert effective_track_duration({'start': '00:01', 'end': '00:06'}) == pytest.approx(5.0)
    assert effective_track_duration({'actual_duration': 7}) == pytest.approx(7.0)

def test_sidecars_tolerate_mapping_track_and_missing_index(tmp_path):

    class Harness(MediaProcessingMixin):
        runtime_save_sidecars = True

        def _cover_bytes(self, _book):
            return None

        def _log_book_flow(self, *_args, **_kwargs):
            pass

        def log(self, text):
            raise AssertionError(text)
    book = Book(url='https://example.invalid/book', title='Demo')
    tracks = [{'index': None, 'title': '', 'start': 0, 'end': 10, 'duration': None}, {'index': '2', 'title': 'Second', 'duration': 5}]
    book.tracks = tracks
    Harness()._save_book_sidecars(book, tmp_path, tracks)
    payload = json.loads((tmp_path / 'metadata.json').read_text(encoding='utf-8'))
    assert payload['tracks'][0]['index'] == 1
    assert payload['tracks'][0]['title'] == 'Часть 01'
    assert payload['tracks'][0]['duration'] == pytest.approx(10.0)
    assert payload['tracks'][1]['index'] == 2

def test_parallel_multisource_split_does_not_race_per_track_status_announcements():
    source = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    assert 'def split_group(source_url, group_tracks, *, announce_track=True):' in source
    assert 'if announce_track:' in source
    assert 'pool.submit(split_group, url, group, announce_track=False)' in source

def test_short_source_fallback_fetches_missing_cover(monkeypatch):
    source = Book(url='https://audioknigi.com.ua/demo', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/shared.mp3', start=0, end=100), Track(index=2, title='Two', file='https://cdn.invalid/shared.mp3', start=100, end=200)])
    fallback = Book(url='https://knigavuhe.org/book/demo', title='Demo', cover_url='https://img.invalid/cover.jpg', tracks=[Track(index=1, title='One', file='https://cdn.invalid/one.mp3')])
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=True, fetch_remote_size=False))
    monkeypatch.setattr(service, '_probe_remote_duration', lambda *_args, **_kwargs: 50.0)
    monkeypatch.setattr(service, '_knigavuhe_fallback_candidate', lambda _book: fallback)
    monkeypatch.setattr(service, '_populate_missing_track_durations', lambda _book: None)
    monkeypatch.setattr(service, '_fetch_cover_bytes', lambda *_args, **_kwargs: (b'cover', 'image/jpeg'))
    recovered = service._recover_short_audioknigi_source(source)
    assert recovered is fallback
    assert recovered.cover_cache == (b'cover', 'image/jpeg')


# Origin: test_round75_external_review_followup_20261003.py
ROOT = Path(__file__).resolve().parents[2]

def test_invalid_explicit_split_boundary_is_diagnosable_without_changing_fallback_behavior():
    source = (ROOT / 'audioknigi/download/media.py').read_text(encoding='utf-8')
    block = source[source.index('def _split_track'):source.index('def _save_book_sidecars')]
    assert 'event=split_invalid_explicit_boundary' in block
    assert 'end <= start' in block


# Origin: test_round77_external_review_followup_20261004.py
ROOT = Path(__file__).resolve().parents[2]

def test_display_track_timeline_accepts_mapping_tracks():
    rows = display_track_timeline([{'start': 10, 'end': 20, 'duration': None}, {'duration': 5}])
    assert rows[0] == (10.0, 20.0, 10.0)
    assert rows[1] == (20.0, 25.0, 5.0)

def test_cover_fetch_rejects_explicit_non_image_content_type(monkeypatch):

    class Response:
        headers = {'content-type': 'text/html; charset=utf-8'}

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=0):
            return iter([b'<html>challenge</html>'])

        def close(self):
            return None

    class Session:

        def get(self, *args, **kwargs):
            return Response()
    monkeypatch.setattr(cover_fetch, 'get_http_session', Session)
    assert cover_fetch.fetch_cover_bytes('https://example.invalid/cover.jpg') is None


# Origin: test_round78_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_sidecars_preserve_zero_index_and_unknown_timeline(tmp_path):

    class Harness(MediaProcessingMixin):
        runtime_save_sidecars = True

        def _cover_bytes(self, _book):
            return None

        def _log_book_flow(self, *_args, **_kwargs):
            pass

        def log(self, text):
            raise AssertionError(text)
    book = Book(url='https://example.invalid/book', title='Demo')
    tracks = [Track(index=0, title='Prologue', file='x', duration=None), Track(index=1, title='Chapter', file='y', duration=5)]
    book.tracks = tracks
    Harness()._save_book_sidecars(book, tmp_path, tracks)
    payload = json.loads((tmp_path / 'metadata.json').read_text(encoding='utf-8'))
    assert payload['tracks'][0]['index'] == 0
    assert payload['tracks'][0]['timeline_start'] == 0.0
    assert payload['tracks'][0]['timeline_end'] is None
    assert payload['tracks'][1]['timeline_start'] is None
    info = (tmp_path / 'book_info.txt').read_text(encoding='utf-8')
    assert '00. 00:00:00–—  Prologue' in info
    assert '01. —–—  Chapter' in info


# Origin: test_round79_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_expired_media_indices_accept_mapping_tracks():
    exc = MissingMediaSourceError('gone', source_url='https://cdn.invalid/a.mp3')
    book = SimpleNamespace(tracks=[{'index': '0', 'file': 'https://cdn.invalid/a.mp3', 'fallback_file': ''}, {'index': '1', 'file': 'https://cdn.invalid/b.mp3', 'fallback_file': ''}])
    assert BookFlowMixin._expired_media_track_indices(exc, book, {0, 1}) == [0]

def test_cover_fetch_rejects_oversized_declared_length_before_streaming(monkeypatch):

    class Response:
        headers = {'content-length': str(cover_fetch._MAX_COVER_BYTES + 1), 'content-type': 'image/jpeg'}
        iterated = False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=0):
            self.iterated = True
            yield b'should-not-read'

        def close(self):
            pass
    response = Response()

    class Session:

        def get(self, *args, **kwargs):
            return response
    monkeypatch.setattr(cover_fetch, 'get_http_session', lambda: Session())
    assert cover_fetch.fetch_cover_bytes('https://example.invalid/huge.jpg') is None
    assert response.iterated is False


# Origin: test_round80_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_headless_missing_media_callback_filters_bool_and_malformed_indices():
    captured = []

    def callback(indices, detail, allow_skip):
        captured.append((indices, detail, allow_skip))
        return 'skip'
    dummy = SimpleNamespace(callbacks=SimpleNamespace(missing_media=callback))
    decision = _DownloadEngine._ask_missing_media_action(dummy, [True, False, '3', 'bad', -1, 0, 2], detail='expired', allow_skip=True)
    assert decision == 'skip'
    assert captured == [([0, 2, 3], 'expired', True)]

def test_probe_strict_selection_validation_is_an_intentional_disk_space_guard():
    from audioknigi.download.probe import ProbeMixin
    book = Book(url='https://example.invalid/book', title='Book')
    with pytest.raises(ValueError, match='Invalid selected track index'):
        ProbeMixin()._estimate_required_space(book, [True])
    with pytest.raises(ValueError, match='Invalid selected track index'):
        ProbeMixin()._estimate_required_space(book, [1.5])


# Origin: test_round81_external_review_followup_20261006.py
ROOT = Path(__file__).resolve().parents[2]

def test_probe_space_estimation_accepts_mapping_selection_and_mapping_tracks(tmp_path):

    class Harness(ProbeMixin):

        def _book_folder(self, *_args, **_kwargs):
            return tmp_path
    book = Book(url='https://example.invalid/book', title='Book', remote_size=20 * 1024 * 1024)
    book.tracks = [{'index': 0, 'title': 'Zero', 'file': 'https://cdn.invalid/0.mp3', 'duration': 10, 'local_status': 'missing'}, {'index': 1, 'title': 'One', 'file': 'https://cdn.invalid/1.mp3', 'duration': 20, 'local_status': 'missing'}]
    probe = Harness()
    one = probe._estimate_required_space(book, [{'index': 0}])
    all_space = probe._estimate_required_space(book)
    assert one > 0
    assert all_space >= one


# Origin: test_runtime_followup_round7_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_loudnorm_parser_uses_bounded_tail_and_finds_latest_json(monkeypatch):
    import audioknigi.download.media as media_module
    stats = '{"input_i":"-24.5","input_lra":"4.0","input_tp":"-2.0","input_thresh":"-34.0","target_offset":"0.1"}'

    class Dummy(MediaProcessingMixin):

        def _run_ffmpeg_capture(self, cmd, timeout=0):
            return 'diagnostic { not-json } ' * 10000 + '\n' + stats
    monkeypatch.setattr(media_module, 'resolve_executable', lambda _name: 'ffmpeg')
    value = Dummy()._measure_loudnorm('source.mp3', start=0, duration=1)
    assert 'measured_I=-24.5' in value
    assert 'offset=0.1' in value

def test_two_pass_normalization_disables_parallel_single_source_split():
    source = (ROOT / 'audioknigi' / 'download' / 'book_flow.py').read_text(encoding='utf-8')
    assert 'safe_normalization_mode(getattr(self, "runtime_normalization_mode", "off"), "off") != "two_pass"' in source


# Origin: test_runtime_integrity_followup_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_split_module_name_regressions_are_guarded_in_ci():
    ci = (ROOT / '.github' / 'workflows' / 'ci.yml').read_text(encoding='utf-8')
    release = (ROOT / '.github' / 'workflows' / 'release.yml').read_text(encoding='utf-8')
    assert 'undefined_global_audit.py' in ci
    assert 'undefined_global_audit.py' in release


# Origin: test_stability_localization_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_ffmpeg_workers_never_inherit_parent_stdin():
    source = (ROOT / 'audioknigi' / 'download' / 'media.py').read_text(encoding='utf-8')
    run_block = source[source.index('def _run_ffmpeg('):source.index('def _probe_audio_info(')]
    assert run_block.count('stdin=subprocess.DEVNULL') >= 2
    loudnorm = source[source.index('def _measure_loudnorm('):source.index('def _normalization_filter_for_track(')]
    assert '"-nostdin"' in loudnorm

def test_parallel_split_reports_progress_inside_same_lock():
    source = (ROOT / 'audioknigi' / 'download' / 'book_flow.py').read_text(encoding='utf-8')
    block = source[source.index('def split_one(tr):'):source.index('with ThreadPoolExecutor(max_workers=2)')]
    lock_pos = block.index('with progress_lock:')
    stage_pos = block.index('self.set_stage(3, split_text)')
    report_pos = block.index('report(split_text)')
    lines = block[lock_pos:report_pos].splitlines()
    lock_indent = len(lines[0]) - len(lines[0].lstrip())
    stage_line = next((line for line in lines if 'self.set_stage(3, split_text)' in line))
    report_line = next((line for line in block[lock_pos:].splitlines() if 'report(split_text)' in line))
    assert len(stage_line) - len(stage_line.lstrip()) > lock_indent
    assert len(report_line) - len(report_line.lstrip()) > lock_indent

# Post-consolidation: Round 85 external audit follow-up.
def test_probe_audio_info_cancellation_kills_and_reaps_ffprobe(monkeypatch):
    import audioknigi.download.media as media_module

    calls = []

    class Stream:
        def close(self):
            calls.append("close")

    class Proc:
        def __init__(self):
            self.returncode = None
            self.stdin = None
            self.stdout = Stream()
            self.stderr = None

        def poll(self):
            return self.returncode

        def kill(self):
            calls.append("kill")

        def communicate(self, timeout=None):
            calls.append(("communicate", timeout))
            self.returncode = -9
            return "", ""

    proc = Proc()
    monkeypatch.setattr(media_module, "resolve_executable", lambda _name: "ffprobe")
    monkeypatch.setattr(media_module.subprocess, "Popen", lambda *_args, **_kwargs: proc)

    class Harness(MediaProcessingMixin):
        def _register_active_subprocess(self, _proc):
            calls.append("register")

        def _unregister_active_subprocess(self, _proc):
            calls.append("unregister")

        def _check_cancel(self):
            raise Cancelled()

    with pytest.raises(Cancelled):
        Harness()._probe_audio_info("book.mp3")

    assert "kill" in calls
    assert any(isinstance(item, tuple) and item[0] == "communicate" for item in calls)
    assert "unregister" in calls
    assert "close" in calls


def test_loudnorm_parser_skips_trailing_non_json_brace_after_valid_stats(monkeypatch):
    import audioknigi.download.media as media_module

    stats = '{"input_i":"-23.0","input_lra":"3.5","input_tp":"-1.2","input_thresh":"-33.0","target_offset":"0.2"}'

    class Dummy(MediaProcessingMixin):
        def _run_ffmpeg_capture(self, _cmd, timeout=0):
            return stats + "\n[ffmpeg summary] trailing {not-json"

    monkeypatch.setattr(media_module, "resolve_executable", lambda _name: "ffmpeg")
    value = Dummy()._measure_loudnorm("source.mp3")
    assert "measured_I=-23.0" in value
    assert "offset=0.2" in value
