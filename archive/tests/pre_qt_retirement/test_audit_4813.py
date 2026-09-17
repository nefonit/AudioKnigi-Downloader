from __future__ import annotations

from types import SimpleNamespace

from audioknigi.dnd import DragDropMixin, DND_FILES, DND_TEXT
from audioknigi.models import SearchResult
from audioknigi import AudioKnigiApp


class _DropTarget:
    def __init__(self):
        self.registered = []
        self.bindings = []
        self.text = None

    def drop_target_register(self, *types):
        self.registered.append(types)

    def dnd_bind(self, sequence, handler):
        self.bindings.append((sequence, handler))

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]


class _DnDHost(DragDropMixin):
    def __init__(self):
        self.dnd_available = True
        self.queue_drop_label = _DropTarget()
        self.queue_url_entry = _DropTarget()
        self.logged = []

    def _on_drop_queue(self, event):
        return "copy"

    def _on_drop_root(self, event):
        return "copy"

    def drop_target_register(self, *types):
        self.root_registered = types

    def dnd_bind(self, sequence, handler):
        self.root_binding = (sequence, handler)

    def log(self, text):
        self.logged.append(text)


def test_queue_drop_banner_is_registered_by_central_dnd_manager():
    host = _DnDHost()
    host._register_drag_and_drop_targets()

    assert host.queue_drop_label.registered
    assert host.queue_drop_label.bindings
    assert host.queue_drop_label.bindings[0][0] == "<<Drop>>"
    assert host.queue_drop_label.text == "Перетащи сюда одну или несколько ссылок — они добавятся в очередь"


def test_text_settings_are_debounced_for_autosave():
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        tab = app.settings_tab_view
        calls = []
        app._save_settings = lambda *args, **kwargs: calls.append(True)

        for var in (
            app.folder_template_var,
            app.track_template_var,
            app.abs_url_var,
            app.abs_api_key_var,
            app.abs_library_id_var,
        ):
            var.set(str(var.get()) + "x")
            assert tab._autosave_after_id is not None
            tab._flush_text_settings_save()

        assert len(calls) == 5
    finally:
        app.destroy()


def test_settings_helper_never_returns_none_for_live_app_vars():
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        tab = app.settings_tab_view
        assert tab._ensure_string_var("folder_template_var", "{Book_Title}") is app.folder_template_var
        assert tab._ensure_string_var("abs_url_var", "") is app.abs_url_var
        assert tab.speed_var._tk is app.tk
        # 4.12.20 removed the output-format selector together with M4B.
        # Current MP3-only settings variables must still belong to the app Tcl interpreter.
        assert app.quality_preset_var._tk is app.tk
    finally:
        app.destroy()


def test_search_result_action_is_safe_without_selection():
    app = AudioKnigiApp()
    app.settings["first_run_complete"] = True
    try:
        app.search_results = [SearchResult(title="Book", url="https://audioknigi.com.ua/audio-123-test")]
        app.search_tree.selection_remove(app.search_tree.selection())
        before = app.url_var.get()
        app.use_selected_search_result()
        assert app.url_var.get() == before
    finally:
        app.destroy()
