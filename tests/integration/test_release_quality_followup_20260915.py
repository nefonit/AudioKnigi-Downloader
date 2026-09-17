from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from audioknigi.core import extract_metadata_from_html
from audioknigi.logging_utils import sanitize_log_text
from audioknigi.models import Book, SearchResult, Track
from audioknigi.services.download_request import DownloadRequest
from audioknigi.services.library_service import export_history
from audioknigi.services.queue_service import QueueStore, task_from_dict, task_to_dict

ROOT = Path(__file__).resolve().parents[2]


def _load_tool(name: str):
    path = ROOT / "tools" / name
    spec = importlib.util.spec_from_file_location(f"test_tool_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_accessibility_selftest_prints_report_and_runtime_selftest_has_no_asserts():
    source = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")
    assert 'audit_text = result.report().rstrip("\\n") + "\\n"' in source
    assert 'print(report, file=sys.stderr' in source
    assert 'assert SearchOutcome("abc")' not in source
    assert 'required_objects = {' in source
    assert 'Historical compatibility note: Phase 39 is Qt-only' in source
    assert 'Tk retirement happened in the earlier Phase 13' in source


def test_frozen_extension_normalizer_preserves_package_path():
    tool = _load_tool("qt_frozen_module_audit.py")
    assert tool._normalise_entry_name("pygame/_camera.cp314-win_amd64.pyd", "EXTENSION") == "pygame/_camera"
    assert tool._matches_root("pygame/_camera", "pygame")
    toc = [("pygame/_camera.cp314-win_amd64.pyd", "x", "EXTENSION")]
    leaks = tool.find_forbidden_modules(toc)
    assert leaks and leaks[0][0].startswith("pygame/")


def test_undefined_global_audit_knows_standard_module_globals():
    tool = _load_tool("undefined_global_audit.py")
    assert {"__doc__", "__annotations__", "__path__", "WindowsError"} <= tool._SPECIAL_GLOBALS


def test_localization_audit_recognizes_direct_and_qualified_calls(tmp_path: Path):
    tool = _load_tool("qt_localization_audit.py")
    sample = tmp_path / "sample.py"
    sample.write_text(
        'from x import _l\nimport y as i18n\n_l("Русский текст")\ni18n.ui_text("uk", "Другой текст")\n',
        encoding="utf-8",
    )
    assert "Русский текст" in tool._literal_l_calls(sample)
    assert "Другой текст" in tool._ui_text_literals(sample)


def test_logging_sanitizer_does_not_hide_harmless_token_words():
    text = sanitize_log_text("folder_tokens: 5 tokenize_words=1 oauth_token=secret active_session_cookie=abc")
    assert "folder_tokens: 5" in text
    assert "tokenize_words=1" in text
    assert "oauth_token=<hidden>" in text
    assert "active_session_cookie=<hidden>" in text
    assert "secret" not in text


def test_metadata_title_falls_back_to_og_title_then_html_title():
    title, author, cover = extract_metadata_from_html(
        '<meta property="og:title" content="OG Book"><meta property="og:image" content="cover.jpg">',
        fallback_title="fallback",
    )
    assert title == "OG Book"
    title2, _, _ = extract_metadata_from_html("<title>  HTML   Book </title>", fallback_title="")
    assert title2 == "HTML Book"


def test_history_export_does_not_silently_truncate_to_500(tmp_path: Path):
    rows = [{"title": f"Book {index}", "date": str(index)} for index in range(650)]
    target = export_history(rows, tmp_path / "history.json", "json")
    exported = json.loads(target.read_text(encoding="utf-8"))
    assert len(exported) == 650


def test_support_bundle_masks_only_private_configured_url():
    from audioknigi.diagnostics.support_bundle import sanitized_settings

    result = sanitized_settings({"abs_url": "http://private.local", "update_url": "https://public.example/release"})
    assert result["abs_url"] == "<configured-url>"
    assert result["update_url"] == "https://public.example/release"


def test_search_dedup_source_uses_dataclass_replace_not_in_place_mutation():
    source = (ROOT / "audioknigi/services/search_service.py").read_text(encoding="utf-8")
    assert "replace(result, url=canonical)" in source
    assert "result.url = canonical" not in source


def test_text_sidecars_use_atomic_writer():
    source = (ROOT / "audioknigi/download/media.py").read_text(encoding="utf-8")
    assert 'atomic_write_text(folder / "book_info.txt"' in source
    assert 'atomic_write_text(folder / "book.nfo"' in source
    assert 'atomic_write_text(folder / "desc.txt"' in source
    assert 'atomic_write_text(folder / "reader.txt"' in source


def _request() -> DownloadRequest:
    book = Book(
        url="https://knigavuhe.org/book/1",
        title="Book",
        tracks=[Track(index=1, title="One", file="https://cdn.example/1.mp3")],
    )
    return DownloadRequest(book=book, selected_indices=None, output_dir=Path("."))


def test_queue_persists_full_mp3_download_mode():
    task = QueueStore.new_task(_request(), download_mode="full_mp3")
    payload = task_to_dict(task)
    assert payload["download_mode"] == "full_mp3"
    restored = task_from_dict(payload)
    assert restored.download_mode == "full_mp3"


def test_queue_ui_launches_stored_mode_and_exposes_action():
    queue_source = (ROOT / "audioknigi/qt/mixins/queue.py").read_text(encoding="utf-8")
    page_source = (ROOT / "audioknigi/qt/main_window_pages.py").read_text(encoding="utf-8")
    assert "mode=task.download_mode" in queue_source
    assert "def add_current_full_mp3_to_queue" in queue_source
    assert 'self._l("Добавить одним MP3 в очередь")' in page_source


def test_search_model_is_initialized_before_ui_build():
    source = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    init_pos = source.index("self.search_model = SearchResultsModel(self)")
    build_pos = source.index("self._build_ui()")
    assert init_pos < build_pos


def test_search_keeps_query_widget_enabled_and_restores_focus_on_empty_result():
    source = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    assert "self.search_edit.setReadOnly(True)" in source
    assert "self.search_edit.setEnabled(False)" not in source
    empty_branch = source[source.index('self.set_status("Ничего не найдено.")'):]
    assert "self.search_edit.setFocus" in empty_branch[:400]


def test_provider_analysis_prefetches_cover_for_knigavuhe_and_poleknig():
    source = (ROOT / "audioknigi/services/book_analysis_service.py").read_text(encoding="utf-8")
    assert source.count("normalize_cover_cache(self._fetch_cover_bytes(book.cover_url, book.url))") >= 2


def test_historical_gate_uses_line_anchored_pytest_error_detection():
    source = (ROOT / "tools/historical_regression_audit.py").read_text(encoding="utf-8")
    assert 're.search(r"^ERROR\\s+", combined, re.MULTILINE)' in source
