"""Consolidated integration tests for the localization domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


import json
from pathlib import Path
from types import SimpleNamespace
from tools import qt_windows_acceptance
from tools.undefined_global_audit import _SPECIAL_GLOBALS
import pytest
import ast
import os
from audioknigi.core import Cancelled
from audioknigi.diagnostics import support_bundle as support_bundle__recovery_diagnostics_hardening_20260912
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _hydrate_search_result_titles
from audioknigi.models import SearchResult
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.library_service import scan_unfinished
from audioknigi.download.errors import MissingSelectedTracksError
from audioknigi.metadata import APP_VERSION
from audioknigi.services.queue_service import task_from_dict
from tools.exception_audit import audit as exception_audit__release_integrity_followup_20260913
from tools.historical_regression_audit import _normalize_nodeid
from tools.qt_localization_audit import _assignment_value
from audioknigi.core import effective_track_duration, safe_float
from audioknigi.i18n import localize_runtime_text, tr
from audioknigi.models import Book, Track
import threading
from audioknigi.knigavuhe import _extract_call_argument, _usable_search_title
from audioknigi.models import Book, SearchResult, Track
from audioknigi.poleknig import _discover_narration_variants
from audioknigi.providers.audioknigi_search import _audioknigi_page_metadata
from audioknigi.services.download_request import DownloadRequest
import csv
import zipfile
import base64
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download.common import atomic_write_text
from audioknigi.i18n import localize_runtime_text
from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, migrate_ui_scale_settings
from audioknigi.i18n import _normalize_runtime_regex_catalog
from audioknigi.services.search_service import search_all_sources
from audioknigi.sources import is_supported_url, normalize_supported_url
from audioknigi import poleknig
from audioknigi.download.media import MediaProcessingMixin
from audioknigi.services import book_analysis_service as analysis_module
from audioknigi.models import Book, SearchResult
from audioknigi import knigavuhe, poleknig
from audioknigi.core import fmt_eta, parse_time_seconds
from audioknigi.download.probe import ProbeMixin
from audioknigi.providers import audioknigi_search as search_module
from audioknigi.services.queue_service import _parse_selected_indices_payload
from audioknigi.config.settings import migrate_settings
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.providers.audioknigi_search import _canonical_title
from audioknigi.services.book_analysis_service import _playlist_track_title
from audioknigi.core import Cancelled, load_json
from audioknigi.templates import template_values
from audioknigi.download_engine import _DownloadEngine
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi import core
from audioknigi.cover_fetch import fetch_cover_bytes
from audioknigi.download_engine import DownloadService, _DownloadEngine
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
import audioknigi.config.settings as settings_module
import audioknigi.diagnostics.support_bundle as support_bundle__report_followup_round47_20260923
from audioknigi.core import safe_int
from audioknigi.providers import audioknigi_search
from audioknigi.download import book_flow
from tools import exception_audit as exception_audit__report_followup_round53_20260926, package_source_release, qt_localization_audit
from tools import qt_windows_acceptance, undefined_global_audit
from audioknigi.diagnostics.support_bundle import _sanitize_log_bytes, _tail
from audioknigi.qt.acceptance_contract import ACCEPTANCE_SCHEMA, acceptance_issues
from tools import qt_localization_audit, qt_windows_acceptance
from audioknigi.brand import version_label
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.core import load_browser_context_profile
from audioknigi.network_dns import _parse_proxy_authority
from audioknigi.providers.audioknigi_search import _split_audioknigi_title
from dataclasses import dataclass
from audioknigi.core import UI_SCALE_MIGRATION_KEY, extract_extended_metadata_from_html
from audioknigi.diagnostics import support_bundle as support_bundle__round61_external_review_followup_20260929
from audioknigi.providers.audioknigi_search import _author_detail_score, _matches_query
from audioknigi.services.queue_service import _item_to_dict
from audioknigi.models import Book, Track, TRACK_STATUS_READY
from audioknigi.providers.audioknigi_search import _response_html_text
from audioknigi.services.player_position_store import PlayerPositionStore
from audioknigi.config.settings import AppSettings, normalize_settings
from audioknigi.diagnostics import support_bundle as support_bundle__round63_followup_20260929
from audioknigi.services import library_service, source_health_service
import socket
from audioknigi import network_dns
from audioknigi.services import library_service
from audioknigi.services.queue_service import _parse_created_at
from audioknigi.brand import AUTHOR_EMAIL, AUTHOR_GITHUB_URL, AUTHOR_NAME, COPYRIGHT_YEAR, PROJECT_URL
from tools.windows_version_info import render_version_info
from audioknigi.download.errors import MissingMediaSourceError
from audioknigi.download.network import NetworkDownloadMixin
from audioknigi.download_engine import DownloadCallbacks, DownloadResult, DuplicatePreflight, _DownloadEngine
from audioknigi.download.errors import SharedSourceTimelineError
from audioknigi.services.search_service import downloadable_search_results, search_result_sort_key
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
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services.queue_service import _book_from_dict
from audioknigi.templates import _safe_track_index
from audioknigi.core import safe_name
from audioknigi.knigavuhe import _extract_narration_variants
from audioknigi.core import SiteStructureChanged
from audioknigi.diagnostics.support_bundle import _privacy_path
from audioknigi.knigavuhe import parse_book_html
from audioknigi.download.common import source_target_assignments
from audioknigi.models import Book
from audioknigi.services import source_health_service
from audioknigi.download import network as network_module
from audioknigi.download import source_analysis as source_analysis_module
from audioknigi.download.source_analysis import SourceAnalysisMixin
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
import subprocess
import sys
from audioknigi.diagnostics import support_bundle as support_bundle__structured_hardening_20260912
from audioknigi.knigavuhe import _merge_narration_variants
from audioknigi.models import NarrationVariant, SearchResult, Track, TRACK_STATUS_MISSING
from audioknigi.services import search_service
from audioknigi.providers import provider_for_key


# Origin: test_acceptance_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_ukrainian_legacy_literals_cover_common_search_and_book_prompts():
    literals = json.loads((ROOT / 'audioknigi' / 'locales' / 'legacy_literals.json').read_text(encoding='utf-8'))
    uk = literals['uk']
    expected = {'Ничего не найдено.': 'Нічого не знайдено.', 'Сначала выберите книгу в результатах поиска.': 'Спочатку оберіть книгу в результатах пошуку.', 'Сначала выберите часть книги.': 'Спочатку оберіть частину книги.', 'Сначала проанализируйте книгу.': 'Спочатку проаналізуйте книгу.'}
    for key, value in expected.items():
        assert uk.get(key) == value


# Origin: test_cancellation_cover_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_download_progress_runtime_translation_is_complete():
    from audioknigi.i18n import localize_runtime_text
    assert localize_runtime_text('en', 'Скачано 15 MB из 100 MB') == 'Downloaded 15 MB of 100 MB'
    assert localize_runtime_text('de', 'Скачано 15 MB из 100 MB') == 'Heruntergeladen 15 MB von 100 MB'
    assert localize_runtime_text('uk', 'Скачано 15 MB из 100 MB') == 'Завантажено 15 MB із 100 MB'

def test_queue_unresolved_summary_uses_stable_translations():
    from audioknigi.i18n import tr
    assert tr('en', 'queue_stopped_unresolved', details=tr('en', 'queue_unresolved_errors', count=2)) == 'Queue stopped; tasks remain (with error: 2).'
    source = (ROOT / 'audioknigi/qt/mixins/queue.py').read_text(encoding='utf-8')
    assert 'details.append(f"на паузе:' not in source
    assert 'tr(self.language, "queue_stopped_unresolved"' in source


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

def test_help_center_is_full_guide_in_all_languages() -> None:
    topics = _topics()
    assert set(topics) == {'ru', 'uk', 'de', 'en'}
    expected_keys = ['start', 'modes', 'book', 'search', 'download', 'quality', 'queue', 'history', 'player', 'settings', 'files', 'backup', 'accessibility', 'shortcuts', 'diagnostics', 'troubleshooting']
    for language, rows in topics.items():
        assert [key for key, _title, _body in rows] == expected_keys, language
        assert len(rows) == 16
        assert all((title.strip() for _key, title, _body in rows))
        assert all((len(body.strip()) >= 550 for _key, _title, body in rows)), language
        assert all(('\n\n' in body for _key, _title, body in rows)), language


# Origin: test_recovery_diagnostics_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_ui_text_does_not_format_literal_braces_without_kwargs(monkeypatch):
    import audioknigi.i18n as i18n
    monkeypatch.setitem(i18n._PHASE29_LITERAL_TRANSLATIONS.setdefault('en', {}), 'Example {Book_Title}', 'Example {Book_Title}')
    assert ui_text('en', 'Example {Book_Title}') == 'Example {Book_Title}'

def test_runtime_backup_translation_accepts_crlf():
    translated = localize_runtime_text('en', 'Резервная копия создана:\r\nC:/Backup/file.zip')
    assert translated == 'Backup created:\nC:/Backup/file.zip'


# Origin: test_release_integrity_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_localization_ast_helper_supports_annotated_assignments():
    node = ast.parse("TOPICS: dict[str, str] = {'a': 'b'}").body[0]
    value = _assignment_value(node, 'TOPICS')
    assert value is not None
    assert ast.literal_eval(value) == {'a': 'b'}

def test_ukrainian_undo_and_appearance_are_not_collapsed_into_cancel_and_view():
    literals = json.loads((ROOT / 'audioknigi' / 'locales' / 'legacy_literals.json').read_text(encoding='utf-8'))
    uk = literals['uk']
    assert uk['Отмена'] != uk['Отменить']
    assert uk['Вид'] != uk['Внешний вид']


# Origin: test_report_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_range_and_full_mp3_log_are_fully_localized():
    range_text = 'Range 2/4 • 10 MB из 20 MB • 1 MB/s • ETA 00:10'
    assert localize_runtime_text('de', range_text) == 'Range 2/4 • 10 MB von 20 MB • 1 MB/s • ETA 00:10'
    full_text = 'Обрабатываю полный файл (исходный кодек: aac) с выбранным профилем качества и нормализацией.'
    assert localize_runtime_text('en', full_text) == 'Processing full file (source codec: aac) with the selected quality profile and normalization.'

def test_full_mp3_stage_ids_exist_for_all_languages():
    for language in ('ru', 'uk', 'de', 'en'):
        assert tr(language, 'stage_full_mp3_download')
        assert tr(language, 'stage_full_mp3_processing')
        assert tr(language, 'stage_full_mp3_tags')


# Origin: test_report_followup_round10_20260916.py
ROOT = Path(__file__).resolve().parents[2]

class _Response:
    text = '<html><head><title>Тестовая книга</title></head><body>Исполнитель: Иван Иванов, Жанр: Фантастика</body></html>'

    def raise_for_status(self):
        return None

class _Session:

    def get(self, *args, **kwargs):
        return _Response()

def test_ui_text_can_reuse_exact_runtime_catalog_for_static_qt_labels():
    assert ui_text('en', 'Озвучка {index}', index=2) == 'Narration 2'
    assert ui_text('de', 'доступно') == 'verfügbar'
    assert ui_text('uk', 'недоступно') == 'недоступно'

def test_search_failure_prefix_is_localized():
    assert localize_runtime_text('en', 'Поиск не выполнен: timeout') == 'Search failed: timeout'
    assert localize_runtime_text('de', 'Поиск не выполнен: timeout') == 'Suche fehlgeschlagen: timeout'

def test_empty_history_export_message_is_localized():
    source = 'История пуста — экспортировать нечего.'
    assert localize_runtime_text('en', source) != source
    assert localize_runtime_text('de', source) != source


# Origin: test_report_followup_round13_20260916.py
def test_dynamic_download_progress_is_localized():
    from audioknigi.i18n import localize_runtime_text
    assert localize_runtime_text('en', 'Скачивается 1/3') == 'Downloading 1/3'
    assert localize_runtime_text('de', 'Скачивается 2/5') == 'Wird heruntergeladen 2/5'


# Origin: test_report_followup_round15_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_range_runtime_translation_accepts_flexible_bullet_spacing():
    text = 'Range 2/4  •   1 MB из 10 MB   •  2 MB/s •   ETA 00:04'
    assert localize_runtime_text('en', text) == 'Range 2/4 • 1 MB of 10 MB • 2 MB/s • ETA 00:04'


# Origin: test_report_followup_round17_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_malformed_runtime_regex_rows_are_filtered_instead_of_crashing_import() -> None:
    rows = _normalize_runtime_regex_catalog([[], ['^ok$', {'en': 'OK'}], ['missing variants'], {'pattern': '^bad$'}, [123, {'en': 'bad'}], ['^bad variants$', 'not-a-mapping']])
    assert rows == (('^ok$', {'en': 'OK'}),)

def test_no_search_provider_error_uses_existing_localized_literal() -> None:
    outcome = search_all_sources('test query', sources=[])
    assert outcome.errors == ['Выберите хотя бы один сайт для поиска.']


# Origin: test_report_followup_round19_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_round19_player_dialogs_and_f1_help_are_localized_and_consistent() -> None:
    player = (ROOT / 'audioknigi/qt/player_mixin.py').read_text(encoding='utf-8')
    accessibility = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'self._l("Файл не найден")' in player
    assert 'self._l("Ошибка плеера")' in player
    assert 'show_context_help(topic="shortcuts")' in accessibility


# Origin: test_report_followup_round20_20260917.py
ROOT = Path(__file__).resolve().parents[2]

def test_dynamic_narration_label_is_runtime_localized() -> None:
    assert localize_runtime_text('en', 'Озвучка 3') == 'Narration 3'
    assert localize_runtime_text('de', 'Озвучка 3') == 'Sprecherfassung 3'
    assert localize_runtime_text('uk', 'Озвучка 3') == 'Озвучення 3'


# Origin: test_report_followup_round24_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def test_round24_runtime_localization_covers_tray_variants_and_placeholder_style() -> None:
    catalog = json.loads((ROOT / 'audioknigi/locales/runtime_exact.json').read_text(encoding='utf-8'))
    assert 'Системный трей активен.' in catalog
    assert 'Системный трей недоступен.' in catalog
    placeholder = catalog['Введите название/автора для поиска или вставьте ссылку на поддерживаемый сайт']
    assert all((not value.endswith('.') for value in placeholder.values()))


# Origin: test_report_followup_round32_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round32_20260918(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

def test_settings_page_honors_persisted_quality_preset_and_localizes_abs_id() -> None:
    source = src__report_followup_round32_20260918('audioknigi/qt/main_window_pages.py')
    assert 'explicit_quality = str(self.settings.get("quality_preset", "") or "").strip()' in source
    assert 'name=self._l("ID библиотеки Audiobookshelf")' in source

def test_localization_followups_present_and_german_uses_du_sprecherfassung() -> None:
    exact = json.loads((ROOT / 'audioknigi/locales/runtime_exact.json').read_text(encoding='utf-8'))
    legacy = json.loads((ROOT / 'audioknigi/locales/legacy_literals.json').read_text(encoding='utf-8'))
    assert exact['Выберите озвучку']['de'] == 'Sprecherfassung auswählen'
    assert exact['Выберите чтеца перед анализом книги']['de'].startswith('Wählen Sie ')
    assert 'Wählen Sie' in exact['Найдено вариантов озвучки: {count}. Выберите чтеца.']['de']
    for key in ('Завершаю поиск', 'Найден исправный резервный источник knigavuhe.org.', 'Анализ отменён.', 'Не удалось проанализировать книгу.'):
        assert key in exact
    for key in ('Дата', 'Попытки', 'Частей', 'Папка'):
        assert all((key in legacy[lang] for lang in ('de', 'en', 'uk')))
    assert legacy['en']['Range от размера:'] == 'Range min. file size:'

def test_german_help_engine_grammar_fixed() -> None:
    source = src__report_followup_round32_20260918('audioknigi/qt/help_center.py')
    assert 'die Download-Engine ist jedoch dieselbe' in source
    assert 'der Download-Engine ist jedoch derselbe' not in source

def test_runtime_localization_regex_precedes_prefixes() -> None:
    source = src__report_followup_round32_20260918('audioknigi/i18n.py')
    regex = source.index('for pattern, variants in _PHASE29_RUNTIME_REGEX')
    prefix = source.index('for prefix, variants in _PHASE29_RUNTIME_PREFIXES.items()')
    assert regex < prefix


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_dynamic_runtime_messages_and_german_narration_term_are_localized() -> None:
    patterns = json.loads((ROOT / 'audioknigi/locales/runtime_regex.json').read_text(encoding='utf-8'))
    mapping = {pattern: variants for pattern, variants in patterns}
    assert mapping['^Озвучка (\\d+)$']['de'] == 'Sprecherfassung {0}'
    for pattern in ('^Ошибка источника (.+)$', '^Найден исправный резервный источник knigavuhe\\.org\\. Переключаю загрузку автоматически: (.+)\\.$', '^Удалены временные файлы устаревшего источника: (.+)\\.$', '^Плейлист обновлён: частей (.+), изменённых аудиоссылок (.+)\\. Повторяю загрузку один раз\\.$', '^Пользователь пропустил недоступные части: (.+)\\. Остальные выбранные части продолжаю скачивать\\.$'):
        assert pattern in mapping


# Origin: test_report_followup_round3_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_runtime_exact_tolerates_non_mapping_entry(monkeypatch):
    import audioknigi.i18n as module
    monkeypatch.setitem(module._PHASE29_RUNTIME_EXACT, 'Malformed', 'not-a-dict')
    assert module.localize_runtime_text('en', 'Malformed') == 'Malformed'

def test_search_short_query_uses_localizable_error():
    outcome = search_all_sources('ab')
    assert outcome.errors == ['Введите минимум 3 символа для поиска.']

def test_dynamic_search_status_and_completed_duration_are_localized():
    assert localize_runtime_text('en', 'Найдено 12 книг, источников: 3.') == 'Found 12 books, sources: 3.'
    assert localize_runtime_text('de', 'Найдено 2 книг.') == '2 Bücher gefunden.'
    assert localize_runtime_text('uk', 'Часть источников недоступна.') == 'Частина джерел недоступна.'
    assert localize_runtime_text('en', 'Определена длительность частей: 4/4') == 'Part durations determined: 4/4'


# Origin: test_report_followup_round47_20260923.py
def test_localized_context_menu_delete_slot_accepts_triggered_bool():
    source = (Path(__file__).resolve().parents[2] / 'audioknigi/qt/localized_context_menu.py').read_text(encoding='utf-8')
    assert 'delete_action.triggered.connect(lambda *_: _delete_selection(widget))' in source


# Origin: test_report_followup_round53_20260926.py
def test_localization_detects_keyword_literals_and_dynamic_text(tmp_path, monkeypatch):
    monkeypatch.setattr(qt_localization_audit, 'ROOT', tmp_path)
    sample = tmp_path / 'sample.py'
    sample.write_text('QLabel(text="Текст")\nQGroupBox(title="Группа")\nQAction(icon, text="Действие")\nbutton.setText(text="Кнопка")\nbutton.setAccessibleName(name="Имя")\nbutton.setText(text=f"Глав: {count}")\nQLabel(text=_l("Переведено"))\nQLabel(text="English")\n', encoding='utf-8')
    assert len(qt_localization_audit._direct_visible_russian(sample)) == 5
    assert len(qt_localization_audit._unwrapped_dynamic_visible_russian(sample)) == 1

def test_localization_reports_missing_required_file(monkeypatch):
    original = Path.is_file
    missing = qt_localization_audit.ROOT / 'audioknigi/downloader.py'
    monkeypatch.setattr(Path, 'is_file', lambda self: False if self == missing else original(self))
    assert 'missing runtime localization source: audioknigi/downloader.py' in qt_localization_audit.audit()


# Origin: test_report_followup_round54_20260926.py
def test_localization_detects_icon_text_overloads_and_constructor_fstring(tmp_path, monkeypatch):
    monkeypatch.setattr(qt_localization_audit, 'ROOT', tmp_path)
    sample = tmp_path / 'sample.py'
    sample.write_text('QAction(icon, "Открыть", parent)\nQPushButton(icon, "Пуск", parent)\nmenu.addAction(icon, "Действие")\ncombo.addItem(icon, "Выбор", data)\nQLabel(text=f"Глав: {count}")\n', encoding='utf-8')
    direct = qt_localization_audit._direct_visible_russian(sample)
    dynamic = qt_localization_audit._unwrapped_dynamic_visible_russian(sample)
    assert len(direct) == 4
    assert len(dynamic) == 1


# Origin: test_report_followup_round5_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_accessibility_descriptions_are_localized():
    cases = [('Введите название/автора для поиска или вставьте ссылку на поддерживаемый сайт', 'Enter a title/author'), ('Найти resume.json, повторно проанализировать книгу и восстановить выбранные части', 'Find resume.json'), ('Получить сведения о книге и список доступных частей', 'Get book information'), ('Применится после перезапуска', 'Applies after restart')]
    for source, prefix in cases:
        translated = localize_runtime_text('en', source)
        assert translated.startswith(prefix)
        assert translated != source


# Origin: test_report_followup_round9_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_dynamic_generic_error_prefix_is_localized():
    assert localize_runtime_text('en', 'Ошибка: Таймаут соединения') == 'Error: Таймаут соединения'
    assert localize_runtime_text('de', 'Ошибка: Таймаут соединения') == 'Fehler: Таймаут соединения'


# Origin: test_round61_external_review_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_runtime_narration_terminology_is_consistent_in_english():
    assert ui_text('en', 'Озвучка {index}', index=2) == 'Narration 2'
    assert localize_runtime_text('en', 'Озвучка 3') == 'Narration 3'


# Origin: test_round62_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_non_german_locales_do_not_leak_german_key_names():
    messages = json.loads((ROOT / 'audioknigi/locales/messages.json').read_text(encoding='utf-8'))
    literals = json.loads((ROOT / 'audioknigi/locales/legacy_literals.json').read_text(encoding='utf-8'))
    for language in ('en', 'ru', 'uk'):
        combined = '\n'.join((str(value) for value in messages[language].values()))
        if language in literals:
            combined += '\n' + '\n'.join((str(value) for value in literals[language].values()))
        assert 'Leertaste' not in combined
        assert 'Umschalt' not in combined
    assert 'Space' in messages['en']['help_shortcuts_body']
    assert 'Пробел' in messages['ru']['help_shortcuts_body']
    assert 'Пробіл' in messages['uk']['help_shortcuts_body']
    assert 'Shift+F10' in messages['en']['help_shortcuts_body']
    assert 'Shift+F10' in messages['ru']['help_shortcuts_body']
    assert 'Shift+F10' in messages['uk']['help_shortcuts_body']

def test_reported_german_and_ukrainian_wording_is_consistent():
    literals = json.loads((ROOT / 'audioknigi/locales/legacy_literals.json').read_text(encoding='utf-8'))
    assert literals['de']['Вставьте ссылку на книгу или введите название/автора для поиска, затем выберите нужные части.'] == 'Fügen Sie einen Buch-Link ein oder suchen Sie nach Titel/Autor und wählen Sie anschließend die gewünschten Teile.'
    assert literals['de']['Вставьте ссылку на книгу или введите название/автора для поиска.'] == 'Fügen Sie einen Buch-Link ein oder geben Sie Titel/Autor für die Suche ein.'
    assert literals['uk']['Главы текущей книги'] == 'Розділи поточної книги'


# Origin: test_round63_followup_20260929.py
def test_runtime_exact_json_has_no_duplicate_keys_at_any_object_level():
    path = Path(__file__).resolve().parents[2] / 'audioknigi/locales/runtime_exact.json'
    payload = path.read_text(encoding='utf-8')

    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, f'duplicate JSON key: {key!r}'
            result[key] = value
        return result
    json.loads(payload, object_pairs_hook=no_duplicates)

def test_round63_removes_unreachable_unlink_return_and_keeps_runtime_regex_precedence():
    root = Path(__file__).resolve().parents[2]
    common = (root / 'audioknigi/download/common.py').read_text(encoding='utf-8')
    i18n = (root / 'audioknigi/i18n.py').read_text(encoding='utf-8')
    unlink_block = common[common.index('def unlink_with_retry'):common.index('def atomic_write_text')]
    assert 'return False' not in unlink_block
    assert i18n.index('for pattern, variants in _PHASE29_RUNTIME_REGEX') < i18n.index('for prefix, variants in _PHASE29_RUNTIME_PREFIXES.items()')


# Origin: test_round66_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_reported_runtime_exact_duplicate_is_not_present():
    path = ROOT / 'audioknigi/locales/runtime_exact.json'
    text = path.read_text(encoding='utf-8')
    assert text.count('"Проверить системный звук"') == 1

    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, f'duplicate JSON key: {key!r}'
            result[key] = value
        return result
    json.loads(text, object_pairs_hook=no_duplicates)


# Origin: test_round67_runtime_followup_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_runtime_regex_still_precedes_prefix_fallback__round67_runtime_followup_20260929():
    source = (ROOT / 'audioknigi/i18n.py').read_text(encoding='utf-8')
    regex_pos = source.index('for pattern, variants in _PHASE29_RUNTIME_REGEX')
    prefix_pos = source.index('for prefix, variants in _PHASE29_RUNTIME_PREFIXES.items()')
    assert regex_pos < prefix_pos


# Origin: test_round68_creator_metadata_20260929.py
ROOT = Path(__file__).resolve().parents[2]

def test_about_localization_exists_in_all_languages():
    data = json.loads((ROOT / 'audioknigi/locales/messages.json').read_text(encoding='utf-8'))
    keys = {'about_window_title', 'about_summary', 'about_author_role', 'about_accessibility_note', 'about_email_label', 'about_github_label', 'about_project_label', 'about_write_email', 'about_copy_email', 'about_open_github', 'about_open_project', 'about_email_copied', 'about_info_accessible'}
    for language in ('ru', 'en', 'de', 'uk'):
        assert keys <= set(data[language])
        assert all((str(data[language][key]).strip() for key in keys))


# Origin: test_round69_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

def test_operation_cancel_has_context_specific_translation():
    main_window = (ROOT / 'audioknigi/qt/main_window.py').read_text(encoding='utf-8')
    assert 'cancel_text=tr(self.language, "cancel_operation")' in main_window
    messages = json.loads((ROOT / 'audioknigi/locales/messages.json').read_text(encoding='utf-8'))
    assert messages['en']['cancel_operation'] == 'Cancel'
    assert messages['de']['cancel_operation'] == 'Abbrechen'
    assert messages['ru']['cancel_operation'] == 'Отменить'
    assert messages['uk']['cancel_operation'] == 'Скасувати'
    legacy = json.loads((ROOT / 'audioknigi/locales/legacy_literals.json').read_text(encoding='utf-8'))
    assert legacy['en']['Отменить'] == 'Undo'
    assert legacy['en']['Повторить'] == 'Redo'

def test_german_shortcut_names_are_consistent():
    messages = json.loads((ROOT / 'audioknigi/locales/messages.json').read_text(encoding='utf-8'))
    legacy = json.loads((ROOT / 'audioknigi/locales/legacy_literals.json').read_text(encoding='utf-8'))
    assert 'Tab / Umschalt+Tab' in messages['de']['help_shortcuts_body']
    assert 'Tab / Shift+Tab' not in messages['de']['help_shortcuts_body']
    key = 'Анализ завершён. Стрелками просмотрите части; пробел меняет выбор. Затем Tab до «Скачать книгу» или нажмите Ctrl+D.'
    assert 'Strg+D' in legacy['de'][key]
    assert 'Ctrl+D' not in legacy['de'][key]


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

@pytest.mark.parametrize(('language', 'source', 'expected_fragment'), [('en', 'Auto-Chunker: снижаю активные Range-потоки 4 → 2 из-за низкой скорости на поток.', 'reducing active Range workers'), ('de', 'Сегментированная загрузка: 4 поток(а/ов), 8 Range-задач.', 'Segmentierter Download'), ('uk', 'Range-запрос временно не удался (2/5); повторяю с того же байта.', 'Range-запит тимчасово не вдався'), ('en', 'chapter.mp3: прямое копирование аудиопотока не удалось; повторяю с совместимым MP3-кодированием.', 'direct audio stream copy failed'), ('de', 'Загрузка остановлена: выбранная часть отсутствует в обновлённом плейлисте.', 'Download gestoppt')])
def test_new_core_runtime_messages_are_localized(language, source, expected_fragment):
    translated = localize_runtime_text(language, source)
    assert translated != source
    assert expected_fragment in translated


# Origin: test_round71_runtime_followup_20260930.py
ROOT = Path(__file__).resolve().parents[2]

@pytest.mark.parametrize(('language', 'fragment'), [('en', 'source is already MP3'), ('de', 'Quelle ist bereits MP3'), ('uk', 'джерело вже MP3')])
def test_smart_format_runtime_message_is_localized(language, fragment):
    source = 'Smart Format: источник уже MP3 96k/2ch; повышать его до профиля 128k/2ch перекодированием не имеет смысла — сохраняю исходный поток без потери качества.'
    translated = localize_runtime_text(language, source)
    assert translated != source
    assert fragment in translated


# Origin: test_round72_search_sorting_availability_layout_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def _result(title: str, *, author: str='', narrator: str='', availability: str='') -> SearchResult:
    return SearchResult(title=title, author=author, narrator=narrator, availability=availability, url=f'https://example.invalid/{title}', source='demo')

def test_search_sort_strings_exist_for_all_supported_languages():
    messages = json.loads((ROOT / 'audioknigi/locales/messages.json').read_text(encoding='utf-8'))
    keys = {'search_sort_button', 'search_sort_title', 'search_sort_author', 'search_sort_narrator', 'search_sort_accessible', 'search_sort_description', 'search_sorted'}
    for language in ('ru', 'uk', 'de', 'en'):
        assert keys <= set(messages[language])
        assert all((str(messages[language][key]).strip() for key in keys))


# Origin: test_round73_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_search_parallel_source_status_is_localized():
    source = 'Ищу одновременно на источниках: 3'
    assert 'Searching across sources simultaneously: 3' == localize_runtime_text('en', source)
    assert 'Suche gleichzeitig auf Quellen: 3' == localize_runtime_text('de', source)
    assert 'Шукаю одночасно на джерелах: 3' == localize_runtime_text('uk', source)

def test_runtime_exact_lookup_precedes_regex_and_static_entries_moved_to_exact():
    source = (ROOT / 'audioknigi/i18n.py').read_text(encoding='utf-8')
    assert source.index('exact_entry = _PHASE29_RUNTIME_EXACT.get(raw)') < source.index('for pattern, variants in _PHASE29_RUNTIME_REGEX')
    exact = json.loads((ROOT / 'audioknigi/locales/runtime_exact.json').read_text(encoding='utf-8'))
    regex_rows = json.loads((ROOT / 'audioknigi/locales/runtime_regex.json').read_text(encoding='utf-8'))
    assert 'Анализирую audioknigi.com.ua быстрым HTTP-способом…' in exact
    assert 'HTTP-анализ не сработал. Пробую Playwright fallback…' in exact
    patterns = {row[0] for row in regex_rows}
    assert '^Анализирую audioknigi\\.com\\.ua быстрым HTTP-способом…$' not in patterns
    assert '^HTTP-анализ не сработал\\. Пробую Playwright fallback…$' not in patterns

def test_help_details_are_present_for_all_supported_languages_and_german_style_is_consistent():
    source = (ROOT / 'audioknigi/qt/help_center.py').read_text(encoding='utf-8')
    for name in ('ROUND55_TOPIC_DETAILS_RU', 'ROUND55_TOPIC_DETAILS_EN', 'ROUND55_TOPIC_DETAILS_DE', 'ROUND55_TOPIC_DETAILS_UK'):
        assert name in source
    assert 'ROUND55_TOPIC_DETAILS.get(self.language, {}).get(key, "")' in source
    messages = json.loads((ROOT / 'audioknigi/locales/messages.json').read_text(encoding='utf-8'))
    german = '\n'.join((str(value) for value in messages['de'].values()))
    assert not re.search('\\b(?:Du|du|Gib|Füge|Wähle|Klicke|Kopiere|Nutze|Prüfe)\\b', german)
    for name in ('runtime_exact.json', 'runtime_regex.json', 'legacy_literals.json'):
        assert 'Wiedergabeliste' not in (ROOT / 'audioknigi/locales' / name).read_text(encoding='utf-8')


# Origin: test_round74_runtime_followup_20261002.py
ROOT = Path(__file__).resolve().parents[2]

def test_runtime_regex_still_precedes_prefix_fallback__round74_runtime_followup_20261002():
    from audioknigi.i18n import localize_runtime_text
    assert localize_runtime_text('en', 'История обновлена: 10 записей.') == 'History refreshed: 10 entries.'

def test_identity_tokens_preserve_ukrainian_and_belarusian_letters():
    service_tokens = BookAnalysisService._identity_tokens('Марія Ґрунт Ўзор')
    assert {'марія', 'ґрунт', 'ўзор'} <= service_tokens
    probe_source = (ROOT / 'audioknigi/download/probe.py').read_text(encoding='utf-8')
    assert 're.findall(r"[^\\W_]+", text, re.UNICODE)' in probe_source

def test_german_onboarding_and_commands_use_sie_form_and_restart_badge_has_no_period():
    onboarding = (ROOT / 'audioknigi/qt/onboarding.py').read_text(encoding='utf-8')
    assert 'Wählen Sie die wichtigsten Einstellungen' in onboarding
    assert 'können Sie später' in onboarding
    assert 'kannst du' not in onboarding
    legacy = json.loads((ROOT / 'audioknigi/locales/legacy_literals.json').read_text(encoding='utf-8'))
    assert legacy['de']['Дождитесь завершения анализа книги.'].startswith('Warten Sie')
    assert legacy['de']['Сначала остановите очередь загрузок.'].startswith('Stoppen Sie')
    assert 'Analysieren Sie' in legacy['de']['Повтор невозможен: сначала заново проанализируйте импортированную книгу.']
    assert legacy['de']['Сначала завершите текущую загрузку или очередь.'].startswith('Beenden Sie')
    exact = json.loads((ROOT / 'audioknigi/locales/runtime_exact.json').read_text(encoding='utf-8'))
    restart = exact['Применится после перезапуска']
    assert restart['de'] == 'Wird nach einem Neustart angewendet'
    assert restart['en'] == 'Applies after restart'
    assert restart['uk'] == 'Застосується після перезапуску'


# Origin: test_round75_external_review_followup_20261003.py
ROOT = Path(__file__).resolve().parents[2]

def test_reviewed_runtime_localizations_are_consistent():
    player_message = 'У выбранной части пока нет доступного локального файла. Сначала скачайте её или откройте готовый аудиофайл на вкладке «Плеер».'
    assert 'Laden Sie ihn zuerst herunter' in localize_runtime_text('de', player_message)
    cancelled = 'Скачивание отменено. Можно изменить выбор частей или снова нажать «Скачать книгу».'
    assert localize_runtime_text('en', cancelled).startswith('Download cancelled.')
    segmented = 'Сегментированная загрузка: 4 поток(а/ов), 12 Range-задач.'
    assert localize_runtime_text('uk', segmented) == 'Сегментоване завантаження: 4 потік(ів), 12 Range-завдань.'


# Origin: test_round77_external_review_followup_20261004.py
ROOT = Path(__file__).resolve().parents[2]

def test_qtextedit_gets_localized_context_menu_installation():
    source = (ROOT / 'audioknigi/qt/mixins/accessibility_ui.py').read_text(encoding='utf-8')
    assert 'QTextEdit' in source
    assert 'for widget_type in (QLineEdit, QPlainTextEdit, QTextEdit):' in source


# Origin: test_round78_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_runtime_template_entries_are_intentionally_formatted_by_ui_text():
    assert ui_text('en', 'Найдено вариантов озвучки: {count}. Выберите чтеца.', count=3) == 'Narration options found: 3. Choose a narrator.'
    assert ui_text('en', 'Озвучка {index}', index=2) == 'Narration 2'

def test_new_book_flow_runtime_error_localizations_are_available():
    missing = 'В плейлисте отсутствует адрес аудиофайла для частей: 0, 2. Повторите анализ книги.'
    assert localize_runtime_text('en', missing) == 'The playlist is missing the audio-file address for parts: 0, 2. Analyze the book again.'
    failed = 'Не удалось корректно создать 01.mp3: ожидалось 01:00, получено 00:40.'
    assert localize_runtime_text('de', failed) == '01.mp3 konnte nicht korrekt erstellt werden: erwartet 01:00, erhalten 00:40.'
    static = 'Локальный исходник для нарезки не найден. Повторите анализ или загрузку книги.'
    assert localize_runtime_text('uk', static).startswith('Локальний вихідний файл')

def test_german_shortcuts_are_supported_by_help_formatter_source():
    source = (ROOT / 'audioknigi/qt/help_center.py').read_text(encoding='utf-8')
    block = source[source.index('shortcut = re.compile'):source.index('return shortcut.sub', source.index('shortcut = re.compile'))]
    assert 'Ctrl|Strg' in block
    assert 'Shift|Umschalt' in block
    assert 'Leertaste' in block


# Origin: test_round79_external_review_followup_20261005.py
ROOT = Path(__file__).resolve().parents[2]

def test_search_accessibility_descriptions_are_localized():
    assert localize_runtime_text('en', 'Введите название аудиокниги или автора, минимум три символа').startswith('Enter the audiobook')
    assert localize_runtime_text('de', 'Поиск одновременно на трёх поддерживаемых сайтах').startswith('Gleichzeitige Suche')
    assert 'варіантів озвучення' in localize_runtime_text('uk', 'Таблица с названием, автором, чтецом, количеством озвучек и источником')


# Origin: test_round81_external_review_followup_20261006.py
ROOT = Path(__file__).resolve().parents[2]

def test_round81_runtime_error_localizations_are_available():
    assert localize_runtime_text('en', 'После обновления плейлиста эта озвучка стала недоступна.').startswith('After refreshing')
    assert localize_runtime_text('de', 'Аудиофайл недоступен (HTTP 404/410) даже после обновления плейлиста. Возможно, файл временно удалён на сервере или эта часть книги недоступна.').startswith('Die Audiodatei')
    assert localize_runtime_text('uk', 'Не выбрано ни одной части.') == 'Не вибрано жодної частини.'
    assert localize_runtime_text('en', 'Загрузка оборвалась: получено 3 B из 10 B.') == 'Download was interrupted: received 3 B of 10 B.'


# Origin: test_runtime_followup_round7_20260916.py
ROOT = Path(__file__).resolve().parents[2]

def test_localized_track_statuses_normalize_to_canonical_values():
    assert normalize_track_status('немає') == TRACK_STATUS_MISSING
    assert normalize_track_status('fehlt') == TRACK_STATUS_MISSING
    assert normalize_track_status('є') == TRACK_STATUS_PRESENT
    assert normalize_track_status('fertig') == TRACK_STATUS_READY
    assert normalize_track_status('пошкоджено') == TRACK_STATUS_DAMAGED
    assert normalize_track_status('beschädigt') == TRACK_STATUS_DAMAGED

def test_round7_localization_and_quality_contracts_are_consistent():
    assert localize_runtime_text('de', 'Range 2/4 • 10 MB из 20 MB • 1 MB/s • ETA 00:10').startswith('Range 2/4')
    onboarding = (ROOT / 'audioknigi' / 'qt' / 'onboarding.py').read_text(encoding='utf-8')
    settings = (ROOT / 'audioknigi' / 'qt' / 'mixins' / 'settings.py').read_text(encoding='utf-8')
    assert '"audio_preset": "128k_stereo", "normalization_mode": "two_pass"' in onboarding
    assert 'Merely saving unrelated settings in Easy mode must not erase' in settings
    assert 'quality_preset = self.easy_quality_combo.currentData() or quality_preset' in settings


# Origin: test_runtime_integrity_followup_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_runtime_translation_specific_rule_precedes_generic_analyze_rule():
    source = 'Анализирую audioknigi.com.ua быстрым HTTP-способом…'
    assert localize_runtime_text('en', source) == 'Analyzing audioknigi.com.ua using the fast HTTP method…'
    assert 'быстрым' not in localize_runtime_text('de', source)

def test_ukrainian_legacy_literals_cover_cancellation_and_queue_statuses():
    keys = ('Запрошена отмена анализа…', 'Запрошена отмена скачивания…', 'Очередь завершена.', 'Скачивание отменено пользователем.', 'Скачивание уже выполняется.')
    for key in keys:
        assert ui_text('uk', key) != key

def test_runtime_exact_catalog_orientation_matches_lookup_contract():
    source = 'Настройки сохранены. Масштаб применится после перезапуска приложения.'
    translated = localize_runtime_text('uk', source)
    assert translated != source
    assert 'застосується' in translated


# Origin: test_stability_localization_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def test_runtime_progress_and_duration_messages_are_fully_localized():
    text = 'Скачано 15 MB из 100 MB  •  2 MB/s  •  ETA 00:42'
    assert localize_runtime_text('en', text) == 'Downloaded 15 MB of 100 MB • 2 MB/s • ETA 00:42'
    assert localize_runtime_text('de', text) == 'Heruntergeladen 15 MB von 100 MB • 2 MB/s • ETA 00:42'
    assert localize_runtime_text('uk', 'Определена длительность частей: 2/4') == 'Визначено тривалість частин: 2/4'

def test_stage_messages_use_stable_message_ids():
    assert tr('en', 'stage_playlist_refresh') == 'Refreshing playlist'
    assert tr('de', 'stage_source_download') == 'Quelldatei wird heruntergeladen'
    source = (ROOT / 'audioknigi' / 'download' / 'book_flow.py').read_text(encoding='utf-8')
    assert '"stage_playlist_refresh"' in source
    assert '"stage_source_download"' in source

def test_restore_and_present_terminology_is_consistent():
    assert ui_text('en', 'Восстановить') == 'Restore'
    assert ui_text('de', 'Восстановить') == 'Wiederherstellen'
    assert ui_text('en', 'есть') == 'present'

def test_backup_multiline_runtime_translation_accepts_multiple_lines():
    raw = 'Резервная копия создана:\nC:/Backup/file.zip\nsettings, history'
    out = localize_runtime_text('en', raw)
    assert out == 'Backup created:\nC:/Backup/file.zip\nsettings, history'


# Origin: test_structured_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_track_status_is_language_neutral_and_legacy_value_normalizes():
    assert Track(1, 'One', 'one.mp3').local_status == TRACK_STATUS_MISSING
    assert Track(1, 'One', 'one.mp3', local_status='нет').local_status == TRACK_STATUS_MISSING
    assert TRACK_STATUS_MISSING == 'missing'

def test_missing_file_loaded_literal_is_translated_in_all_non_russian_languages():
    assert ui_text('en', 'Файл загружен: {name}', name='chapter.mp3') == 'File loaded: chapter.mp3'
    assert ui_text('de', 'Файл загружен: {name}', name='chapter.mp3') == 'Datei geladen: chapter.mp3'
    assert ui_text('uk', 'Файл загружен: {name}', name='chapter.mp3') == 'Файл завантажено: chapter.mp3'

def test_runtime_regex_supports_multiline_capture():
    text = 'Резервная копия создана:\nC:/Books/backup.zip\nextra'
    translated = localize_runtime_text('en', text)
    assert translated.startswith('Backup created:\n')
    assert 'extra' in translated
