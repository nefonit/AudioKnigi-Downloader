"""Regression checks for the site's current /search?text=... contract."""

from __future__ import annotations

from audioknigi import search as search_module
from audioknigi.search import SEARCH_URL, SearchMixin


FIXTURE = r'''
<form id="header-search-form" method="get" action="/search">
  <input minlength="3" id="story" name="text" value="Сандерсон">
</form>
<div class="search-results">
  <a href="/audio-49051-sanderson-brendon-davshiy-klyatvu">
    <img alt="Слушать онлайн аудиокниги Сандерсон Брендон - Давший клятву" src="cover.jpg">
  </a>
  <a href="/audio-49051-sanderson-brendon-davshiy-klyatvu">Сандерсон Брендон - Давший клятву</a>
  <a href="https://audioknigi.com.ua/audio-48456-sanderson-brendon-slova-siyaniya">Сандерсон Брендон - Слова сияния</a>
</div>
<aside class="popular">
  <a href="/audio-90422-filatov-valeriy-ubiystvo-na-stancii">Филатов Валерий - Убийство на станции</a>
  <a href="/audio-12345-other-book"><img alt="Совсем другая книга"></a>
</aside>
'''


class _Response:
    text = FIXTURE
    url = "https://audioknigi.com.ua/search?text=%D0%A1%D0%B0%D0%BD%D0%B4%D0%B5%D1%80%D1%81%D0%BE%D0%BD"

    def raise_for_status(self):
        return None


class _Session:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _Response()


class _Host(SearchMixin):
    def __init__(self):
        self.search_results = []
        self.statuses = []
        self.logs = []

    def ui(self, callback):
        callback()

    def _refresh_search_results(self):
        return None

    def set_status(self, text):
        self.statuses.append(text)

    def log(self, text):
        self.logs.append(text)


def main():
    host = _Host()
    parsed = host._parse_search_results(FIXTURE, "https://audioknigi.com.ua/search", query="Сандерсон")
    assert [item.title for item in parsed] == [
        "Слова сияния",
        "Давший клятву",
    ], parsed
    assert [item.author for item in parsed] == ["Сандерсон Брендон", "Сандерсон Брендон"]
    assert all("Филатов" not in item.title for item in parsed)

    # Multi-word searches are token based, so author/name word order is tolerant.
    parsed2 = host._parse_search_results(FIXTURE, "https://audioknigi.com.ua/search", query="Брендон Сандерсон")
    assert len(parsed2) == 2

    fake = _Session()
    original = search_module.get_http_session
    search_module.get_http_session = lambda: fake
    try:
        host._search_worker("Сандерсон")
    finally:
        search_module.get_http_session = original

    assert len(fake.calls) == 1
    url, kwargs = fake.calls[0]
    assert url == SEARCH_URL == "https://audioknigi.com.ua/search"
    assert kwargs.get("params") == {"text": "Сандерсон"}
    assert "story" not in kwargs.get("params", {})
    assert "do" not in kwargs.get("params", {})
    assert [item.title for item in host.search_results] == [
        "Слова сияния",
        "Давший клятву",
    ]
    assert host.statuses[-1].endswith("найдено 2")

    print("SEARCH ENDPOINT /search?text=: OK")
    print("SEARCH AUTHOR FILTER: OK")
    print("SEARCH SIDEBAR REJECTION: OK")
    print("SEARCH DUPLICATE MERGE: OK")
    print("SEARCH ACCURACY 4.8.2: OK")


if __name__ == "__main__":
    main()


def test_audioknigi_results_split_author_and_book_title():
    host = _Host()
    parsed = host._parse_search_results(
        FIXTURE,
        "https://audioknigi.com.ua/search",
        query="Сандерсон",
    )
    assert [(item.title, item.author) for item in parsed] == [
        ("Слова сияния", "Сандерсон Брендон"),
        ("Давший клятву", "Сандерсон Брендон"),
    ]
