from __future__ import annotations

from types import SimpleNamespace

from audioknigi.help_center import HelpCenter
from audioknigi.poleknig import _extract_js_property, parse_search_results
from audioknigi.queue_manager import QueueMixin


class _Var:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = value


class _Text:
    def __init__(self):
        self.value = ""

    def configure(self, **_kwargs):
        pass

    def delete(self, *_args):
        self.value = ""

    def insert(self, _where, value):
        self.value += value


def test_help_center_uses_stable_topic_key_when_titles_collide():
    help_center = HelpCenter.__new__(HelpCenter)
    help_center.topics = [
        ("help_a", "Одинаковый заголовок", "Тело A"),
        ("help_b", "Одинаковый заголовок", "Тело B"),
    ]
    help_center.topic_title_var = _Var()
    help_center.text = _Text()

    help_center.show("help_b")

    assert help_center.topic_title_var.value == "Одинаковый заголовок"
    assert help_center.text.value == "Тело B"


def test_poleknig_search_ignores_service_action_labels():
    html = '''
      <a href="/books/1">Слушать онлайн</a>
      <a href="/books/1"><img alt="Автор - Очень длинное настоящее название книги"></a>
      <a href="/books/2">Скачать</a>
      <a href="/books/2" title="Вторая настоящая книга">Подробнее о книге</a>
    '''

    rows = parse_search_results(html)

    assert [(row.title, row.url) for row in rows] == [
        ("Очень длинное настоящее название книги", "https://poleknig.com/books/1"),
        ("Вторая настоящая книга", "https://poleknig.com/books/2"),
    ]


def test_playerjs_property_search_skips_property_text_inside_string():
    js = '''{
      title: "Аудиокнига, file: поддельное значение",
      description: 'текст с playlist: тоже не свойство',
      file: "https://cdn.example/real.mp3"
    }'''

    assert _extract_js_property(js, "file") == '"https://cdn.example/real.mp3"'


def test_playerjs_property_search_skips_comments():
    js = '''{
      // file: "https://cdn.example/comment.mp3",
      /* playlist: "https://cdn.example/comment.json" */
      file: "/audio/real.mp3"
    }'''

    assert _extract_js_property(js, "file") == '"/audio/real.mp3"'


class _DummyVar:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = value


class _Tree:
    def __init__(self):
        self.selected = None
        self.focused = None

    def identify_row(self, _y):
        return ""

    def get_children(self, _parent):
        return ("0", "1")

    def bbox(self, iid):
        # Simulate a first row that has already scrolled out and produces a
        # malformed/partial bbox while the last row remains visible.
        return (0,) if iid == "0" else (0, 10, 100, 20)

    def selection_set(self, iid):
        self.selected = iid

    def focus(self, iid):
        self.focused = iid

    def see(self, _iid):
        pass


def test_queue_drag_motion_tolerates_partial_bbox_and_still_targets_visible_end():
    host = QueueMixin()
    host.queue_running = False
    host._queue_drag_source = "0"
    host._queue_drag_target = None
    host.queue_tree = _Tree()
    host.queue_items = [SimpleNamespace(title="Первая"), SimpleNamespace(title="Вторая")]
    host.queue_drag_var = _DummyVar()

    host._queue_drag_motion(SimpleNamespace(y=40))

    assert host._queue_drag_target == "1"
    assert host._queue_drag_after is True
    assert host.queue_tree.selected == "1"
