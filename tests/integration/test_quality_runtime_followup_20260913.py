from __future__ import annotations

import json
from pathlib import Path
import threading

import pytest
import requests

from audioknigi.download.book_flow import BookFlowMixin
from audioknigi.download_engine import DownloadCallbacks, _DownloadEngine
from audioknigi.knigavuhe import _extract_call_argument
from audioknigi.models import Book, Track
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.queue_service import _parse_selected_indices_payload
from tools.exception_audit import scan as exception_scan
from tools.qt_localization_audit import _ui_text_literals
from tools.unused_import_audit import unused_imports

ROOT = Path(__file__).resolve().parents[2]


def test_exception_audit_distinguishes_duplicate_broad_handlers_and_bare_except(tmp_path):
    package = tmp_path / "audioknigi"
    package.mkdir()
    (package / "sample.py").write_text(
        """
def f():
    try: x = 1
    except Exception: pass
    try: x = 2
    except Exception: pass
    try: x = 3
    except BaseException: pass
    try: x = 4
    except: pass
""",
        encoding="utf-8",
    )
    keys = [item["key"] for item in exception_scan(tmp_path)]
    assert any(key.endswith(":Exception#1") for key in keys)
    assert any(key.endswith(":Exception#2") for key in keys)
    assert any(key.endswith(":BaseException#1") for key in keys)
    assert any(key.endswith(":bare#1") for key in keys)
    assert len(keys) == 4


def test_unused_import_audit_checks_conditional_and_except_imports_and_forward_annotations(tmp_path):
    path = tmp_path / "sample.py"
    path.write_text(
        """
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from package import SomeClass
try:
    import json
except ImportError:
    import simplejson as json

def f(value: 'SomeClass'):
    return json.dumps(value)
""",
        encoding="utf-8",
    )
    assert unused_imports(path) == []


def test_acceptance_status_can_explicitly_disable_windows_requirement(monkeypatch):
    import tools.qt_windows_acceptance as acceptance

    seen = {}
    monkeypatch.setattr(
        acceptance,
        "acceptance_complete",
        lambda report, **kwargs: seen.setdefault("require_windows", kwargs["require_windows"]) is False,
    )
    report = {"exe_sha256": "abc"}
    acceptance._refresh_status(report, require_windows=False)
    assert seen["require_windows"] is False
    assert report["status"] == "pass"


def test_localization_audit_reads_keyword_ui_text_literal(tmp_path):
    path = tmp_path / "sample.py"
    path.write_text('value = ui_text("uk", russian_text="Русский текст")\n', encoding="utf-8")
    assert _ui_text_literals(path) == {"Русский текст"}


def test_sidecar_duplicate_check_fails_closed_on_invalid_current_track_index(tmp_path):
    book = Book(
        url="https://audioknigi.com.ua/audio-1",
        title="Demo",
        tracks=[Track(index="bad", title="Part", file="https://cdn.invalid/1.mp3")],
    )
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    engine = _DownloadEngine(request, {}, threading.Event(), DownloadCallbacks())
    (tmp_path / "metadata.json").write_text(
        json.dumps(
            {
                "source_url": book.url,
                "title": "Demo",
                "author": "",
                "narrator": "",
                "tracks": [{"index": 1, "title": "Part"}],
            }
        ),
        encoding="utf-8",
    )
    assert engine._sidecar_metadata_matches_book(book, tmp_path) is False


def test_history_callback_failure_does_not_break_completed_download_bookkeeping(tmp_path, monkeypatch):
    import audioknigi.download_engine as engine_module

    book = Book(url="https://audioknigi.com.ua/audio-1", title="Demo", tracks=[])
    request = DownloadRequest(book=book, selected_indices=None, output_dir=tmp_path)
    callbacks = DownloadCallbacks(history_changed=lambda: (_ for _ in ()).throw(RuntimeError("ui failed")))
    engine = _DownloadEngine(request, {}, threading.Event(), callbacks)
    monkeypatch.setattr(engine_module, "HISTORY_FILE", tmp_path / "history.json")
    engine._add_history(book, tmp_path, 0)
    assert (tmp_path / "history.json").exists()


def test_knigavuhe_call_argument_supports_backtick_template_strings():
    source = 'BookController.enter(`title: "A,B" (demo)`, secondArg)'
    assert _extract_call_argument(source) == '`title: "A,B" (demo)`'


def test_expired_media_indices_can_be_inferred_from_http_response_url():
    book = Book(
        url="https://audioknigi.com.ua/audio-1",
        title="Demo",
        tracks=[
            Track(index=1, title="One", file="https://cdn.invalid/one.mp3"),
            Track(index=2, title="Two", file="https://cdn.invalid/two.mp3"),
        ],
    )
    response = requests.Response()
    response.status_code = 404
    response.url = "https://cdn.invalid/two.mp3"
    error = requests.HTTPError("404", response=response)
    assert BookFlowMixin._expired_media_track_indices(error, book, {1, 2}) == [2]


def test_queue_recovery_preserves_explicit_empty_selection():
    assert _parse_selected_indices_payload(None) is None
    assert _parse_selected_indices_payload([]) == []
    assert _parse_selected_indices_payload([None, "bad", ""]) == []


def test_runtime_stage_and_accessibility_contract_are_current():
    qt_init = (ROOT / "audioknigi" / "qt" / "__init__.py").read_text(encoding="utf-8")
    access = (ROOT / "audioknigi" / "qt" / "accessibility_audit.py").read_text(encoding="utf-8")
    pages = (ROOT / "audioknigi" / "qt" / "main_window_pages.py").read_text(encoding="utf-8")
    assert 'QT_RUNTIME_STAGE = "qt-only-4.12.42"' in qt_init
    assert '"easy_book_cover"' in access
    assert 'description=self._l("Секретное поле")' in pages


def test_ukrainian_catalog_has_search_period_variant_and_secret_field_translation():
    literals = json.loads((ROOT / "audioknigi" / "locales" / "legacy_literals.json").read_text(encoding="utf-8"))
    assert literals["uk"]["Введите минимум 3 символа для поиска."] == "Введіть мінімум 3 символи для пошуку."
    for lang in ("uk", "de", "en"):
        assert literals[lang]["Секретное поле"]


def test_media_probe_defensively_validates_stream_list_shape():
    source = (ROOT / "audioknigi" / "download" / "media.py").read_text(encoding="utf-8")
    assert "isinstance(streams, list)" in source
    assert "isinstance(streams[0], dict)" in source


def test_source_hosts_are_reused_by_provider_modules():
    knigavuhe = (ROOT / "audioknigi" / "knigavuhe.py").read_text(encoding="utf-8")
    poleknig = (ROOT / "audioknigi" / "poleknig.py").read_text(encoding="utf-8")
    adapters = (ROOT / "audioknigi" / "providers" / "adapters.py").read_text(encoding="utf-8")
    assert "KNIGAVUHE_HOST" in knigavuhe
    assert "POLEKNIG_HOST" in poleknig
    assert "AUDIOKNIGI_HOST" in adapters


def test_qt_import_audit_no_longer_keeps_identity_alias_table():
    source = (ROOT / "tools" / "qt_import_audit.py").read_text(encoding="utf-8")
    assert 'aliases = {"pyside6": "pyside6", "pillow": "pillow"}' not in source
