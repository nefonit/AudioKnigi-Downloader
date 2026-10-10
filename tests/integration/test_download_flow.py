"""Consolidated integration tests for the download flow domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


import threading
from pathlib import Path
import pytest
from audioknigi.core import Cancelled
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _extract_call_argument, _usable_search_title
from audioknigi.models import Book, SearchResult, Track
from audioknigi.poleknig import _discover_narration_variants
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.services.download_request import DownloadRequest
import base64
from types import SimpleNamespace
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.common import atomic_write_text
from audioknigi.i18n import localize_runtime_text
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.queue_service import task_from_dict
from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, migrate_ui_scale_settings
from audioknigi.i18n import _normalize_runtime_regex_catalog
from audioknigi.services.search_service import search_all_sources
from audioknigi.sources import is_supported_url, normalize_supported_url
from audioknigi import poleknig
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.services import book_analysis_service as analysis_module
from audioknigi.models import Book, SearchResult
import inspect
import socket
from audioknigi import core, poleknig
from audioknigi.download_engine import _DownloadEngine
from audioknigi.network_dns import _relay_bidirectional
import json
from audioknigi import core
from audioknigi.config.settings import save_app_settings
from audioknigi.core import load_json
from audioknigi.services.library_service import scan_unfinished
from audioknigi.core import fmt_size
from audioknigi.models import Book, Track
from audioknigi.templates import render_text_template
from audioknigi.config.settings import migrate_settings
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
import sys
from types import ModuleType, SimpleNamespace
import audioknigi.config.settings as settings_module
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round52_20260924
from audioknigi.services.download_request import DownloadRequest, build_download_request
from audioknigi.brand import version_label
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
import subprocess
from audioknigi.download.errors import MissingMediaSourceError
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.models import SearchResult
from audioknigi.providers import audioknigi_search
from audioknigi.download.probe import ProbeMixin
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, _DownloadEngine
from audioknigi.services.player_position_store import PlayerPositionStore
from audioknigi.download.errors import SharedSourceTimelineError
from audioknigi.services.search_service import downloadable_search_results, search_result_sort_key
from audioknigi.core import effective_track_duration
from audioknigi.models import Book, NarrationVariant, Track
from audioknigi import cover_fetch
from audioknigi.core import display_track_timeline
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services.queue_service import _book_from_dict
from audioknigi.templates import _safe_track_index
from audioknigi.core import SiteStructureChanged
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.knigavuhe import parse_book_html
from audioknigi.download.common import source_target_assignments
from audioknigi.models import Book
from audioknigi.services import source_health_service
from audioknigi.download import network as network_module
from audioknigi.download import source_analysis as source_analysis_module
from audioknigi.download.source_analysis import SourceAnalysisMixin
from threading import Event
from audioknigi.download_engine import DownloadService
from audioknigi.i18n import tr
from audioknigi.providers.audioknigi_search import search_audioknigi
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict
from audioknigi.download.network import SlidingSpeedMeter
from audioknigi.models import Book, SearchResult, TRACK_STATUS_DAMAGED, TRACK_STATUS_MISSING, TRACK_STATUS_PRESENT, TRACK_STATUS_READY, normalize_track_status
from audioknigi.services.queue_service import _parse_selected_indices_payload
import types
from audioknigi.diagnostics import support_bundle as support_bundle__runtime_integrity_followup_20260912
from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.sources import normalize_supported_url
import ast
import os
import re
import zipfile
from audioknigi.diagnostics import support_bundle as support_bundle__structured_hardening_20260912
from audioknigi.knigavuhe import _merge_narration_variants
from audioknigi.models import NarrationVariant, SearchResult, Track, TRACK_STATUS_MISSING
from audioknigi.services import search_service
from audioknigi.providers import provider_for_key


# Origin: test_report_followup_round10_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_download_request_exposes_public_track_index_and_keeps_compat_alias():
    track = Track(index='7', title='x', file='https://example.invalid/7.mp3')
    assert DownloadRequest.track_index(track) == 7
    assert DownloadRequest._track_index(track) == 7

class _Response:
    text = '<html><head><title>Тестовая книга</title></head><body>Исполнитель: Иван Иванов, Жанр: Фантастика</body></html>'

    def raise_for_status(self):
        return None

class _Session:

    def get(self, *args, **kwargs):
        return _Response()


# Origin: test_report_followup_round15_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_stale_source_cleanup_removes_only_engine_owned_artifacts(tmp_path):
    owned = [tmp_path / '_source.mp3', tmp_path / '_source_01.mp3.part', tmp_path / '_source_02.mp3.part.seg000', tmp_path / '_repair_source_01.mp3.part.segments.json']
    keep = [tmp_path / '_source of wisdom.mp3', tmp_path / '_source_notes.mp3', tmp_path / 'normal.mp3']
    for item in [*owned, *keep]:
        item.write_bytes(b'x')

    class Flow(BookFlowMixin):

        def _book_folder(self, _book, create=False):
            assert create is False
            return tmp_path

        def log(self, _message):
            pass
    removed = Flow()._clear_stale_source_downloads(SimpleNamespace())
    assert removed == len(owned)
    assert all((not item.exists() for item in owned))
    assert all((item.exists() for item in keep))


# Origin: test_report_followup_round17_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_download_request_track_index_accepts_raw_scalars_mappings_and_tracks() -> None:
    assert DownloadRequest.track_index(3) == 3
    assert DownloadRequest.track_index('04') == 4
    assert DownloadRequest.track_index({'index': '5'}) == 5
    assert DownloadRequest.track_index(SimpleNamespace(index='06')) == 6
    with pytest.raises(ValueError):
        DownloadRequest.track_index('intro')


# Origin: test_report_followup_round19_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_round19_full_mp3_uses_whole_book_selection_contract() -> None:
    source = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    block = source.split('def start_full_mp3', 1)[1].split('def ', 1)[0]
    assert 'build_download_request(self.current_book, live_settings, None)' in block
    assert '[DownloadRequest.track_index(track)' not in block


# Origin: test_report_followup_round22_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_delete_existing_outputs_uses_download_request_track_index_for_mappings(tmp_path) -> None:
    target = tmp_path / '003.mp3'
    target.write_bytes(b'old')
    book = SimpleNamespace(tracks=[{'index': '3'}])
    request = DownloadRequest(book=book, selected_indices=[3], output_dir=tmp_path)
    engine = object.__new__(_DownloadEngine)
    engine.request = request
    engine._track_path = lambda *_a, **_k: target
    assert engine.delete_existing_outputs() == 1
    assert not target.exists()

def test_book_flow_counts_only_sources_that_really_existed() -> None:
    source = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    block = source[source.index('removed_sources = 0'):source.index('self._log_book_flow("source_cleanup"')]
    assert 'unlink_with_retry(path, missing_ok=False)' in block
    assert 'except FileNotFoundError:' in block


# Origin: test_report_followup_round27_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def _source__report_followup_round27_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_download_worker_never_calls_gui_handlers_directly_from_worker_thread() -> None:
    source = _source__report_followup_round27_20260918('audioknigi/qt/mixins/analysis_download.py')
    relay_slots = ('download_status', 'download_log', 'download_stage', 'download_progress', 'download_transfer', 'download_missing_media', 'download_history_changed', 'download_request_changed', 'download_finished')
    for slot in relay_slots:
        assert f'connect(self._worker_ui_relay.{slot}, Qt.ConnectionType.QueuedConnection)' in source
    assert 'thread.finished.connect(self._worker_ui_relay.download_thread_finished, Qt.ConnectionType.QueuedConnection)' in source


# Origin: test_report_followup_round28_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def _source__report_followup_round28_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_analysis_download_and_abs_callbacks_all_use_relay() -> None:
    analysis = _source__report_followup_round28_20260918('audioknigi/qt/mixins/analysis_download.py')
    settings = _source__report_followup_round28_20260918('audioknigi/qt/mixins/settings.py')
    for slot in ('analysis_progress', 'analysis_finished', 'analysis_thread_finished', 'download_status', 'download_log', 'download_stage', 'download_progress', 'download_transfer', 'download_missing_media', 'download_history_changed', 'download_request_changed', 'download_finished', 'download_thread_finished'):
        assert f'self._worker_ui_relay.{slot}' in analysis
    assert 'self._worker_ui_relay.audiobookshelf_finished' in settings
    assert 'self._worker_ui_relay.audiobookshelf_thread_finished' in settings


# Origin: test_report_followup_round2_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_download_request_reports_invalid_track_index_cleanly(tmp_path):
    book = Book(url='https://example.invalid', title='Book', tracks=[Track(index=None, title='x', file='x')])
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    with pytest.raises(ValueError, match='Некорректный индекс части'):
        request.validate()


# Origin: test_report_followup_round33_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round33_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_download_request_track_index_already_accepts_objects_and_scalars() -> None:
    track = Track(index=7, title='x', file='u')
    assert DownloadRequest.track_index(track) == 7
    assert DownloadRequest.track_index(7) == 7
    assert DownloadRequest.track_index('7') == 7

def test_disk_space_proportional_recommendation_is_intentionally_not_applied_to_shared_source() -> None:
    source = src__report_followup_round33_20260918('audioknigi/services/book_analysis_service.py')
    probe = src__report_followup_round33_20260918('audioknigi/download/probe.py')
    assert 'if self.options.fetch_remote_size and len(unique_files) == 1:' in source
    assert 'remote_size * (missing_duration / total_duration)' not in probe[probe.index('source_remaining = 0'):probe.index('outputs = 0')]


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_full_mp3_retained_source_suffix_uses_container_and_codec() -> None:
    assert _DownloadEngine._retained_source_suffix('https://x/source', {'codec': 'mp3'}) == '.mp3'
    assert _DownloadEngine._retained_source_suffix('https://x/source', {'codec': 'aac', 'format_name': 'mov,mp4,m4a,3gp,3g2,mj2'}) == '.m4a'
    assert _DownloadEngine._retained_source_suffix('https://x/source', {'codec': 'flac'}) == '.flac'
    assert _DownloadEngine._retained_source_suffix('https://x/source.ogg', {'codec': 'vorbis'}) == '.ogg'


# Origin: test_report_followup_round52_20260924.py
def test_download_request_rejects_boolean_track_indices(tmp_path: Path) -> None:
    book = Book(url='https://example.invalid/book', title='Book', tracks=[Track(index=1, title='One', file='https://example.invalid/1.mp3')])
    with pytest.raises(ValueError, match='Некорректный индекс части'):
        DownloadRequest.track_index(True)
    with pytest.raises(ValueError, match='Некорректный индекс части'):
        build_download_request(book, {'output_dir': str(tmp_path)}, [True])

def test_book_flow_skips_malformed_internal_track_indices() -> None:
    captured = {}

    class Flow(BookFlowMixin):

        def _process_book_once(self, _book, selected_indices=None, status_callback=None):
            captured['selected'] = set(selected_indices or set())
            return 'ok'
    book = SimpleNamespace(tracks=[SimpleNamespace(index=1), SimpleNamespace(index='2'), SimpleNamespace(index=None), SimpleNamespace(index='bad'), SimpleNamespace(index=True)])
    assert Flow()._process_book(book) == 'ok'
    assert captured['selected'] == {1, 2}


# Origin: test_report_followup_round5_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_full_mp3_copy_mode_retains_source_when_delete_source_is_false(monkeypatch, tmp_path):
    book = Book(url='https://audioknigi.com.ua/book/1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.example/demo.mp3')], remote_size=4)
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    engine = _DownloadEngine(request, {'delete_source': False, 'embed_tags': False, 'save_sidecars': False, 'audio_preset': 'copy'}, threading.Event(), DownloadCallbacks())
    monkeypatch.setattr(engine, '_write_resume_manifest', lambda *a, **k: None)
    monkeypatch.setattr(engine, '_book_folder', lambda _book, create=True: tmp_path)
    monkeypatch.setattr(engine, '_full_mp3_target', lambda _book, _folder: tmp_path / 'Demo.mp3')
    monkeypatch.setattr(engine, '_disk_free_for_path', lambda _path: 10 ** 9)
    monkeypatch.setattr(engine, 'set_stage', lambda *a, **k: None)
    monkeypatch.setattr(engine, 'set_status', lambda *a, **k: None)
    monkeypatch.setattr(engine, 'set_progress', lambda *a, **k: None)
    monkeypatch.setattr(engine, '_download_source_with_fallback', lambda _url, _fallback, target, _referer: Path(target).write_bytes(b'mp3data'))
    monkeypatch.setattr(engine, '_cached_probe_audio_info', lambda _path: {'codec': 'mp3', 'bit_rate': 128000})
    monkeypatch.setattr(engine, '_effective_mp3_profile', lambda _path: (True, None, None))
    monkeypatch.setattr(engine, '_save_book_sidecars', lambda *a, **k: None)
    monkeypatch.setattr(engine, '_scan_audiobookshelf_after_book', lambda *a, **k: None)
    monkeypatch.setattr(engine, '_add_history', lambda *a, **k: None)
    monkeypatch.setattr(engine, '_remove_resume_manifest', lambda *a, **k: None)
    result = engine.run_full_mp3()
    assert result.target_file == tmp_path / 'Demo.mp3'
    assert (tmp_path / 'Demo.mp3').read_bytes() == b'mp3data'
    assert (tmp_path / 'Demo (исходник).mp3').read_bytes() == b'mp3data'


# Origin: test_round4_circular_import_20260915.py
def test_download_package_keeps_source_analysis_mixin_public_export():
    from audioknigi.download import SourceAnalysisMixin
    from audioknigi.download.source_analysis import SourceAnalysisMixin as DirectMixin
    assert SourceAnalysisMixin is DirectMixin


# Origin: test_round69_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_fallback_download_skips_empty_primary_and_uses_fallback_once(tmp_path):

    class Harness(NetworkDownloadMixin):
        cancel_event = threading.Event()

        def __init__(self):
            self.calls = []

        def _download_with_resume(self, url, target, referer):
            self.calls.append((url, Path(target), referer))
            return Path(target)

        def log(self, _text):
            pass
    target = tmp_path / 'source.mp3'
    harness = Harness()
    result = harness._download_source_with_fallback('', ' https://cdn.invalid/fallback.mp3 ', target, 'ref')
    assert result == target
    assert [item[0] for item in harness.calls] == ['https://cdn.invalid/fallback.mp3']


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

def test_full_mp3_reports_and_persists_all_processed_indices(tmp_path):
    engine = _full_mp3_engine(tmp_path, selected=[1])
    result = engine.run_full_mp3()
    assert isinstance(result, DownloadResult)
    assert result.selected_indices == [1, 2]
    assert engine.request.selected_indices == [1, 2]

def test_full_mp3_duplicate_preflight_treats_stat_race_as_missing(tmp_path):
    engine = _full_mp3_engine(tmp_path, selected=[1])

    class FlakyTarget:

        def is_file(self):
            return True

        def stat(self):
            raise OSError('file disappeared')
    engine._book_folder = lambda *_args, **_kwargs: tmp_path
    engine._full_mp3_target = lambda *_args, **_kwargs: FlakyTarget()
    result = engine.duplicate_preflight(full_mp3=True)
    assert isinstance(result, DuplicatePreflight)
    assert result.exact_duplicate is False
    assert result.evidence == 'full-mp3-missing'


# Origin: test_round71_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_primary_download_rejects_zero_track_book_explicitly():
    source = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    start = source.index('def _start_primary_download')
    end = source.index('def _update_download_primary_button', start)
    block = source[start:end]
    assert 'len(list(getattr(self.current_book, "tracks", None) or []))' in block
    assert 'if total <= 0 or selected <= 0:' in block


# Origin: test_round72_search_sorting_availability_layout_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def _result(title: str, *, author: str='', narrator: str='', availability: str='') -> SearchResult:
    return SearchResult(title=title, author=author, narrator=narrator, availability=availability, url=f'https://example.invalid/{title}', source='demo')

def test_book_download_layout_reserves_graph_and_description_geometry():
    pages = (ROOT / 'audioknigi/qt/main_window_pages.py').read_text(encoding='utf-8')
    graph = (ROOT / 'audioknigi/qt/speed_graph.py').read_text(encoding='utf-8')
    assert 'self.download_activity_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)' in pages
    assert 'self.book_details_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)' in pages
    assert 'self.book_description.setMaximumHeight(72)' in pages
    assert 'self.book_description.setMinimumHeight(52)' in pages
    assert 'self._expanded_height = 56' in graph


# Origin: test_round74_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_full_mp3_refresh_updates_manifest_and_result_indices():
    source = (ROOT / 'audioknigi/download_engine.py').read_text(encoding='utf-8')
    block = source[source.index('def run_full_mp3'):source.index('def run(self)')]
    assert 'full_indices = list(req.selected_indices)' in block
    assert 'self._write_resume_manifest(book, full_indices, download_mode="full_mp3")' in block
    assert 'selected_indices=list(getattr(self.request, "selected_indices", None) or full_indices)' in block

def test_track_model_source_uses_safe_selected_indices_without_importing_qt():
    source = (ROOT / 'audioknigi/qt/track_model.py').read_text(encoding='utf-8')
    block = source[source.index('def selected_indices'):source.index('def selected_count')]
    assert 'self._safe_track_index(track, row)' in block
    assert 'int(track.index)' not in block


# Origin: test_round77_external_review_followup_20261004.py
ROOT = Path(__file__).resolve().parents[2]

def test_book_flow_remaining_track_index_paths_are_safe():
    source = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    assert 'affected_tracks = [int(tr.index)' not in source
    assert 'track_indices=[int(tr.index)]' not in source
    assert 'safe_int(getattr(tr, "index", None), -1)' in source


# Origin: test_round79_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_download_engine_uses_retrying_unlink_for_manifest_and_full_source():
    source = (ROOT / 'audioknigi/download_engine.py').read_text(encoding='utf-8')
    manifest = source[source.index('def _remove_resume_manifest'):source.index('@staticmethod', source.index('def _remove_resume_manifest'))]
    assert 'unlink_with_retry(path, missing_ok=True)' in manifest
    full = source[source.index('def run_full_mp3'):source.index('def run(self)')]
    assert 'unlink_with_retry(source_target, missing_ok=True)' in full
    assert 'source_target.unlink(missing_ok=True)' not in full


# Origin: test_round81_external_review_followup_20261006.py
ROOT = Path(__file__).resolve().parents[2]

def test_source_target_assignments_preserve_mapping_track_slots(tmp_path):
    book = SimpleNamespace(tracks=[{'file': 'https://cdn.invalid/a.mp3'}, {'file': 'https://cdn.invalid/b.mp3'}])
    rows = source_target_assignments(book, ['https://cdn.invalid/b.mp3'], tmp_path)
    assert rows[0][0] == 2
    assert rows[0][2].name == '_source_02.mp3'

def test_book_flow_only_calls_ui_when_dispatcher_is_callable():
    source = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    assert source.count('callable(getattr(self, "ui", None))') >= 2
    assert 'hasattr(self, "ui") and hasattr(self, "_refresh_book_timing_ui")' not in source


# Origin: test_runtime_contract_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def _book() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3'), Track(index=2, title='Two', file='https://cdn.invalid/2.mp3')])

def test_duplicate_preflight_treats_none_as_full_selection(tmp_path):
    request = DownloadRequest(book=_book(), selected_indices=None, output_dir=tmp_path)
    result = DownloadService().duplicate_preflight(request, probe_durations=False)
    assert result.evidence == 'files-incomplete'


# Origin: test_runtime_followup_round7_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_restricted_book_gets_specific_download_validation_error(tmp_path):
    request = DownloadRequest(book=Book(url='https://example.test/book', title='Blocked', restricted=True, tracks=[]), selected_indices=None, output_dir=tmp_path)
    with pytest.raises(ValueError, match='ограничению правообладателя'):
        request.validate()


# Origin: test_runtime_integrity_followup_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_none_selected_indices_means_whole_book(tmp_path):
    book = Book(url='https://audioknigi.com.ua/audio-1', title='Book', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3')])
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    request.validate()
    assert request.resolved_selected_indices() == [1]
    result = DownloadService().duplicate_preflight(request, probe_durations=False)
    assert result.exact_duplicate is False
    assert result.evidence == 'files-incomplete'

def test_disk_preflight_does_not_create_book_folder(tmp_path):
    host = DownloaderMixin()
    host.runtime_output_dir = tmp_path
    book = Book(url='https://audioknigi.com.ua/audio-1', title='Must Not Exist Yet', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3')], remote_size=0)
    expected = host._book_folder(book, create=False)
    assert not expected.exists()
    host._estimate_required_space(book, [1])
    host._disk_space_info(book, [1])
    assert not expected.exists()


# Origin: test_structured_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_download_book_info_uses_dynamic_track_number_width():
    source = (ROOT / 'audioknigi' / 'download' / 'media.py').read_text(encoding='utf-8')
    assert 'width = track_number_width(book)' in source
    assert "{row['index']:0{width}d}" in source

# Post-consolidation: Round 83 external audit follow-up.
def test_download_errors_filter_boolean_malformed_and_negative_indices():
    from audioknigi.download.errors import MissingMediaSourceError, MissingSelectedTracksError

    media = MissingMediaSourceError('missing', track_indices=[True, False, None, '3', 'bad', -1, 0, 2])
    selected = MissingSelectedTracksError([True, False, None, '3', 'bad', -1, 0, 2])
    assert media.track_indices == [0, 2, 3]
    assert selected.track_indices == [0, 2, 3]


def test_full_mp3_custom_track_number_prefix_is_removed(tmp_path):
    engine = _DownloadEngine.__new__(_DownloadEngine)
    engine.runtime_use_templates = True
    engine.runtime_track_template = '{Track_Number} - {Track_Title}.mp3'
    engine.runtime_language = 'en'
    book = Book(url='https://example.test/book', title='My Book', tracks=[Track(index=1, title='One', file='x')])
    assert engine._full_mp3_target(book, tmp_path).name == 'My Book.mp3'


def test_full_mp3_failed_retained_copy_removes_partial_target_but_keeps_source(monkeypatch, tmp_path):
    import audioknigi.download_engine as download_engine_module

    book = Book(
        url='https://audioknigi.com.ua/book/1',
        title='Demo',
        tracks=[Track(index=1, title='One', file='https://cdn.example/demo.mp3')],
        remote_size=8,
    )
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    engine = _DownloadEngine(
        request,
        {'delete_source': False, 'embed_tags': False, 'save_sidecars': False, 'audio_preset': 'copy'},
        threading.Event(),
        DownloadCallbacks(),
    )
    monkeypatch.setattr(engine, '_write_resume_manifest', lambda *a, **k: None)
    monkeypatch.setattr(engine, '_book_folder', lambda _book, create=True: tmp_path)
    monkeypatch.setattr(engine, '_disk_free_for_path', lambda _path: 10 ** 9)
    monkeypatch.setattr(engine, 'set_stage', lambda *a, **k: None)
    monkeypatch.setattr(engine, 'set_status', lambda *a, **k: None)
    monkeypatch.setattr(engine, 'set_progress', lambda *a, **k: None)
    monkeypatch.setattr(engine, '_download_source_with_fallback', lambda _url, _fallback, target, _referer: Path(target).write_bytes(b'complete-source'))
    monkeypatch.setattr(engine, '_cached_probe_audio_info', lambda _path: {'codec': 'mp3', 'bit_rate': 128000})
    monkeypatch.setattr(engine, '_effective_mp3_profile', lambda _path: (True, None, None))

    real_copy2 = download_engine_module.shutil.copy2

    def failing_copy(source, target, *args, **kwargs):
        Path(target).write_bytes(b'partial')
        raise OSError('disk full')

    monkeypatch.setattr(download_engine_module.shutil, 'copy2', failing_copy)
    with pytest.raises(OSError, match='disk full'):
        engine.run_full_mp3()

    target = tmp_path / 'Demo.mp3'
    source_target = tmp_path / '.Demo.full-source'
    assert not target.exists()
    assert source_target.read_bytes() == b'complete-source'
    monkeypatch.setattr(download_engine_module.shutil, 'copy2', real_copy2)
