"""Consolidated integration tests for the accessibility domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


import json
from pathlib import Path
from types import SimpleNamespace
from tools import qt_windows_acceptance
from tools.undefined_global_audit import _SPECIAL_GLOBALS
import ast
import socket
import threading
from audioknigi.models import NarrationVariant
from audioknigi.download.errors import MissingSelectedTracksError
from audioknigi.metadata import APP_VERSION
from audioknigi.services.queue_service import task_from_dict
from tools.exception_audit import audit as exception_audit
from tools.historical_regression_audit import _normalize_nodeid
from tools.qt_localization_audit import _assignment_value
import importlib.util
import pytest
from audioknigi.core import extract_metadata_from_html
from audioknigi.logging_utils import sanitize_log_text
from audioknigi.models import Book, SearchResult, Track
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.library_service import export_history
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict
from audioknigi.core import _first_json_ld
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.library_service import scan_unfinished
from collections import UserDict
from audioknigi.core import Cancelled, _structured_book_nodes
from audioknigi.diagnostics import support_bundle as support_bundle__report_followup_round12_20260916
from audioknigi.download_engine import _DownloadEngine
from audioknigi.models import Book, Track
from audioknigi.services.download_request import build_download_request
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
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.core import _walk_json
from audioknigi.download.common import replace_with_retry
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services import library_service
import os
from audioknigi import core as core__report_followup_round21_20260917, knigavuhe as knigavuhe__report_followup_round21_20260917, poleknig as poleknig__report_followup_round21_20260917
from audioknigi.diagnostics.support_bundle import create_support_bundle
from audioknigi.services.player_position_store import PlayerPositionStore
from audioknigi import core as core__report_followup_round2_20260915
from audioknigi.config.settings import save_app_settings
from audioknigi.core import load_json
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.core import Cancelled, load_json
from audioknigi.services.queue_service import _parse_selected_indices_payload
from audioknigi.templates import template_values
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi.providers import audioknigi_search
from audioknigi import core as core__report_followup_round3_20260915
from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.download.probe import ProbeMixin
from audioknigi.download_engine import DownloadService, _DownloadEngine
from audioknigi.services.search_service import search_all_sources
import audioknigi.config.settings as settings_module
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round43_20260920
import audioknigi.download.network as network_module__report_followup_round43_20260920
import audioknigi.knigavuhe as knigavuhe__report_followup_round43_20260920
import audioknigi.poleknig as poleknig__report_followup_round43_20260920
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata, _merge_author_names
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
from audioknigi.knigavuhe import _extract_names
from audioknigi.services.queue_service import _normalize_queue_download_mode, _track_from_dict
from audioknigi.services import search_service
from audioknigi.services.source_health_service import SourceHealthItem, SourceHealthOutcome
import subprocess
import sys
from audioknigi import network_dns
from audioknigi.config.settings import normalize_settings
from audioknigi.brand import AUTHOR_EMAIL, AUTHOR_GITHUB_URL, AUTHOR_NAME, COPYRIGHT_YEAR, PROJECT_URL
from tools.windows_version_info import render_version_info
from audioknigi.services.search_service import downloadable_search_results, search_result_sort_key
import re
from audioknigi.config.settings import AppSettings
from audioknigi.diagnostics import support_bundle as support_bundle__round73_runtime_followup_20261002
from audioknigi.knigavuhe import _usable_search_title
from audioknigi.services.book_analysis_service import BookAnalysisService, _playlist_track_title
from audioknigi.services.library_service import _validated_backup_payloads
from audioknigi.services.queue_service import _optional_persisted_bool
from audioknigi.core import effective_track_duration
from audioknigi.models import Book, NarrationVariant, Track
from audioknigi.download.common import source_target_assignments
from audioknigi.services import source_health_service
from audioknigi.download import network as network_module__round81_external_review_followup_20261006
from audioknigi.download import source_analysis as source_analysis_module
from audioknigi.download.source_analysis import SourceAnalysisMixin
from audioknigi.diagnostics.support_bundle import _is_secret_key
from audioknigi.i18n import localize_runtime_text, tr, ui_text
from audioknigi.providers.adapters import KnigavuheProvider, PoleKnigProvider


# Origin: test_acceptance_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_accessibility_selftest_failure_reports_details_not_partial_report():
    source = (ROOT / 'audioknigi_qt.py').read_text(encoding='utf-8')
    marker = 'except Exception:\n        details = "FAILED\\n" + traceback.format_exc()'
    start = source.index(marker, source.index('def _qt_accessibility_selftest'))
    end = source.index('    finally:', start)
    block = source[start:end]
    assert '_write_report(env_name, filename, details)' in block
    assert '_write_report(env_name, filename, report)' not in block


# Origin: test_help_center_round16_20260917.py
ROOT = Path(__file__).resolve().parents[2]

HELP_CENTER = ROOT / 'audioknigi' / 'qt' / 'help_center.py'

MESSAGES = ROOT / 'audioknigi' / 'locales' / 'messages.json'

ACCESSIBILITY_UI = ROOT / 'audioknigi' / 'qt' / 'mixins' / 'accessibility_ui.py'

def _topics() -> dict[str, tuple[tuple[str, str, str], ...]]:
    tree = ast.parse(HELP_CENTER.read_text(encoding='utf-8'), filename=str(HELP_CENTER))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any((isinstance(target, ast.Name) and target.id == 'TOPICS' for target in node.targets)):
            return ast.literal_eval(node.value)
    raise AssertionError('TOPICS not found')

def test_russian_help_covers_complete_workflow() -> None:
    rows = {key: body for key, _title, body in _topics()['ru']}
    assert 'audioknigi.com.ua' in rows['start']
    assert 'Скачать одним MP3' in rows['book']
    assert 'Range' in rows['download']
    assert 'FFmpeg' in rows['quality']
    assert 'Повторить задачу' in rows['queue']
    assert 'CSV' in rows['history']
    assert 'player_positions.json' in rows['player']
    assert 'Audiobookshelf' in rows['settings']
    assert '{Track_Number}' in rows['files']
    assert 'резерв' in rows['backup'].casefold()
    assert 'NVDA/JAWS' in rows['accessibility']
    assert 'Ctrl+Shift+F12' in rows['shortcuts']
    assert 'диагностический пакет' in rows['diagnostics'].casefold()
    assert 'Восстановить' in rows['troubleshooting']

def test_help_header_no_longer_calls_it_short_instructions() -> None:
    messages = json.loads(MESSAGES.read_text(encoding='utf-8'))
    forbidden = {'ru': 'коротк', 'uk': 'коротк', 'en': 'short instruction', 'de': 'kurze anleitung'}
    for language, needle in forbidden.items():
        intro = str(messages[language]['help_short_intro'])
        assert needle not in intro.casefold()
        assert len(intro) >= 60

def test_help_menu_opens_dedicated_shortcuts_topic_on_f1() -> None:
    source = ACCESSIBILITY_UI.read_text(encoding='utf-8')
    assert 'shortcuts_action.triggered.connect(self.show_shortcuts_help)' in source
    assert 'def show_shortcuts_help(self, _checked=False):' in source
    assert 'self.show_context_help(topic="shortcuts")' in source
    assert 'help_action.setShortcut(QKeySequence("Shift+F1"))' in source
    assert any((key == 'shortcuts' for key, _title, _body in _topics()['ru']))


# Origin: test_network_parser_retention_round6_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_qt_accessibility_selftest_passes_offscreen_platform_explicitly():
    source = (ROOT / 'audioknigi_qt.py').read_text(encoding='utf-8')
    start = source.index('def _qt_accessibility_selftest')
    end = source.index('def main', start)
    block = source[start:end]
    assert 'create_application([sys.argv[0], "-platform", "offscreen"])' in block


# Origin: test_release_integrity_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_main_window_has_application_level_accessible_description():
    source = (ROOT / 'audioknigi' / 'qt' / 'main_window.py').read_text(encoding='utf-8')
    assert 'description=tr(self.language, "main_window_description")' in source
    messages = json.loads((ROOT / 'audioknigi' / 'locales' / 'messages.json').read_text(encoding='utf-8'))
    for language in ('ru', 'uk', 'de', 'en'):
        assert messages[language].get('main_window_description')


# Origin: test_release_quality_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_accessibility_selftest_prints_report_and_runtime_selftest_has_no_asserts():
    source = (ROOT / 'audioknigi_qt.py').read_text(encoding='utf-8')
    assert 'audit_text = result.report().rstrip("\\n") + "\\n"' in source
    assert 'print(report, file=sys.stderr' in source
    assert 'assert SearchOutcome("abc")' not in source
    assert 'required_objects = {' in source
    assert 'Historical compatibility note: Phase 39 is Qt-only' in source
    assert 'Tk retirement happened in the earlier Phase 13' in source

def _request() -> DownloadRequest:
    book = Book(url='https://knigavuhe.org/book/1', title='Book', tracks=[Track(index=1, title='One', file='https://cdn.example/1.mp3')])
    return DownloadRequest(book=book, selected_indices=None, output_dir=Path('.'))

def test_search_keeps_query_widget_enabled_and_restores_focus_on_empty_result():
    source = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    assert 'self.search_edit.setReadOnly(True)' in source
    assert 'self.search_edit.setEnabled(False)' not in source
    empty_branch = source[source.index('self.set_status("Ничего не найдено.")'):]
    assert 'self.search_edit.setFocus' in empty_branch[:400]


# Origin: test_report_followup_round11_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_help_text_uses_same_labels_as_visible_actions():
    messages = json.loads((ROOT / 'audioknigi/locales/messages.json').read_text(encoding='utf-8'))
    assert 'Fürs Smartphone' in messages['de']['help_quality_body']
    assert 'Buch suchen oder Link öffnen' in messages['de']['help_search_body']
    assert 'Find a book or open a link' in messages['en']['help_search_body']
    assert 'Найти книгу или открыть ссылку' in messages['ru']['help_search_body']
    assert 'Знайти книгу або відкрити посилання' in messages['uk']['help_search_body']


# Origin: test_report_followup_round12_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_shortcut_parser_only_adopts_supported_url():
    source = (ROOT / 'audioknigi/qt/mixins/clipboard.py').read_text(encoding='utf-8')
    start = source.index('match = re.search(r"(?im)^URL=(.+)$", content)')
    block = source[start:start + 320]
    assert 'shortcut_url = match.group(1).strip()' in block
    assert 'if valid_site_url(shortcut_url):' in block


# Origin: test_report_followup_round13_20260916.py
def test_qt_sources_harden_invalid_track_index_and_keyboard_seek_without_importing_pyside():
    root = Path(__file__).resolve().parents[2]
    track_model = (root / 'audioknigi/qt/track_model.py').read_text(encoding='utf-8')
    player_controller = (root / 'audioknigi/qt/player_controller.py').read_text(encoding='utf-8')
    player_mixin = (root / 'audioknigi/qt/player_mixin.py').read_text(encoding='utf-8')
    assert 'def _safe_track_index' in track_model
    assert 'safe_int(getattr(track, "index"' in track_model
    assert 'self.save_position(force=False, explicit_seconds=target / 1000.0)' in player_controller
    assert 'seek(int(value) * 1000)' in player_mixin


# Origin: test_report_followup_round14_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_player_chapter_activation_does_not_steal_focus_to_play_button():
    source = (ROOT / 'audioknigi' / 'qt' / 'player_mixin.py').read_text(encoding='utf-8')
    block = source[source.index('def _player_chapter_activated'):source.index('def _refresh_player_context')]
    assert 'activate_ui=False' in block

def test_queue_and_history_rows_do_not_duplicate_native_screen_reader_speech():
    queue = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'queue.py').read_text(encoding='utf-8')
    history = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'history.py').read_text(encoding='utf-8')
    qblock = queue[queue.index('def _queue_current_cell_changed'):queue.index('def _update_queue_action_states')]
    hblock = history[history.index('def _history_current_cell_changed'):history.index('def _update_history_action_states')]
    assert 'announce(' not in qblock
    assert 'announce(' not in hblock
    assert 'AccessibleDescriptionRole' in queue
    assert 'AccessibleDescriptionRole' in history


# Origin: test_report_followup_round15_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_history_delete_reloads_rows_to_refresh_accessibility_descriptions():
    source = (ROOT / 'audioknigi/qt/mixins/history.py').read_text(encoding='utf-8')
    block = source[source.index('def history_delete'):source.index('def export_library')]
    assert 'self._load_history()' in block
    assert 'history_table.removeRow(row)' not in block


# Origin: test_report_followup_round18_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_round18_accessibility_and_easy_settings_contracts() -> None:
    search_model = (ROOT / 'audioknigi/qt/search_model.py').read_text(encoding='utf-8')
    settings = (ROOT / 'audioknigi/qt/mixins/settings.py').read_text(encoding='utf-8')
    accessibility = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'Qt.ItemDataRole.AccessibleDescriptionRole' in search_model
    assert 'Merely saving unrelated settings in Easy mode must not erase' in settings
    assert 'combo.accessibleName() or self._l("Список")' in accessibility
    assert 'combo.objectName()' not in accessibility.split('def _announce_combo_value', 1)[1].split('@Slot(int)', 1)[0]


# Origin: test_report_followup_round21_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_delete_existing_outputs_uses_retry_helper(tmp_path, monkeypatch) -> None:
    target = tmp_path / 'book.mp3'
    target.write_bytes(b'old')
    engine = object.__new__(_DownloadEngine)
    engine.request = SimpleNamespace(book=SimpleNamespace())
    engine._book_folder = lambda *_a, **_k: tmp_path
    engine._full_mp3_target = lambda *_a, **_k: target
    calls = []

    def fake_unlink(path, *, missing_ok=True, attempts=5):
        calls.append((Path(path), missing_ok, attempts))
        Path(path).unlink(missing_ok=missing_ok)
        return True
    import audioknigi.download_engine as engine_module
    monkeypatch.setattr(engine_module, 'unlink_with_retry', fake_unlink)
    assert engine.delete_existing_outputs(full_mp3=True) == 1
    assert calls and calls[0][0] == target
    assert not target.exists()

def test_network_cleanup_uses_windows_retry_helper_everywhere() -> None:
    source = (ROOT / 'audioknigi/download/network.py').read_text(encoding='utf-8')
    assert 'from .common import atomic_write_text, replace_with_retry, unlink_with_retry' in source
    assert '.unlink(' not in source
    assert 'unlink_with_retry(seg, missing_ok=True)' in source
    assert 'unlink_with_retry(part.with_name(part.name + ".assembling"), missing_ok=True)' in source


# Origin: test_report_followup_round2_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_accessibility_fallback_keeps_visible_text_independent_of_script():
    source = (ROOT / 'audioknigi/qt/accessibility.py').read_text(encoding='utf-8')
    block = source[source.index('def _fallback_accessible_name'):source.index('def _default_accessible_description')]
    assert 'if visible:\n                return visible' in block
    assert 're.search' not in block

def test_easy_mode_empty_search_focus_and_clipboard_suppression_are_hardened():
    search_source = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    assert 'if self.current_ui_mode() == "easy":\n                self.easy_input.setFocus' in search_source
    clipboard_source = (ROOT / 'audioknigi/qt/mixins/clipboard.py').read_text(encoding='utf-8')
    assert 'same_clipboard_url = text == suppress' in clipboard_source
    assert 'normalize_supported_url(text) == normalize_supported_url(suppress)' in clipboard_source

def test_f1_shortcut_targets_shortcuts_help_and_history_delete_is_in_place():
    access_source = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'show_context_help(topic="shortcuts")' in access_source
    assert 'weakref.ref(combo)' in access_source
    history_source = (ROOT / 'audioknigi/qt/mixins/history.py').read_text(encoding='utf-8')
    block = history_source[history_source.index('def history_delete'):history_source.index('def export_library')]
    assert 'self._load_history()' in block
    assert 'history_table.removeRow(row)' not in block


# Origin: test_report_followup_round31_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_easy_mode_has_accessible_annotation_block() -> None:
    source = _source('audioknigi/qt/main_window.py')
    assert 'self.easy_description_title = QLabel(self._l("Аннотация"))' in source
    assert 'self.easy_description = QPlainTextEdit()' in source
    assert 'self.easy_description.setReadOnly(True)' in source
    assert 'self.easy_description.setMaximumHeight(150)' in source
    assert 'identifier="easy_book_description"' in source
    assert 'self.easy_description_title.setVisible(False)' in source
    assert 'self.easy_description.setVisible(False)' in source


# Origin: test_report_followup_round32_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round32_20260918(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

def test_player_fields_initialized_and_context_delete_restores_focus() -> None:
    main = src__report_followup_round32_20260918('audioknigi/qt/main_window.py')
    menu = src__report_followup_round32_20260918('audioknigi/qt/localized_context_menu.py')
    for field in ('_last_player_chapter_activation', '_player_book_folder', '_player_book_files', '_player_local_metadata'):
        assert f'self.{field}' in main
    assert menu.count('widget.setFocus(Qt.FocusReason.OtherFocusReason)') >= 2


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_keyboard_track_context_menu_selects_first_row_when_needed() -> None:
    source = src__report_followup_round34_20260919('audioknigi/qt/mixins/clipboard.py')
    block = source[source.index('def _show_track_context_menu'):source.index('def open_selected_track_file')]
    assert 'elif pos is None and not self.track_table.currentIndex().isValid() and self.track_model.rowCount() > 0:' in block
    assert 'focus_table_row(self.track_table, 0, focus=False)' in block


# Origin: test_report_followup_round38_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round38_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_visual_keyboard_focus_ring_covers_both_easy_and_advanced_controls() -> None:
    theme = src__report_followup_round38_20260919('audioknigi/qt/theme.py')
    accessibility = src__report_followup_round38_20260919('audioknigi/qt/accessibility.py')
    window = src__report_followup_round38_20260919('audioknigi/qt/main_window.py')
    assert 'focus = "#e5a93c"' in theme
    assert 'QFocusFrame#keyboardFocusFrame' in theme
    assert 'border: 2px solid {focus}' in theme
    assert 'class KeyboardFocusFrameManager' in accessibility
    assert 'self._frame.setWidget(target)' in accessibility
    assert 'install_keyboard_focus_frame(app, self)' in window

def test_easy_mode_has_explicit_tab_chain_and_text_views_do_not_trap_tab() -> None:
    main = src__report_followup_round38_20260919('audioknigi/qt/main_window.py')
    pages = src__report_followup_round38_20260919('audioknigi/qt/main_window_pages.py')
    assert 'def _configure_keyboard_tab_order' in main
    assert 'QWidget.setTabOrder(current, following)' in main
    for identifier in ('self.easy_input', 'self.easy_paste_button', 'self.easy_action_button', 'self.easy_quality_combo', 'self.easy_output_edit', 'self.easy_folder_button', 'self.easy_download_button', 'self.easy_search_table', 'self.easy_narration_combo', 'self.easy_description', 'self.easy_open_listen_button', 'self.easy_another_button', 'self.tabs'):
        assert identifier in main
    assert 'self.easy_description.setTabChangesFocus(True)' in main
    assert 'self.session_log.setTabChangesFocus(True)' in pages


# Origin: test_report_followup_round39_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round39_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_production_theme_polishes_buttons_inputs_and_focus_without_weakening_focus_ring() -> None:
    theme = src__report_followup_round39_20260919('audioknigi/qt/theme.py')
    assert 'QPushButton[role="primary"]' in theme
    assert 'QPushButton[role="segment"]' in theme
    assert 'QLineEdit:hover' in theme
    assert 'QComboBox::drop-down' in theme
    assert 'QFocusFrame#keyboardFocusFrame' in theme
    assert 'border: 2px solid {focus}' in theme

def test_easy_search_and_book_card_are_visually_clean_but_accessible() -> None:
    source = src__report_followup_round39_20260919('audioknigi/qt/main_window.py')
    assert 'self.easy_search_table.setShowGrid(False)' in source
    assert 'self.easy_search_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)' in source
    assert 'easy_book_layout.setContentsMargins(18, 18, 18, 18)' in source
    assert 'easy_book_layout.setSpacing(18)' in source
    assert 'self.easy_cover_label.setFixedSize(168, 168)' in source
    assert 'self.easy_description.setMaximumHeight(150)' in source
    assert 'self.easy_description.setTabChangesFocus(True)' in source


# Origin: test_report_followup_round3_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_accessibility_followups_are_present_in_ui_sources():
    pages = (ROOT / 'audioknigi/qt/main_window_pages.py').read_text(encoding='utf-8')
    assert 'localized_accessible_name = str(label or "").rstrip(":：").strip()' in pages
    player = (ROOT / 'audioknigi/qt/player_mixin.py').read_text(encoding='utf-8')
    assert 'current = self.track_table.currentIndex()' in player
    dialogs = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    assert dialogs.count('identifier="duplicate_dialog"') >= 2
    assert 'identifier="duplicate_open_folder"' in dialogs


# Origin: test_report_followup_round40_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round40_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_focus_rings_are_refined_to_external_two_pixel_frame() -> None:
    theme = src__report_followup_round40_20260920('audioknigi/qt/theme.py')
    accessibility = src__report_followup_round40_20260920('audioknigi/qt/accessibility.py')
    assert 'focus = "#e5a93c"' in theme
    assert 'QFocusFrame#keyboardFocusFrame' in theme
    assert 'border: 2px solid {focus};' in theme
    assert 'border-radius: 9px;' in theme
    assert 'QFocusFrame' in accessibility
    assert 'WA_TransparentForMouseEvents' in accessibility

def test_help_center_uses_rich_text_headings_lists_and_keyboard_badges() -> None:
    help_source = src__report_followup_round40_20260920('audioknigi/qt/help_center.py')
    assert 'def _format_help_body_html' in help_source
    assert '<h2>{escaped_title}</h2>' in help_source
    assert '<kbd>' in help_source
    assert 'line-height: 1.42' in help_source
    assert 'self.text.setHtml(_format_help_body_html(title, body))' in help_source
    assert 'self.text.setPlainText(' not in help_source


# Origin: test_report_followup_round42_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round42_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_keyboard_focus_uses_external_qfocusframe() -> None:
    accessibility = src__report_followup_round42_20260920('audioknigi/qt/accessibility.py')
    theme = src__report_followup_round42_20260920('audioknigi/qt/theme.py')
    window = src__report_followup_round42_20260920('audioknigi/qt/main_window.py')
    assert 'class KeyboardFocusFrameManager(QObject)' in accessibility
    assert 'QFocusFrame(window)' in accessibility
    assert 'setObjectName("keyboardFocusFrame")' in accessibility
    assert 'self._frame.setWidget(target)' in accessibility
    assert 'def _discard_frame(self) -> None:' in accessibility
    assert 'self._frame = None' in accessibility
    assert 'Never touch the stale wrapper a second time' in accessibility
    assert 'QFocusFrame#keyboardFocusFrame' in theme
    assert 'QPushButton:focus' not in theme
    assert 'QLineEdit:focus' not in theme
    assert 'install_keyboard_focus_frame(app, self)' in window

def test_light_theme_uses_accessible_blue_focus_stronger_cards_and_soft_table_hover() -> None:
    theme = src__report_followup_round42_20260920('audioknigi/qt/theme.py')
    assert 'focus = "#0066cc"' in theme
    assert 'card_border = "#d1d9e2"' in theme
    assert 'table_selection = "#0d74de"' in theme
    assert 'table_hover = "#edf4fc"' in theme
    assert 'border: 1px solid {card_border};' in theme
    assert 'selection-background-color: {table_selection};' in theme
    assert 'QTableView::item:hover, QTableWidget::item:hover' in theme
    assert 'focus = "#e5a93c"' in theme


# Origin: test_report_followup_round43_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round43_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_dead_browser_session_flag_and_dead_bookflow_transient_helper_are_removed() -> None:
    assert 'cookies_provided =' not in src__report_followup_round43_20260920('audioknigi/core.py')
    assert 'def _is_transient_error' not in src__report_followup_round43_20260920('audioknigi/download/book_flow.py')


# Origin: test_report_followup_round44_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round44_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_ffmpeg_helpers_close_subprocess_pipes_in_finally() -> None:
    media = src__report_followup_round44_20260920('audioknigi/download/media.py')
    assert media.count('_close_subprocess_pipes(proc)') >= 2
    for name in ('def _run_ffmpeg(', 'def _run_ffmpeg_capture('):
        start = media.index(name)
        end = media.find('\n    def ', start + len(name))
        block = media[start:] if end < 0 else media[start:end]
        assert '_close_subprocess_pipes(proc)' in block

def test_accessibility_trace_disconnects_focus_signal_before_stream_close() -> None:
    source = src__report_followup_round44_20260920('audioknigi/qt/accessibility_trace.py')
    start = source.index('def close(self)')
    end = source.index('def extract_focus_trace_argument', start)
    block = source[start:end]
    assert 'self.app.focusChanged.disconnect(self._focus_changed)' in block
    assert block.index('focusChanged.disconnect') < block.index('stream.close()')


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

def test_keyboard_seek_is_coalesced_before_touching_media_backend() -> None:
    source = src__report_followup_round45_20260921('audioknigi/qt/player_mixin.py')
    init_start = source.index('def _init_player')
    init_end = source.index('def _selected_track', init_start)
    init = source[init_start:init_end]
    assert 'self._player_keyboard_seek_timer = QTimer(self)' in init
    assert 'setSingleShot(True)' in init
    assert 'setInterval(120)' in init
    preview_start = source.index('def _player_seek_preview')
    preview_end = source.index('def _on_player_volume_slider_moved', preview_start)
    preview = source[preview_start:preview_end]
    assert 'self._player_keyboard_seek_timer.start()' in preview
    assert 'self.player_controller.seek(int(value) * 1000)' not in preview
    commit_start = source.index('def _commit_keyboard_seek')
    commit_end = source.index('def _player_seek_preview', commit_start)
    commit = source[commit_start:commit_end]
    assert 'value = self.player_seek_slider.value()' in commit
    assert 'self.player_controller.seek(int(value) * 1000)' in commit


# Origin: test_report_followup_round46_20260922.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round46_20260922(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_windows_url_shortcut_accepts_matching_wrapping_quotes() -> None:
    source = src__report_followup_round46_20260922('audioknigi/qt/mixins/clipboard.py')
    start = source.index('match = re.search(r"(?im)^URL=(.+)$"')
    block = source[start:start + 500]
    assert 'shortcut_url = _unquote_shortcut_url(shortcut_url)' in block
    assert block.index('_unquote_shortcut_url(shortcut_url)') < block.index('valid_site_url(shortcut_url)')
    helper_start = source.index('def _unquote_shortcut_url')
    helper_end = source.index('class ClipboardUiMixin', helper_start)
    helper = source[helper_start:helper_end]
    assert 'text[0] == text[-1]' in helper
    assert 'return text[1:-1].strip()' in helper


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

def test_player_controls_have_explicit_screenreader_instructions_and_enter_shortcuts():
    player = (ROOT / 'audioknigi/qt/player_mixin.py').read_text(encoding='utf-8')
    access = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'Enter или пробел' in player
    assert 'for sequence in ("Return", "Enter")' in access
    assert 'Qt.ShortcutContext.WidgetShortcut' in access
    assert 'Space remains the native QPushButton action' in access

def test_narration_selection_auto_analyzes_and_focuses_download_after_analysis():
    search = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    analysis = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    assert 'def _easy_narration_selected' in search
    assert 'QTimer.singleShot(0, self.use_selected_result)' in search
    assert 'self._focus_download_after_analysis = True' in search
    assert 'self._focus_download_after_analysis = True' in analysis
    assert 'target = self.easy_download_button if self.current_ui_mode() == "easy" else self.download_all_button' in analysis
    assert 'Нажмите Enter или пробел, чтобы начать скачивание' in analysis

def test_help_center_uses_splitter_and_non_overlapping_topic_rows():
    source = (ROOT / 'audioknigi/qt/help_center.py').read_text(encoding='utf-8')
    assert 'QSplitter' in source
    assert 'self.topics.setWordWrap(True)' in source
    assert 'self.topics.setSpacing(4)' in source
    assert 'topic_row_height = max(42, self.topics.fontMetrics().height() * 2 + 12)' in source
    assert 'item.setSizeHint(QSize(0, topic_row_height))' in source
    assert 'splitter.setChildrenCollapsible(False)' in source
    tree = ast.parse(source)
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {'TOPICS', 'ROUND55_TOPIC_DETAILS_RU'}:
                    values[target.id] = ast.literal_eval(node.value)
    expected = {key for key, _title, _body in values['TOPICS']['ru']}
    details = values['ROUND55_TOPIC_DETAILS_RU']
    assert set(details) == expected
    assert all((len(text) >= 120 for text in details.values()))

def test_current_step_guidance_is_visible_and_accessible():
    main = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    access = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'identifier="current_guidance"' in main
    assert 'def _guidance_for_tab' in access
    for label in ('Книга:', 'Поиск:', 'Очередь:', 'История:', 'Настройки:', 'Плеер:'):
        assert label in access


# Origin: test_round56_qt_lifecycle_20260926.py
ROOT = Path(__file__).resolve().parents[2]

def test_accessibility_selftest_promotes_async_callback_exceptions_to_failure():
    source = (ROOT / 'audioknigi_qt.py').read_text(encoding='utf-8')
    assert 'capture_async_callback_error' in source
    assert 'sys.excepthook = capture_async_callback_error' in source
    assert 'Asynchronous Qt callback exception:' in source
    assert 'return 26' in source

def test_qt_accessibility_selftest_has_no_deleted_qt_callback_traceback():
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    result = subprocess.run([sys.executable, str(ROOT / 'audioknigi_qt.py'), '--qt-accessibility-selftest'], cwd=ROOT, env=env, text=True, capture_output=True, timeout=45, check=False)
    combined = (result.stdout or '') + '\n' + (result.stderr or '')
    assert result.returncode == 0, combined
    assert 'QT ACCESSIBILITY SELFTEST: OK' in combined
    assert 'Internal C++ object' not in combined
    assert 'already deleted' not in combined
    assert 'Traceback (most recent call last)' not in combined


# Origin: test_round57_selftest_finally_20260926.py
ROOT = Path(__file__).resolve().parents[2]

ENTRYPOINT = ROOT / 'audioknigi_qt.py'

def test_accessibility_selftest_is_warning_and_traceback_free_after_cleanup():
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    env['PYTHONWARNINGS'] = 'error::SyntaxWarning'
    result = subprocess.run([sys.executable, str(ENTRYPOINT), '--qt-accessibility-selftest'], cwd=ROOT, env=env, text=True, capture_output=True, timeout=45, check=False)
    combined = (result.stdout or '') + '\n' + (result.stderr or '')
    assert result.returncode == 0, combined
    assert 'QT ACCESSIBILITY SELFTEST: OK' in combined
    assert 'SyntaxWarning' not in combined
    assert 'Traceback (most recent call last)' not in combined
    assert 'Internal C++ object' not in combined


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

def test_qt_exposes_dns_mode_and_accessible_fallback_feedback():
    pages = (ROOT / 'audioknigi/qt/main_window_pages.py').read_text(encoding='utf-8')
    settings = (ROOT / 'audioknigi/qt/mixins/settings.py').read_text(encoding='utf-8')
    sync = (ROOT / 'audioknigi/qt/settings_sync.py').read_text(encoding='utf-8')
    accessibility = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    window = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    application = (ROOT / 'audioknigi/qt/application.py').read_text(encoding='utf-8')
    assert '"dns_mode_combo"' in pages
    assert '"Автоматически — Cloudflare с резервным системным DNS"' in pages
    assert '"dns_mode": self.dns_mode_combo.currentData() or "auto"' in settings
    assert 'install_cloudflare_dns(mode=str(updated.get("dns_mode", "auto") or "auto"))' in settings
    assert '("dns_mode_combo", data.get("dns_mode", "auto"))' in sync
    assert 'def _poll_dns_runtime_status' in accessibility
    assert 'автоматически переключилась на системный DNS' in accessibility
    assert '_dns_status_timer.timeout.connect(self._poll_dns_runtime_status)' in window
    assert 'install_cloudflare_dns(mode=str(settings.get("dns_mode", "auto") or "auto"))' in application

def test_help_center_explains_automatic_dns_recovery():
    help_text = (ROOT / 'audioknigi/qt/help_center.py').read_text(encoding='utf-8')
    assert 'пятиминутная пауза для Cloudflare' in help_text
    assert 'Такое переключение видно на экране и объявляется NVDA/JAWS' in help_text


# Origin: test_round68_creator_metadata_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_about_dialog_exposes_creator_and_keyboard_actions():
    source = (ROOT / 'audioknigi/qt/mixins/settings.py').read_text(encoding='utf-8')
    block = source[source.index('def _show_about'):source.index('__all__', source.index('def _show_about'))]
    assert 'QDialog(self)' in block
    assert 'QTextBrowser(dialog)' in block
    assert 'AUTHOR_NAME' in block
    assert 'AUTHOR_EMAIL' in block
    assert 'AUTHOR_GITHUB_URL' in block
    assert 'PROJECT_URL' in block
    assert 'QDesktopServices.openUrl' in block
    assert 'QApplication.clipboard().setText(AUTHOR_EMAIL)' in block
    assert 'text.setFocus' in block


# Origin: test_round72_search_sorting_availability_layout_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def _result(title: str, *, author: str='', narrator: str='', availability: str='') -> SearchResult:
    return SearchResult(title=title, author=author, narrator=narrator, availability=availability, url=f'https://example.invalid/{title}', source='demo')

def test_search_ui_has_no_status_column_and_has_accessible_sort_controls():
    model = (ROOT / 'audioknigi/qt/search_model.py').read_text(encoding='utf-8')
    search = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    easy = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    assert '("Статус", "availability")' not in model
    assert 'search_only_available_action' not in search
    assert 'identifier="search_sort"' in search
    assert 'sort_title.triggered.connect(lambda: self._sort_search_results("title"))' in search
    assert 'search_header.sectionClicked.connect(self._sort_search_results_by_column)' in search
    assert 'easy_header.sectionClicked.connect(self._sort_search_results_by_column)' in easy


# Origin: test_round73_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_easy_mode_recognizes_supported_schemeless_urls_and_reset_clears_focus_flag():
    source = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    update = source[source.index('def _update_easy_action_text'):source.index('def _set_operation_ui_blocked')]
    reset = source[source.index('def _easy_reset_to_initial_state'):source.index('def _easy_user_input_edited')]
    assert 'or valid_site_url(value)' in update
    assert 'self._focus_download_after_analysis = False' in reset


# Origin: test_round74_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_clipboard_shortcut_read_is_bounded_and_track_index_is_safe():
    source = (ROOT / 'audioknigi/qt/mixins/clipboard.py').read_text(encoding='utf-8')
    assert 'shortcut_file.read(65536)' in source
    assert 'track_index = safe_int(getattr(track, "index", None), 0)' in source
    assert 'int(track.index)' not in source[source.index('def download_selected_track_only'):]


# Origin: test_round81_external_review_followup_20261006.py
ROOT = Path(__file__).resolve().parents[2]

def test_help_accessibility_polish_is_present():
    messages = (ROOT / 'audioknigi/locales/messages.json').read_text(encoding='utf-8')
    assert 'розташовані в розширених налаштуваннях' in messages
    accessibility = (ROOT / 'audioknigi/qt/accessibility.py').read_text(encoding='utf-8')
    assert '"install_keyboard_focus_frame"' in accessibility
    assert '"KeyboardFocusFrameManager"' in accessibility
    context_menu = (ROOT / 'audioknigi/qt/localized_context_menu.py').read_text(encoding='utf-8')
    assert 'viewport.mapToGlobal(point)' in context_menu
    assert 'point.setX(max(visible.left(), min(visible.right(), point.x())))' in context_menu
    assert 'widget.mapToGlobal(widget.rect().bottomLeft())' in context_menu
    help_center = (ROOT / 'audioknigi/qt/help_center.py').read_text(encoding='utf-8')
    assert 'Leertaste|Пробел|Пробіл|Esc' in help_center


# Origin: test_stability_localization_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_accessibility_worker_path_never_calls_widget_window():
    source = (ROOT / 'audioknigi' / 'qt' / 'accessibility.py').read_text(encoding='utf-8')
    announce = source[source.index('def announce('):source.index('class AccessibleAnnouncer')]
    assert 'widget.window()' not in announce
    assert '_DEFAULT_ANNOUNCER_REF' in announce

def test_player_tab_has_alt_shortcut_too():
    source = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'accessibility_ui.py').read_text(encoding='utf-8')
    marker = 'for number, tab_index in enumerate([self.TAB_BOOK, self.TAB_SEARCH, self.TAB_QUEUE, self.TAB_HISTORY, self.TAB_SETTINGS, self.TAB_PLAYER], start=1):'
    assert source.count(marker) >= 2

# Post-consolidation: Round 83 external audit follow-up.
def test_focus_table_row_fails_closed_for_deleted_qt_wrappers_source_contract():
    source = (ROOT / 'audioknigi/qt/accessibility.py').read_text(encoding='utf-8')
    start = source.index('def focus_table_row(')
    end = source.index('__all__', start)
    block = source[start:end]
    assert 'except RuntimeError:' in block
    assert 'return False' in block


def test_ui_mode_switch_releases_easy_only_operation_block_source_contract():
    source = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    start = source.index('def set_ui_mode(')
    end = source.index('def current_ui_mode', start)
    block = source[start:end]
    assert 'if self._operation_dialog is not None:' in block
    assert 'self._set_operation_ui_blocked(mode == "easy")' in block

# Post-consolidation: Round 84 user-log/accessibility follow-up.
def test_f1_shortcuts_action_uses_triggered_bool_compatible_slot():
    source = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'def show_shortcuts_help(self, _checked=False):' in source
    assert 'shortcuts_action.triggered.connect(self.show_shortcuts_help)' in source
    assert 'shortcuts_action.triggered.connect(lambda: self.show_context_help(topic="shortcuts"))' not in source


def test_context_help_action_and_f1_shortcuts_keep_separate_topics():
    source = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'help_action.setShortcut(QKeySequence("Shift+F1"))' in source
    assert 'help_action.triggered.connect(self.show_context_help)' in source
    assert 'shortcuts_action.setShortcut(QKeySequence("F1"))' in source
    shortcuts = source[source.index('def show_shortcuts_help'):source.index('def copy_last_crash_report')]
    assert 'self.show_context_help(topic="shortcuts")' in shortcuts


# Post-consolidation: Round 86 external audit follow-up.
def test_accessibility_round86_keyboard_and_localization_contracts():
    accessibility = (ROOT / "audioknigi/qt/accessibility.py").read_text(encoding="utf-8")
    help_center = (ROOT / "audioknigi/qt/help_center.py").read_text(encoding="utf-8")
    context_menu = (ROOT / "audioknigi/qt/localized_context_menu.py").read_text(encoding="utf-8")
    pages = (ROOT / "audioknigi/qt/main_window_pages.py").read_text(encoding="utf-8")
    track_model = (ROOT / "audioknigi/qt/track_model.py").read_text(encoding="utf-8")

    assert "_DIRECT_ANNOUNCE_LAST_AT < 0.25" in accessibility
    assert "Leertaste|Пробел|Пробіл|Esc" in help_center
    assert "point.setX(max(visible.left(), min(visible.right(), point.x())))" in context_menu
    assert "point.setY(max(visible.top(), min(visible.bottom(), point.y())))" in context_menu

    # Accessible names/descriptions in the page builder are now localized.
    assert 'name="' not in pages
    assert 'description="' not in pages
    assert 'settings_general' in pages
    assert 'settings_download_network' in pages
    assert 'settings_appearance_sound' in pages
    assert 'settings_integrations_backup' in pages
    assert 'identifier="settings_" + title.lower()' not in pages

    assert "Qt.ItemDataRole.CheckStateRole" in track_model
    assert "Qt.ItemDataRole.AccessibleTextRole" in track_model
    assert "Qt.ItemDataRole.AccessibleDescriptionRole" in track_model
    assert "self.dataChanged.emit(left, right, [])" not in track_model


def test_missing_media_skip_is_resolved_only_after_clicked_button_is_known():
    source = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")
    block = source[source.index("def _resolve_missing_media"):source.index("def _download_request_changed")]
    assert "box.finished.connect(" not in block
    assert "clicked_button = box.clickedButton()" in block
    assert 'prompt.resolve("skip" if skip_button is not None and clicked_button is skip_button else "stop")' in block


def test_queue_move_and_easy_mode_preserve_single_accessible_focus_context():
    queue = (ROOT / "audioknigi/qt/mixins/queue.py").read_text(encoding="utf-8")
    move = queue[queue.index("def move_queue_selected"):queue.index("def remove_queue_selected")]
    assert "QSignalBlocker(self.queue_table)" in move
    assert "self.queue_table.selectRow(new_idx)" not in move
    assert "focus_table_row(self.queue_table, new_idx, column=2, focus=True)" in move

    main = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    block = main[main.index("def _easy_operation_active"):main.index("def _easy_reset_to_initial_state")]
    assert 'getattr(self, "_queue_running", False)' in block


def test_ui_scale_uses_resolved_immutable_baseline_and_speed_graph_clamps_bounds():
    application = (ROOT / "audioknigi/qt/application.py").read_text(encoding="utf-8")
    scale = application[application.index("def apply_ui_scale"):application.index("def create_application")]
    assert "if base_font.pointSizeF() <= 0 and base_font.pixelSize() <= 0:" in scale
    assert "base_font.setPointSizeF(effective)" in scale
    assert "app._audioknigi_base_font_py = QFont(base_font)" in scale

    graph = (ROOT / "audioknigi/qt/speed_graph.py").read_text(encoding="utf-8")
    assert "graph_bottom = max(graph_top, self.height() - 3)" in graph
    assert "min(float(self.height() - 2), y)" in graph


def test_event_sound_shutdown_balances_unconsumed_sentinel_source_contract():
    source = (ROOT / "audioknigi/qt/event_sounds.py").read_text(encoding="utf-8")
    shutdown = source[source.index("def shutdown(self):"):source.index("__all__")]
    assert shutdown.count("self._system_sound_queue.get_nowait()") >= 2
    assert shutdown.count("self._system_sound_queue.task_done()") >= 2
