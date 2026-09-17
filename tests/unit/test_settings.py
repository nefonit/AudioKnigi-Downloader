from pathlib import Path

from audioknigi.config import CURRENT_SETTINGS_VERSION, AppSettings, migrate_settings, normalize_settings


def test_settings_schema_adds_defaults_and_version():
    data = normalize_settings({})
    assert data["settings_version"] == CURRENT_SETTINGS_VERSION
    assert data["folder_template"] == "{Book_Title}"
    assert data["track_template"] == "{Track_Number}.mp3"
    assert data["embed_tags"] is True


def test_legacy_auto_chunk_key_migrates_without_unit_change():
    data, changed = migrate_settings({"auto_chunk_min_kbps": 512})
    assert changed is True
    assert data["auto_chunk_min_kbytes_per_sec"] == 512
    assert "auto_chunk_min_kbps" not in data


def test_unknown_settings_are_preserved():
    data = normalize_settings({"plugin_future_value": 42})
    assert data["plugin_future_value"] == 42


def test_settings_ranges_are_normalized():
    data = normalize_settings({"scale": 999, "event_sound_volume": -4, "player_rate": 9})
    assert data["scale"] == 200
    assert data["event_sound_volume"] == 0
    assert data["player_rate"] == 3.0


def test_app_settings_is_mutable_mapping_and_roundtrips():
    settings = AppSettings.from_mapping({"language": "de"})
    settings["language"] = "en"
    assert settings.get("language") == "en"
    assert settings.to_dict()["settings_version"] == CURRENT_SETTINGS_VERSION
