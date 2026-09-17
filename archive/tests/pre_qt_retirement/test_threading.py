import inspect

from audioknigi.actions import ActionsMixin
from audioknigi.search import SearchMixin
from audioknigi.queue_manager import QueueMixin
from audioknigi.event_bus import UIEventBus

# User-triggered network workflows must schedule workers instead of performing HTTP
# synchronously inside the Tk/CustomTkinter callback.
analysis_src = inspect.getsource(ActionsMixin._begin_analysis)
abs_src = inspect.getsource(ActionsMixin.test_audiobookshelf)
search_src = inspect.getsource(SearchMixin.search_books)
queue_src = inspect.getsource(QueueMixin.start_queue)

for name, source in {
    "analysis": analysis_src,
    "Audiobookshelf test": abs_src,
    "search": search_src,
    "queue": queue_src,
}.items():
    assert ("threading.Thread" in source or "_spawn_worker" in source), f"{name} no longer starts a worker thread"

# UI updates from workers are routed through the event bus.
ui_src = inspect.getsource(ActionsMixin.ui)
assert "event_bus.post" in ui_src
assert hasattr(UIEventBus, "post")

print("GUI THREADING TEST: OK")
