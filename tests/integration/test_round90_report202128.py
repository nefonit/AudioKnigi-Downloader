"""Regression checks for the 20:21 audit, without UI/Internet dependencies."""
from __future__ import annotations

import ast
import html as html_lib
import json
import re
import threading
from concurrent.futures import Future
from pathlib import Path

import pytest
from audioknigi.config.settings import save_app_settings
from audioknigi.core import Cancelled
from audioknigi.models import Book, Track
from audioknigi.services.book_analysis_service import BookAnalysisService, AnalysisOptions, _iter_completed_cancellable
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.qt.acceptance_contract import save_report, load_report

ROOT = Path(__file__).resolve().parents[2]


def test_save_new_partial_settings_still_requires_onboarding(tmp_path):
    file = tmp_path / 'settings.json'
    assert save_app_settings({'language': 'ru'}, file)
    assert json.loads(file.read_text())['first_run_complete'] is False


def test_save_existing_legacy_settings_completes_onboarding(tmp_path):
    file = tmp_path / 'settings.json'
    file.write_text(json.dumps({'language': 'de', 'scale': 125}))
    assert save_app_settings({'player_rate': 1.5}, file)
    data = json.loads(file.read_text())
    assert data['first_run_complete'] is True
    assert data['language'] == 'de'
    assert data['player_rate'] == 1.5


def test_save_existing_incomplete_onboarding_preserves_false(tmp_path):
    file = tmp_path / 'settings.json'
    file.write_text(json.dumps({'first_run_complete': False, 'language': 'en'}))
    assert save_app_settings({'player_volume': 25}, file)
    assert json.loads(file.read_text())['first_run_complete'] is False


def test_late_chapter_duration_contributes_to_shared_source_lower_bound(monkeypatch):
    book = Book(url='https://audioknigi.com.ua/book/', title='Book', tracks=[
        Track(index=1,title='First',file='https://example.com/one.mp3',start=0,end=3600),
        Track(index=2,title='Last',file='https://example.com/one.mp3',start=3600,end=None,duration=900),
    ])
    fallback = Book(url='https://knigavuhe.org/book/', title='Fallback')
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False))
    monkeypatch.setattr(service, '_probe_remote_duration', lambda *_: 3700.0)
    monkeypatch.setattr(service, '_knigavuhe_fallback_candidate', lambda *_: fallback)
    monkeypatch.setattr(service, '_populate_missing_track_durations', lambda *_: None)
    assert service._recover_short_audioknigi_source(book) is fallback


def test_shared_source_no_known_final_duration_does_not_invent_one(monkeypatch):
    book = Book(url='https://audioknigi.com.ua/book/', title='Book', tracks=[
        Track(index=1,title='First',file='https://example.com/one.mp3',start=0,end=3600),
        Track(index=2,title='Last',file='https://example.com/one.mp3',start=3600,end=None),
    ])
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False))
    monkeypatch.setattr(service, '_probe_remote_duration', lambda *_: 3700.0)
    assert service._recover_short_audioknigi_source(book) is book


def test_cancellation_marks_pending_futures_cancelled():
    pending = [Future(),Future()]
    cancel = threading.Event();cancel.set()
    with pytest.raises(Cancelled):
        list(_iter_completed_cancellable(pending,cancel))
    assert all(f.cancelled() for f in pending)


def _help_renderer():
    source = ast.parse((ROOT/'audioknigi/qt/help_center.py').read_text(encoding='utf-8'))
    node = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == '_format_help_body_html')
    ns = {'html_lib': html_lib, 're':re}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'help_center.py','exec'),ns)
    return ns['_format_help_body_html']


def test_help_preserves_ordered_steps_and_bullet_lists():
    render=_help_renderer()
    result=render('Help','1. First\n2) Second\n\n- Note\n• Another')
    assert '<ol>' in result and '<li>First</li>' in result and '<li>Second</li>' in result
    assert '<ul>' in result and result.index('</ol>') < result.index('<ul>')


def test_help_preserves_numbering_start_and_switch_between_list_types():
    html=_help_renderer()('Help','5. Fifth\n6. Sixth\n- Note\n7) Seventh')
    assert '<ol start="5">' in html
    assert html.count('<ol') == 2 and '<ul>' in html


def test_disk_space_dialog_translation_preserves_paragraph_break():
    source = 'Недостаточно свободного места.\n\nНужно примерно: 1 ГБ\nСвободно: 500 МБ'
    for lang in ('en','de','uk'):
        result = localize_runtime_text(lang,source)
        assert '\n\n' in result and '500 МБ' in result


def test_template_placeholder_hint_remains_literal():
    source = 'Доступно: {Author} {Book_Title} {Year} {Genre} {Narrator} {Track_Number} {Track_Title}'
    for lang in ('en','de','uk','ru'):
        assert '{Author}' in ui_text(lang,source)


def test_acceptance_report_atomic_save(tmp_path):
    path=tmp_path/'acceptance.json'
    report={'schema':1,'checks':[]}
    assert save_report(path,report) == path
    assert load_report(path)==report
    assert not (tmp_path/'acceptance.json.tmp').exists()


def test_qt_contracts_source_helpers_have_fixed_selection_and_queue_errors():
    model = (ROOT/'audioknigi/qt/track_model.py').read_text(encoding='utf-8')
    analysis = (ROOT/'audioknigi/qt/mixins/analysis_download.py').read_text(encoding='utf-8')
    assert 'if indices is None:\n            self.set_all_selected(True)' in model
    assert 'task.last_error = str(payload)' in analysis
    assert 'self._persist_queue()' in analysis


def test_context_menu_scrolls_focused_cell_before_positioning():
    for p in ('history.py','queue.py'):
        source=(ROOT/'audioknigi/qt/mixins'/p).read_text(encoding='utf-8')
        assert '.scrollTo(current, QAbstractItemView.ScrollHint.EnsureVisible)' in source
