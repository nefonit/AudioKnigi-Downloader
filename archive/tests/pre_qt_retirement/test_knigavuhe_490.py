from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from audioknigi.core import valid_site_url
from audioknigi.downloader import DownloaderMixin
from audioknigi.knigavuhe import parse_book_html, parse_search_results
from audioknigi.sources import normalize_supported_url, source_key, source_name


def test_supported_sources_and_mobile_normalization():
    assert valid_site_url("https://audioknigi.com.ua/audio-123-test")
    assert valid_site_url("https://knigavuhe.org/book/test/")
    assert valid_site_url("https://m.knigavuhe.org/book/test/")
    assert not valid_site_url("https://example.com/book/test")
    assert source_key("https://knigavuhe.org/book/test/") == "knigavuhe"
    assert source_name("https://knigavuhe.org/book/test/") == "knigavuhe.org"
    assert normalize_supported_url("https://m.knigavuhe.org/book/test/?x=1") == "https://knigavuhe.org/book/test/?x=1"


def test_knigavuhe_search_parser_uses_only_book_links():
    html = """
    <a href="/author/123/">Леонид Филатов</a>
    <article><a href="/book/pro-fedota/"><img alt="Про Федота-стрельца"></a></article>
    <article><a href="https://knigavuhe.org/book/5-minut/">5 минут до рассвета</a></article>
    <a href="/reader/42/">Вячеслав Румянцев</a>
    """
    results = parse_search_results(html, "https://knigavuhe.org/search/?q=filatov")
    assert [(x.title, x.url, x.source) for x in results] == [
        ("Про Федота-стрельца", "https://knigavuhe.org/book/pro-fedota/", "knigavuhe.org"),
        ("5 минут до рассвета", "https://knigavuhe.org/book/5-minut/", "knigavuhe.org"),
    ]


def test_knigavuhe_bookcontroller_parser_maps_metadata_and_fallback_playlist():
    payload = {
        "id": 42,
        "book": {
            "name": "Тестовая книга",
            "authors": {"10": {"name": "Автор Один"}, "11": {"name": "Автор Два"}},
            "readers": {"20": {"name": "Чтец"}},
            "cover": "https://img.example/cover-320x500.jpg",
            "url": "/book/test/",
        },
        "playlist": [
            {"title": "Глава 1", "url": "https://audio.example/main/01.mp3?token=a"},
            {"title": "Глава 2", "url": "https://audio.example/main/02.mp3"},
        ],
        "merged_playlist": [
            {"title": "Глава 1", "url": "https://backup.example/01.mp3"},
            {"title": "Глава 2", "url": "https://backup.example/02.mp3"},
        ],
    }
    html = f'''<html><head><title>Тест</title></head><body>
    <div class="bookDescription">Описание <b>книги</b>.</div>
    <script>BookController.enter({json.dumps(payload, ensure_ascii=False)});</script>
    </body></html>'''
    book = parse_book_html(html, "https://knigavuhe.org/book/test/")
    assert book.title == "Тестовая книга"
    assert book.author == "Автор Один, Автор Два"
    assert book.narrator == "Чтец"
    assert book.description == "Описание книги."
    assert book.cover_url.endswith("cover-320x500.jpg")
    assert len(book.tracks) == 2
    assert book.tracks[0].title == "Глава 1"
    assert book.tracks[0].file == "https://audio.example/main/01.mp3?token=a"
    assert book.tracks[0].fallback_file == "https://backup.example/01.mp3"


def test_knigavuhe_restricted_page_is_not_bypassed():
    with pytest.raises(RuntimeError, match="правообладателя"):
        parse_book_html(
            "<html>Доступ к аудиокниге ограничен по просьбе правообладателя.</html>",
            "https://knigavuhe.org/book/restricted/",
        )


def test_download_source_fallback_tries_second_url_and_cleans_partial(tmp_path):
    class Host(DownloaderMixin):
        def __init__(self):
            self.calls = []
            self.cancel_event = SimpleNamespace(is_set=lambda: False)

        def log(self, _text):
            pass

        def _download_with_resume(self, url, target, referer):
            self.calls.append(url)
            target = Path(target)
            if len(self.calls) == 1:
                target.with_suffix(target.suffix + ".part").write_bytes(b"partial")
                raise RuntimeError("primary failed")
            target.write_bytes(b"ok")
            return target

    host = Host()
    target = tmp_path / "source.mp3"
    result = host._download_source_with_fallback(
        "https://main.example/01.mp3",
        "https://backup.example/01.mp3",
        target,
        "https://knigavuhe.org/book/test/",
    )
    assert result == target
    assert host.calls == ["https://main.example/01.mp3", "https://backup.example/01.mp3"]
    assert target.read_bytes() == b"ok"
    assert not target.with_suffix(target.suffix + ".part").exists()


def test_knigavuhe_legacy_script_mp3_fallback():
    html = """
    <title>Книга X (слушать аудиокнигу бесплатно) - автор Автор X</title>
    <script>var tracks=[\"https:\\/\\/cdn.example/1.mp3\",\"https:\\/\\/cdn.example/2.mp3\"];</script>
    """
    book = parse_book_html(html, "https://knigavuhe.org/book/x/")
    assert book.title == "Книга X"
    assert book.author == "Автор X"
    assert [t.file for t in book.tracks] == [
        "https://cdn.example/1.mp3",
        "https://cdn.example/2.mp3",
    ]


def test_knigavuhe_search_ignores_comments_and_genre_links():
    html = """
    <div class="book-item">
      <a class="book-title" href="/book/leonid-filatov/">Леонид Филатов</a>
      <span>автор <a href="/author/voroneckaya/">Татьяна Воронецкая</a></span>
      <a class="genre" href="/genre/biografii-memuary/">Биографии и мемуары</a>
      <a class="comments" href="/book/leonid-filatov/#comments_block">1</a>
    </div>
    <div class="book-item">
      <a class="book-title" href="/book/pro-fedota-strelca-udalogo-molodca/?from=search">Про Федота-стрельца, удалого молодца</a>
      <a href="/genre/dlya-detey/">Для детей и Аудиосказки</a>
      <a href="https://knigavuhe.org/book/pro-fedota-strelca-udalogo-molodca/#comments_block">12</a>
    </div>
    """
    results = parse_search_results(html, "https://knigavuhe.org/search/?q=филатов")
    assert [(x.title, x.url) for x in results] == [
        ("Леонид Филатов", "https://knigavuhe.org/book/leonid-filatov/"),
        ("Про Федота-стрельца, удалого молодца", "https://knigavuhe.org/book/pro-fedota-strelca-udalogo-molodca/"),
    ]
    assert all("#" not in x.url and "/genre/" not in x.url for x in results)


def test_knigavuhe_search_nested_links_do_not_replace_book_title():
    # Some card templates are structurally complex.  A non-book link inside a
    # book anchor must not overwrite the outer book label.
    html = """
    <a href="/book/test-book/">
      Название книги
      <span><a href="/genre/fantastika/">Фантастика и фэнтези</a></span>
    </a>
    <a href="/book/test-book/#comments_block">23</a>
    """
    results = parse_search_results(html)
    assert len(results) == 1
    assert results[0].title == "Название книги"
    assert results[0].url == "https://knigavuhe.org/book/test-book/"


def test_knigavuhe_search_hydrates_real_book_title_instead_of_genre(monkeypatch):
    import audioknigi.knigavuhe as kv

    search_html = """
    <div class="book-item">
      <a href="/book/leonid-filatov/">Биографии</a>
      <a href="/book/pro-fedota-strelca-udalogo-molodca/">Для детей</a>
    </div>
    """
    pages = {
        "https://knigavuhe.org/book/leonid-filatov/": (
            "<html><head><title>Леонид Филатов (слушать аудиокнигу бесплатно) - "
            "автор Татьяна Воронецкая</title></head></html>"
        ),
        "https://knigavuhe.org/book/pro-fedota-strelca-udalogo-molodca/": (
            "<html><head><title>Про Федота-стрельца, удалого молодца "
            "(слушать аудиокнигу бесплатно) - автор Леонид Филатов</title></head></html>"
        ),
    }

    class Response:
        def __init__(self, text, url):
            self.text = text
            self.url = url

        def raise_for_status(self):
            return None

    class Session:
        def get(self, url, **kwargs):
            if url == kv.SEARCH_URL:
                return Response(search_html, "https://knigavuhe.org/search/?q=филатов")
            return Response(pages[url], url)

    monkeypatch.setattr(kv, "get_http_session", lambda: Session())
    results = kv.search("филатов")
    assert [(item.title, item.url) for item in results] == [
        ("Леонид Филатов", "https://knigavuhe.org/book/leonid-filatov/"),
        (
            "Про Федота-стрельца, удалого молодца",
            "https://knigavuhe.org/book/pro-fedota-strelca-udalogo-molodca/",
        ),
    ]


def test_knigavuhe_title_hydration_failure_keeps_search_result(monkeypatch):
    import audioknigi.knigavuhe as kv

    class Session:
        def get(self, *_args, **_kwargs):
            raise OSError("offline")

    monkeypatch.setattr(kv, "get_http_session", lambda: Session())
    original = kv.SearchResult(
        title="Резервное название",
        url="https://knigavuhe.org/book/test/",
        source="knigavuhe.org",
    )
    resolved = kv._hydrate_search_result_titles([original])
    assert resolved == [original]


def test_knigavuhe_search_filters_reader_only_matches_and_keeps_author_title(monkeypatch):
    import audioknigi.knigavuhe as kv

    search_html = """
    <a href="/book/fedot/">Для детей</a>
    <a href="/book/master-i-margarita/">Аудиоспектакли</a>
    <a href="/book/leonid-filatov/">Биографии</a>
    """
    pages = {
        "https://knigavuhe.org/book/fedot/": (
            "<title>Про Федота-стрельца (слушать аудиокнигу бесплатно) - "
            "автор Леонид Филатов, читает Леонид Филатов</title>"
        ),
        "https://knigavuhe.org/book/master-i-margarita/": (
            "<title>Мастер и Маргарита (слушать аудиокнигу бесплатно) - "
            "автор Михаил Булгаков, читает Эраст Гарин, Леонид Филатов</title>"
        ),
        "https://knigavuhe.org/book/leonid-filatov/": (
            "<title>Леонид Филатов (слушать аудиокнигу бесплатно) - "
            "автор Татьяна Воронецкая, читает Ирина Петрова</title>"
        ),
    }

    class Response:
        def __init__(self, text, url):
            self.text = text
            self.url = url
        def raise_for_status(self):
            return None

    class Session:
        def get(self, url, **kwargs):
            if url == kv.SEARCH_URL:
                return Response(search_html, "https://knigavuhe.org/search/?q=филатов")
            return Response(pages[url], url)

    monkeypatch.setattr(kv, "get_http_session", lambda: Session())
    results = kv.search("филатов")

    assert [item.url for item in results] == [
        "https://knigavuhe.org/book/fedot/",
        "https://knigavuhe.org/book/leonid-filatov/",
    ]
    assert results[0].author == "Леонид Филатов"
    assert results[0].narrator == "Леонид Филатов"
    assert results[1].author == "Татьяна Воронецкая"
    assert results[1].narrator == "Ирина Петрова"


def test_knigavuhe_page_metadata_separates_author_and_reader():
    import audioknigi.knigavuhe as kv

    meta = kv._book_page_search_metadata(
        "<title>Про Федота-стрельца, удалого молодца (слушать аудиокнигу бесплатно) "
        "- автор Леонид Филатов, читает Кристина Лари</title>"
    )
    assert meta == {
        "title": "Про Федота-стрельца, удалого молодца",
        "author": "Леонид Филатов",
        "narrator": "Кристина Лари",
    }


def test_knigavuhe_extracts_alternative_narrations():
    import audioknigi.knigavuhe as kv

    html = """
    <h2>Другие озвучки</h2>
    <a href="/book/fedot-kriv/">Про Федота-стрельца, удалого молодца</a>
    в исполнении <a href="/reader/krivosheev-ilja/">Ильи Кривошеева</a>
    <a href="/book/fedot-lari/">Про Федота-стрельца, удалого молодца</a>
    в исполнении <a href="/reader/lari-kristina/">Кристины Лари</a>
    <h2>Рекомендации</h2>
    <a href="/book/not-a-variant/">Другая книга</a>
    """
    variants = kv._extract_narration_variants(
        html,
        "https://knigavuhe.org/book/fedot-filatov/",
        title="Про Федота-стрельца, удалого молодца",
        current_narrator="Леонид Филатов",
    )
    assert [(v.narrator, v.url, v.current) for v in variants] == [
        ("Леонид Филатов", "https://knigavuhe.org/book/fedot-filatov/", True),
        ("Ильи Кривошеева", "https://knigavuhe.org/book/fedot-kriv/", False),
        ("Кристины Лари", "https://knigavuhe.org/book/fedot-lari/", False),
    ]


def test_knigavuhe_restricted_recording_with_alternatives_returns_choice_book():
    html = """
    <html><head><title>Про Федота-стрельца (слушать аудиокнигу бесплатно) - автор Леонид Филатов, читает Леонид Филатов</title></head>
    <body>
      Доступ к аудиокниге ограничен по просьбе правообладателя.
      <h2>Другие озвучки</h2>
      <a href="/book/fedot-kriv/">Про Федота-стрельца</a> в исполнении
      <a href="/reader/krivosheev/">Ильи Кривошеева</a>
      <h2>Рекомендации</h2>
    </body></html>
    """
    book = parse_book_html(html, "https://knigavuhe.org/book/fedot-filatov/")
    assert book.restricted is True
    assert book.title == "Про Федота-стрельца"
    assert book.author == "Леонид Филатов"
    assert book.narrator == "Леонид Филатов"
    assert book.tracks == []
    assert len(book.narration_variants) == 2
    assert book.narration_variants[1].url == "https://knigavuhe.org/book/fedot-kriv/"


def test_knigavuhe_current_search_card_separates_title_author_reader():
    html = """
    <div class="bookitem">
      <a class="bookitem_cover" href="/book/pro-fedota/"><img class="bookitem_cover_img" alt="Про Федота-стрельца"><div class="bookitem_cover_genre">Для детей</div></a>
      <div class="bookitem_right">
        <div class="bookitem_name"><a class="is_black" href="/book/pro-fedota/">Про <span>Федота</span>-стрельца</a></div>
        <div class="bookitem_meta">
          <div class="bookitem_meta_block icon_author"><div><a href="/author/leonid-filatov/">Леонид <span>Филатов</span></a></div></div>
          <div class="bookitem_meta_block icon_reader"><div><a href="/reader/filatov-leonid/">Леонид Филатов</a></div></div>
        </div>
      </div>
    </div>
    """
    results = parse_search_results(html, "https://knigavuhe.org/search/?q=филатов")
    assert len(results) == 1
    item = results[0]
    assert item.title == "Про Федота-стрельца"
    assert "Для детей" not in item.title
    assert item.author == "Леонид Филатов"
    assert item.narrator == "Леонид Филатов"
    assert item.url == "https://knigavuhe.org/book/pro-fedota/"


def test_knigavuhe_search_follows_pagination_and_filters_reader_only(monkeypatch):
    import audioknigi.knigavuhe as kv

    def card(slug, title, author, reader):
        return f"""
        <div class="bookitem">
          <a class="bookitem_cover" href="/book/{slug}/"><img class="bookitem_cover_img" alt="{title}"><div class="bookitem_cover_genre">Жанр</div></a>
          <div class="bookitem_right">
            <div class="bookitem_name"><a class="is_black" href="/book/{slug}/">{title}</a></div>
            <div class="bookitem_meta">
              <div class="bookitem_meta_block icon_author"><div>{author}</div></div>
              <div class="bookitem_meta_block icon_reader"><div>{reader}</div></div>
            </div>
          </div>
        </div>
        """

    pages = {
        1: card("fedot", "Про Федота", "Леонид Филатов", "Леонид Филатов")
           + '<a class="pn_button is_page" data-page="2" href="/search/?q=филатов&page=2">2</a>'
           + '<a class="pn_button is_page" data-page="3" href="/search/?q=филатов&page=3">3</a>',
        2: card("master", "Мастер и Маргарита", "Михаил Булгаков", "Леонид Филатов"),
        3: card("labirint", "Лабиринт искажений", "Валерий Филатов", "Алекс Збаровский"),
    }

    class Response:
        def __init__(self, page):
            self.text = pages[page]
            suffix = "" if page == 1 else f"&page={page}"
            self.url = f"https://knigavuhe.org/search/?q=филатов{suffix}"

        def raise_for_status(self):
            return None

    class Session:
        def __init__(self):
            self.calls = []

        def get(self, url, **kwargs):
            params = kwargs.get("params", {})
            page = int(params.get("page", 1))
            self.calls.append(page)
            return Response(page)

    session = Session()
    monkeypatch.setattr(kv, "get_http_session", lambda: session)
    results = kv.search("филатов")

    assert sorted(session.calls) == [1, 2, 3]
    assert [item.title for item in results] == ["Про Федота", "Лабиринт искажений"]
    assert [item.author for item in results] == ["Леонид Филатов", "Валерий Филатов"]
    assert all("master" not in item.url for item in results)


def test_knigavuhe_pagination_parser_reads_last_page():
    import audioknigi.knigavuhe as kv

    html = """
    <a class="pn_button is_page" data-page="1" href="/search/?q=x">1</a>
    <a class="pn_button is_page" data-page="2" href="/search/?q=x&page=2">2</a>
    <span>...</span>
    <a class="pn_button is_page" data-page="17" href="/search/?q=x&page=17">17</a>
    """
    assert kv._search_last_page(html) == 17
