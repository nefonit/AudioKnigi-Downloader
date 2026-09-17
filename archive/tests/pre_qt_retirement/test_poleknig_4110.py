from __future__ import annotations

from audioknigi.models import SearchResult
from audioknigi.poleknig import (
    _book_page_metadata,
    _search_last_page,
    _tracks_from_playerjs,
    parse_book_html,
    parse_search_results,
)
from audioknigi.sources import is_supported_url, normalize_supported_url, source_key, source_name


def test_poleknig_source_is_supported_with_or_without_scheme():
    assert source_key("https://poleknig.com/books/147736") == "poleknig"
    assert source_key("poleknig.com/books/147736") == "poleknig"
    assert is_supported_url("poleknig.com/books/147736") is True
    assert normalize_supported_url("poleknig.com/books/147736") == "https://poleknig.com/books/147736"
    assert source_name("https://poleknig.com/books/147736") == "poleknig.com"


def test_playerjs_compact_playlist_becomes_tracks():
    html = '''
    <script>
      var player = new Playerjs({
        id: "player",
        file: "[Глава 1]https://cdn.example/01.mp3,[Глава 2]/audio/02.mp3"
      });
    </script>
    '''
    tracks = _tracks_from_playerjs(html, "https://poleknig.com/books/1")
    assert [(t.title, t.file) for t in tracks] == [
        ("Глава 1", "https://cdn.example/01.mp3"),
        ("Глава 2", "https://poleknig.com/audio/02.mp3"),
    ]


def test_playerjs_array_playlist_becomes_tracks():
    html = '''
    <script>
      new Playerjs({id:'player', playlist:[
        {'title':'Первая','file':'/a/1.mp3','duration':'00:01:30'},
        {'title':'Вторая','file':'https://cdn.example/2.mp3'}
      ]});
    </script>
    '''
    tracks = _tracks_from_playerjs(html, "https://poleknig.com/books/2")
    assert len(tracks) == 2
    assert tracks[0].title == "Первая"
    assert tracks[0].duration == 90
    assert tracks[0].file == "https://poleknig.com/a/1.mp3"


def test_poleknig_metadata_and_restricted_page():
    html = '''
    <html><head>
      <meta property="og:image" content="/covers/1.jpg">
      <meta name="description" content="Описание книги">
    </head><body>
      <h1>Лисья нора</h1>
      <h2><a href="/authors/100">Нора Сакавич</a></h2>
      <div>Год выхода: 2022</div>
      <div>Читает <a href="/readers/7">Пётр Коврижных</a></div>
      <div><a href="/genres/1">Фантастика</a></div>
      <p>Удалено правообладателем.</p>
    </body></html>
    '''
    meta = _book_page_metadata(html, "https://poleknig.com/books/218019")
    assert meta["title"] == "Лисья нора"
    assert meta["author"] == "Нора Сакавич"
    assert meta["narrator"] == "Пётр Коврижных"
    book = parse_book_html(html, "https://poleknig.com/books/218019")
    assert book.restricted is True
    assert book.tracks == []


def test_search_parser_keeps_only_books_and_deduplicates_cover_title_links():
    html = '''
    <a href="/authors/1">Леонид Филатов</a>
    <a href="/books/147736"><img alt="Леонид Филатов - Про Федота-стрельца"></a>
    <a href="/books/147736">Про Федота-стрельца</a>
    <a href="/books/189971">Любовь к трем апельсинам</a>
    '''
    rows = parse_search_results(html, "https://poleknig.com/?q=филатов")
    assert [(r.title, r.url) for r in rows] == [
        ("Про Федота-стрельца", "https://poleknig.com/books/147736"),
        ("Любовь к трем апельсинам", "https://poleknig.com/books/189971"),
    ]


def test_poleknig_search_pagination_uses_p_parameter():
    html = '''
    <a href="/?q=филатов&p=2">2</a>
    <a href="/?p=7&q=филатов">7</a>
    <a href="/?p=99&q=другой">99</a>
    '''
    assert _search_last_page(html, "филатов") == 7
