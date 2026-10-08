"""Consolidated integration tests for the search domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


import json
from pathlib import Path
import threading
import time
import pytest
from audioknigi.config import settings as settings_module
from audioknigi.core import Cancelled
from audioknigi.models import Book, Track
from audioknigi.providers import audioknigi_search
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.library_service import scan_unfinished
from audioknigi.services.queue_service import QueueTask, task_from_dict, task_to_dict
from audioknigi.services import search_service
import importlib.util
from audioknigi.core import extract_metadata_from_html
from audioknigi.logging_utils import sanitize_log_text
from audioknigi.models import Book, SearchResult, Track
from audioknigi.services.library_service import export_history
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict
from types import SimpleNamespace
from audioknigi.sources import is_supported_url, normalize_supported_url
from audioknigi import poleknig
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.services import book_analysis_service as analysis_module
from audioknigi.models import Book, SearchResult
from audioknigi.config.settings import migrate_settings
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.providers.audioknigi_search import _canonical_title
from audioknigi.services.book_analysis_service import _playlist_track_title
from audioknigi import core
from audioknigi.core import fmt_size
from audioknigi.templates import render_text_template
from audioknigi.download_engine import _DownloadEngine
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi.knigavuhe import _extract_names
from audioknigi.services.queue_service import _normalize_queue_download_mode, _track_from_dict
import ast
from audioknigi.models import SearchResult
from audioknigi.services.source_health_service import SourceHealthItem, SourceHealthOutcome
from audioknigi.config.settings import AppSettings
from audioknigi.download.probe import ProbeMixin
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, _DownloadEngine
from audioknigi.i18n import localize_runtime_text
from audioknigi.services.player_position_store import PlayerPositionStore
from audioknigi.services.search_service import downloadable_search_results, search_result_sort_key
from audioknigi import cover_fetch
from audioknigi.core import display_track_timeline
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services.queue_service import _book_from_dict
from audioknigi.templates import _safe_track_index
from threading import Event
from audioknigi.download_engine import DownloadService
from audioknigi.i18n import tr
from audioknigi.providers.audioknigi_search import search_audioknigi
from audioknigi.services.download_request import DownloadRequest, build_download_request


# Origin: test_persistence_cancellation_hardening_20260929.py
def _book__persistence_cancellation_hardening_20260929() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1-test', title='Test', tracks=[Track(index=1, title='Part 1', file='https://example.com/1.mp3')])

def test_multi_source_search_cooperative_cancel_returns_promptly(monkeypatch):

    class Provider:
        key = 'fake'
        display_name = 'fake.example'

        def search(self, query, *, cancel_event=None):
            while cancel_event is None or not cancel_event.is_set():
                time.sleep(0.01)
            raise Cancelled('cancelled')

        def enrich_search_results(self, results, *, cancel_event=None):
            return list(results)
    monkeypatch.setattr(search_service, 'registered_providers', lambda: [Provider()])
    cancel = threading.Event()
    outcome = {}

    def run():
        try:
            search_service.search_all_sources('test', cancel_event=cancel)
        except BaseException as exc:
            outcome['error'] = exc
    thread = threading.Thread(target=run)
    thread.start()
    time.sleep(0.05)
    cancel.set()
    thread.join(timeout=1.0)
    assert not thread.is_alive()
    assert isinstance(outcome.get('error'), Cancelled)


# Origin: test_release_quality_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_search_dedup_source_uses_dataclass_replace_not_in_place_mutation():
    source = (ROOT / 'audioknigi/services/search_service.py').read_text(encoding='utf-8')
    assert 'replace(result, url=canonical)' in source
    assert 'result.url = canonical' not in source

def _request() -> DownloadRequest:
    book = Book(url='https://knigavuhe.org/book/1', title='Book', tracks=[Track(index=1, title='One', file='https://cdn.example/1.mp3')])
    return DownloadRequest(book=book, selected_indices=None, output_dir=Path('.'))


# Origin: test_report_followup_round19_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_round19_easy_mode_free_text_search_is_not_treated_as_stale_url() -> None:
    source = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    block = source.split('def _update_easy_action_text', 1)[1].split('def _l', 1)[0]
    assert 'incoming_url = normalize_supported_url(value) if is_url and valid_site_url(value) else ""' in block
    assert 'easy_stale = bool(is_url and not' in block


# Origin: test_report_followup_round24_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_easy_mode_has_blocking_progress_for_search_analysis_and_download() -> None:
    main = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    dialog = (ROOT / 'audioknigi/qt/operation_dialog.py').read_text(encoding='utf-8')
    search = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    analysis = (ROOT / 'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    assert 'self.current_ui_mode() != "easy"' in main
    assert 'Qt.WindowModality.NonModal' in dialog
    assert 'central.setEnabled(not blocked)' in main
    assert '_show_blocking_operation(\n            "search"' in search
    assert '_show_blocking_operation(\n            "analysis"' in analysis
    assert '_show_blocking_operation(\n                "download"' in analysis
    assert 'cancelRequested' in dialog


# Origin: test_report_followup_round25_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_search_service_reserves_100_percent_for_actual_worker_completion() -> None:
    source = (ROOT / 'audioknigi/services/search_service.py').read_text(encoding='utf-8')
    assert 'report(99, "Завершаю поиск")' in source
    assert 'report(100, "Поиск завершён")' not in source

def test_search_finished_closes_modal_before_deferred_table_render() -> None:
    source = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    start = source.index('def _search_finished')
    end = source.index('def _clear_search_thread', start)
    block = source[start:end]
    assert 'self._finish_blocking_operation("search")' in block
    assert 'QTimer.singleShot(0, lambda outcome=outcome: self._apply_search_outcome(outcome))' in block
    assert block.index('self._finish_blocking_operation("search")') < block.index('QTimer.singleShot(0, lambda outcome=outcome: self._apply_search_outcome(outcome))')
    assert '.resizeColumnsToContents()' not in block
    assert 'def _apply_search_outcome' in block
    assert 'def _focus_search_result_after_render' in block

def test_search_completion_has_worker_and_ui_diagnostic_boundaries() -> None:
    workers = (ROOT / 'audioknigi/qt/workers.py').read_text(encoding='utf-8')
    ui = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    for marker in ('event=run_start', 'event=service_return', 'event=finished_emit', 'event=finished_emit_return'):
        assert marker in workers
    for marker in ('event=finished_slot_enter', 'event=modal_finished', 'event=result_render_start', 'event=model_reset_complete', 'event=result_render_complete', 'event=focus_complete'):
        assert marker in ui


# Origin: test_report_followup_round26_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_search_completion_tears_down_progress_window_before_final_progress_update() -> None:
    source = (ROOT / 'audioknigi/qt/mixins/search.py').read_text(encoding='utf-8')
    start = source.index('def _search_finished')
    end = source.index('def _apply_search_outcome', start)
    block = source[start:end]
    assert block.index('self._finish_blocking_operation("search")') < block.index('self._set_search_progress(100, "Поиск завершён", visible=True)')
    assert 'event=before_operation_finish' in block
    assert 'event=after_operation_finish' in block


# Origin: test_report_followup_round28_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def _source__report_followup_round28_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_search_callbacks_route_through_qobject_relay() -> None:
    source = _source__report_followup_round28_20260918('audioknigi/qt/mixins/search.py')
    assert 'worker.progress.connect(self._worker_ui_relay.search_progress, Qt.ConnectionType.QueuedConnection)' in source
    assert 'worker.finished.connect(self._worker_ui_relay.search_finished, Qt.ConnectionType.QueuedConnection)' in source
    assert 'thread.finished.connect(self._worker_ui_relay.search_thread_finished, Qt.ConnectionType.QueuedConnection)' in source

def test_relay_forwards_search_callbacks_to_existing_ui_handlers() -> None:
    relay = _source__report_followup_round28_20260918('audioknigi/qt/worker_ui_relay.py')
    assert 'owner._search_progress_changed(percent, message)' in relay
    assert 'owner._search_finished(outcome)' in relay
    assert 'owner._clear_search_thread()' in relay
    assert 'event=search_finished_dispatch' in relay


# Origin: test_report_followup_round29_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_easy_search_table_uses_available_width_without_horizontal_scroll() -> None:
    source = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    assert 'card.setMaximumWidth(1500)' in source
    assert 'easy_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)' in source
    assert 'if key in {"index", "availability", "variants", "source"}:' in source
    assert 'easy_header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)' in source
    assert 'self.easy_search_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)' in source
    assert 'self.easy_search_table.setTextElideMode(Qt.TextElideMode.ElideRight)' in source
    assert 'self.easy_search_table.setWordWrap(True)' in source
    assert 'self.easy_search_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)' in source
    assert 'easy_header.setStretchLastSection(False)' in source

def test_easy_search_keeps_all_search_model_columns_visible() -> None:
    source = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    block = source[source.index('self.easy_search_table = QTableView()'):source.index('easy_search_actions = QHBoxLayout()')]
    assert '.setColumnHidden(' not in block
    assert 'SearchResultsModel.COLUMNS' in block


# Origin: test_report_followup_round31_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def _source__report_followup_round31_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_easy_reset_clears_book_search_variant_and_description_state() -> None:
    source = _source__report_followup_round31_20260918('audioknigi/qt/main_window.py')
    start = source.index('def _easy_reset_to_initial_state')
    end = source.index('def _easy_user_input_edited', start)
    block = source[start:end]
    for expected in ('self.current_book = None', 'self._pending_search_result = None', 'self._known_narration_variants = None', 'self.search_model.set_results([])', 'self.easy_description.clear()', 'self.easy_book_card.setVisible(False)', 'self.easy_download_button.setEnabled(False)', 'self.book_url_edit.clear()'):
        assert expected in block


# Origin: test_report_followup_round33_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round33_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_easy_search_card_is_wider_and_long_titles_wrap() -> None:
    source = src__report_followup_round33_20260918('audioknigi/qt/main_window.py')
    assert 'card.setMaximumWidth(1500)' in source
    assert 'self.easy_search_table.setWordWrap(True)' in source
    assert 'self.easy_search_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)' in source
    assert 'self.easy_search_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)' in source


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_easy_download_is_disabled_for_new_text_query() -> None:
    source = src__report_followup_round34_20260919('audioknigi/qt/main_window.py')
    block = source[source.index('def _update_easy_action_text'):source.index('def _set_operation_ui_blocked')]
    assert 'matches_current = bool(incoming_url and current_url and incoming_url == current_url)' in block
    assert 'easy_stale = bool(is_url and not matches_current)' in block
    assert 'and matches_current' in block

def test_search_deferred_render_is_safe_during_exit() -> None:
    source = src__report_followup_round34_20260919('audioknigi/qt/mixins/search.py')
    block = source[source.index('def _apply_search_outcome'):source.index('def _focus_search_result_after_render')]
    assert 'if getattr(self, "_exit_requested", False):' in block
    assert 'event=result_render_skipped' in block


# Origin: test_report_followup_round40_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round40_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_search_and_track_tables_keep_descriptive_columns_near_each_other() -> None:
    search = src__report_followup_round40_20260920('audioknigi/qt/mixins/search.py')
    book = src__report_followup_round40_20260920('audioknigi/qt/main_window_pages.py')
    assert 'search_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)' in search
    assert 'search_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)' in search
    assert 'search_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)' in search
    assert 'search_header.setStretchLastSection(False)' in search
    assert 'track_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)' in book
    assert 'track_header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)' in book
    assert 'track_header.setStretchLastSection(False)' in book

def test_menu_bar_has_more_vertical_air_without_touching_search_progress_dialog() -> None:
    theme = src__report_followup_round40_20260920('audioknigi/qt/theme.py')
    assert 'padding: 3px 6px 3px 10px;' in theme
    search_progress = src__report_followup_round40_20260920('audioknigi/qt/operation_dialog.py')
    assert 'BlockingOperationDialog' in search_progress


# Origin: test_report_followup_round46_20260922.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round46_20260922(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_easy_search_uses_all_sources_when_hidden_advanced_filters_are_off() -> None:
    source = src__report_followup_round46_20260922('audioknigi/qt/mixins/search.py')
    start = source.index('def start_search')
    end = source.index('def _search_finished', start)
    block = source[start:end]
    assert 'if not sources and self.current_ui_mode() == "easy":' in block
    assert 'sources = list(source_actions)' in block
    assert block.index('sources = list(source_actions)') < block.index('self.set_status(self._l("Выберите хотя бы один сайт для поиска."')


# Origin: test_report_followup_round51_20260924.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round51_20260924(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_search_results_have_one_shared_active_state_for_both_modes() -> None:
    search = src__report_followup_round51_20260924('audioknigi/qt/mixins/search.py')
    assert 'def _set_search_results_active(self, active: bool) -> None:' in search
    assert 'self._search_results_active = active' in search
    assert 'self.search_results_stack.setCurrentIndex(1 if active else 0)' in search
    assert 'self.easy_search_table.setVisible(active)' in search
    assert 'self.easy_use_result_button.setVisible(active)' in search
    assert 'self.easy_copy_url_button.setVisible(active)' in search
    assert 'self._set_search_results_active(True)' in search

def test_switching_to_advanced_with_pending_results_opens_search_tab() -> None:
    main = src__report_followup_round51_20260924('audioknigi/qt/main_window.py')
    search = src__report_followup_round51_20260924('audioknigi/qt/mixins/search.py')
    assert 'search_owns_view = self._sync_search_presentation_for_mode(mode)' in main
    assert 'elif search_owns_view:' in main
    assert 'target = self.search_table' in main
    assert 'def _sync_search_presentation_for_mode(self, mode: str) -> bool:' in search
    assert 'if mode == "advanced":' in search
    assert 'self.tabs.setCurrentIndex(self.TAB_SEARCH)' in search

def test_search_selection_is_mirrored_between_easy_and_advanced_tables() -> None:
    search = src__report_followup_round51_20260924('audioknigi/qt/mixins/search.py')
    assert 'selection_model.selectionChanged.connect(self._advanced_search_selection_changed)' in search
    assert 'def _sync_search_selection(self, source_table, target_table) -> None:' in search
    assert 'focus_table_row(target_table, row, column=1, focus=False)' in search
    assert 'self._sync_search_selection(self.search_table, self.easy_search_table)' in search
    assert 'self._sync_search_selection(self.easy_search_table, self.search_table)' in search

def test_all_query_fields_are_synchronized_across_modes() -> None:
    settings = src__report_followup_round51_20260924('audioknigi/qt/mixins/settings.py')
    assert 'for name in ("book_url_edit", "easy_input", "search_edit")' in settings

def test_selecting_a_result_ends_shared_search_selection_stage() -> None:
    search = src__report_followup_round51_20260924('audioknigi/qt/mixins/search.py')
    marker = 'self._pending_search_result = selected_result\n        self._set_search_results_active(False)'
    assert marker in search


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

def test_search_sources_run_concurrently_and_keep_registry_order(monkeypatch):
    barrier = threading.Barrier(3)
    providers = (_FakeProvider('first', 'First', barrier, 0.12), _FakeProvider('second', 'Second', barrier, 0.01), _FakeProvider('third', 'Third', barrier, 0.05))
    monkeypatch.setattr(search_service, 'registered_providers', lambda: providers)
    outcome = search_service.search_all_sources('book')
    assert [item.source for item in outcome.results] == ['First', 'Second', 'Third']
    assert outcome.errors == []


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

def test_advanced_search_edit_no_longer_overwrites_analyzed_book_url():
    source = (ROOT / 'audioknigi/qt/mixins/settings.py').read_text(encoding='utf-8')
    start = source.index('def _sync_book_input_text')
    end = source.index('@Slot(int)', start)
    block = source[start:end]
    assert 'if source is book_edit:' in block
    assert 'elif source is search_edit:' in block
    assert block.count('targets = (easy_edit,)') == 2
    assert 'targets = (book_edit, search_edit)' in block


# Origin: test_round72_search_sorting_availability_layout_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def _result(title: str, *, author: str='', narrator: str='', availability: str='') -> SearchResult:
    return SearchResult(title=title, author=author, narrator=narrator, availability=availability, url=f'https://example.invalid/{title}', source='demo')

def test_title_sort_puts_exact_query_first_then_shorter_titles_alphabetically():
    rows = [_result('Двойник запада'), _result('Двойник дурака'), _result('Двойник Декстера'), _result('Двойник'), _result('Двойник старого короля')]
    ordered = sorted(rows, key=lambda item: search_result_sort_key(item, 'title', query='двойник'))
    assert [item.title for item in ordered] == ['Двойник', 'Двойник Декстера', 'Двойник дурака', 'Двойник запада', 'Двойник старого короля']


# Origin: test_round77_external_review_followup_20261004.py
ROOT = Path(__file__).resolve().parents[2]

def test_single_letter_search_tokens_use_boundaries_and_initials():
    assert _matches_query('А Б В', 'А Б В') is True
    assert _matches_query('Азбука', 'А Б В') is False
    assert _matches_query('Книга', 'А Б В', author='Александр Борис Викторов') is False
    assert _matches_query('Книга', 'Л.', author='Лев Толстой') is False


# Origin: test_runtime_contract_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def _book__runtime_contract_hardening_20260912() -> Book:
    return Book(url='https://audioknigi.com.ua/audio-1', title='Demo', tracks=[Track(index=1, title='One', file='https://cdn.invalid/1.mp3'), Track(index=2, title='Two', file='https://cdn.invalid/2.mp3')])

def test_search_service_private_compatibility_wrappers_are_not_dead_imports():
    source = (ROOT / 'audioknigi' / 'services' / 'search_service.py').read_text(encoding='utf-8')
    assert 'def _iter_completed_cancellable' in source
    assert 'def _matches_query' in source
    imported_block = source.split('from ..providers.audioknigi_search import (', 1)[1].split(')', 1)[0]
    assert '_iter_completed_cancellable' not in imported_block
    assert '_matches_query' not in imported_block
