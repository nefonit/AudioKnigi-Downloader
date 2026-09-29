from __future__ import annotations

import json
import threading
from pathlib import Path

from audioknigi.config.settings import AppSettings, normalize_settings
from audioknigi.diagnostics import support_bundle
from audioknigi.models import SearchResult
from audioknigi.providers import audioknigi_search


def test_appsettings_setitem_normalizes_runtime_values():
    settings = AppSettings()
    settings["scale"] = "150"
    settings["large_mode"] = "yes"
    settings["player_rate"] = "9"

    assert settings["scale"] == 150
    assert settings["large_mode"] is True
    assert settings["player_rate"] == 3.0


def test_blank_folder_template_is_intentionally_normalized_to_default():
    # An empty folder template is not an operational "save directly in output"
    # mode: render_folder and the Qt settings UI both fall back to Book_Title.
    assert normalize_settings({"folder_template": ""})["folder_template"] == "{Book_Title}"


def test_support_bundle_collapses_absolute_home_path_after_username_masking():
    private_path = Path.home() / "AudioBooks" / "Author" / "Book"
    assert support_bundle._privacy_path(str(private_path)) == "<configured-path>"


def test_support_bundle_can_keep_relative_home_structure_only_for_embedded_log_text():
    private_path = Path.home() / "AudioBooks" / "Author" / "Book"
    text = f"Output path: {private_path}"
    sanitized = support_bundle._privacy_path(text, collapse_whole_path=False)
    assert str(Path.home()) not in sanitized
    assert "AudioBooks" not in sanitized


def test_audioknigi_detail_hydration_is_bounded(monkeypatch):
    items = [
        SearchResult(title=f"Book {index}", url=f"https://audioknigi.com.ua/audio-{index}", source="audioknigi.com.ua")
        for index in range(50)
    ]
    seen = []
    lock = threading.Lock()

    def fake_metadata(item, cancel_event=None):
        with lock:
            seen.append(item.url)
        return item

    monkeypatch.setattr(audioknigi_search, "_audioknigi_page_metadata", fake_metadata)
    result = audioknigi_search._group_audioknigi_recordings(items)

    assert len(result) == 50
    assert len(seen) == audioknigi_search._MAX_HYDRATED_SEARCH_RESULTS == 30
    assert set(seen) == {item.url for item in items[:30]}


def test_runtime_exact_json_has_no_duplicate_keys_at_any_object_level():
    path = Path(__file__).resolve().parents[2] / "audioknigi/locales/runtime_exact.json"
    payload = path.read_text(encoding="utf-8")

    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, f"duplicate JSON key: {key!r}"
            result[key] = value
        return result

    json.loads(payload, object_pairs_hook=no_duplicates)


def test_round63_removes_unreachable_unlink_return_and_keeps_runtime_regex_precedence():
    root = Path(__file__).resolve().parents[2]
    common = (root / "audioknigi/download/common.py").read_text(encoding="utf-8")
    i18n = (root / "audioknigi/i18n.py").read_text(encoding="utf-8")

    unlink_block = common[common.index("def unlink_with_retry"):common.index("def atomic_write_text")]
    assert "return False" not in unlink_block
    assert i18n.index("for pattern, variants in _PHASE29_RUNTIME_REGEX") < i18n.index(
        "for prefix, variants in _PHASE29_RUNTIME_PREFIXES.items()"
    )
