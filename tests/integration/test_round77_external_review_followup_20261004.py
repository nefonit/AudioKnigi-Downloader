from __future__ import annotations

import json
from pathlib import Path

from audioknigi import cover_fetch
from audioknigi.core import display_track_timeline
from audioknigi.providers.audioknigi_search import _matches_query
from audioknigi.services.queue_service import _book_from_dict
from audioknigi.templates import _safe_track_index

ROOT = Path(__file__).resolve().parents[2]


def test_book_flow_remaining_track_index_paths_are_safe():
    source = (ROOT / "audioknigi/download/book_flow.py").read_text(encoding="utf-8")
    assert "affected_tracks = [int(tr.index)" not in source
    assert "track_indices=[int(tr.index)]" not in source
    assert 'safe_int(getattr(tr, "index", None), -1)' in source


def test_single_letter_search_tokens_use_boundaries_and_initials():
    assert _matches_query("А Б В", "А Б В") is True
    assert _matches_query("Азбука", "А Б В") is False
    assert _matches_query("Книга", "А Б В", author="Александр Борис Викторов") is False
    assert _matches_query("Книга", "Л.", author="Лев Толстой") is False


def test_queue_book_deserializer_uses_public_dataclass_fields_api():
    source = (ROOT / "audioknigi/services/queue_service.py").read_text(encoding="utf-8")
    block = source[source.index("def _book_from_dict"):source.index("def task_to_dict")]
    assert "fields(Book)" in block
    assert "Book.__dataclass_fields__" not in block
    book = _book_from_dict({"url": "https://example.invalid/book", "title": "Demo", "unknown": 1})
    assert book.title == "Demo"


def test_integrations_json_decode_error_uses_old_requests_safe_fallback():
    source = (ROOT / "audioknigi/integrations.py").read_text(encoding="utf-8")
    assert '_JSONDecodeError = getattr(requests.exceptions, "JSONDecodeError", ValueError)' in source
    assert "except (ValueError, _JSONDecodeError) as exc:" in source


def test_template_track_index_rejects_bool_field_values():
    assert _safe_track_index({"index": True}) == 0
    assert _safe_track_index({"index": False}) == 0
    assert _safe_track_index({"index": "7"}) == 7


def test_display_track_timeline_accepts_mapping_tracks():
    rows = display_track_timeline([
        {"start": 10, "end": 20, "duration": None},
        {"duration": 5},
    ])
    assert rows[0] == (10.0, 20.0, 10.0)
    assert rows[1] == (20.0, 25.0, 5.0)


def test_cover_fetch_rejects_explicit_non_image_content_type(monkeypatch):
    class Response:
        headers = {"content-type": "text/html; charset=utf-8"}
        def raise_for_status(self):
            return None
        def iter_content(self, chunk_size=0):
            return iter([b"<html>challenge</html>"])
        def close(self):
            return None

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr(cover_fetch, "get_http_session", Session)
    assert cover_fetch.fetch_cover_bytes("https://example.invalid/cover.jpg") is None


def test_qtextedit_gets_localized_context_menu_installation():
    source = (ROOT / "audioknigi/qt/mixins/accessibility_ui.py").read_text(encoding="utf-8")
    assert "QTextEdit" in source
    assert "for widget_type in (QLineEdit, QPlainTextEdit, QTextEdit):" in source


def test_locale_catalog_has_no_reported_duplicate_or_prefix_regex_conflict():
    exact_path = ROOT / "audioknigi/locales/runtime_exact.json"
    raw = exact_path.read_text(encoding="utf-8")
    assert raw.count('"Проверить системный звук"') == 1

    prefixes = json.loads((ROOT / "audioknigi/locales/runtime_prefixes.json").read_text(encoding="utf-8"))
    regex_rows = json.loads((ROOT / "audioknigi/locales/runtime_regex.json").read_text(encoding="utf-8"))
    prefix = "Скачивание завершено. Пропущены недоступные части: "
    assert prefix in prefixes
    assert any("Пропущены недоступные части" in row[0] for row in regex_rows)

    i18n_source = (ROOT / "audioknigi/i18n.py").read_text(encoding="utf-8")
    assert i18n_source.index("for pattern, variants in _PHASE29_RUNTIME_REGEX") < i18n_source.index(
        "for prefix, variants in _PHASE29_RUNTIME_PREFIXES.items()"
    )


def test_reviewed_locale_wording_is_consistent():
    legacy = json.loads((ROOT / "audioknigi/locales/legacy_literals.json").read_text(encoding="utf-8"))
    assert legacy["en"]["Выделить всё"] == "Select all"
    assert all("озвучк" not in value.casefold() for value in legacy["uk"].values())
    exact = json.loads((ROOT / "audioknigi/locales/runtime_exact.json").read_text(encoding="utf-8"))
    assert exact["Аннотация выбранной книги"]["de"] == "Beschreibung des ausgewählten Buchs"


def test_support_bundle_file_redaction_preserves_diagnostic_tail():
    from audioknigi.diagnostics.support_bundle import _privacy_path

    value = r"C:\App\test.mp3 finished with error code 500"
    cleaned = _privacy_path(value, collapse_whole_path=False)
    assert cleaned == "<configured-path> finished with error code 500"
