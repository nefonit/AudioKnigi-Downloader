import tkinter as tk
from types import SimpleNamespace

from audioknigi.accessibility import AccessibilityManager
from audioknigi.search import _AudioLinkParser, _title_score
from audioknigi.ui.history_tab import HistoryTab


def test_search_tie_prefers_shorter_label_and_parser_preserves_inline_punctuation():
    query = "Мастер"
    assert _title_score("Мастер", query) > _title_score("Мастер длинная серия коллекция", query)

    parser = _AudioLinkParser()
    parser.feed('<a href="/audio-123-test">Слово<span>!</span></a>')
    assert parser.links
    _href, labels = parser.links[0]
    assert labels[0] == "Слово!"


class _AfterHost:
    def __init__(self):
        self.next_id = 0
        self.callbacks = {}
        self.cancelled = []

    def after(self, _delay, callback):
        self.next_id += 1
        key = f"after-{self.next_id}"
        self.callbacks[key] = callback
        return key

    def after_cancel(self, key):
        self.cancelled.append(key)
        self.callbacks.pop(key, None)

    def winfo_children(self):
        return []


def test_accessibility_close_cancels_pending_poll_callbacks(monkeypatch):
    # Avoid external screen-reader probing in this lifecycle-only unit test.
    monkeypatch.setattr("audioknigi.accessibility.ScreenReaderBridge._init_backend", lambda self: None)
    app = _AfterHost()
    manager = AccessibilityManager(app)
    manager.install()
    assert len(manager._after_ids) == 3
    scheduled = set(manager._after_ids)
    manager.close()
    assert manager._closed is True
    assert not manager._after_ids
    assert scheduled.issubset(set(app.cancelled))


def test_history_double_click_empty_area_does_not_reuse_old_selection():
    root = tk.Tk()
    root.geometry("900x500")
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True)
    calls = []
    app = SimpleNamespace(
        history_open_folder=lambda: calls.append("open"),
        history_redownload=lambda: None,
        create_backup=lambda: None,
        restore_backup=lambda: None,
        export_library=lambda _kind: None,
        history_delete=lambda: None,
        history_clear=lambda: None,
    )
    tab = HistoryTab(app, frame)
    app.history_tree.insert("", "end", iid="0", text="", values=("date", "Book", "Author", 1, "/tmp", "url"))
    app.history_tree.selection_set("0")
    root.update_idletasks()
    # Two real button clicks at the same empty location let Tk synthesize the
    # Double-1 binding without event_generate's forbidden Double modifier.
    y = max(120, app.history_tree.winfo_height() - 8)
    assert not app.history_tree.identify_row(y)
    for _ in range(2):
        app.history_tree.event_generate("<ButtonPress-1>", x=120, y=y)
        app.history_tree.event_generate("<ButtonRelease-1>", x=120, y=y)
        root.update()
    assert calls == []
    frame.destroy()
    root.update_idletasks()
    assert tab.tooltips == []
    root.destroy()
