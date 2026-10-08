"""Consolidated integration tests for the settings domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import threading
import time
from audioknigi.config import settings as settings_module__persistence_cancellation_hardening_20260929
from audioknigi.core import Cancelled
from audioknigi.models import Book, Track
from audioknigi.providers import audioknigi_search
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.library_service import scan_unfinished
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict
from audioknigi.services import search_service
import csv
import zipfile
from audioknigi.config.settings import migrate_settings
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.download.network import _segment_files
from audioknigi.models import SearchResult
import audioknigi.poleknig as poleknig__report_followup_round14_20260916
import base64
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.common import atomic_write_text
from audioknigi.i18n import localize_runtime_text
from audioknigi.services.queue_service import task_from_dict
from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, migrate_ui_scale_settings
from audioknigi.i18n import _normalize_runtime_regex_catalog
from audioknigi.services.search_service import search_all_sources
from audioknigi import knigavuhe as knigavuhe__report_followup_round20_20260917, poleknig as poleknig__report_followup_round20_20260917
from audioknigi.core import fmt_eta, parse_time_seconds
from audioknigi.download.probe import ProbeMixin
from audioknigi.models import Book, SearchResult
from audioknigi.providers import audioknigi_search as search_module
from audioknigi.services.queue_service import _parse_selected_indices_payload
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.providers.audioknigi_search import _canonical_title
from audioknigi.services.book_analysis_service import _playlist_track_title
from audioknigi import core as core__report_followup_round2_20260915
from audioknigi.config.settings import save_app_settings
from audioknigi.core import load_json
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.models import Book, SearchResult, Track
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.download_engine import _DownloadEngine
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi import core as core__report_followup_round3_20260915
from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.download_engine import DownloadService, _DownloadEngine
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
import audioknigi.config.settings as settings_module__report_followup_round43_20260920
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round43_20260920
import audioknigi.download.network as network_module
import audioknigi.knigavuhe as knigavuhe__report_followup_round43_20260920
import audioknigi.poleknig as poleknig__report_followup_round43_20260920
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata, _merge_author_names
import audioknigi.config.settings as settings_module__report_followup_round44_20260920
import audioknigi.core as core__report_followup_round44_20260920
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round44_20260920
import audioknigi.services.player_position_store as position_module
from audioknigi.models import Book
from audioknigi.providers.audioknigi_search import _matches_query, _response_html_text, parse_audioknigi_results
from audioknigi.services.player_position_store import PlayerPositionStore
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
import sys
from types import ModuleType, SimpleNamespace
import audioknigi.config.settings as settings_module__report_followup_round52_20260924
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round52_20260924
from audioknigi.services.download_request import DownloadRequest, build_download_request
from audioknigi.core import load_browser_context_profile
from audioknigi.network_dns import _parse_proxy_authority
from audioknigi.providers.audioknigi_search import _split_audioknigi_title
from dataclasses import dataclass
from audioknigi.core import UI_SCALE_MIGRATION_KEY, extract_extended_metadata_from_html
from audioknigi.diagnostics import support_bundle as support_bundle__round61_external_review_followup_20260929
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.providers.audioknigi_search import _author_detail_score, _matches_query
from audioknigi.services.queue_service import _item_to_dict
from audioknigi.config.settings import AppSettings, normalize_settings as normalize_settings__round63_followup_20260929
from audioknigi.diagnostics import support_bundle as support_bundle__round63_followup_20260929
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
from audioknigi.core import safe_name
from audioknigi.knigavuhe import _extract_narration_variants
from audioknigi.services import book_analysis_service as analysis_module
from audioknigi.templates import template_values
from audioknigi import cover_fetch
from audioknigi.core import SiteStructureChanged
from audioknigi.download.errors import MissingMediaSourceError
from audioknigi.knigavuhe import parse_book_html
from threading import Event
from audioknigi.download_engine import DownloadService
from audioknigi.i18n import tr
from audioknigi.providers.audioknigi_search import search_audioknigi
import types
from audioknigi.diagnostics import support_bundle as support_bundle__runtime_integrity_followup_20260912
from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.sources import normalize_supported_url
from audioknigi.config import normalize_settings as normalize_settings__services
from audioknigi.services.download_request import build_download_request
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict


# Origin: test_cancellation_cover_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_onboarding_accepted_settings_use_normalized_writer():
    source = (ROOT / 'audioknigi/qt/application.py').read_text(encoding='utf-8')
    assert 'settings = onboarding.result_settings()\n            save_app_settings(settings)' in source


# Origin: test_persistence_cancellation_hardening_20260929.py
def _book__persistence_cancellation_hardening_20260929() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1-test', title='Test', tracks=[Track(index=1, title='Part 1', file='https://example.com/1.mp3')])

def test_scan_unfinished_missing_template_fields_inherit_global_settings(tmp_path):
    folder = tmp_path / 'book'
    folder.mkdir()
    (folder / 'resume.json').write_text(json.dumps({'url': 'https://audioknigi.com.ua/audio-1-test', 'title': 'Test', 'selected_indices': [1]}), encoding='utf-8')
    record = scan_unfinished(tmp_path)[0]
    assert record.use_templates is None
    assert record.folder_template is None
    assert record.track_template is None

def test_resume_ui_only_overwrites_template_settings_when_manifest_stored_them():
    source = Path('audioknigi/qt/mixins/clipboard.py').read_text(encoding='utf-8')
    assert 'for key in ("use_templates", "folder_template", "track_template"):' in source
    assert 'if value is not None:' in source


# Origin: test_report_followup_round13_20260916.py
def test_app_settings_uses_mapping_equality_contract():
    from audioknigi.config.settings import AppSettings, DEFAULT_SETTINGS
    settings = AppSettings({'scale': 100, 'language': 'ru'})
    expected = dict(DEFAULT_SETTINGS)
    expected.update({'scale': 100, 'language': 'ru'})
    assert settings == expected
    assert settings != {**expected, 'scale': 125}


# Origin: test_report_followup_round14_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_legacy_normalize_audio_true_migrates_to_single_pass():
    migrated, changed = migrate_settings({'normalize_audio': True})
    assert changed is True
    assert migrated['normalization_mode'] == 'single'

def test_choose_output_dir_relies_on_debounced_refresh_only():
    source = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'settings.py').read_text(encoding='utf-8')
    block = source[source.index('def _choose_output_dir'):source.index('def _preview_theme')]
    assert 'edit.setText(selected)' in block
    assert 'self._refresh_unfinished()' not in block


# Origin: test_report_followup_round15_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_legacy_queue_base64_cover_and_normalize_audio_are_preserved(tmp_path):
    payload = b'\x89PNG\r\n\x1a\nlegacy-cover'
    task = task_from_dict({'url': 'https://knigavuhe.org/book/test/', 'title': 'Legacy', 'output_dir': str(tmp_path), 'cover_cache': base64.b64encode(payload).decode('ascii'), 'cover_cache_mime': 'image/png', 'normalize_audio': True})
    assert task.request.book.cover_cache == (payload, 'image/png')
    assert task.request.normalization_mode == 'single'


# Origin: test_report_followup_round17_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_ui_scale_migration_accepts_appsettings_mapping_without_losing_keys() -> None:
    source = AppSettings({'scale': 125, 'custom_plugin_key': 'keep-me'})
    migrated, changed = migrate_ui_scale_settings(source)
    assert changed is True
    assert migrated['scale'] == 100
    assert migrated['custom_plugin_key'] == 'keep-me'
    assert migrated[UI_SCALE_MIGRATION_KEY] is True


# Origin: test_report_followup_round20_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_poleknig_external_playlist_finds_variable_config_without_browser() -> None:
    html = '<script>\n    var player_cfg = {playlist: "/media/book-list.json"};\n    var player = new Playerjs(player_cfg);\n    </script>'
    assert poleknig__report_followup_round20_20260917._external_playlist_url(html, 'https://poleknig.com/books/123') == 'https://poleknig.com/media/book-list.json'


# Origin: test_report_followup_round24_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_legacy_normalize_audio_is_migrated_then_removed() -> None:
    settings, changed = migrate_settings({'normalize_audio': True})
    assert changed is True
    assert settings['normalization_mode'] == 'single'
    assert 'normalize_audio' not in settings


# Origin: test_report_followup_round2_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_deliberate_settings_save_preserves_explicit_125_percent(tmp_path):
    path = tmp_path / 'settings.json'
    assert save_app_settings({'scale': 125}, path)
    saved = load_json(path, {})
    assert saved['scale'] == 125
    assert saved[core__report_followup_round2_20260915.UI_SCALE_MIGRATION_KEY] is True


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_string_false_boolean_settings_are_not_truthy() -> None:
    normalized, _changed = migrate_settings({'first_run_complete': 'false', 'embed_tags': '0', 'save_sidecars': 'no', 'delete_source': 'off', 'clipboard_auto': 'true'})
    assert normalized['first_run_complete'] is False
    assert normalized['embed_tags'] is False
    assert normalized['save_sidecars'] is False
    assert normalized['delete_source'] is False
    assert normalized['clipboard_auto'] is True

def test_dot_output_directory_remains_a_valid_explicit_path_contract() -> None:
    source = src__report_followup_round34_20260919('audioknigi/services/download_request.py')
    assert 'if not str(self.output_dir).strip():' in source


# Origin: test_report_followup_round3_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_header_only_browser_profile_preserves_cookie_count(monkeypatch):
    writes = []
    monkeypatch.setattr(core__report_followup_round3_20260915, '_load_persisted_profile', lambda: {'headers': {}, 'cookies_saved': 7})
    monkeypatch.setattr(core__report_followup_round3_20260915, 'save_json', lambda path, payload: writes.append((path, payload)) or True)
    monkeypatch.setattr(core__report_followup_round3_20260915, 'refresh_http_session_profile', lambda: None)
    core__report_followup_round3_20260915.persist_browser_session(None, {'User-Agent': 'UA'})
    profile = [payload for path, payload in writes if path == core__report_followup_round3_20260915.SESSION_PROFILE_FILE][-1]
    assert profile['cookies_saved'] == 7


# Origin: test_report_followup_round42_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round42_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_settings_no_longer_duplicate_ui_mode_selector() -> None:
    pages = src__report_followup_round42_20260920('audioknigi/qt/main_window_pages.py')
    settings = src__report_followup_round42_20260920('audioknigi/qt/mixins/settings.py')
    sync = src__report_followup_round42_20260920('audioknigi/qt/settings_sync.py')
    assert 'self.ui_mode_combo = QComboBox()' not in pages
    assert 'ui.addRow(self._l("Режим:"), self.ui_mode_combo)' not in pages
    assert '"ui_mode": self.current_ui_mode()' in settings
    assert 'hasattr(self, "ui_mode_combo")' not in sync

def test_settings_card_expands_instead_of_becoming_one_third_width() -> None:
    pages = src__report_followup_round42_20260920('audioknigi/qt/main_window_pages.py')
    assert 'settings_card.setMinimumWidth(820)' in pages
    assert 'settings_card.setMaximumWidth(1180)' in pages
    assert 'settings_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)' in pages
    assert 'center.addWidget(settings_card, 4)' in pages
    assert 'center.addWidget(settings_card, 1)' not in pages


# Origin: test_report_followup_round43_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round43_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_safe_bool_uses_default_for_missing_or_empty_values_and_direct_settings_have_defaults() -> None:
    assert settings_module__report_followup_round43_20260920._safe_bool(None, True) is True
    assert settings_module__report_followup_round43_20260920._safe_bool('', True) is True
    assert settings_module__report_followup_round43_20260920._safe_bool('false', True) is False
    settings = settings_module__report_followup_round43_20260920.AppSettings()
    assert settings['language'] == settings_module__report_followup_round43_20260920.DEFAULT_SETTINGS['language']
    assert settings['minimize_to_tray'] is True


# Origin: test_report_followup_round44_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round44_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_partial_direct_app_settings_constructor_supplies_missing_defaults_without_changing_explicit_mapping() -> None:
    settings = settings_module__report_followup_round44_20260920.AppSettings({'language': 'en', 'scale': '125'})
    assert settings['language'] == 'en'
    assert settings['scale'] == 125
    assert settings['theme'] == settings_module__report_followup_round44_20260920.DEFAULT_SETTINGS['theme']
    assert settings['minimize_to_tray'] is True
    assert 'theme' in settings.keys()
    assert len(settings) >= len(settings_module__report_followup_round44_20260920.DEFAULT_SETTINGS)


# Origin: test_report_followup_round45_20260921.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round45_20260921(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_existing_profile_without_onboarding_flag_does_not_reopen_first_run() -> None:
    migrated, changed = settings_module__report_followup_round45_20260921.migrate_settings({'language': 'de', 'scale': 100})
    assert changed is True
    assert migrated['first_run_complete'] is True
    fresh, _changed = settings_module__report_followup_round45_20260921.migrate_settings({})
    assert fresh['first_run_complete'] is False
    explicit, _changed = settings_module__report_followup_round45_20260921.migrate_settings({'first_run_complete': False})
    assert explicit['first_run_complete'] is False
    plugin_only, _changed = settings_module__report_followup_round45_20260921.migrate_settings({'plugin_future_value': 42})
    assert plugin_only['first_run_complete'] is False

class _SplitDummy(MediaProcessingMixin):

    def __init__(self, target: Path):
        self.target = target

    def _track_path(self, _book, _track):
        return self.target

    def log(self, _message):
        pass

def test_output_directory_resume_scan_runs_after_editing_not_each_character() -> None:
    source = src__report_followup_round45_20260921('audioknigi/qt/mixins/settings.py')
    wire_start = source.index('def _wire_output_dir_sync')
    wire_end = source.index('def _easy_quality_preset_changed', wire_start)
    wire = source[wire_start:wire_end]
    assert 'edit.editingFinished.connect(self._schedule_unfinished_refresh)' in wire
    sync_start = source.index('def _sync_output_dir_text')
    sync_end = source.index('def _schedule_unfinished_refresh', sync_start)
    sync = source[sync_start:sync_end]
    assert '_schedule_unfinished_refresh' not in sync
    choose_start = source.index('def _choose_output_dir')
    choose_end = source.index('def _preview_theme', choose_start)
    choose = source[choose_start:choose_end]
    assert 'self._schedule_unfinished_refresh()' in choose


# Origin: test_report_followup_round46_20260922.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round46_20260922(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_settings_save_preserves_shared_settings_object_identity() -> None:
    source = src__report_followup_round46_20260922('audioknigi/qt/mixins/settings.py')
    start = source.index('def _save_settings')
    end = source.index('def test_audiobookshelf', start)
    block = source[start:end]
    assert 'self.settings.clear()' in block
    assert 'self.settings.update(updated)' in block
    assert 'self.settings = AppSettings.from_mapping(updated)' not in block
    assert 'AppSettings' not in source.splitlines()[6]


# Origin: test_report_followup_round47_20260923.py
def test_appsettings_partial_mapping_has_consistent_keys_length_and_delete():
    settings = settings_module__report_followup_round47_20260923.AppSettings({'scale': 120, 'plugin_key': 'x'})
    assert settings['language'] == settings_module__report_followup_round47_20260923.DEFAULT_SETTINGS['language']
    assert 'language' in settings.keys()
    assert len(settings) == len(settings.to_dict())
    assert settings.to_dict()['plugin_key'] == 'x'
    del settings['language']
    assert 'language' not in settings
    try:
        settings['language']
    except KeyError:
        pass
    else:
        raise AssertionError('deleted mapping key unexpectedly resurrected from defaults')

def test_legacy_only_settings_mark_profile_as_first_run_complete():
    data, _changed = settings_module__report_followup_round47_20260923.migrate_settings({'auto_chunk_min_kbps': 512})
    assert data['first_run_complete'] is True
    data2, _changed2 = settings_module__report_followup_round47_20260923.migrate_settings({'normalize_audio': True})
    assert data2['first_run_complete'] is True


# Origin: test_report_followup_round49_20260924.py
class _FallbackHost(SourceAnalysisMixin):
    cancel_event = None
    _book_identity_hints = staticmethod(BookAnalysisService._book_identity_hints)
    _identity_tokens = staticmethod(BookAnalysisService._identity_tokens)

    def _check_cancel(self) -> None:
        return None

def test_direct_appsettings_constructor_normalizes_types_and_ranges() -> None:
    settings = settings_module__report_followup_round49_20260924.AppSettings({'scale': '150', 'player_volume': 150, 'minimize_to_tray': 'false'})
    assert settings['scale'] == 150
    assert settings['player_volume'] == 100
    assert settings['minimize_to_tray'] is False


# Origin: test_report_followup_round52_20260924.py
def test_settings_migrate_legacy_chunk_value_when_new_key_is_none() -> None:
    data, _changed = settings_module__report_followup_round52_20260924.migrate_settings({'auto_chunk_min_kbytes_per_sec': None, 'auto_chunk_min_kbps': 640})
    assert data['auto_chunk_min_kbytes_per_sec'] == 640
    assert 'auto_chunk_min_kbps' not in data


# Origin: test_report_followup_round9_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_browser_profile_adapter_filters_expired_cookies(monkeypatch):
    import audioknigi.core as core
    now = 2000000000
    monkeypatch.setattr(core.time, 'time', lambda: now)

    def fake_load(path, default):
        if path == core.SESSION_PROFILE_FILE:
            return {'headers': {'User-Agent': 'UA', 'Accept-Language': 'de-DE', 'X-Secret': 'no'}}
        if path == core.COOKIE_FILE:
            return [{'name': 'good', 'value': '1', 'domain': '.example.test', 'path': '/', 'expires': now + 50, 'secure': True}, {'name': 'expired', 'value': '2', 'domain': '.example.test', 'expires': now - 1}, {'name': 'no-domain', 'value': '3'}]
        return default
    monkeypatch.setattr(core, 'load_json', fake_load)
    headers, cookies = load_browser_context_profile()
    assert headers == {'User-Agent': 'UA', 'Accept-Language': 'de-DE'}
    assert [item['name'] for item in cookies] == ['good']
    assert cookies[0]['expires'] == pytest.approx(now + 50)


# Origin: test_round61_external_review_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_appsettings_direct_and_from_mapping_match_for_partial_current_mapping():
    direct = AppSettings({'theme': 'dark'})
    factory = AppSettings.from_mapping({'theme': 'dark'})
    assert direct['first_run_complete'] is False
    assert factory['first_run_complete'] is False
    assert direct.to_dict() == factory.to_dict()
    assert UI_SCALE_MIGRATION_KEY not in direct
    assert UI_SCALE_MIGRATION_KEY not in factory


# Origin: test_round63_followup_20260929.py
def test_appsettings_setitem_normalizes_runtime_values():
    settings = AppSettings()
    settings['scale'] = '150'
    settings['large_mode'] = 'yes'
    settings['player_rate'] = '9'
    assert settings['scale'] == 150
    assert settings['large_mode'] is True
    assert settings['player_rate'] == 3.0


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

def test_settings_bulk_replace_normalizes_once_and_preserves_identity_contract():
    settings = AppSettings({'language': 'ru', 'scale': 100, 'first_run_complete': True})
    identity = id(settings)
    settings.replace_all({'language': 'en', 'scale': 999, 'first_run_complete': True})
    assert id(settings) == identity
    assert settings['language'] == 'en'
    assert settings['scale'] == 200
    assert settings['first_run_complete'] is True
    ui_source = (ROOT / 'audioknigi/qt/mixins/settings.py').read_text(encoding='utf-8')
    assert 'replace_all = getattr(self.settings, "replace_all", None)' in ui_source


# Origin: test_round73_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_replace_all_partial_mapping_keeps_first_run_semantics_consistent():
    settings = AppSettings({'theme': 'dark'})
    settings.replace_all({'theme': 'light'})
    assert settings['theme'] == 'light'
    assert settings['first_run_complete'] is False


# Origin: test_round74_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_output_dir_none_and_easy_download_state_are_guarded():
    pages = (ROOT / 'audioknigi/qt/main_window_pages.py').read_text(encoding='utf-8')
    assert 'self.output_edit = QLineEdit(str(self.settings.get("output_dir") or DEFAULT_OUTPUT))' in pages
    main = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    block = main[main.index('def _update_easy_action_text'):main.index('def _set_operation_ui_blocked')]
    assert 'elif hasattr(self, "easy_download_button"):' in block
    assert 'self.easy_download_button.setEnabled(False)' in block


# Origin: test_round75_external_review_followup_20261003.py
ROOT = Path(__file__).resolve().parents[2]

def test_appsettings_unrelated_write_does_not_resurrect_deleted_default_key():
    settings = AppSettings({'theme': 'dark', 'scale': 100})
    del settings['theme']
    settings['scale'] = 999
    assert 'theme' not in settings
    assert settings['scale'] == 200


# Origin: test_round76_external_review_followup_20261003.py
ROOT = Path(__file__).resolve().parents[2]

def test_appsettings_legacy_write_aliases_update_only_canonical_keys():
    settings = AppSettings({'theme': 'dark', 'normalization_mode': 'two_pass'})
    del settings['theme']
    settings['normalize_audio'] = True
    assert settings['normalization_mode'] == 'single'
    assert 'normalize_audio' not in settings
    assert 'theme' not in settings
    settings['normalize_audio'] = False
    assert settings['normalization_mode'] == 'off'
    assert 'normalize_audio' not in settings
    settings['auto_chunk_min_kbps'] = 512
    assert settings['auto_chunk_min_kbytes_per_sec'] == 512
    assert 'auto_chunk_min_kbps' not in settings
    assert 'theme' not in settings

def test_config_settings_imports_match_real_package_layout():
    assert (ROOT / 'audioknigi/config/settings.py').is_file()
    request_source = (ROOT / 'audioknigi/services/download_request.py').read_text(encoding='utf-8')
    engine_source = (ROOT / 'audioknigi/download_engine.py').read_text(encoding='utf-8')
    assert 'from ..config.settings import normalize_settings' in request_source
    assert 'from .config.settings import normalize_settings' in engine_source


# Origin: test_round78_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_appsettings_legacy_read_aliases_match_legacy_semantics():
    settings = AppSettings({'auto_chunk_min_kbytes_per_sec': 512, 'normalization_mode': 'two_pass'})
    assert settings['auto_chunk_min_kbps'] == 512
    assert settings.get('auto_chunk_min_kbps') == 512
    assert settings['normalize_audio'] is True
    settings['normalize_audio'] = False
    assert settings['normalize_audio'] is False
    assert settings['normalization_mode'] == 'off'


# Origin: test_round79_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_reported_runtime_templates_and_settings_membership_are_intentional_contracts():
    assert ui_text('en', 'Озвучка {index}', index=3) == 'Narration 3'
    assert ui_text('en', 'Найдено вариантов озвучки: {count}. Выберите чтеца.', count=2) == 'Narration options found: 2. Choose a narrator.'
    settings = AppSettings({'normalization_mode': 'single', 'auto_chunk_min_kbytes_per_sec': 512})
    assert settings['normalize_audio'] is True
    assert settings.get('auto_chunk_min_kbps') == 512
    assert 'normalize_audio' not in settings
    assert 'auto_chunk_min_kbps' not in settings


# Origin: test_round80_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_settings_legacy_alias_membership_remains_canonical_storage_contract():
    settings = AppSettings({'normalization_mode': 'single', 'auto_chunk_min_kbytes_per_sec': 512})
    assert settings['normalize_audio'] is True
    assert settings.get('auto_chunk_min_kbps') == 512
    assert 'normalize_audio' not in settings
    assert 'auto_chunk_min_kbps' not in settings


# Origin: test_runtime_contract_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def _book__runtime_contract_hardening_20260912() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3'), Track(index=2, title='Two', file='https://cdn.invalid/2.mp3')])

def test_appsettings_is_used_by_qt_settings_sync_contract():
    source = (ROOT / 'audioknigi' / 'qt' / 'settings_sync.py').read_text(encoding='utf-8')
    assert 'from collections.abc import Mapping' in source
    assert 'isinstance(self.settings, Mapping)' in source
    assert 'isinstance(self.settings, dict)' not in source

def test_backup_restore_reloads_typed_settings():
    source = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'history.py').read_text(encoding='utf-8')
    assert 'load_app_settings' in source
    assert 'self.settings = load_app_settings()' in source
    assert 'self.settings = load_json' not in source

def test_first_run_cancel_is_skip_not_process_exit():
    source = (ROOT / 'audioknigi' / 'qt' / 'application.py').read_text(encoding='utf-8')
    block = source[source.index('if not bool(settings.get("first_run_complete"'):source.index('app.setProperty("audioknigi_language"')]
    assert 'settings["first_run_complete"] = True' in block
    assert 'save_app_settings(settings)' in block
    assert 'return 0' not in block


# Origin: test_runtime_integrity_followup_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_invalid_normalization_mode_is_normalized_at_settings_boundary():
    settings, _changed = migrate_settings({'normalization_mode': 'not-a-real-mode'})
    assert settings['normalization_mode'] == 'off'


# Origin: test_services.py
def test_download_request_uses_normalized_settings(tmp_path):
    book = Book(url='https://example.invalid', title='Book', tracks=[Track(1, 'One', 'https://example.invalid/1.mp3')])
    request = build_download_request(book, {'output_dir': str(tmp_path), 'auto_chunk_min_kbps': 512}, [1])
    assert request.output_dir == tmp_path
    assert request.selected_indices == [1]
