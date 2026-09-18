from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def lifecycle_source() -> str:
    return (ROOT / "audioknigi/qt/mixins/lifecycle.py").read_text(encoding="utf-8")


def test_exit_action_does_not_prearm_or_cancel_active_work_before_close_event_confirmation() -> None:
    source = lifecycle_source()
    start = source.index("def request_exit")
    end = source.index("def _notify_tray_if_hidden", start)
    body = source[start:end]

    assert "self.close()" in body
    assert "self._exit_requested = True" not in body
    assert "self._cancel_all_workers_for_exit()" not in body
    assert "UI LIFECYCLE | event=request_exit" in body


def test_deferred_exit_timeout_never_hard_kills_process() -> None:
    source = lifecycle_source()
    start = source.index("def closeEvent")
    end = source.index("__all__", start)
    body = source[start:end]

    assert "os._exit" not in source
    assert "event=deferred_exit_timeout" in body
    assert "action=abort_close" in body
    assert "self._exit_requested = False" in body
    assert "event.ignore()" in body
    assert "Закрытие отменено" in body


def test_confirmed_active_operation_still_uses_bounded_deferred_exit() -> None:
    source = lifecycle_source()
    assert "_EXIT_GRACE_SECONDS = 5.0" in source
    assert "self._begin_deferred_exit()" in source
    assert "self._cancel_all_workers_for_exit()" in source
    assert "QTimer.singleShot(_EXIT_POLL_MS, self._poll_deferred_exit)" in source
