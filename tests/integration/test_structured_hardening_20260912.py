from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from audioknigi.diagnostics import support_bundle
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.knigavuhe import _merge_narration_variants
from audioknigi.models import (
    NarrationVariant,
    SearchResult,
    Track,
    TRACK_STATUS_MISSING,
)
from audioknigi.services import search_service
from audioknigi.providers import provider_for_key

ROOT = Path(__file__).resolve().parents[2]


def test_release_docs_and_dependency_contract_are_consistent():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    runtime = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    qt_alias = (ROOT / "requirements-qt.txt").read_text(encoding="utf-8")
    release = (ROOT / "requirements-release.txt").read_text(encoding="utf-8")

    assert "Python 3.11+ for source/runtime compatibility" in readme
    assert "CPython 3.14.7 x64" in readme
    assert runtime.splitlines()[0] == "# Qt-only runtime dependencies (Python 3.11+)."
    assert qt_alias.strip().endswith("-r requirements.txt")
    assert "PySide6==6.11.2" in release
    assert "playwright==1.62.0" in release
    assert "Pillow==12.3.0" in release
    assert "pyinstaller==6.22.2" in release

    assert changelog.count("# Changelog") == 1
    assert len(re.findall(r"^## 4\.12\.31\b", changelog, re.M)) == 1
    assert len(re.findall(r"^## 4\.12\.32\b", changelog, re.M)) == 1
    assert not re.search(r"^# 4\.12\.\d+", changelog, re.M)


def test_ci_exercises_minimum_and_release_python_and_unused_import_gate():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert 'python-version: ["3.11", "3.14.7"]' in workflow
    assert "python tools/unused_import_audit.py" in workflow


def test_retry_constructor_does_not_require_urllib3_2_only_other_keyword():
    source = (ROOT / "audioknigi" / "core.py").read_text(encoding="utf-8")
    block = source[source.index("retry = Retry("): source.index("adapter = HTTPAdapter", source.index("retry = Retry("))]
    assert "other=" not in block


def test_knigavuhe_variant_merge_clones_inputs_before_enrichment():
    first = NarrationVariant(url="https://knigavuhe.org/book/demo/", narrator="", title="", current=False)
    second = NarrationVariant(url="https://knigavuhe.org/book/demo/", narrator="Reader", title="Book", current=True)
    merged = _merge_narration_variants([first], [second])
    assert len(merged) == 1
    assert merged[0] is not first
    assert merged[0].narrator == "Reader"
    assert merged[0].title == "Book"
    assert merged[0].current is True
    assert first.narrator == ""
    assert first.title == ""
    assert first.current is False


def test_track_status_is_language_neutral_and_legacy_value_normalizes():
    assert Track(1, "One", "one.mp3").local_status == TRACK_STATUS_MISSING
    assert Track(1, "One", "one.mp3", local_status="нет").local_status == TRACK_STATUS_MISSING
    assert TRACK_STATUS_MISSING == "missing"


def test_support_bundle_path_privacy_handles_both_windows_slash_styles(monkeypatch):
    monkeypatch.setattr(support_bundle.Path, "home", classmethod(lambda cls: cls("C:/Users/Alice")))
    placeholder = "%USERPROFILE%" if os.name == "nt" else "~"
    assert support_bundle._privacy_path(r"C:\Users\Alice\Books") == placeholder + r"\Books"
    assert support_bundle._privacy_path("C:/Users/Alice/Books") == placeholder + "/Books"


def test_support_bundle_tail_starts_at_clean_utf8_line_boundary(tmp_path):
    path = tmp_path / "log.txt"
    text = "строка один\nстрока два\nстрока три\n"
    path.write_text(text, encoding="utf-8")
    payload = support_bundle._tail(path, max_bytes=20)
    decoded = payload.decode("utf-8")
    assert decoded
    normalized = decoded.replace("\r\n", "\n")
    assert normalized in text
    assert not normalized.startswith("ока")


def test_support_bundle_queue_uses_opaque_nonempty_ids_and_excludes_private_book_data(tmp_path, monkeypatch):
    queue_file = tmp_path / "queue.json"
    private_url = "https://example.invalid/private-book"
    queue_file.write_text(
        json.dumps([{"url": private_url, "title": "PRIVATE TITLE", "status_code": "pending", "attempts": 2}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(support_bundle, "QT_QUEUE_FILE", queue_file)
    target = support_bundle.create_support_bundle(tmp_path / "bundle.zip", settings={"language": "en"})
    with zipfile.ZipFile(target) as archive:
        payload = json.loads(archive.read("diagnostics/queue.summary.json").decode("utf-8"))
        combined = b"\n".join(archive.read(name) for name in archive.namelist())
    assert payload[0]["id"] and payload[0]["id"] != private_url
    assert payload[0]["status_code"] == "pending"
    assert payload[0]["attempts"] == 2
    assert private_url.encode() not in combined
    assert b"PRIVATE TITLE" not in combined


def test_search_source_filter_accepts_internal_provider_keys(monkeypatch):
    knigavuhe = provider_for_key("knigavuhe")
    poleknig = provider_for_key("poleknig")
    audioknigi = provider_for_key("audioknigi")
    monkeypatch.setattr(knigavuhe, "search", lambda q, cancel_event=None: [SearchResult("K", "https://knigavuhe.org/book/k/", source="knigavuhe.org")])
    monkeypatch.setattr(knigavuhe, "enrich_search_results", lambda items, cancel_event=None: items)
    monkeypatch.setattr(poleknig, "search", lambda q, cancel_event=None: [SearchResult("P", "https://poleknig.com/books/1", source="poleknig.com")])
    monkeypatch.setattr(audioknigi, "search", lambda q, cancel_event=None: pytest.fail("audioknigi provider must be filtered out"))

    outcome = search_service.search_all_sources("demo", sources=["knigavuhe", "poleknig"])
    assert not outcome.errors
    assert {item.source for item in outcome.results} == {"knigavuhe.org", "poleknig.com"}


def test_search_service_uses_registry_without_provider_search_cycle():
    service_source = (ROOT / "audioknigi" / "services" / "search_service.py").read_text(encoding="utf-8")
    adapters_source = (ROOT / "audioknigi" / "providers" / "adapters.py").read_text(encoding="utf-8")
    assert "registered_providers" in service_source
    assert "provider.search(" in service_source
    assert "services.search_service" not in adapters_source


def test_book_analysis_service_has_real_knigavuhe_fetch_binding():
    source = (ROOT / "audioknigi" / "services" / "book_analysis_service.py").read_text(encoding="utf-8")
    assert "from ..knigavuhe import fetch_book as fetch_knigavuhe_book" in source
    assert "fallback = fetch_knigavuhe_book(" in source


def test_qt_refactor_contracts_are_present_without_importing_pyside():
    main_source = (ROOT / "audioknigi" / "qt" / "main_window.py").read_text(encoding="utf-8")
    accessibility_source = (ROOT / "audioknigi" / "qt" / "mixins" / "accessibility_ui.py").read_text(encoding="utf-8")
    audit_source = (ROOT / "audioknigi" / "qt" / "accessibility_audit.py").read_text(encoding="utf-8")
    assert "from .player_controller import QtPlayerController" in main_source
    assert 'self._l("Неподдерживаемая ссылка")' in main_source
    assert "from ..accessibility_audit import audit_accessibility_window" in accessibility_source
    assert audit_source.count('"download_options"') >= 2


def test_missing_file_loaded_literal_is_translated_in_all_non_russian_languages():
    assert ui_text("en", "Файл загружен: {name}", name="chapter.mp3") == "File loaded: chapter.mp3"
    assert ui_text("de", "Файл загружен: {name}", name="chapter.mp3") == "Datei geladen: chapter.mp3"
    assert ui_text("uk", "Файл загружен: {name}", name="chapter.mp3") == "Файл завантажено: chapter.mp3"


def test_runtime_regex_supports_multiline_capture():
    text = "Резервная копия создана:\nC:/Books/backup.zip\nextra"
    translated = localize_runtime_text("en", text)
    assert translated.startswith("Backup created:\n")
    assert "extra" in translated


def test_download_book_info_uses_dynamic_track_number_width():
    source = (ROOT / "audioknigi" / "download" / "media.py").read_text(encoding="utf-8")
    assert "width = track_number_width(book)" in source
    assert "{row['index']:0{width}d}" in source


def test_unused_import_quality_gate_passes():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "unused_import_audit.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "UNUSED IMPORT AUDIT: OK" in proc.stdout
