from __future__ import annotations

import ast
import json
from pathlib import Path

from audioknigi.download.errors import MissingSelectedTracksError
from audioknigi.metadata import APP_VERSION
from audioknigi.services.queue_service import task_from_dict
from tools.exception_audit import audit as exception_audit
from tools.historical_regression_audit import _normalize_nodeid
from tools.qt_localization_audit import _assignment_value
from tools.undefined_global_audit import _SPECIAL_GLOBALS

ROOT = Path(__file__).resolve().parents[2]


def test_release_version_and_entrypoint_do_not_hardcode_previous_patch():
    assert APP_VERSION == "4.12.42"
    source = (ROOT / "audioknigi_qt.py").read_text(encoding="utf-8")
    assert "4.12.34 runtime" not in source
    assert "The active runtime is Qt-only" in source
    assert "Historical compatibility note: Phase 39 is Qt-only" in source


def test_windows_acceptance_uses_metadata_and_reaps_killed_process():
    source = (ROOT / "tools" / "qt_windows_acceptance.py").read_text(encoding="utf-8")
    assert "from audioknigi.metadata import APP_VERSION" in source
    assert "from audioknigi.core import APP_VERSION" not in source
    kill_block = source[source.index("process.kill()") : source.index('block["app_exit_code"]')]
    assert "process.wait()" in kill_block


def test_historical_nodeid_normalization_is_windows_safe():
    raw = r".historical-regression-abcd\test_queue.py::test_case"
    assert _normalize_nodeid(raw, ".historical-regression-abcd") == "test_queue.py::test_case"


def test_localization_ast_helper_supports_annotated_assignments():
    node = ast.parse("TOPICS: dict[str, str] = {'a': 'b'}").body[0]
    value = _assignment_value(node, "TOPICS")
    assert value is not None
    assert ast.literal_eval(value) == {"a": "b"}


def test_undefined_global_gate_accepts_package_path_special():
    assert "__path__" in _SPECIAL_GLOBALS


def test_exception_allowlist_has_no_stale_entries_and_is_sorted():
    findings, unknown, stale = exception_audit(ROOT)
    assert findings
    assert unknown == []
    assert stale == []
    data = json.loads((ROOT / "tools" / "exception_allowlist.json").read_text(encoding="utf-8"))
    assert list(data) == sorted(data)
    assert not any("source_analysis.py:_remote_size" in key for key in data)
    assert not any("source_analysis.py:on_request" in key for key in data)


def test_legacy_queue_selected_indices_skip_invalid_values_without_losing_task(tmp_path):
    payload = {
        "url": "https://audioknigi.com.ua/audio-1",
        "title": "Legacy",
        "selected_indices": ["1", None, "all", "2", "bad", "2"],
        "output_dir": str(tmp_path),
    }
    task = task_from_dict(payload)
    assert task.request.selected_indices == [1, 2]


def test_legacy_queue_all_marker_means_whole_book(tmp_path):
    payload = {
        "url": "https://audioknigi.com.ua/audio-1",
        "title": "Legacy",
        "selected_indices": "all",
        "output_dir": str(tmp_path),
    }
    task = task_from_dict(payload)
    assert task.request.selected_indices is None


def test_missing_selected_tracks_error_reports_truncated_count():
    error = MissingSelectedTracksError(range(1, 16))
    message = str(error)
    assert "12" in message
    assert "(и ещё 3)" in message


def test_main_window_has_application_level_accessible_description():
    source = (ROOT / "audioknigi" / "qt" / "main_window.py").read_text(encoding="utf-8")
    assert 'description=tr(self.language, "main_window_description")' in source
    messages = json.loads((ROOT / "audioknigi" / "locales" / "messages.json").read_text(encoding="utf-8"))
    for language in ("ru", "uk", "de", "en"):
        assert messages[language].get("main_window_description")


def test_ukrainian_undo_and_appearance_are_not_collapsed_into_cancel_and_view():
    literals = json.loads((ROOT / "audioknigi" / "locales" / "legacy_literals.json").read_text(encoding="utf-8"))
    uk = literals["uk"]
    assert uk["Отмена"] != uk["Отменить"]
    assert uk["Вид"] != uk["Внешний вид"]


def test_split_module_style_regressions_are_cleaned():
    source_analysis = (ROOT / "audioknigi" / "download" / "source_analysis.py").read_text(encoding="utf-8")
    book_flow = (ROOT / "audioknigi" / "download" / "book_flow.py").read_text(encoding="utf-8")
    lifecycle = (ROOT / "audioknigi" / "qt" / "mixins" / "lifecycle.py").read_text(encoding="utf-8")
    clipboard = (ROOT / "audioknigi" / "qt" / "mixins" / "clipboard.py").read_text(encoding="utf-8")
    search = (ROOT / "audioknigi" / "qt" / "mixins" / "search.py").read_text(encoding="utf-8")
    assert "return unknown_narrator_choice\n\n    def _service" in source_analysis
    assert 'reason="disabled")\n\n        self._save_book_sidecars' in book_flow
    assert "try: self.tray_controller.shutdown()" not in lifecycle
    assert "; self.track_table.selectRow" not in clipboard
    assert "; table.selectRow" not in search
