from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from audioknigi.config.settings import AppSettings
from audioknigi.core import UI_SCALE_MIGRATION_KEY, extract_extended_metadata_from_html
from audioknigi.diagnostics import support_bundle
from audioknigi.i18n import localize_runtime_text, ui_text
from audioknigi.providers.audioknigi_search import _author_detail_score, _matches_query
from audioknigi.services.queue_service import _item_to_dict

ROOT = Path(__file__).resolve().parents[2]


def test_appsettings_direct_and_from_mapping_match_for_partial_current_mapping():
    direct = AppSettings({"theme": "dark"})
    factory = AppSettings.from_mapping({"theme": "dark"})
    assert direct["first_run_complete"] is False
    assert factory["first_run_complete"] is False
    assert direct.to_dict() == factory.to_dict()
    assert UI_SCALE_MIGRATION_KEY not in direct
    assert UI_SCALE_MIGRATION_KEY not in factory


def test_support_bundle_redacts_secret_key_and_preserves_text_after_drive_root(monkeypatch):
    monkeypatch.setattr(support_bundle.os, "name", "nt", raising=False)
    assert support_bundle.sanitized_settings({"secret_key": "abc"})["secret_key"] == "<redacted>"
    text = r"Check C:\ finished, starting download from https://site.com/file.mp3"
    sanitized = support_bundle._privacy_path(text, collapse_whole_path=False)
    assert sanitized == "Check <configured-path> finished, starting download from https://site.com/file.mp3"
    assert support_bundle._privacy_path(r"C:\Users\Name\Audiobooks\Author\Book") == "<configured-path>"


def test_queue_supports_plain_dataclass_without_bypassing_model_serializer_contract():
    @dataclass
    class Plain:
        one: int
        two: str

    assert _item_to_dict(Plain(1, "x")) == {"one": 1, "two": "x"}
    source = (ROOT / "audioknigi/services/queue_service.py").read_text(encoding="utf-8")
    assert "asdict(" not in source


def test_one_letter_book_title_queries_are_retained_and_author_detail_prefers_more_initials():
    assert _matches_query("Я, робот", "я робот", author="Айзек Азимов") is True
    assert _author_detail_score("А. С. Пушкин") > _author_detail_score("А. Пушкин")


def test_runtime_narration_terminology_is_consistent_in_english():
    assert ui_text("en", "Озвучка {index}", index=2) == "Narration 2"
    assert localize_runtime_text("en", "Озвучка 3") == "Narration 3"


def test_core_narrator_parser_stops_before_duration_and_quality_metadata():
    _description, narrator, _genre, _year = extract_extended_metadata_from_html(
        "Исполнитель: Илья Кривошеев, Время звучания: 12:45:00, Качество: 128 kbps"
    )
    assert narrator == "Илья Кривошеев"


def test_round61_static_contracts_cover_reported_runtime_regressions():
    source_analysis = (ROOT / "audioknigi/download/source_analysis.py").read_text(encoding="utf-8")
    book_analysis = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    book_flow = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    probe = (ROOT / "audioknigi/download/probe.py").read_text(encoding="utf-8")
    player = (ROOT / "audioknigi/qt/player_mixin.py").read_text(encoding="utf-8")
    analysis_ui = (ROOT / "audioknigi/qt/mixins/analysis_download.py").read_text(encoding="utf-8")

    assert "best_by_url" in source_analysis
    assert "best_by_url" in book_analysis
    assert book_flow.count("req.selected_indices = sorted(active_selected)") >= 3
    assert "for segment_path in _segment_files(part_target)" in probe
    assert "starts = [" in probe and "expected_end = max(starts)" in probe
    assert "save_app_settings(self.settings)" in player
    assert "known_paths = {Path(candidate).expanduser().resolve() for candidate in files}" in player
    assert 'self._pending_queue_urls = []' in analysis_ui
