"""Consolidated integration tests for the quality gates domain.

Historical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.
"""


from __future__ import annotations


import json
from pathlib import Path
from types import SimpleNamespace
from tools import qt_windows_acceptance
from tools.undefined_global_audit import _SPECIAL_GLOBALS
import ast
import importlib.util
import threading
import zipfile
import pytest
from audioknigi.core import Cancelled
from audioknigi.download.common import atomic_write_text
from audioknigi.models import Book, Track
import requests
from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.queue_service import _parse_selected_indices_payload
from tools.exception_audit import scan as exception_scan
from tools.qt_localization_audit import _ui_text_literals
from tools.unused_import_audit import unused_imports
import os
from audioknigi.diagnostics import support_bundle
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
from audioknigi.core import extract_metadata_from_html
from audioknigi.logging_utils import sanitize_log_text
from audioknigi.models import Book, SearchResult, Track
from audioknigi.services.library_service import export_history
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict
from audioknigi import core
from audioknigi.core import fmt_size
from audioknigi.templates import render_text_template
from audioknigi.config.settings import migrate_settings
from audioknigi.download_engine import _DownloadEngine
from audioknigi.poleknig import _book_page_metadata
from audioknigi.providers.audioknigi_search import _strip_author_prefix_from_title
from audioknigi.providers import audioknigi_search
from audioknigi.download import book_flow
from audioknigi.download.probe import ProbeMixin
from tools import exception_audit as exception_audit__report_followup_round53_20260926, package_source_release, qt_localization_audit
from tools import qt_windows_acceptance, undefined_global_audit
from audioknigi.diagnostics.support_bundle import _sanitize_log_bytes, _tail
from audioknigi.qt.acceptance_contract import ACCEPTANCE_SCHEMA, acceptance_issues
from tools import qt_localization_audit, qt_windows_acceptance
import time
from audioknigi.services import search_service
from audioknigi.services.source_health_service import SourceHealthItem, SourceHealthOutcome
import subprocess
import sys
import re
from audioknigi.knigavuhe import _merge_narration_variants
from audioknigi.models import NarrationVariant, SearchResult, Track, TRACK_STATUS_MISSING
from audioknigi.providers import provider_for_key


# Origin: test_acceptance_localization_followup_20260914.py
ROOT = Path(__file__).resolve().parents[2]

def test_acceptance_gate_accepts_bom_prefixed_ok_report(tmp_path, monkeypatch):
    output = tmp_path / 'gate.txt'

    def fake_run(*args, **kwargs):
        output.write_text('\ufeffOK\nvalidated\n', encoding='utf-8')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(qt_windows_acceptance.subprocess, 'run', fake_run)
    result = qt_windows_acceptance._run_gate(tmp_path / 'dummy.exe', '--qt-runtime-selftest', 'AUDIOKNIGI_QT_RUNTIME_SELFTEST_REPORT', output)
    assert result['status'] == 'pass'
    assert result['report_ok'] is True

def test_undefined_global_gate_is_portable_for_windows_error_alias():
    assert 'WindowsError' in _SPECIAL_GLOBALS


# Origin: test_acceptance_parser_diagnostics_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool__acceptance_parser_diagnostics_followup_20260915(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_candidate_manifest_accepts_report_style_gate_objects(tmp_path: Path):
    tool = _load_tool__acceptance_parser_diagnostics_followup_20260915('qt_windows_acceptance.py')
    exe = tmp_path / 'app.exe'
    exe.write_bytes(b'binary')
    gates = {name: {'status': 'pass', 'exit_code': 0} for name in ('runtime', 'accessibility', 'playwright_edge', 'import_boundary', 'frozen_module_boundary')}
    manifest = {'schema': tool.ACCEPTANCE_SCHEMA, 'app_version': tool.APP_VERSION, 'migration_stage': tool.QT_MIGRATION_STAGE, 'platform': 'linux', 'exe_sha256': tool.sha256_file(exe), 'automated': gates}
    path = tmp_path / 'candidate.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    loaded = tool.validate_candidate_manifest(path, exe, require_windows=False)
    assert loaded['automated']['runtime']['status'] == 'pass'

def test_unused_import_audit_parses_nested_string_forward_refs():
    tool = _load_tool__acceptance_parser_diagnostics_followup_20260915('unused_import_audit.py')
    tree = ast.parse('from typing import Optional\nfrom pkg import MyModel\nvalue: Optional["MyModel"] = None\n')
    assert 'MyModel' in tool._annotation_loaded_names(tree)

def test_localization_audit_scans_qt_mixins_and_pages():
    source = (ROOT / 'tools/qt_localization_audit.py').read_text(encoding='utf-8')
    assert 'ROOT / "audioknigi/qt/main_window_pages.py"' in source
    assert '(ROOT / "audioknigi/qt/mixins").glob("*.py")' in source

def test_full_parity_uses_source_bundle_paths_before_declaring_missing_file():
    source = (ROOT / 'tools/full_parity_audit.py').read_text(encoding='utf-8')
    assert 'source_paths(root, rel)' in source
    assert 'failures.append(f"missing source bundle {rel}")' in source

def test_historical_failure_parser_preserves_spaces_and_dashes_inside_params():
    tool = _load_tool__acceptance_parser_diagnostics_followup_20260915('historical_regression_audit.py')
    line = 'test_x.py::test_case[param 1 - case 2] - AssertionError: boom'
    assert tool._failed_nodeid_from_line(line) == 'test_x.py::test_case[param 1 - case 2]'


# Origin: test_quality_runtime_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_exception_audit_distinguishes_duplicate_broad_handlers_and_bare_except(tmp_path):
    package = tmp_path / 'audioknigi'
    package.mkdir()
    (package / 'sample.py').write_text('\ndef f():\n    try: x = 1\n    except Exception: pass\n    try: x = 2\n    except Exception: pass\n    try: x = 3\n    except BaseException: pass\n    try: x = 4\n    except: pass\n', encoding='utf-8')
    keys = [item['key'] for item in exception_scan(tmp_path)]
    assert any((key.endswith(':Exception#1') for key in keys))
    assert any((key.endswith(':Exception#2') for key in keys))
    assert any((key.endswith(':BaseException#1') for key in keys))
    assert any((key.endswith(':bare#1') for key in keys))
    assert len(keys) == 4

def test_unused_import_audit_checks_conditional_and_except_imports_and_forward_annotations(tmp_path):
    path = tmp_path / 'sample.py'
    path.write_text("\nfrom typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from package import SomeClass\ntry:\n    import json\nexcept ImportError:\n    import simplejson as json\n\ndef f(value: 'SomeClass'):\n    return json.dumps(value)\n", encoding='utf-8')
    assert unused_imports(path) == []

def test_localization_audit_reads_keyword_ui_text_literal(tmp_path):
    path = tmp_path / 'sample.py'
    path.write_text('value = ui_text("uk", russian_text="Русский текст")\n', encoding='utf-8')
    assert _ui_text_literals(path) == {'Русский текст'}

def test_qt_import_audit_no_longer_keeps_identity_alias_table():
    source = (ROOT / 'tools' / 'qt_import_audit.py').read_text(encoding='utf-8')
    assert 'aliases = {"pyside6": "pyside6", "pillow": "pillow"}' not in source


# Origin: test_recovery_diagnostics_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_readme_quality_gate_paths_are_cross_platform():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert 'tools\\full_parity_audit.py' not in readme
    assert 'python tools/full_parity_audit.py' in readme


# Origin: test_release_integrity_followup_20260913.py
ROOT = Path(__file__).resolve().parents[2]

def test_undefined_global_gate_accepts_package_path_special():
    assert '__path__' in _SPECIAL_GLOBALS

def test_exception_allowlist_has_no_stale_entries_and_is_sorted():
    findings, unknown, stale = exception_audit__release_integrity_followup_20260913(ROOT)
    assert findings
    assert unknown == []
    assert stale == []
    data = json.loads((ROOT / 'tools' / 'exception_allowlist.json').read_text(encoding='utf-8'))
    assert list(data) == sorted(data)
    assert not any(('source_analysis.py:_remote_size' in key for key in data))
    assert not any(('source_analysis.py:on_request' in key for key in data))


# Origin: test_release_quality_followup_20260915.py
ROOT = Path(__file__).resolve().parents[2]

def _load_tool__release_quality_followup_20260915(name: str):
    path = ROOT / 'tools' / name
    spec = importlib.util.spec_from_file_location(f'test_tool_{path.stem}', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def test_undefined_global_audit_knows_standard_module_globals():
    tool = _load_tool__release_quality_followup_20260915('undefined_global_audit.py')
    assert {'__doc__', '__annotations__', '__path__', 'WindowsError'} <= tool._SPECIAL_GLOBALS

def test_localization_audit_recognizes_direct_and_qualified_calls(tmp_path: Path):
    tool = _load_tool__release_quality_followup_20260915('qt_localization_audit.py')
    sample = tmp_path / 'sample.py'
    sample.write_text('from x import _l\nimport y as i18n\n_l("Русский текст")\ni18n.ui_text("uk", "Другой текст")\n', encoding='utf-8')
    assert 'Русский текст' in tool._literal_l_calls(sample)
    assert 'Другой текст' in tool._ui_text_literals(sample)

def _request() -> DownloadRequest:
    book = Book(url='https://knigavuhe.org/book/1', title='Book', tracks=[Track(index=1, title='One', file='https://cdn.example/1.mp3')])
    return DownloadRequest(book=book, selected_indices=None, output_dir=Path('.'))

def test_historical_gate_uses_line_anchored_pytest_error_detection():
    source = (ROOT / 'tools/historical_regression_audit.py').read_text(encoding='utf-8')
    assert 're.search(r"^ERROR\\s+", combined, re.MULTILINE)' in source


# Origin: test_report_followup_round33_20260918.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round33_20260918(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_duplicate_open_folder_updates_book_state_and_audit_timeout_is_relaxed() -> None:
    analysis = src__report_followup_round33_20260918('audioknigi/qt/mixins/analysis_download.py')
    assert analysis.count('self.last_completed_book = self.current_book') >= 3
    audit = src__report_followup_round33_20260918('tools/historical_regression_audit.py')
    assert 'timeout=240' in audit


# Origin: test_report_followup_round34_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round34_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_audit_items_intentionally_left_unchanged_have_existing_safety_contracts() -> None:
    templates = src__report_followup_round34_20260919('audioknigi/templates.py')
    analysis = src__report_followup_round34_20260919('audioknigi/qt/mixins/analysis_download.py')
    i18n = src__report_followup_round34_20260919('audioknigi/i18n.py')
    assert 'values = template_values(book, output_dir="", language=language)' in templates
    assert 'if prompt.event.is_set()' in analysis
    assert 'return value.format(**kwargs)' in i18n


# Origin: test_report_followup_round38_20260919.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round38_20260919(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_accessibility_audit_covers_easy_dynamic_reader_controls() -> None:
    audit = src__report_followup_round38_20260919('audioknigi/qt/accessibility_audit.py')
    required = audit.split('REQUIRED_ACCESSIBLE_IDS = (', 1)[1].split(')\n\n', 1)[0]
    focusable = audit.split('FOCUSABLE_ACCESSIBLE_IDS = (', 1)[1].split(')\n\n', 1)[0]
    for identifier in ('easy_narration_variant', 'easy_book_description'):
        assert f'"{identifier}"' in required
        assert f'"{identifier}"' in focusable


# Origin: test_report_followup_round42_20260920.py
ROOT = Path(__file__).resolve().parents[2]

def src__report_followup_round42_20260920(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')

def test_accessibility_audit_tracks_segmented_mode_buttons_not_removed_combo() -> None:
    audit = src__report_followup_round42_20260920('audioknigi/qt/accessibility_audit.py')
    assert '"ui_mode_easy"' in audit
    assert '"ui_mode_advanced"' in audit
    assert '"ui_mode_stack"' in audit
    assert '    "ui_mode",' not in audit


# Origin: test_report_followup_round53_20260926.py
def test_exception_audit_uses_requested_root_and_detects_tuple_and_ellipsis(tmp_path):
    (tmp_path / 'audioknigi').mkdir()
    (tmp_path / 'tools').mkdir()
    (tmp_path / 'audioknigi/sample.py').write_text('def f():\n    try: work()\n    except (RuntimeError, Exception): pass\n    try: work()\n    except Exception: ...\n    try: work()\n    except (Exception, BaseException): ...\n    try: work()\n    except ValueError: pass\n    try: work()\n    except Exception: raise\n', encoding='utf-8')
    (tmp_path / 'tools/exception_allowlist.json').write_text('{}', encoding='utf-8')
    findings, unknown, stale = exception_audit__report_followup_round53_20260926.audit(tmp_path)
    assert len(findings) == 3
    assert findings == unknown
    assert stale == []
    assert [item['handler'] for item in findings] == ['Exception', 'Exception', 'BaseException']
    (tmp_path / 'tools/exception_allowlist.json').write_text(json.dumps({item['key']: 'reviewed test' for item in findings}), encoding='utf-8')
    assert exception_audit__report_followup_round53_20260926.audit(tmp_path)[1:] == ([], [])

def test_undefined_global_audit_checks_entrypoint(tmp_path, monkeypatch, capsys):
    package = tmp_path / 'audioknigi'
    package.mkdir()
    (tmp_path / 'audioknigi_qt.py').write_text('def main():\n    return absent_name\n', encoding='utf-8')
    monkeypatch.setattr(undefined_global_audit, 'ROOT', tmp_path)
    monkeypatch.setattr(undefined_global_audit, 'PACKAGE_ROOT', package)
    assert undefined_global_audit.main() == 1
    assert 'audioknigi_qt.py:main: unresolved global absent_name' in capsys.readouterr().out


# Origin: test_report_followup_round54_20260926.py
def test_candidate_manifest_malformed_schema_is_rejected_cleanly(tmp_path):
    exe = tmp_path / 'app.exe'
    exe.write_bytes(b'binary')
    manifest = tmp_path / 'candidate.json'
    manifest.write_text(json.dumps({'schema': [], 'app_version': '', 'migration_stage': '', 'platform': 'windows', 'exe_sha256': '', 'automated': {}}), encoding='utf-8')
    with pytest.raises(ValueError, match='schema'):
        qt_windows_acceptance.validate_candidate_manifest(manifest, exe, require_windows=False)


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

def test_accessibility_audit_checks_every_visible_focusable_button():
    source = (ROOT / 'audioknigi/qt/accessibility_audit.py').read_text(encoding='utf-8')
    assert 'window.findChildren(QAbstractButton)' in source
    assert 'empty accessible button name' in source
    assert 'empty accessible button description' in source
    assert '"player_back_30"' in source
    assert '"player_forward_30"' in source


# Origin: test_static_quality_gates.py
ROOT = Path(__file__).resolve().parents[2]

def run_tool(name, *args, timeout=60):
    return subprocess.run([sys.executable, str(ROOT / 'tools' / name), *args], cwd=ROOT, text=True, capture_output=True, timeout=timeout)

def test_full_parity_audit_passes_modular_layout():
    proc = run_tool('full_parity_audit.py', '--root', str(ROOT), '--require-legacy-retired')
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert 'PASS 61/61' in proc.stdout

def test_localization_audit_passes_modular_layout():
    proc = run_tool('qt_localization_audit.py')
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert 'static_ui_literals=translated' in proc.stdout

def test_exception_audit_has_no_unreviewed_bare_pass():
    proc = run_tool('exception_audit.py')
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert 'PASS' in proc.stdout

def test_unused_import_audit_passes_refactored_layers():
    proc = run_tool('unused_import_audit.py')
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert 'UNUSED IMPORT AUDIT: OK' in proc.stdout

def test_undefined_global_audit_catches_split_module_name_errors():
    proc = run_tool('undefined_global_audit.py')
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert 'UNDEFINED GLOBAL AUDIT: OK' in proc.stdout


# Origin: test_structured_hardening_20260912.py
ROOT = Path(__file__).resolve().parents[2]

def test_ci_exercises_minimum_and_release_python_and_unused_import_gate():
    workflow = (ROOT / '.github' / 'workflows' / 'ci.yml').read_text(encoding='utf-8')
    assert 'python-version: ["3.11", "3.14.7"]' in workflow
    assert 'python tools/unused_import_audit.py' in workflow

def test_unused_import_quality_gate_passes():
    proc = subprocess.run([sys.executable, str(ROOT / 'tools' / 'unused_import_audit.py')], cwd=ROOT, text=True, capture_output=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert 'UNUSED IMPORT AUDIT: OK' in proc.stdout
