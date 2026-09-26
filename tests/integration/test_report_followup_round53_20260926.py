from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from audioknigi.download import book_flow
from audioknigi.download.probe import ProbeMixin
from audioknigi.models import Book, Track
from tools import exception_audit, package_source_release, qt_localization_audit
from tools import qt_windows_acceptance, undefined_global_audit


def test_exception_audit_uses_requested_root_and_detects_tuple_and_ellipsis(tmp_path):
    (tmp_path / 'audioknigi').mkdir()
    (tmp_path / 'tools').mkdir()
    (tmp_path / 'audioknigi/sample.py').write_text(
        'def f():\n'
        '    try: work()\n'
        '    except (RuntimeError, Exception): pass\n'
        '    try: work()\n'
        '    except Exception: ...\n'
        '    try: work()\n'
        '    except (Exception, BaseException): ...\n'
        '    try: work()\n'
        '    except ValueError: pass\n'
        '    try: work()\n'
        '    except Exception: raise\n', encoding='utf-8',
    )
    (tmp_path / 'tools/exception_allowlist.json').write_text('{}', encoding='utf-8')
    findings, unknown, stale = exception_audit.audit(tmp_path)
    assert len(findings) == 3
    assert findings == unknown
    assert stale == []
    assert [item['handler'] for item in findings] == ['Exception', 'Exception', 'BaseException']
    (tmp_path / 'tools/exception_allowlist.json').write_text(
        json.dumps({item['key']: 'reviewed test' for item in findings}), encoding='utf-8',
    )
    assert exception_audit.audit(tmp_path)[1:] == ([], [])


def test_localization_detects_keyword_literals_and_dynamic_text(tmp_path, monkeypatch):
    monkeypatch.setattr(qt_localization_audit, 'ROOT', tmp_path)
    sample = tmp_path / 'sample.py'
    sample.write_text(
        'QLabel(text="Текст")\n'
        'QGroupBox(title="Группа")\n'
        'QAction(icon, text="Действие")\n'
        'button.setText(text="Кнопка")\n'
        'button.setAccessibleName(name="Имя")\n'
        'button.setText(text=f"Глав: {count}")\n'
        'QLabel(text=_l("Переведено"))\n'
        'QLabel(text="English")\n', encoding='utf-8',
    )
    assert len(qt_localization_audit._direct_visible_russian(sample)) == 5
    assert len(qt_localization_audit._unwrapped_dynamic_visible_russian(sample)) == 1


def test_localization_reports_missing_required_file(monkeypatch):
    original = Path.is_file
    missing = qt_localization_audit.ROOT / 'audioknigi/downloader.py'
    monkeypatch.setattr(Path, 'is_file', lambda self: False if self == missing else original(self))
    assert 'missing runtime localization source: audioknigi/downloader.py' in qt_localization_audit.audit()


def test_undefined_global_audit_checks_entrypoint(tmp_path, monkeypatch, capsys):
    package = tmp_path / 'audioknigi'
    package.mkdir()
    (tmp_path / 'audioknigi_qt.py').write_text('def main():\n    return absent_name\n', encoding='utf-8')
    monkeypatch.setattr(undefined_global_audit, 'ROOT', tmp_path)
    monkeypatch.setattr(undefined_global_audit, 'PACKAGE_ROOT', package)
    assert undefined_global_audit.main() == 1
    assert 'audioknigi_qt.py:main: unresolved global absent_name' in capsys.readouterr().out


def test_source_package_keeps_fixtures_but_not_nested_private_state_or_binaries(tmp_path):
    root = tmp_path / 'project'
    names = ['tests/fixtures/settings.json', 'tests/fixtures/nested/history.json',
             'settings.json', 'profile/cookies.json', 'plugins/module.pyd',
             'native/lib.so', 'native/LIB.DLL', 'app.py']
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'fixture')
    output = package_source_release.build_source_zip(root, tmp_path / 'source.zip', root_name='src')
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == {'src/tests/fixtures/settings.json',
                                         'src/tests/fixtures/nested/history.json', 'src/app.py'}


def test_missing_audio_message_preserves_zero_index(tmp_path, monkeypatch):
    monkeypatch.setattr(book_flow, 'resolve_executable', lambda name: 'ffmpeg')

    class Flow(book_flow.BookFlowMixin):
        def _check_cancel(self): pass
        def _scan_book_files(self, *args, **kwargs): pass
        def _check_disk_space(self, *args, **kwargs): return True
        def _write_resume_manifest(self, *args): pass
        def _book_folder(self, *args): return tmp_path
        def _log_book_flow(self, *args, **kwargs): pass

    book = Book(url='https://example.invalid/book', title='Book',
                tracks=[Track(index=0, title='Prologue', file='', local_status='missing')])
    with pytest.raises(RuntimeError, match=r'частей: 0\.'):
        Flow()._process_book_once(book, [0])


@pytest.mark.parametrize('selection', ['all', '*', ['all'], ['*'], [0, 'all']])
def test_space_estimation_all_markers_include_entire_book(tmp_path, selection):
    class Probe(ProbeMixin):
        def _book_folder(self, *args, **kwargs): return tmp_path

    book = Book(url='https://example.invalid/book', title='Book', tracks=[
        Track(index=0, title='Zero', file='https://example.invalid/0.mp3', duration=10, local_status='missing'),
        Track(index=1, title='One', file='https://example.invalid/1.mp3', duration=20, local_status='missing'),
    ])
    probe = Probe()
    assert probe._estimate_required_space(book, selection) == probe._estimate_required_space(book)
    assert probe._estimate_required_space(book) > probe._estimate_required_space(book, [0]) > 0


@pytest.mark.parametrize('selection', [[True], ['bad'], [-1], ['1.5']])
def test_space_estimation_rejects_invalid_selection_instead_of_underestimating(selection):
    book = Book(url='https://example.invalid/book', title='Book')
    with pytest.raises(ValueError, match='Invalid selected track index'):
        ProbeMixin()._estimate_required_space(book, selection)


@pytest.mark.parametrize('candidate_valid', [False, True])
def test_acceptance_status_displays_existing_report_without_rewriting(
    tmp_path, monkeypatch, capsys, candidate_valid,
):
    exe = tmp_path / 'app.exe'
    exe.write_bytes(b'current binary')
    report_path = tmp_path / 'report.json'
    report = qt_windows_acceptance._new_report(exe)
    report['exe_sha256'] = '0' * 64
    raw = json.dumps(report).encode('utf-8')
    report_path.write_bytes(raw)
    if candidate_valid:
        monkeypatch.setattr(qt_windows_acceptance, 'validate_candidate_manifest', lambda *a, **kw: {})
    result = qt_windows_acceptance.main([
        '--exe', str(exe), '--report', str(report_path),
        '--candidate-manifest', str(tmp_path / 'missing.json'), '--status', '--allow-non-windows',
    ])
    out = capsys.readouterr().out
    assert result == (1 if candidate_valid else 43)
    assert 'INCOMPLETE' in out
    assert '0' * 64 in out
    assert ('Release-candidate manifest rejected' in out) is not candidate_valid
    assert report_path.read_bytes() == raw


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_support_tail_keeps_short_utf8_content_for_both_line_endings(tmp_path, newline):
    from audioknigi.diagnostics.support_bundle import _tail

    text = newline.join(["строка один", "строка два", "строка три", ""])
    path = tmp_path / "app.log"
    path.write_bytes(text.encode("utf-8"))
    payload = _tail(path, max_bytes=20)
    assert 0 < len(payload) <= 20
    assert payload.decode("utf-8") in text
    assert not payload.decode("utf-8").startswith("ока")
