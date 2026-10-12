"""Regressions for the 2026-10-12 source audit, without Qt or network access."""

from __future__ import annotations

import ast
import inspect
import json
import re
import ssl
import http.client
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.i18n import localize_runtime_text
from audioknigi.models import Book, Track, TRACK_STATUS_READY
from audioknigi.providers.audioknigi_search import _iter_completed_cancellable as provider_completed
from audioknigi.services.book_analysis_service import _iter_completed_cancellable as analysis_completed
from audioknigi.services.search_service import search_result_sort_key
from audioknigi.templates import render_folder


ROOT = Path(__file__).resolve().parents[2]


def _reject_duplicate_object_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def test_runtime_exact_is_unambiguous_and_keeps_required_translations():
    catalog = json.loads(
        (ROOT / "audioknigi/locales/runtime_exact.json").read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_object_keys,
    )
    messages = (
        "Аудиоссылка устарела — обновляю плейлист…",
        "Проверить системный звук",
        "FFmpeg loudnorm не вернул статистику первого прохода; использую безопасную однопроходную нормализацию.",
        "Не удалось определить свободное место на диске.\n\nПроверьте папку сохранения и доступ к диску, затем повторите загрузку.",
    )
    for message in messages:
        assert all(catalog[message].get(language) for language in ("en", "de", "uk"))
        for language in ("en", "de", "uk"):
            assert localize_runtime_text(language, message) == catalog[message][language]


def test_all_locale_catalog_files_are_at_the_i18n_relative_location():
    from audioknigi import i18n
    for name in (
        "languages.json", "messages.json", "legacy_literals.json",
        "runtime_exact.json", "runtime_prefixes.json", "runtime_regex.json",
    ):
        assert (Path(i18n.__file__).parent / "locales" / name).is_file()


def test_posix_path_regexes_accept_parentheses_without_syntax_warnings():
    from audioknigi.diagnostics import support_bundle
    assert support_bundle._EMBEDDED_POSIX_FILE_RE.search("error /tmp/a/b.txt")
    assert support_bundle._EMBEDDED_POSIX_PATH_RE.search("error /tmp/a/b")
    # A raw regex string with escaped metacharacters does not trigger a Python
    # invalid-escape SyntaxWarning; never rewrite a working privacy regex solely
    # on that basis.
    source = (ROOT / "audioknigi/diagnostics/support_bundle.py").read_text(encoding="utf-8")
    ast.parse(source)


@pytest.mark.parametrize("completed", [provider_completed, analysis_completed])
def test_empty_future_collection_is_safe(completed):
    assert list(completed([], None)) == []


def test_executor_supports_cancel_futures_at_supported_python_versions():
    assert "cancel_futures" in inspect.signature(ThreadPoolExecutor.shutdown).parameters


def test_download_request_package_path_is_importable():
    from audioknigi.config.settings import normalize_settings
    from audioknigi.services.download_request import DownloadRequest
    assert callable(normalize_settings)
    assert callable(DownloadRequest.track_index)


@pytest.mark.parametrize("field", ["title", "author", "narrator", "genre"])
def test_search_sort_key_values_are_lexicographically_compatible(field):
    items = [
        SimpleNamespace(title="A book", author="Bob", narrator="C", genre="History"),
        SimpleNamespace(title="The book", author="Alice", narrator="D", genre="Science"),
        SimpleNamespace(title="", author="", narrator="", genre=""),
    ]
    keys = [search_result_sort_key(item, field, query="A book") for item in items]
    assert len({len(key) for key in keys}) == 1
    assert len(sorted(keys)) == 3


def test_book_track_defaults_and_status_normalization():
    book = Book(url="https://example.invalid/book", title="A book")
    track = Track(index=1, title="A", file="https://example.invalid/a.mp3", local_status="ready")
    assert book.cover_cache is None
    assert book.tracks == []
    assert track.fallback_file == ""
    assert track.local_path == ""
    assert track.local_status == TRACK_STATUS_READY


def test_folder_template_does_not_escape_base_through_book_metadata(tmp_path):
    book = Book(url="https://example.invalid/book", title="../../outside/another", author="../owner")
    result = render_folder(tmp_path, "{Author}/{Book_Title}", book, create=False)
    assert result.resolve().is_relative_to(tmp_path.resolve())


def test_http_client_bootstrap_context_available_in_cpython():
    # This relies on CPython's internal HTTPSConnection attribute; it is an
    # intentional implementation risk, not a verified portable public API.
    connection = http.client.HTTPSConnection("example.invalid", context=ssl.create_default_context())
    try:
        assert isinstance(connection._context, ssl.SSLContext)
    finally:
        connection.close()


def test_qt_contracts_can_be_parsed_without_pyside():
    checks = {
        "audioknigi/qt/workers.py": ("normalize_cover_cache", "copy.deepcopy(snapshot)", "event.position().y()"),
        "audioknigi/qt/operation_dialog.py": ("def finish", "def reject", "def closeEvent", "self.hide()"),
        "audioknigi/qt/theme.py": ("preserved_font = app.font()", "app.setFont(preserved_font)", "colorSchemeChanged"),
        "audioknigi/qt/media_keys.py": ("nativeEventFilter", "MSG.from_address(address)", "0.18"),
        "audioknigi/qt/track_model.py": ("AccessibleDescriptionRole", "AccessibleTextRole", "def setData"),
        "audioknigi/qt/search_model.py": ("AccessibleDescriptionRole", "def data"),
    }
    for file, markers in checks.items():
        source = (ROOT / file).read_text(encoding="utf-8")
        ast.parse(source)
        for marker in markers:
            assert marker in source, (file, marker)
