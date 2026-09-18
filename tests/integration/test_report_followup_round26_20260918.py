from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_easy_progress_window_uses_manual_ui_blocking_not_native_modality() -> None:
    dialog = (ROOT / "audioknigi/qt/operation_dialog.py").read_text(encoding="utf-8")
    main = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    assert "Qt.WindowModality.NonModal" in dialog
    assert "self.setModal(False)" in dialog
    assert "Qt.WindowModality.ApplicationModal" not in dialog
    assert "self.setModal(True)" not in dialog
    assert "central.setEnabled(not blocked)" in main
    assert "menu.setEnabled(not blocked)" in main


def test_operation_finish_hides_dialog_without_accept_or_done() -> None:
    dialog = (ROOT / "audioknigi/qt/operation_dialog.py").read_text(encoding="utf-8")
    start = dialog.index("def finish")
    end = dialog.index("def reject", start)
    block = dialog[start:end]
    assert "self.hide()" in block
    assert "self.accept()" not in block
    assert "self.done(" not in block


def test_search_completion_tears_down_progress_window_before_final_progress_update() -> None:
    source = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    start = source.index("def _search_finished")
    end = source.index("def _apply_search_outcome", start)
    block = source[start:end]
    assert block.index('self._finish_blocking_operation("search")') < block.index('self._set_search_progress(100, "Поиск завершён", visible=True)')
    assert "event=before_operation_finish" in block
    assert "event=after_operation_finish" in block


def test_operation_finish_has_begin_end_diagnostics_and_reenables_ui() -> None:
    source = (ROOT / "audioknigi/qt/main_window.py").read_text(encoding="utf-8")
    start = source.index("def _finish_blocking_operation")
    end = source.index("def _l", start)
    block = source[start:end]
    assert "event=finish_begin" in block
    assert "event=finish_end" in block
    assert "self._set_operation_ui_blocked(False)" in block
