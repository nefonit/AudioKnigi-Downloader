"""Yakniga book-description fallback regression checks (offline only)."""
import threading

import pytest
import requests

from audioknigi.core import Cancelled
from audioknigi.providers import extra_sources as extra

URL = "https://yakniga.org/rouling-dzhoan/garri-potter-i-dary-smerti"
DESCRIPTION = (
    "Лето перед последним курсом обучения Гарри в Хогвартсе. "
    "Раскол в волшебном мире произошёл окончательно, и сторонники Волан-де-Морта "
    "становятся всё сильнее. Служащие министерства магии один за другим "
    "подчиняются им, а новым директором Хогвартса стал Северус Снегг, "
    "убивший Дамблдора. Гарри Поттер пока скрывается от врагов, однако "
    "они подбираются к нему всё ближе. А ведь просто отсиживаться в "
    "безопасном месте он не может – необходимо найти крестражи, содержащие "
    "части души Волан-де-Морта, не уничтожив которые, нельзя надеяться "
    "на победу. Гарри принимает решение не возвращаться в школу и вместо "
    "этого вместе с друзьями отправляется на поиски."
)
PAGE = f'''<html><head><meta name="description" content="Неверный метатег"></head>
<body><div class="page__description page__description-hide" data-v-e6b00818="">
{DESCRIPTION}</div><h2>Аудиокниги серии: Гарри Поттер</h2><section>Другие книги</section></body></html>'''


def graph_book(description=None, restricted=False):
    return {"title": "Гарри Поттер и Дары Смерти", "authorName": "Роулинг Джоан",
            "readers": [{"name": "Клюквин Александр"}], "isBiblio": restricted,
            "description": description, "chapters": {"collection": [
                {"name": "Глава 1", "fileUrl": "https://cdn.example.test/1.mp3", "duration": 100}]}}


def test_css_collapsed_block_gets_correct_full_description():
    assert extra._yakniga_description_from_html(PAGE) == DESCRIPTION


def test_description_only_from_book_div_no_nearby_content():
    page = '<div class="page__sidebar">Не описание</div><div class="page__description-hide">Неправильный блок</div>' \
           '<div class="page__description">Основное описание. <script>bad();</script><b>Вторая часть.</b></div><section>Отзывы</section>'
    assert extra._yakniga_description_from_html(page) == 'Основное описание. Вторая часть.'


def test_graphql_missing_description_uses_html_and_keeps_chapters(monkeypatch):
    calls = []
    class Response:
        text = PAGE
    def request(url, *, cancel_event=None, json_payload=None):
        calls.append((url, json_payload is not None))
        return Response()
    monkeypatch.setattr(extra, "_yakniga_payload", lambda payload, cancel_event=None: {"book": graph_book()})
    monkeypatch.setattr(extra, "_request", request)
    book = extra.fetch_yakniga(URL)
    assert book.description == DESCRIPTION
    assert book.title == "Гарри Поттер и Дары Смерти"
    assert book.narrator == "Клюквин Александр"
    assert len(book.tracks) == 1
    assert calls == [(URL, False)]


def test_graphql_description_not_overwritten_or_extra_request(monkeypatch):
    monkeypatch.setattr(extra, "_yakniga_payload", lambda payload, cancel_event=None: {
        "book": graph_book("<p>Аннотация из API</p>")})
    monkeypatch.setattr(extra, "_request", lambda *a, **k: pytest.fail("unnecessary GET"))
    assert extra.fetch_yakniga(URL).description == "Аннотация из API"


def test_empty_html_does_not_leak_meta_description(monkeypatch):
    class Response:
        text = '<meta name="description" content="Слушайте онлайн"><div class="other">Серия Гарри Поттер</div>'
    monkeypatch.setattr(extra, "_yakniga_payload", lambda payload, cancel_event=None: {"book": graph_book()})
    monkeypatch.setattr(extra, "_request", lambda *a, **k: Response())
    assert extra.fetch_yakniga(URL).description == ""


def test_html_error_is_nonfatal_when_chapters_are_available(monkeypatch):
    monkeypatch.setattr(extra, "_yakniga_payload", lambda payload, cancel_event=None: {"book": graph_book()})
    def request(*a, **k):
        raise requests.exceptions.ReadTimeout("unable to get HTML")
    monkeypatch.setattr(extra, "_request", request)
    book = extra.fetch_yakniga(URL)
    assert book.description == ""
    assert len(book.tracks) == 1


def test_cancellation_during_fallback_not_swallowed(monkeypatch):
    event = threading.Event()
    monkeypatch.setattr(extra, "_yakniga_payload", lambda payload, cancel_event=None: {"book": graph_book()})
    def request(*a, **k):
        event.set()
        raise Cancelled("stop")
    monkeypatch.setattr(extra, "_request", request)
    with pytest.raises(Cancelled):
        extra.fetch_yakniga(URL, cancel_event=event)


def test_restricted_book_does_not_make_html_request(monkeypatch):
    monkeypatch.setattr(extra, "_yakniga_payload", lambda payload, cancel_event=None: {"book": graph_book(restricted=True)})
    monkeypatch.setattr(extra, "_request", lambda *a, **k: pytest.fail("restricted GET"))
    with pytest.raises(RuntimeError, match="лицензии"):
        extra.fetch_yakniga(URL)


def test_fallback_rejects_unexpected_host(monkeypatch):
    monkeypatch.setattr(extra, "_request", lambda *a, **k: pytest.fail("unsafe GET"))
    assert extra._yakniga_html_description_fallback("https://other.example/path/book") == ""
