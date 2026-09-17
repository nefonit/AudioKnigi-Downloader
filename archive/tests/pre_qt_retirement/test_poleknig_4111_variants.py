from __future__ import annotations

from audioknigi.models import NarrationVariant
from audioknigi.poleknig import _discover_narration_variants, _logical_title_key


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
        if params:
            page = int(params.get("p", 1))
            key = f"{url}?p={page}"
        else:
            key = url
        self.calls.append(key)
        text = self.mapping[key]
        return _Response(text, key)


def _book_page(title: str, narrator: str, *, restricted: bool = False) -> str:
    marker = "<div>Удалено правообладателем.</div>" if restricted else "<script>new Playerjs({file:'/audio/test.mp3'})</script>"
    return f"""
    <html><head><title>{title}: слушать аудиокнигу</title></head><body>
      <h1>{title}</h1>
      <a href='/authors/126878'>Леонид Филатов</a>
      <div>Читает <a href='/readers/42'>{narrator}</a></div>
      {marker}
    </body></html>
    """


def test_logical_title_key_groups_poleknig_presentation_prefixes():
    expected = _logical_title_key("Про Федота-стрельца, удалого молодца")
    assert _logical_title_key("Сказ про Федота-стрельца, удалого молодца") == expected
    assert _logical_title_key("Пьеса: Сказ про Федота-стрельца, удалого молодца") == expected


def test_discover_variants_from_author_catalogue_skips_restricted_alternatives():
    current_url = "https://poleknig.com/books/147736"
    author_url = "https://poleknig.com/authors/126878"
    current_html = _book_page("Про Федота-стрельца, удалого молодца", "Леонид Филатов", restricted=True)
    author_html = """
    <html><body>
      <a href='/books/147736'>Про Федота-стрельца, удалого молодца</a>
      <a href='/books/210880'>Про Федота-стрельца, удалого молодца</a>
      <a href='/books/211644'>Сказ про Федота-стрельца, удалого молодца</a>
      <a href='/books/198852'>Пьеса: Сказ про Федота-стрельца, удалого молодца</a>
    </body></html>
    """
    session = _Session({
        author_url: author_html,
        "https://poleknig.com/books/210880": _book_page("Про Федота-стрельца, удалого молодца", "Илья Кривошеев", restricted=True),
        "https://poleknig.com/books/211644": _book_page("Сказ про Федота-стрельца, удалого молодца", "Кристина Лари", restricted=False),
        "https://poleknig.com/books/198852": _book_page("Пьеса: Сказ про Федота-стрельца, удалого молодца", "Илья Кривошеев", restricted=True),
    })
    meta = {
        "title": "Про Федота-стрельца, удалого молодца",
        "author": "Леонид Филатов",
        "narrator": "Леонид Филатов",
    }

    variants = _discover_narration_variants(current_html, current_url, meta, session=session)

    assert [(v.url, v.narrator, v.current) for v in variants] == [
        ("https://poleknig.com/books/147736", "Леонид Филатов", True),
        ("https://poleknig.com/books/211644", "Кристина Лари", False),
    ]


def test_discover_variants_can_follow_author_pagination():
    current_url = "https://poleknig.com/books/147736"
    author_url = "https://poleknig.com/authors/126878"
    current_html = _book_page("Про Федота-стрельца, удалого молодца", "Леонид Филатов", restricted=True)
    page1 = """
    <html><body>
      <a href='/books/147736'>Про Федота-стрельца, удалого молодца</a>
      <a href='/authors/126878?p=2'>2</a>
    </body></html>
    """
    page2 = "<html><body><a href='/books/211644'>Сказ про Федота-стрельца, удалого молодца</a></body></html>"
    session = _Session({
        author_url: page1,
        f"{author_url}?p=2": page2,
        "https://poleknig.com/books/211644": _book_page("Сказ про Федота-стрельца, удалого молодца", "Кристина Лари"),
    })
    meta = {"title": "Про Федота-стрельца, удалого молодца", "author": "Леонид Филатов", "narrator": "Леонид Филатов"}

    variants = _discover_narration_variants(current_html, current_url, meta, session=session)

    assert len(variants) == 2
    assert variants[1].url == "https://poleknig.com/books/211644"
    assert f"{author_url}?p=2" in session.calls
