from __future__ import annotations

import json
import os
from pathlib import Path
import pytest

from audioknigi.core import Cancelled
from audioknigi.diagnostics import support_bundle
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _hydrate_search_result_titles
from audioknigi.models import SearchResult
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.library_service import scan_unfinished

ROOT = Path(__file__).resolve().parents[2]


def test_whole_book_resume_manifest_null_or_empty_is_discoverable(tmp_path):
    for name, selected in (("null", None), ("legacy-empty", [])):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "resume.json").write_text(
            json.dumps({"url": "https://example.test/book", "title": name, "selected_indices": selected}),
            encoding="utf-8",
        )
    records = scan_unfinished(tmp_path)
    assert len(records) == 2
    assert all(record.selected_indices is None for record in records)


def test_support_bundle_home_redaction_does_not_replace_filesystem_root(monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: Path("/"))
    assert support_bundle._privacy_path("/var/log/audio/app.log") == "/var/log/audio/app.log"


def test_support_bundle_home_placeholder_matches_platform(monkeypatch, tmp_path):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    value = str(tmp_path / "Books")
    redacted = support_bundle._privacy_path(value)
    expected = "%USERPROFILE%" if os.name == "nt" else "~"
    assert redacted.startswith(expected)


def test_ui_text_does_not_format_literal_braces_without_kwargs(monkeypatch):
    import audioknigi.i18n as i18n

    monkeypatch.setitem(i18n._PHASE29_LITERAL_TRANSLATIONS.setdefault("en", {}), "Example {Book_Title}", "Example {Book_Title}")
    assert ui_text("en", "Example {Book_Title}") == "Example {Book_Title}"


def test_runtime_backup_translation_accepts_crlf():
    translated = localize_runtime_text("en", "Резервная копия создана:\r\nC:/Backup/file.zip")
    assert translated == "Backup created:\nC:/Backup/file.zip"


def test_knigavuhe_hydration_propagates_cancelled(monkeypatch):
    import audioknigi.knigavuhe as kv

    result = SearchResult(title="Demo", url="https://knigavuhe.org/book/demo/", source="knigavuhe.org")

    def cancelled(_result):
        raise Cancelled("cancel")

    monkeypatch.setattr(kv, "_resolve_search_result_title", cancelled)
    with pytest.raises(Cancelled):
        _hydrate_search_result_titles([result])


def test_playwright_private_entry_uses_runtime_error_not_assert(monkeypatch):
    import audioknigi.services.book_analysis_service as module

    monkeypatch.setattr(module, "sync_playwright", None)
    service = BookAnalysisService()
    with pytest.raises(RuntimeError, match="Playwright"):
        service._analyze_audioknigi_playwright("https://example.test")


def test_qt_selftest_uses_binding_safe_deferred_delete_call():
    source = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")
    assert "send_posted_events = QCoreApplication.sendPostedEvents" in source
    assert "send_posted_events(None, QEvent.Type.DeferredDelete)" in source
    assert "send_posted_events(event_type=QEvent.Type.DeferredDelete)" in source


def test_readme_quality_gate_paths_are_cross_platform():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "tools\\full_parity_audit.py" not in readme
    assert "python tools/full_parity_audit.py" in readme


def test_third_party_notice_covers_pyinstaller_and_license_status():
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "PyInstaller / PyInstaller bootloader" in notices
    assert "No top-level project license is declared" in notices
    assert (ROOT / "docs" / "development" / "RELEASE_LICENSING.md").is_file()


def test_refactored_network_and_playerjs_hot_paths_are_not_semicolon_compressed():
    network = (ROOT / "audioknigi" / "download" / "network.py").read_text(encoding="utf-8")
    pole = (ROOT / "audioknigi" / "poleknig.py").read_text(encoding="utf-8")
    network_head = network[: network.index("class NetworkDownloadMixin:")]
    playerjs = pole[pole.index("def _iter_js_object_literals"): pole.index("def _normalize_js_literals_for_python")]
    assert ";" not in network_head
    assert ";" not in playerjs
