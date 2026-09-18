from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_search_service_reserves_100_percent_for_actual_worker_completion() -> None:
    source = (ROOT / "audioknigi/services/search_service.py").read_text(encoding="utf-8")
    assert 'report(99, "Завершаю поиск")' in source
    assert 'report(100, "Поиск завершён")' not in source


def test_search_finished_closes_modal_before_deferred_table_render() -> None:
    source = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    start = source.index("def _search_finished")
    end = source.index("def _clear_search_thread", start)
    block = source[start:end]
    assert 'self._finish_blocking_operation("search")' in block
    assert 'QTimer.singleShot(0, lambda outcome=outcome: self._apply_search_outcome(outcome))' in block
    assert block.index('self._finish_blocking_operation("search")') < block.index('QTimer.singleShot(0, lambda outcome=outcome: self._apply_search_outcome(outcome))')
    assert ".resizeColumnsToContents()" not in block
    assert "def _apply_search_outcome" in block
    assert "def _focus_search_result_after_render" in block


def test_search_completion_has_worker_and_ui_diagnostic_boundaries() -> None:
    workers = (ROOT / "audioknigi/qt/workers.py").read_text(encoding="utf-8")
    ui = (ROOT / "audioknigi/qt/mixins/search.py").read_text(encoding="utf-8")
    for marker in ("event=run_start", "event=service_return", "event=finished_emit", "event=finished_emit_return"):
        assert marker in workers
    for marker in ("event=finished_slot_enter", "event=modal_finished", "event=result_render_start", "event=model_reset_complete", "event=result_render_complete", "event=focus_complete"):
        assert marker in ui
