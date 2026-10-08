"""Consolidated integration tests for the qt ui domain.

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
import ast
from audioknigi.download.errors import MissingSelectedTracksError
from audioknigi.metadata import APP_VERSION
from audioknigi.services.queue_service import task_from_dict
from tools.exception_audit import audit as exception_audit
from tools.historical_regression_audit import _normalize_nodeid
from tools.qt_localization_audit import _assignment_value
from tools.undefined_global_audit import _SPECIAL_GLOBALS
from collections import UserDict
from audioknigi.core import Cancelled, _structured_book_nodes
from audioknigi.diagnostics import support_bundle as support_bundle__report_followup_round12_20260916
from audioknigi.download_engine import _DownloadEngine
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.services.download_request import build_download_request
from types import SimpleNamespace
from audioknigi.sources import is_supported_url, normalize_supported_url
from audioknigi import poleknig
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.services import book_analysis_service as analysis_module
from audioknigi.models import Book, SearchResult
import inspect
import socket
from audioknigi import core, poleknig
from audioknigi.network_dns import _relay_bidirectional
from audioknigi import core
from audioknigi.core import fmt_size
from audioknigi.templates import render_text_template
from audioknigi.knigavuhe import _description_from_html as knigavuhe_description
from audioknigi.poleknig import _book_page_metadata as poleknig_metadata
import hashlib
import math
import zipfile
import audioknigi.config.settings as settings_module__report_followup_round49_20260924
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round49_20260924
import audioknigi.download.source_analysis as source_analysis_module
from audioknigi.download.source_analysis import SourceAnalysisMixin
from audioknigi.services.player_position_store import PlayerPositionStore
from audioknigi.diagnostics.support_bundle import _sanitize_log_bytes, _tail
from audioknigi.download.probe import ProbeMixin
from audioknigi.qt.acceptance_contract import ACCEPTANCE_SCHEMA, acceptance_issues
from tools import qt_localization_audit, qt_windows_acceptance
import os
import subprocess
import sys
from audioknigi.models import SearchResult
from audioknigi import network_dns
from audioknigi.services import library_service
from audioknigi.services.queue_service import _parse_created_at


# Origin: test_persistence_cancellation_hardening_20260929.py
def _book() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1-test', title='Test', tracks=[Track(index=1, title='Part 1', file='https://example.com/1.mp3')])

def test_scale_is_clamped_after_ui_migration(monkeypatch):

    def migrate(payload):
        data = dict(payload)
        data['scale'] = 999
        return (data, True)
    monkeypatch.setattr(settings_module__persistence_cancellation_hardening_20260929, 'migrate_ui_scale_settings', migrate)
    normalized, migrated = settings_module__persistence_cancellation_hardening_20260929.migrate_settings({'scale': 100})
    assert migrated is True
    assert normalized['scale'] == 200


# Origin: test_release_integrity_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_historical_nodeid_normalization_is_windows_safe():
    raw = '.historical-regression-abcd\\test_queue.py::test_case'
    assert _normalize_nodeid(raw, '.historical-regression-abcd') == 'test_queue.py::test_case'


# Origin: test_report_followup_round12_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_support_tail_keeps_valid_utf8_when_byte_window_cuts_codepoints(tmp_path):
    path = tmp_path / 'app.log'
    path.write_bytes(('я' * 20).encode('utf-8'))
    payload = support_bundle__report_followup_round12_20260916._tail(path, max_bytes=7)
    payload.decode('utf-8')
    assert payload


# Origin: test_report_followup_round19_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_round19_windows_file_retry_contracts_are_used() -> None:
    network = (ROOT / 'audioknigi/download/network.py').read_text(encoding='utf-8')
    flow = (ROOT / 'audioknigi/download/book_flow.py').read_text(encoding='utf-8')
    assert 'replace_with_retry(part, target)' in network
    assert 'from .common import replace_with_retry, source_target_assignments, unlink_with_retry' in flow
    assert 'unlink_with_retry(path, missing_ok=False)' in flow


# Origin: test_report_followup_round22_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_safe_name_replaces_windows_control_characters() -> None:
    value = core.safe_name('part\x00one\x1f?.mp3')
    assert value.endswith('.mp3')
    assert '?' not in value
    assert all((ord(ch) >= 32 for ch in value))
    assert 'part_one__' in value


# Origin: test_report_followup_round26_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_easy_progress_window_uses_manual_ui_blocking_not_native_modality() -> None:
    dialog = (ROOT / 'audioknigi/qt/operation_dialog.py').read_text(encoding='utf-8')
    main = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    assert 'Qt.WindowModality.NonModal' in dialog
    assert 'self.setModal(False)' in dialog
    assert 'Qt.WindowModality.ApplicationModal' not in dialog
    assert 'self.setModal(True)' not in dialog
    assert 'central.setEnabled(not blocked)' in main
    assert 'menu.setEnabled(not blocked)' in main

def test_operation_finish_hides_dialog_without_accept_or_done() -> None:
    dialog = (ROOT / 'audioknigi/qt/operation_dialog.py').read_text(encoding='utf-8')
    start = dialog.index('def finish')
    end = dialog.index('def reject', start)
    block = dialog[start:end]
    assert 'self.hide()' in block
    assert 'self.accept()' not in block
    assert 'self.done(' not in block

def test_operation_finish_has_begin_end_diagnostics_and_reenables_ui() -> None:
    source = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    start = source.index('def _finish_blocking_operation')
    end = source.index('def _l', start)
    block = source[start:end]
    assert 'event=finish_begin' in block
    assert 'event=finish_end' in block
    assert 'self._set_operation_ui_blocked(False)' in block


# Origin: test_report_followup_round27_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def _source__report_followup_round27_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_no_known_worker_to_window_gui_connection_bypasses_qobject_relay() -> None:
    for relative in ('audioknigi/qt/mixins/search.py', 'audioknigi/qt/mixins/analysis_download.py', 'audioknigi/qt/mixins/settings.py'):
        source = _source__report_followup_round27_20260918(relative)
        for line in source.splitlines():
            stripped = line.strip()
            if 'worker.' in stripped and '.connect(self.' in stripped:
                assert 'self._worker_ui_relay.' in stripped, (relative, stripped)
                assert 'Qt.ConnectionType.QueuedConnection' in stripped, (relative, stripped)
            if 'thread.finished.connect(self.' in stripped:
                assert 'self._worker_ui_relay.' in stripped, (relative, stripped)
                assert 'Qt.ConnectionType.QueuedConnection' in stripped, (relative, stripped)


# Origin: test_report_followup_round28_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def _source__report_followup_round28_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_worker_ui_relay_is_real_qobject_owned_by_main_window() -> None:
    relay = _source__report_followup_round28_20260918('audioknigi/qt/worker_ui_relay.py')
    main = _source__report_followup_round28_20260918('audioknigi/qt/main_window.py')
    assert 'class WorkerUiRelay(QObject):' in relay
    assert 'super().__init__(owner)' in relay
    assert 'self._worker_ui_relay = WorkerUiRelay(self)' in main


# Origin: test_report_followup_round31_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def _source__report_followup_round31_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_manual_empty_easy_input_uses_same_reset_path_as_next_book_button() -> None:
    source = _source__report_followup_round31_20260918('audioknigi/qt/main_window.py')
    assert 'self.easy_input.textEdited.connect(self._easy_user_input_edited)' in source
    assert 'def _easy_reset_to_initial_state' in source
    assert 'def _easy_user_input_edited' in source
    assert 'if self._easy_operation_active():' in source
    assert 'self._easy_reset_to_initial_state(clear_input=False, focus=False)' in source
    easy_start = source.index('def easy_add_another_book')
    easy_end = source.index('def _play_event_sound', easy_start)
    easy_block = source[easy_start:easy_end]
    assert 'self.book_url_edit.clear()' in easy_block
    assert 'self._easy_reset_to_initial_state(clear_input=True, focus=True)' in easy_block


# Origin: test_report_followup_round33_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round33_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_ctrl_d_respects_selected_tracks_and_batch_errors_do_not_stack_dialogs() -> None:
    accessibility = src__report_followup_round33_20260918('audioknigi/qt/mixins/accessibility_ui.py')
    analysis = src__report_followup_round33_20260918('audioknigi/qt/mixins/analysis_download.py')
    assert '_add_window_shortcut("Ctrl+D", self._start_primary_download)' in accessibility
    assert 'Qt.ShortcutContext.WindowShortcut' in accessibility
    error_block = analysis[analysis.index('if kind == "error":'):analysis.index('book = payload')]
    assert 'batch_pending = bool(getattr(self, "_pending_queue_urls", None))' in error_block
    assert 'if batch_pending:' in error_block
    assert 'self._append_log("Ошибка анализа при пакетном добавлении: " + str(payload))' in error_block
    assert 'else:\n                self._show_message' in error_block


# Origin: test_report_followup_round36_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round36_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_easy_card_is_substantially_wider_and_table_keeps_adaptive_header_modes() -> None:
    source = src__report_followup_round36_20260919('audioknigi/qt/main_window.py')
    assert 'card.setMinimumWidth(820)' in source
    assert 'card.setMaximumWidth(1500)' in source
    assert 'card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)' in source
    assert 'center_row.addWidget(card, 8)' in source
    assert 'easy_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)' in source
    assert 'if key in {"index", "availability", "variants", "source"}:' in source
    assert 'self.easy_search_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)' in source

def test_both_ui_modes_render_the_same_book_description_field() -> None:
    source = src__report_followup_round36_20260919('audioknigi/qt/mixins/analysis_download.py')
    assert 'self.book_description.setText(str(book.description or self._l("Описание отсутствует.")))' in source
    assert 'easy_description = str(book.description or "").strip()' in source
    assert 'self.easy_description.setPlainText(easy_description)' in source


# Origin: test_report_followup_round39_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round39_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_production_theme_has_cohesive_app_chrome() -> None:
    theme = src__report_followup_round39_20260919('audioknigi/qt/theme.py')
    for selector in ('QWidget#appHeader', 'QLabel#appBrand', 'QLabel#appSubtitle', 'QMenuBar', 'QMenu', 'QStatusBar', 'QToolTip'):
        assert selector in theme
    assert 'accent = "#0a6ed1"' in theme
    assert 'focus = "#e5a93c"' in theme

def test_tables_lists_headers_tabs_and_scrollbars_have_production_styling() -> None:
    theme = src__report_followup_round39_20260919('audioknigi/qt/theme.py')
    for selector in ('QTableView, QTableWidget', 'QListWidget, QTreeView', 'QHeaderView::section', 'QTabWidget::pane', 'QTabBar::tab', 'QScrollBar:vertical', 'QScrollBar:horizontal'):
        assert selector in theme
    assert 'gridline-color: {table_grid}' in theme
    assert 'selection-background-color' in theme

def test_main_window_uses_named_production_header_and_roomier_easy_card() -> None:
    source = src__report_followup_round39_20260919('audioknigi/qt/main_window.py')
    assert 'header.setObjectName("appHeader")' in source
    assert 'title.setObjectName("appBrand")' in source
    assert 'self.subtitle_label.setObjectName("appSubtitle")' in source
    assert 'layout.setContentsMargins(30, 28, 30, 28)' in source
    assert 'self.easy_input.setMinimumHeight(42)' in source
    assert 'self.easy_download_button.setMinimumHeight(48)' in source

def test_advanced_tables_use_clean_gridless_per_pixel_scrolling() -> None:
    expectations = {'audioknigi/qt/main_window_pages.py': 'self.track_table', 'audioknigi/qt/mixins/search.py': 'self.search_table', 'audioknigi/qt/mixins/history.py': 'self.history_table', 'audioknigi/qt/mixins/queue.py': 'self.queue_table'}
    for relative, widget in expectations.items():
        source = src__report_followup_round39_20260919(relative)
        assert f'{widget}.setShowGrid(False)' in source
        assert f'{widget}.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)' in source


# Origin: test_report_followup_round40_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round40_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_secondary_text_has_stronger_dark_theme_contrast() -> None:
    theme = src__report_followup_round40_20260920('audioknigi/qt/theme.py')
    assert 'secondary = "#9ba3af"' in theme
    assert 'QLabel#secondaryText {{ color: {secondary}; }}' in theme
    assert 'QLabel#emptyState {{\n    color: {secondary};' in theme

def test_advanced_workspace_width_policy_is_explicit() -> None:
    window = src__report_followup_round40_20260920('audioknigi/qt/main_window.py')
    assert 'self.tabs.setMaximumWidth(16777215)' in window
    assert 'self.mode_stack.addWidget(self.tabs)' in window
    assert 'self.tabs.setMaximumWidth(1500)' not in window


# Origin: test_report_followup_round41_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round41_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_advanced_data_tabs_use_full_workspace_width() -> None:
    window = src__report_followup_round41_20260920('audioknigi/qt/main_window.py')
    assert 'layout.setContentsMargins(16, 10, 16, 12)' in window
    assert 'layout.setSpacing(8)' in window
    assert 'self.tabs.setMaximumWidth(16777215)' in window
    assert 'self.mode_stack.addWidget(self.tabs)' in window
    assert 'self.tabs.setMaximumWidth(1500)' not in window

def test_wide_tables_have_stronger_zebra_striping() -> None:
    theme = src__report_followup_round41_20260920('audioknigi/qt/theme.py')
    assert 'table_bg = "#181a1f"' in theme
    assert 'table_alt = "#20242c"' in theme
    assert 'table_grid = "#2d333f"' in theme
    assert 'QTableView, QTableWidget {{' in theme
    assert 'background: {table_bg};' in theme
    assert 'alternate-background-color: {table_alt};' in theme
    assert 'QTableView::item, QTableWidget::item {{ padding: 6px 10px;' in theme

def test_menu_is_shifted_away_from_top_left_overlay() -> None:
    theme = src__report_followup_round41_20260920('audioknigi/qt/theme.py')
    assert 'spacing: 6px;' in theme
    assert 'padding: 3px 6px 3px 10px;' in theme


# Origin: test_report_followup_round42_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round42_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_event_and_windows_system_sound_preview_are_distinct() -> None:
    pages = src__report_followup_round42_20260920('audioknigi/qt/main_window_pages.py')
    settings = src__report_followup_round42_20260920('audioknigi/qt/mixins/settings.py')
    events = src__report_followup_round42_20260920('audioknigi/qt/event_sounds.py')
    assert 'QPushButton(self._l("Проверить звук события"))' in pages
    assert 'QPushButton(self._l("Проверить системный звук"))' in pages
    assert 'self.preview_voice_button.clicked.connect(self.preview_event_sound)' in pages
    assert 'self.preview_system_button.clicked.connect(self.preview_system_sound)' in pages
    assert 'self.event_sound_manager.play_media_only("search_complete", force=True)' in settings
    assert 'self.event_sound_manager.play_system("app_ready")' in settings
    assert 'def play_media_only(self, event: str, *, force=False) -> bool:' in events
    assert 'allow_system_fallback=False' in events
    assert 'return self.play_system(event) if allow_system_fallback else False' in events
    assert 'if media_status == QMediaPlayer.MediaStatus.InvalidMedia:' in events
    assert '"search_complete": "search_complete.mp3"' in events
    assert (ROOT / 'assets/sounds/search_complete.mp3').is_file()

def test_system_theme_uses_qt_color_scheme_and_stable_tokens() -> None:
    theme = src__report_followup_round42_20260920('audioknigi/qt/theme.py')
    assert 'app.styleHints().colorScheme()' in theme
    assert 'scheme == Qt.ColorScheme.Dark' in theme
    assert 'scheme == Qt.ColorScheme.Light' in theme
    assert 'colorSchemeChanged.connect' in theme
    assert 'native_palette = app.style().standardPalette()' in theme
    assert 'app.setPalette(_dark_palette() if system_dark else _light_palette())' in theme
    assert 'system_palette.color(QPalette.ColorRole.Window).lightness() < 128' in theme
    assert 'if system_dark:' in theme
    assert 'window = "#171a1f"' in theme
    assert 'surface = "#22262d"' in theme
    assert 'window = "#f3f5f8"' in theme
    assert 'surface = "#ffffff"' in theme
    system_block = theme.split('    else:\n        system_palette = palette or QPalette()', 1)[1].split('\n    return f', 1)[0]
    assert 'surface = "palette(base)"' not in system_block
    assert 'border = "palette(mid)"' not in system_block

def test_system_theme_never_mixes_native_palette_with_custom_dark_or_light_qss() -> None:
    theme = src__report_followup_round42_20260920('audioknigi/qt/theme.py')
    refresh = theme.split('def _refresh_system_theme', 1)[1].split('def _ensure_system_scheme_listener', 1)[0]
    apply_block = theme.split('def apply_theme', 1)[1]
    assert 'app.setPalette(_dark_palette() if system_dark else _light_palette())' in refresh
    assert 'app.setPalette(_dark_palette() if system_dark else _light_palette())' in apply_block
    assert 'app.setPalette(app.style().standardPalette())' not in refresh
    assert 'System theme' in theme or 'System mode' in theme

def test_preview_buttons_report_success_or_failure_to_status_bar() -> None:
    settings = src__report_followup_round42_20260920('audioknigi/qt/mixins/settings.py')
    assert 'def preview_event_sound(self):' in settings
    assert 'def preview_system_sound(self):' in settings
    assert 'Не удалось воспроизвести встроенный звук события.' in settings
    assert 'Системный звук Windows недоступен.' in settings


# Origin: test_report_followup_round48_20260923.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round48_20260923(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_advanced_book_table_keeps_stable_column_policy_after_analysis() -> None:
    pages = src__report_followup_round48_20260923('audioknigi/qt/main_window_pages.py')
    analysis = src__report_followup_round48_20260923('audioknigi/qt/mixins/analysis_download.py')
    assert 'track_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)' in pages
    assert 'track_header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)' in pages
    assert 'self.track_table.setColumnWidth(7, 280)' in pages
    assert 'self.track_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)' in pages
    assert 'self.track_table.setMinimumWidth(0)' in pages
    assert 'self.track_table.resizeColumnsToContents()' not in analysis

def test_advanced_book_description_is_bounded_scrollable_text() -> None:
    pages = src__report_followup_round48_20260923('audioknigi/qt/main_window_pages.py')
    assert 'self.book_description = QTextEdit()' in pages
    assert 'self.book_description.setReadOnly(True)' in pages
    assert 'self.book_description.setTabChangesFocus(True)' in pages
    assert 'self.book_description.setMaximumHeight(72)' in pages
    assert 'self.book_summary.setMaximumHeight(58)' in pages

def test_advanced_book_details_are_a_compact_stateful_card() -> None:
    pages = src__report_followup_round48_20260923('audioknigi/qt/main_window_pages.py')
    analysis = src__report_followup_round48_20260923('audioknigi/qt/mixins/analysis_download.py')
    window = src__report_followup_round48_20260923('audioknigi/qt/main_window.py')
    assert 'self.book_details_panel.setObjectName("bookCard")' in pages
    assert 'self.book_details_panel.setVisible(False)' in pages
    assert 'self.book_details_panel.setVisible(True)' in analysis
    assert 'self.book_details_panel.setVisible(False)' in window
    assert 'self.book_cover_label.setFixedSize(108, 108)' in pages

def test_advanced_result_controls_and_table_only_consume_space_for_real_book() -> None:
    pages = src__report_followup_round48_20260923('audioknigi/qt/main_window_pages.py')
    analysis = src__report_followup_round48_20260923('audioknigi/qt/mixins/analysis_download.py')
    window = src__report_followup_round48_20260923('audioknigi/qt/main_window.py')
    assert 'self.track_controls_panel.setVisible(False)' in pages
    assert 'self.track_table.setVisible(False)' in pages
    assert 'self.track_controls_panel.setVisible(enabled)' in analysis
    assert 'self.track_table.setVisible(enabled)' in analysis
    assert 'self.track_controls_panel.setVisible(False)' in window
    assert 'self.track_table.setVisible(False)' in window

def test_advanced_progress_panels_only_take_layout_space_while_active() -> None:
    pages = src__report_followup_round48_20260923('audioknigi/qt/main_window_pages.py')
    analysis = src__report_followup_round48_20260923('audioknigi/qt/mixins/analysis_download.py')
    assert 'self.analysis_progress.setVisible(False)' in pages
    assert 'self.analysis_progress.setVisible(True)' in analysis
    assert 'self.download_activity_panel.setVisible(False)' in pages
    assert 'self.download_activity_panel.setVisible(True)' in analysis
    assert 'self.download_activity_panel.setVisible(False)' in analysis


# Origin: test_report_followup_round49_20260924.py
class _FallbackHost(SourceAnalysisMixin):
    cancel_event = None
    _book_identity_hints = staticmethod(BookAnalysisService._book_identity_hints)
    _identity_tokens = staticmethod(BookAnalysisService._identity_tokens)

    def _check_cancel(self) -> None:
        return None

def test_easy_card_minimum_matches_declared_900px_window_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    assert 'self.setMinimumSize(900, 620)' in source
    assert 'card.setMinimumWidth(820)' in source
    assert 'card.setMinimumWidth(860)' not in source


# Origin: test_report_followup_round50_20260924.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round50_20260924(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_advanced_empty_book_state_owns_spare_vertical_space() -> None:
    pages = src__report_followup_round50_20260924('audioknigi/qt/main_window_pages.py')
    assert 'intro.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)' in pages
    assert 'url_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)' in pages
    assert 'self.book_empty_state.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)' in pages
    assert 'layout.addWidget(self.book_empty_state, 1)' in pages
    assert 'layout.addWidget(self.track_table, 1)' in pages

def test_easy_and_advanced_universal_inputs_are_wired_bidirectionally() -> None:
    main = src__report_followup_round50_20260924('audioknigi/qt/main_window.py')
    settings = src__report_followup_round50_20260924('audioknigi/qt/mixins/settings.py')
    assert 'self._syncing_book_inputs = False' in main
    assert 'self._wire_book_input_sync()' in main
    assert 'def _wire_book_input_sync(self):' in settings
    assert 'for name in ("book_url_edit", "easy_input", "search_edit")' in settings
    assert 'def _sync_book_input_text(self, source, text: str):' in settings
    assert 'edit.setText(text)' in settings


# Origin: test_report_followup_round54_20260926.py
def test_support_tail_drops_partial_line_that_can_hide_windows_path_prefix(tmp_path):
    path = tmp_path / 'app.log'
    path.write_bytes(('prefix ' + 'X' * 80 + 'C:\\Users\\Alice\\Private\\Book\\chapter.mp3' + '\r\n').encode('utf-8'))
    payload = _tail(path, max_bytes=24, privacy_safe=True)
    assert payload == b'[truncated]\n'
    sanitized = _sanitize_log_bytes(payload).decode('utf-8')
    assert 'Alice' not in sanitized
    assert 'Private' not in sanitized


# Origin: test_round56_qt_lifecycle_20260926.py
ROOT = Path(__file__).resolve().parents[2]

def test_delayed_window_callbacks_use_lifecycle_safe_scheduler():
    source = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    assert 'def _single_shot_if_alive' in source
    assert '"Internal C++ object" in message and "already deleted" in message' in source
    assert 'self._single_shot_if_alive(300, "_schedule_clipboard_prompt_check")' in source
    assert 'self._single_shot_if_alive(900, "_start_source_health_check")' in source
    assert 'self._single_shot_if_alive(0, "_refresh_context_guidance", announce_now=True)' in source
    assert 'QTimer.singleShot(0, lambda: self._refresh_context_guidance' not in source


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

def test_extra_catalog_terms_still_keep_stable_two_word_title_phrase(monkeypatch):
    rows = [SearchResult(title='Гарри Поттер и философский камень', author='Джоан Роулинг', url='https://poleknig.com/books/1', source='poleknig.com')]
    results = _run_search(monkeypatch, 'гарри поттер аудиокнига росмэн', rows)
    assert [item.url for item in results] == ['https://poleknig.com/books/1']


# Origin: test_round67_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_qt_worker_callbacks_are_signal_emitters_not_widget_methods():
    source = (ROOT / 'audioknigi/qt/workers.py').read_text(encoding='utf-8')
    start = source.index('callbacks = DownloadCallbacks(')
    end = source.index(')', start) + 1
    block = source[start:end]
    assert 'stage=self.stage.emit' in block
    assert 'progress=self.progress.emit' in block
    assert 'status=self.status.emit' in block
