"""Consolidated integration tests for the build release domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


import json
from pathlib import Path
from types import SimpleNamespace
from tools import qt_windows_acceptance
from tools.undefined_global_audit import _SPECIAL_GLOBALS
import importlib.util
import subprocess
import sys
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
from tools.exception_audit import audit as exception_audit
from tools.historical_regression_audit import _normalize_nodeid
from tools.qt_localization_audit import _assignment_value
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
from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, migrate_ui_scale_settings
from audioknigi.i18n import _normalize_runtime_regex_catalog
from audioknigi.services.search_service import search_all_sources
from audioknigi import core, knigavuhe as knigavuhe__report_followup_round21_20260917, poleknig as poleknig__report_followup_round21_20260917
from audioknigi.diagnostics.support_bundle import create_support_bundle
from audioknigi import core
from audioknigi.core import fmt_size
from audioknigi.templates import render_text_template
import audioknigi.config.settings as settings_module
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round43_20260920
import audioknigi.download.network as network_module
import audioknigi.knigavuhe as knigavuhe__report_followup_round43_20260920
import audioknigi.poleknig as poleknig__report_followup_round43_20260920
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.download.probe import ProbeMixin
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata, _merge_author_names
import time
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round45_20260921
import audioknigi.services.player_position_store as position_module
from audioknigi.download.errors import SharedSourceTimelineError
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.poleknig import _parse_playlist_objects
from audioknigi.providers.audioknigi_search import parse_audioknigi_results
from audioknigi.brand import version_label
from audioknigi.i18n import localize_runtime_text
from audioknigi import network_dns
from audioknigi.config.settings import normalize_settings
from audioknigi.brand import AUTHOR_EMAIL, AUTHOR_GITHUB_URL, AUTHOR_NAME, COPYRIGHT_YEAR, PROJECT_URL
from tools.windows_version_info import render_version_info
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, _DownloadEngine
from threading import Event
from audioknigi.download_engine import DownloadService
from audioknigi.i18n import tr
from audioknigi.providers.audioknigi_search import search_audioknigi
from audioknigi.services.download_request import DownloadRequest, build_download_request
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict
import types
from audioknigi.config.settings import migrate_settings
from audioknigi.diagnostics import support_bundle as support_bundle__runtime_integrity_followup_20260912
from audioknigi.downloader import DownloaderMixin
from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.sources import normalize_supported_url
from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.diagnostics.support_bundle import _is_secret_key
from audioknigi.i18n import localize_runtime_text, tr, ui_text
from audioknigi.providers.adapters import KnigavuheProvider, PoleKnigProvider
from audioknigi.services import library_service
from audioknigi.services.queue_service import _book_to_dict
import re
import zipfile
from audioknigi.diagnostics import support_bundle as support_bundle__structured_hardening_20260912
from audioknigi.knigavuhe import _merge_narration_variants
from audioknigi.models import NarrationVariant, SearchResult, Track, TRACK_STATUS_MISSING
from audioknigi.services import search_service
from audioknigi.providers import provider_for_key


# Origin: test_acceptance_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_release_baseline_comment_and_runtime_stage_are_current():
    release = (ROOT / 'requirements-release.txt').read_text(encoding='utf-8')
    qt_init = (ROOT / 'audioknigi' / 'qt' / '__init__.py').read_text(encoding='utf-8')
    assert 'Verified published release baseline for 2026-09-18' in release
    assert 'QT_RUNTIME_STAGE = "qt-only-4.12.42"' in qt_init


# Origin: test_build_wmi_bootstrap_round8_20260916.py
ROOT = Path(__file__).resolve().parents[2]

BOOTSTRAP = ROOT / 'tools' / 'pyinstaller_bootstrap.py'

BUILD_PS1 = ROOT / 'build_qt_ci.ps1'

BUILD_BAT = ROOT / 'build_qt_exe.bat'

def _load_bootstrap_module():
    spec = importlib.util.spec_from_file_location('round8_pyinstaller_bootstrap', BOOTSTRAP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_bootstrap_imports_without_pyinstaller_and_selftests():
    module = _load_bootstrap_module()
    assert callable(module.prepare_platform_for_pyinstaller)
    proc = subprocess.run([sys.executable, str(BOOTSTRAP), '--bootstrap-selftest'], cwd=ROOT, capture_output=True, text=True, timeout=10, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert 'PYINSTALLER BOOTSTRAP SELFTEST: OK' in proc.stdout

def test_prepare_platform_for_pyinstaller_disables_wmi_on_simulated_py314_windows(monkeypatch):
    module = _load_bootstrap_module()
    sentinel = object()
    monkeypatch.setattr(module.sys, 'platform', 'win32')
    monkeypatch.setattr(module.sys, 'version_info', (3, 14, 7))
    monkeypatch.setattr(module.platform, '_wmi', sentinel, raising=False)
    assert module.prepare_platform_for_pyinstaller() is True
    assert module.platform._wmi is None

def test_bootstrap_disables_only_platform_wmi_before_pyinstaller_import():
    text = BOOTSTRAP.read_text(encoding='utf-8')
    prepare_pos = text.index('prepare_platform_for_pyinstaller()', text.index('def main'))
    import_pos = text.index('from PyInstaller.__main__ import run')
    assert prepare_pos < import_pos
    assert 'sys.platform != "win32"' in text
    assert 'sys.version_info < (3, 14)' in text
    assert 'platform._wmi = None' in text
    assert 'platform.win32_ver =' not in text

def test_powershell_build_uses_bootstrap_instead_of_python_m_pyinstaller():
    text = BUILD_PS1.read_text(encoding='utf-8-sig')
    assert 'tools\\pyinstaller_bootstrap.py' in text
    assert '& $PythonExe $pyinstallerBootstrap "--bootstrap-selftest"' in text
    assert '& $PythonExe $pyinstallerBootstrap @arguments' in text
    assert '"-m", "PyInstaller"' not in text

def test_batch_requires_bootstrap_file_before_build():
    text = BUILD_BAT.read_text(encoding='utf-8-sig')
    assert 'if not exist "tools\\pyinstaller_bootstrap.py" (' in text


# Origin: test_cancellation_cover_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_version_and_runtime_stage_41239():
    from audioknigi.metadata import APP_VERSION
    from audioknigi.qt import QT_RUNTIME_STAGE
    assert APP_VERSION == '4.12.42'
    assert QT_RUNTIME_STAGE == 'qt-only-4.12.42'


# Origin: test_external_review_hardening_20260928.py
ROOT = Path(__file__).resolve().parents[2]

def test_changelog_and_runtime_translation_format_are_clean():
    changelog = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    assert '\\n\\n' not in changelog
    assert 'Acceptance parser, cancellation and diagnostics hardening (2026-09-18)' in changelog
    assert 'Post-release audit updates through 2026-09-29' in changelog
    raw = (ROOT / 'audioknigi/locales/runtime_exact.json').read_text(encoding='utf-8')
    assert raw.count('"Проверить системный звук":') == 1
    data = json.loads(raw)
    for key in ('Проверить звук события', 'Проверить системный звук'):
        assert list(data[key])[:3] == ['de', 'en', 'uk']


# Origin: test_quality_runtime_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_acceptance_status_can_explicitly_disable_windows_requirement(monkeypatch):
    import tools.qt_windows_acceptance as acceptance
    seen = {}
    monkeypatch.setattr(acceptance, 'acceptance_complete', lambda report, **kwargs: seen.setdefault('require_windows', kwargs['require_windows']) is False)
    report = {'exe_sha256': 'abc'}
    acceptance._refresh_status(report, require_windows=False)
    assert seen['require_windows'] is False
    assert report['status'] == 'pass'

def test_runtime_stage_and_accessibility_contract_are_current():
    qt_init = (ROOT / 'audioknigi' / 'qt' / '__init__.py').read_text(encoding='utf-8')
    access = (ROOT / 'audioknigi' / 'qt' / 'accessibility_audit.py').read_text(encoding='utf-8')
    pages = (ROOT / 'audioknigi' / 'qt' / 'main_window_pages.py').read_text(encoding='utf-8')
    assert 'QT_RUNTIME_STAGE = "qt-only-4.12.42"' in qt_init
    assert '"easy_book_cover"' in access
    assert 'description=self._l("Секретное поле")' in pages


# Origin: test_recovery_diagnostics_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_third_party_notice_covers_pyinstaller_and_license_status():
    notices = (ROOT / 'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')
    assert 'PyInstaller / PyInstaller bootloader' in notices
    assert 'No top-level project license is declared' in notices
    assert (ROOT / 'docs' / 'development' / 'RELEASE_LICENSING.md').is_file()


# Origin: test_release_integrity_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_release_version_and_entrypoint_do_not_hardcode_previous_patch():
    assert APP_VERSION == '4.12.42'
    source = (ROOT / 'audioknigi_qt.py').read_text(encoding='utf-8')
    assert '4.12.34 runtime' not in source
    assert 'The active runtime is Qt-only' in source
    assert 'Historical compatibility note: Phase 39 is Qt-only' in source


# Origin: test_release_quality_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_frozen_extension_normalizer_preserves_package_path():
    tool = _load_tool('qt_frozen_module_audit.py')
    assert tool._normalise_entry_name('pygame/_camera.cp314-win_amd64.pyd', 'EXTENSION') == 'pygame/_camera'
    assert tool._matches_root('pygame/_camera', 'pygame')
    toc = [('pygame/_camera.cp314-win_amd64.pyd', 'x', 'EXTENSION')]
    leaks = tool.find_forbidden_modules(toc)
    assert leaks and leaks[0][0].startswith('pygame/')

def _request() -> DownloadRequest:
    book = Book(url='https://knigavuhe.org/book/1', title='Book', tracks=[Track(index=1, title='One', file='https://cdn.example/1.mp3')])
    return DownloadRequest(book=book, selected_indices=None, output_dir=Path('.'))

def test_search_model_is_initialized_before_ui_build():
    source = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    init_pos = source.index('self.search_model = SearchResultsModel(self)')
    build_pos = source.index('self._build_ui()')
    assert init_pos < build_pos


# Origin: test_report_followup_round12_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_build_download_request_accepts_mapping_settings(tmp_path):
    book = Book(url='https://knigavuhe.org/book/demo/', title='Demo', tracks=[Track(index=1, title='One', file='1.mp3')])
    settings = UserDict({'output_dir': str(tmp_path), 'audio_preset': 'copy'})
    request = build_download_request(book, settings, [1])
    assert request.output_dir == tmp_path
    assert request.selected_indices == [1]


# Origin: test_report_followup_round17_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_changelog_round8_is_inside_41242_and_release_date_is_current() -> None:
    changelog = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    assert '## 4.12.42 — Acceptance parser, cancellation and diagnostics hardening (2026-09-18)' in changelog
    assert '## 2026-09-16 — Round 8 Windows build hardening' not in changelog
    round9 = changelog.index('- Round 9 audit (2026-09-16):')
    round8 = changelog.index('- Round 8 Windows build hardening (2026-09-16):')
    round7 = changelog.index('- Round 7 audit (2026-09-16):')
    release_471 = changelog.index('## 4.7.1')
    assert round9 < round8 < round7 < release_471


# Origin: test_report_followup_round21_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_ci_installs_pytest_and_python314_synthetic_global_is_allowlisted() -> None:
    ci = (ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8')
    audit = (ROOT / 'tools/undefined_global_audit.py').read_text(encoding='utf-8')
    assert 'python -m pip install pytest' in ci
    assert 'choco install ffmpeg -y --no-progress' in ci
    assert '"__conditional_annotations__"' in audit


# Origin: test_report_followup_round33_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round33_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_release_dates_are_finalized_to_2026_09_18() -> None:
    changelog = src__report_followup_round33_20260918('CHANGELOG.md')
    requirements = src__report_followup_round33_20260918('requirements-release.txt')
    assert '## 4.12.42 — Acceptance parser, cancellation and diagnostics hardening (2026-09-18)' in changelog
    assert 'Verified published release baseline for 2026-09-18' in requirements


# Origin: test_report_followup_round43_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round43_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_book_flow_rejects_missing_source_before_building_download_jobs() -> None:
    source = src__report_followup_round43_20260920('audioknigi/download/book_flow.py')
    assert 'if not str(getattr(tr, "file", "") or "").strip()' in source
    assert '"В плейлисте отсутствует адрес аудиофайла для частей: "' in source
    assert 'source_url = str(getattr(tr, "file", "") or "").strip()' in source


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

def test_redownload_releases_player_source_and_aborts_if_old_file_cannot_be_removed() -> None:
    source = src__report_followup_round45_20260921('audioknigi/qt/mixins/clipboard.py')
    start = source.index('elif action is redownload:')
    end = source.index('elif action is download:', start)
    block = source[start:end]
    assert 'controller.unload_if_path(path)' in block
    assert 'except Exception as exc:' in block
    assert 'return' in block
    assert block.index('return') < block.index('track.local_status = TRACK_STATUS_MISSING')


# Origin: test_report_followup_round5_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_version_label_does_not_return_bare_v_for_empty_value():
    assert version_label('') == ''
    assert version_label('  ') == ''
    assert version_label(None) == ''
    assert version_label('4.12.42') == 'v4.12.42'
    assert version_label('v4.12.42') == 'v4.12.42'


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

def test_auto_mode_limits_cloudflare_bootstraps_to_ipv4_pair():
    source = (ROOT / 'audioknigi/network_dns.py').read_text(encoding='utf-8')
    assert 'CLOUDFLARE_BOOTSTRAP_IPS[:2]' in source


# Origin: test_round64_qt_fontdir_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_manual_qt_build_sets_windows_fontdir_without_overriding_caller():
    source = (ROOT / 'build_qt_exe.bat').read_text(encoding='utf-8')
    assert 'if not defined QT_QPA_FONTDIR if exist "%WINDIR%\\Fonts"' in source
    assert 'set "QT_QPA_FONTDIR=%WINDIR%\\Fonts"' in source

def test_ci_qt_build_initializes_windows_fontdir_for_direct_invocation():
    source = (ROOT / 'build_qt_ci.ps1').read_text(encoding='utf-8')
    assert 'function Initialize-QtFontDirectory' in source
    assert '$env:QT_QPA_FONTDIR' in source
    assert 'Join-Path $env:WINDIR "Fonts"' in source
    assert 'Initialize-QtFontDirectory' in source
    assert 'if (-not [string]::IsNullOrWhiteSpace($env:QT_QPA_FONTDIR))' in source


# Origin: test_round68_creator_metadata_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_windows_version_info_contains_creator_and_product_identity():
    text = render_version_info()
    assert 'Едуард Саратовцев' in text
    assert 'Автор и разработчик: Едуард Саратовцев' in text
    assert 'AudioKnigi Downloader' in text
    assert 'AudioKnigiDownloader_Qt.exe' in text
    assert '© 2026 Едуард Саратовцев' in text
    assert 'filevers=(4, 12, 42, 0)' in text

def test_qt_build_supplies_generated_version_resource_to_pyinstaller():
    source = (ROOT / 'build_qt_ci.ps1').read_text(encoding='utf-8')
    assert 'tools\\windows_version_info.py' in source
    assert '"--version-file", $versionInfoFile' in source


# Origin: test_round70_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_source_target_assignment_is_shared_helper_not_probe_bookflow_dependency():
    probe = (ROOT / 'audioknigi/download/probe.py').read_text(encoding='utf-8')
    book_flow = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    common = (ROOT / 'audioknigi/download/common.py').read_text(encoding='utf-8')
    assert 'def source_target_assignments(' in common
    assert 'assignments = source_target_assignments(book, source_urls, folder)' in probe
    assert 'return source_target_assignments(book, source_urls, folder)' in book_flow

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

def test_packaged_locale_path_matches_pyinstaller_destination():
    i18n = (ROOT / 'audioknigi/i18n.py').read_text(encoding='utf-8')
    build = (ROOT / 'build_qt_ci.ps1').read_text(encoding='utf-8')
    assert '_LOCALE_DIR = Path(__file__).with_name("locales")' in i18n
    assert '"--add-data", "audioknigi\\locales;audioknigi\\locales"' in build


# Origin: test_runtime_contract_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def _book() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3'), Track(index=2, title='Two', file='https://cdn.invalid/2.mp3')])

def test_build_request_accepts_none_as_whole_book(tmp_path):
    request = build_download_request(_book(), {'output_dir': str(tmp_path)}, None)
    assert request.selected_indices is None
    assert request.resolved_selected_indices() == [1, 2]

def test_release_dependency_pins_are_documented_as_verified_current_releases():
    release = (ROOT / 'requirements-release.txt').read_text(encoding='utf-8')
    for pin in ('PySide6==6.11.2', 'requests==2.32.5', 'playwright==1.62.0', 'Pillow==12.3.0', 'mutagen==1.47.0', 'pyinstaller==6.22.2'):
        assert pin in release

def test_third_party_notice_mentions_packaged_media_and_qt_runtime():
    notices = (ROOT / 'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')
    assert 'PySide6 / Qt for Python' in notices
    assert 'FFmpeg / FFprobe' in notices
    assert 'Playwright for Python' in notices


# Origin: test_runtime_integrity_followup_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_frozen_dependency_report_falls_back_to_module_versions(monkeypatch):

    def missing_metadata(_name):
        raise ValueError('dist-info unavailable in one-file bundle')
    fake = types.SimpleNamespace(__version__='9.9-test')
    monkeypatch.setattr(support_bundle__runtime_integrity_followup_20260912.importlib.metadata, 'version', missing_metadata)
    monkeypatch.setattr(support_bundle__runtime_integrity_followup_20260912.importlib, 'import_module', lambda _name: fake)
    versions = support_bundle__runtime_integrity_followup_20260912._dependency_versions()
    assert set(versions) == {'PySide6', 'requests', 'playwright', 'Pillow', 'mutagen'}
    assert set(versions.values()) == {'9.9-test'}

def test_changelog_release_hierarchy_and_architecture_docs_are_current():
    changelog = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert changelog.startswith('# Changelog\n')
    assert '## 4.12.34 — Whole-book selection and runtime contract hardening' in changelog
    assert not any((line.startswith('## ') and 'Build system — Python 3.14.7' in line for line in changelog.splitlines()))
    assert '## 4.7.1.2' in changelog
    assert 'Additional late 4.12.31 accessibility and UI hardening' in changelog
    assert '`audioknigi/download_engine.py`' in readme

def test_qt_selftest_reports_current_runtime_stage_but_keeps_acceptance_marker():
    qt_init = (ROOT / 'audioknigi' / 'qt' / '__init__.py').read_text(encoding='utf-8')
    entry = (ROOT / 'audioknigi_qt.py').read_text(encoding='utf-8')
    assert 'QT_MIGRATION_STAGE = "phase-39"' in qt_init
    assert 'QT_RUNTIME_STAGE = "qt-only-4.12.42"' in qt_init
    assert 'QT RUNTIME SELFTEST: OK' in entry and 'QT_RUNTIME_STAGE' in entry
    assert 'PLAYWRIGHT EDGE SELFTEST: OK' in entry


# Origin: test_stability_localization_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_version_and_runtime_stage_41240():
    from audioknigi.metadata import APP_VERSION
    from audioknigi.qt import QT_RUNTIME_STAGE
    assert APP_VERSION == '4.12.42'
    assert QT_RUNTIME_STAGE == 'qt-only-4.12.42'


# Origin: test_structured_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_release_docs_and_dependency_contract_are_consistent():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    changelog = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    runtime = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
    qt_alias = (ROOT / 'requirements-qt.txt').read_text(encoding='utf-8')
    release = (ROOT / 'requirements-release.txt').read_text(encoding='utf-8')
    assert 'Python 3.11+ for source/runtime compatibility' in readme
    assert 'CPython 3.14.7 x64' in readme
    assert runtime.splitlines()[0] == '# Qt-only runtime dependencies (Python 3.11+).'
    assert qt_alias.strip().endswith('-r requirements.txt')
    assert 'PySide6==6.11.2' in release
    assert 'playwright==1.62.0' in release
    assert 'Pillow==12.3.0' in release
    assert 'pyinstaller==6.22.2' in release
    assert changelog.count('# Changelog') == 1
    assert len(re.findall('^## 4\\.12\\.31\\b', changelog, re.M)) == 1
    assert len(re.findall('^## 4\\.12\\.32\\b', changelog, re.M)) == 1
    assert not re.search('^# 4\\.12\\.\\d+', changelog, re.M)
