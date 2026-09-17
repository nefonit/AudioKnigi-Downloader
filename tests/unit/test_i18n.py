import json
from pathlib import Path

from audioknigi.i18n import LANGUAGES, STRINGS, localize_runtime_text, message, tr, ui_text

ROOT = Path(__file__).resolve().parents[2]


def test_locale_catalogs_are_external_json_files():
    locale_dir = ROOT / "audioknigi" / "locales"
    for name in ("messages.json", "legacy_literals.json", "runtime_exact.json", "runtime_prefixes.json", "runtime_regex.json"):
        assert (locale_dir / name).is_file()


def test_stable_message_id_api_works_for_all_languages():
    for language in LANGUAGES:
        assert message(language, "download_book")
        assert tr(language, "download_book") == message(language, "download_book")


def test_legacy_literal_layer_remains_compatible():
    assert ui_text("en", "Нет обложки") == "No cover"
    assert ui_text("de", "Нет обложки") == "Kein Cover"


def test_runtime_localization_is_data_driven():
    assert localize_runtime_text("en", "Приложение готово.") == "Application ready."
    assert "Download" in localize_runtime_text("en", "Скачивание завершено: Book")


def test_message_catalog_languages_have_same_core_keys():
    ru = set(STRINGS["ru"])
    assert ru
    for language in ("uk", "de", "en"):
        assert ru <= set(STRINGS[language])
