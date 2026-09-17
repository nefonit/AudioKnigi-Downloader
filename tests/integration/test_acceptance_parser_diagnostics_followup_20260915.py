from __future__ import annotations

import ast
import importlib.util
import json
import threading
import zipfile
from pathlib import Path

import pytest

from audioknigi.core import Cancelled
from audioknigi.download.common import atomic_write_text
from audioknigi.models import Book, Track

ROOT = Path(__file__).resolve().parents[2]


def _load_tool(name: str):
    path = ROOT / "tools" / name
    spec = importlib.util.spec_from_file_location(f"test_tool_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_candidate_manifest_accepts_report_style_gate_objects(tmp_path: Path):
    tool = _load_tool("qt_windows_acceptance.py")
    exe = tmp_path / "app.exe"
    exe.write_bytes(b"binary")
    gates = {
        name: {"status": "pass", "exit_code": 0}
        for name in ("runtime", "accessibility", "playwright_edge", "import_boundary", "frozen_module_boundary")
    }
    manifest = {
        "schema": tool.ACCEPTANCE_SCHEMA,
        "app_version": tool.APP_VERSION,
        "migration_stage": tool.QT_MIGRATION_STAGE,
        "platform": "linux",
        "exe_sha256": tool.sha256_file(exe),
        "automated": gates,
    }
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    loaded = tool.validate_candidate_manifest(path, exe, require_windows=False)
    assert loaded["automated"]["runtime"]["status"] == "pass"


def test_unused_import_audit_parses_nested_string_forward_refs():
    tool = _load_tool("unused_import_audit.py")
    tree = ast.parse('from typing import Optional\nfrom pkg import MyModel\nvalue: Optional["MyModel"] = None\n')
    assert "MyModel" in tool._annotation_loaded_names(tree)


def test_localization_audit_scans_qt_mixins_and_pages():
    source = (ROOT / "tools/qt_localization_audit.py").read_text(encoding="utf-8")
    assert 'ROOT / "audioknigi/qt/main_window_pages.py"' in source
    assert '(ROOT / "audioknigi/qt/mixins").glob("*.py")' in source


def test_full_parity_uses_source_bundle_paths_before_declaring_missing_file():
    source = (ROOT / "tools/full_parity_audit.py").read_text(encoding="utf-8")
    assert "source_paths(root, rel)" in source
    assert 'failures.append(f"missing source bundle {rel}")' in source


def test_historical_failure_parser_preserves_spaces_and_dashes_inside_params():
    tool = _load_tool("historical_regression_audit.py")
    line = "test_x.py::test_case[param 1 - case 2] - AssertionError: boom"
    assert tool._failed_nodeid_from_line(line) == "test_x.py::test_case[param 1 - case 2]"


def test_poleknig_playwright_cancelled_before_browser_work():
    import audioknigi.poleknig as poleknig

    event = threading.Event()
    event.set()
    with pytest.raises(Cancelled):
        poleknig._fetch_book_playwright("https://poleknig.com/books/1", cancel_event=event)


def test_poleknig_author_catalog_future_does_not_swallow_cancelled():
    source = (ROOT / "audioknigi/poleknig.py").read_text(encoding="utf-8")
    block = source[source.index("def _expand_matching_author_catalogs"):source.index("def search(", source.index("def _expand_matching_author_catalogs"))]
    assert "except Cancelled:\n                raise" in block


def test_support_bundle_includes_existing_empty_error_log(tmp_path: Path, monkeypatch):
    import audioknigi.diagnostics.support_bundle as support

    error_log = tmp_path / "errors.log"
    error_log.write_bytes(b"")
    app_log = tmp_path / "app.log"
    crash = tmp_path / "crash.txt"
    queue = tmp_path / "queue.json"
    queue.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(support, "ERROR_LOG_FILE", error_log)
    monkeypatch.setattr(support, "APP_LOG_FILE", app_log)
    monkeypatch.setattr(support, "CRASH_REPORT_FILE", crash)
    monkeypatch.setattr(support, "QT_QUEUE_FILE", queue)

    target = support.create_support_bundle(tmp_path / "support.zip", settings={})
    with zipfile.ZipFile(target) as archive:
        assert "diagnostics/errors.log" in archive.namelist()
        assert archive.read("diagnostics/errors.log") == b""


def test_atomic_write_text_creates_missing_parent_directory(tmp_path: Path):
    target = tmp_path / "nested" / "more" / "file.txt"
    atomic_write_text(target, "hello")
    assert target.read_text(encoding="utf-8") == "hello"


def test_split_track_uses_effective_duration_when_end_is_missing():
    source = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    block = source[source.index("def _split_track"):source.index("def _save_book_sidecars")]
    assert "measured = effective_track_duration(track)" in block
    assert 'cmd += ["-t", str(duration)]' in block


def test_audioknigi_playwright_closes_browser_before_http_playlist_fetch():
    source = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    start = source.index("def _analyze_audioknigi_playwright")
    block = source[start:source.index("def _remote_size", start)]
    close_pos = block.index("browser.close()")
    request_pos = block.index("session.get(playlist_url")
    assert close_pos < request_pos
