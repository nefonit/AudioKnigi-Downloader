from types import SimpleNamespace

from audioknigi.actions import ActionsMixin


def test_removed_container_preview_is_not_exposed():
    assert not hasattr(ActionsMixin, "show_m4b_preview")


def test_set_busy_does_not_require_queue_running_attribute():
    import inspect
    source = inspect.getsource(ActionsMixin.set_busy)
    assert 'getattr(self, "queue_running", False)' in source


def test_context_worker_delegates_without_output_mode_switching():
    calls = []
    host = SimpleNamespace(runtime_output_mode="mp3")
    host._main_download_worker = lambda book, selected: calls.append((book, selected, host.runtime_output_mode))
    ActionsMixin._context_part_download_worker(host, "book", [1])
    assert calls == [("book", [1], "mp3")]
    assert host.runtime_output_mode == "mp3"


def test_context_worker_does_not_swallow_download_error():
    import pytest
    host = SimpleNamespace(runtime_output_mode="mp3")

    def fail(_book, _selected):
        raise RuntimeError("boom")

    host._main_download_worker = fail
    with pytest.raises(RuntimeError, match="boom"):
        ActionsMixin._context_part_download_worker(host, object(), [1])


def test_option_menu_uses_selective_unbind_helper():
    import inspect
    from audioknigi.ui_kit import CTkOptionMenu, _unbind_one
    assert callable(_unbind_one)
    source = inspect.getsource(CTkOptionMenu._set_ctk_command)
    assert '_unbind_one(self, "<<ComboboxSelected>>", old_id)' in source
