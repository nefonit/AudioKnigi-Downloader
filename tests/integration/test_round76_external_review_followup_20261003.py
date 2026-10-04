from __future__ import annotations

from pathlib import Path

from audioknigi.config.settings import AppSettings
from audioknigi.models import NarrationVariant, Track
from audioknigi.services.queue_service import _track_from_dict, _variant_from_dict

ROOT = Path(__file__).resolve().parents[2]


def test_appsettings_legacy_write_aliases_update_only_canonical_keys():
    settings = AppSettings({"theme": "dark", "normalization_mode": "two_pass"})
    del settings["theme"]

    settings["normalize_audio"] = True
    assert settings["normalization_mode"] == "single"
    assert "normalize_audio" not in settings
    assert "theme" not in settings

    settings["normalize_audio"] = False
    assert settings["normalization_mode"] == "off"
    assert "normalize_audio" not in settings

    settings["auto_chunk_min_kbps"] = 512
    assert settings["auto_chunk_min_kbytes_per_sec"] == 512
    assert "auto_chunk_min_kbps" not in settings
    assert "theme" not in settings


def test_queue_track_and_variant_deserializers_use_public_dataclass_fields_api():
    source = (ROOT / "audioknigi/services/queue_service.py").read_text(encoding="utf-8")
    track_block = source[source.index("def _track_from_dict"):source.index("def _variant_from_dict")]
    variant_block = source[source.index("def _variant_from_dict"):source.index("def _item_to_dict")]

    assert "fields(Track)" in track_block
    assert "Track.__dataclass_fields__" not in track_block
    assert "fields(NarrationVariant)" in variant_block
    assert "NarrationVariant.__dataclass_fields__" not in variant_block

    track = _track_from_dict({"index": "7", "title": "Seven", "file": "x", "unknown": 1})
    assert isinstance(track, Track)
    assert track.index == 7
    assert track.title == "Seven"

    variant = _variant_from_dict({"url": "https://example.invalid/v", "unknown": 1})
    assert isinstance(variant, NarrationVariant)
    assert variant.url == "https://example.invalid/v"


def test_config_settings_imports_match_real_package_layout():
    assert (ROOT / "audioknigi/config/settings.py").is_file()

    request_source = (ROOT / "audioknigi/services/download_request.py").read_text(encoding="utf-8")
    engine_source = (ROOT / "audioknigi/download_engine.py").read_text(encoding="utf-8")
    assert "from ..config.settings import normalize_settings" in request_source
    assert "from .config.settings import normalize_settings" in engine_source


def test_support_bundle_keeps_privacy_first_posix_redaction_contract():
    source = (ROOT / "audioknigi/diagnostics/support_bundle.py").read_text(encoding="utf-8")
    assert "Directory-like paths deliberately favor over-redaction" in source
    assert "_EMBEDDED_POSIX_PATH_RE" in source
