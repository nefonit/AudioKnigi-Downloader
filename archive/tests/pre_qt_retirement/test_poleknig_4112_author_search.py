from __future__ import annotations

import audioknigi.poleknig as pk


class _Response:
    def __init__(self, text: str, url: str):
        self.text = text
        self.url = url

    def raise_for_status(self):
        return None


class _Session:
    def __init__(self, mapping):
        self.mapping = mapping
        self.calls = []

    def get(self, url, params=None, **kwargs):
        params = dict(params or {})
        if url == pk.BASE_URL and "q" in params:
            page = int(params.get("p", 1))
            key = f"search:{params['q']}:{page}"
            final = f"{pk.BASE_URL}?q={params['q']}&p={page}"
        elif params and "p" in params:
            page = int(params["p"])
            key = f"{url}?p={page}"
            final = key
        else:
            key = url
            final = url
        self.calls.append(key)
        return _Response(self.mapping[key], final)


def _book(title: str, narrator: str = "Чтец") -> str:
    return f"""
    <html><body>
      <h1>{title}</h1>
      <a href='/authors/126878'>Леонид Филатов</a>
      <div>Читает <a href='/readers/1'>{narrator}</a></div>
      <script>new Playerjs({{file:'/audio/test.mp3'}})</script>
    </body></html>
    """


def test_author_link_parser_returns_visible_name_and_canonical_url():
    html = "<a href='/authors/126878?x=1'>Леонид Филатов</a>"
    assert pk._book_page_author_links(html, "https://poleknig.com/books/1") == [
        ("Леонид Филатов", "https://poleknig.com/authors/126878")
    ]


def test_poleknig_author_query_expands_author_catalog_pagination(monkeypatch):
    author_url = "https://poleknig.com/authors/126878"
    mapping = {
        "search:Филатов:1": "<a href='/books/1'>Первая книга</a>",
        "https://poleknig.com/books/1": _book("Первая книга", "Первый чтец"),
        author_url: """
            <a href='/books/1'>Первая книга</a>
            <a href='/books/2'>Вторая книга</a>
            <a href='/authors/126878?p=2'>2</a>
        """,
        f"{author_url}?p=2": "<a href='/books/3'>Третья книга</a>",
        "https://poleknig.com/books/2": _book("Вторая книга", "Второй чтец"),
        "https://poleknig.com/books/3": _book("Третья книга", "Третий чтец"),
    }
    session = _Session(mapping)
    monkeypatch.setattr(pk, "get_http_session", lambda: session)

    results = pk.search("Филатов")

    assert [item.title for item in results] == ["Первая книга", "Вторая книга", "Третья книга"]
    assert all(item.author == "Леонид Филатов" for item in results)
    assert f"{author_url}?p=2" in session.calls


def test_title_match_does_not_expand_unrelated_author_catalog(monkeypatch):
    mapping = {
        "search:Филатов:1": "<a href='/books/9'>Леонид Филатов: биография</a>",
        "https://poleknig.com/books/9": """
            <h1>Леонид Филатов: биография</h1>
            <a href='/authors/999'>Татьяна Воронецкая</a>
            <div>Читает <a href='/readers/2'>Чтец</a></div>
            <script>new Playerjs({file:'/audio/test.mp3'})</script>
        """,
    }
    session = _Session(mapping)
    monkeypatch.setattr(pk, "get_http_session", lambda: session)

    results = pk.search("Филатов")

    assert len(results) == 1
    assert results[0].author == "Татьяна Воронецкая"
    assert not any(call.startswith("https://poleknig.com/authors/999") for call in session.calls)
