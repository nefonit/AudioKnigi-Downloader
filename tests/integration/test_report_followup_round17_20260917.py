from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, migrate_ui_scale_settings
from audioknigi.i18n import _normalize_runtime_regex_catalog
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.search_service import search_all_sources


ROOT = Path(__file__).resolve().parents[2]


def test_ui_scale_migration_accepts_appsettings_mapping_without_losing_keys() -> None:
    source = AppSettings({"scale": 125, "custom_plugin_key": "keep-me"})
    migrated, changed = migrate_ui_scale_settings(source)
    assert changed is True
    assert migrated["scale"] == 100
    assert migrated["custom_plugin_key"] == "keep-me"
    assert migrated[UI_SCALE_MIGRATION_KEY] is True


def test_download_request_track_index_accepts_raw_scalars_mappings_and_tracks() -> None:
    assert DownloadRequest.track_index(3) == 3
    assert DownloadRequest.track_index("04") == 4
    assert DownloadRequest.track_index({"index": "5"}) == 5
    assert DownloadRequest.track_index(SimpleNamespace(index="06")) == 6
    with pytest.raises(ValueError):
        DownloadRequest.track_index("intro")


def test_malformed_runtime_regex_rows_are_filtered_instead_of_crashing_import() -> None:
    rows = _normalize_runtime_regex_catalog(
        [
            [],
            ["^ok$", {"en": "OK"}],
            ["missing variants"],
            {"pattern": "^bad$"},
            [123, {"en": "bad"}],
            ["^bad variants$", "not-a-mapping"],
        ]
    )
    assert rows == (("^ok$", {"en": "OK"}),)


def test_no_search_provider_error_uses_existing_localized_literal() -> None:
    outcome = search_all_sources("test query", sources=[])
    assert outcome.errors == ["Выберите хотя бы один сайт для поиска."]


def test_round17_formatting_hygiene_for_reported_pep8_rough_edges() -> None:
    crash = (ROOT / "audioknigi/crash_report.py").read_text(encoding="utf-8")
    knigavuhe = (ROOT / "audioknigi/knigavuhe.py").read_text(encoding="utf-8")
    assert "import platform, sys, time, traceback" not in crash
    assert 'availability="available"' not in knigavuhe
    assert 'availability = "available"' in knigavuhe


def test_changelog_round8_is_inside_41242_and_release_date_is_current() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## 4.12.42 — Acceptance parser, cancellation and diagnostics hardening (2026-09-18)" in changelog
    assert "## 2026-09-16 — Round 8 Windows build hardening" not in changelog
    round9 = changelog.index("- Round 9 audit (2026-09-16):")
    round8 = changelog.index("- Round 8 Windows build hardening (2026-09-16):")
    round7 = changelog.index("- Round 7 audit (2026-09-16):")
    release_471 = changelog.index("## 4.7.1")
    assert round9 < round8 < round7 < release_471
