from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from audioknigi.config.settings import migrate_settings
from audioknigi.diagnostics import support_bundle
from audioknigi.download_engine import DownloadService
from audioknigi.downloader import DownloaderMixin
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.services.book_analysis_service import BookAnalysisService
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.library_service import scan_unfinished
from audioknigi.sources import normalize_supported_url

ROOT = Path(__file__).resolve().parents[2]


def test_mapping_base_has_real_docstring_and_safe_to_dict():
    assert MappingDataclass.__doc__
    assert "mapping adapter" in MappingDataclass.__doc__.casefold()
    assert MappingDataclass().to_dict() == {}


def test_malformed_explicit_port_is_rejected_without_value_error():
    assert normalize_supported_url("https://poleknig.com:abc/books/1") == ""


def test_none_selected_indices_means_whole_book(tmp_path):
    book = Book(
        url="https://audioknigi.com.ua/audio-1",
        title="Book",
        tracks=[Track(index=1, title="One", file="https://cdn.invalid/1.mp3")],
    )
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    request.validate()
    assert request.resolved_selected_indices() == [1]
    # Whole-book preflight reaches file validation instead of being mislabeled
    # as a partial selection.
    result = DownloadService().duplicate_preflight(request, probe_durations=False)
    assert result.exact_duplicate is False
    assert result.evidence == "files-incomplete"


def test_unfinished_scan_preserves_zero_based_track_index(tmp_path):
    folder = tmp_path / "book"
    folder.mkdir()
    (folder / "resume.json").write_text(
        json.dumps(
            {
                "url": "https://knigavuhe.org/book/demo/",
                "title": "Demo",
                "selected_indices": [0],
            }
        ),
        encoding="utf-8",
    )
    found = scan_unfinished(tmp_path)
    assert len(found) == 1
    assert found[0].selected_indices == [0]


def test_disk_preflight_does_not_create_book_folder(tmp_path):
    host = DownloaderMixin()
    host.runtime_output_dir = tmp_path
    book = Book(
        url="https://audioknigi.com.ua/audio-1",
        title="Must Not Exist Yet",
        tracks=[Track(index=1, title="One", file="https://cdn.invalid/1.mp3")],
        remote_size=0,
    )
    expected = host._book_folder(book, create=False)
    assert not expected.exists()
    host._estimate_required_space(book, [1])
    host._disk_space_info(book, [1])
    assert not expected.exists()


def test_frozen_dependency_report_falls_back_to_module_versions(monkeypatch):
    def missing_metadata(_name):
        raise ValueError("dist-info unavailable in one-file bundle")

    fake = types.SimpleNamespace(__version__="9.9-test")
    monkeypatch.setattr(support_bundle.importlib.metadata, "version", missing_metadata)
    monkeypatch.setattr(support_bundle.importlib, "import_module", lambda _name: fake)
    versions = support_bundle._dependency_versions()
    assert set(versions) == {"PySide6", "requests", "playwright", "Pillow", "mutagen"}
    assert set(versions.values()) == {"9.9-test"}


def test_invalid_normalization_mode_is_normalized_at_settings_boundary():
    settings, _changed = migrate_settings({"normalization_mode": "not-a-real-mode"})
    assert settings["normalization_mode"] == "off"


def test_runtime_translation_specific_rule_precedes_generic_analyze_rule():
    source = "Анализирую audioknigi.com.ua быстрым HTTP-способом…"
    assert localize_runtime_text("en", source) == "Analyzing audioknigi.com.ua using the fast HTTP method…"
    assert "быстрым" not in localize_runtime_text("de", source)


def test_ukrainian_legacy_literals_cover_cancellation_and_queue_statuses():
    keys = (
        "Запрошена отмена анализа…",
        "Запрошена отмена скачивания…",
        "Очередь завершена.",
        "Скачивание отменено пользователем.",
        "Скачивание уже выполняется.",
    )
    for key in keys:
        assert ui_text("uk", key) != key


def test_runtime_exact_catalog_orientation_matches_lookup_contract():
    source = "Настройки сохранены. Масштаб применится после перезапуска приложения."
    translated = localize_runtime_text("uk", source)
    assert translated != source
    assert "застосується" in translated


def test_cloudflare_http_200_interstitial_detection_is_shared():
    assert BookAnalysisService._looks_like_protection("<title>Just a moment...</title><div class='cf-chl-x'>", 200)
    assert not BookAnalysisService._looks_like_protection("An article mentioning Cloudflare and captcha.", 200)


def test_downloader_source_analysis_delegates_playerjs_to_shared_service():
    source = (ROOT / "audioknigi" / "download" / "source_analysis.py").read_text(encoding="utf-8")
    assert "BookAnalysisService" in source
    assert "def _parse_playlist_data" not in source
    assert "def _extract_playlist_url" not in source


def test_split_module_name_regressions_are_guarded_in_ci():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "undefined_global_audit.py" in ci
    assert "undefined_global_audit.py" in release


def test_changelog_release_hierarchy_and_architecture_docs_are_current():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert changelog.startswith("# Changelog\n")
    assert "## 4.12.34 — Whole-book selection and runtime contract hardening" in changelog
    assert not any(line.startswith("## ") and "Build system — Python 3.14.7" in line for line in changelog.splitlines())
    assert "## 4.7.1.2" in changelog
    assert "Additional late 4.12.31 accessibility and UI hardening" in changelog
    assert "`audioknigi/download_engine.py`" in readme


def test_qt_selftest_reports_current_runtime_stage_but_keeps_acceptance_marker():
    qt_init = (ROOT / "audioknigi" / "qt" / "__init__.py").read_text(encoding="utf-8")
    entry = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")
    assert 'QT_MIGRATION_STAGE = "phase-39"' in qt_init
    assert 'QT_RUNTIME_STAGE = "qt-only-4.12.42"' in qt_init
    assert "QT RUNTIME SELFTEST: OK" in entry and "QT_RUNTIME_STAGE" in entry
    assert "PLAYWRIGHT EDGE SELFTEST: OK" in entry
