"""Regression checks for search-highlight fragments in Izib titles."""
from bs4 import BeautifulSoup

from audioknigi.providers import extra_sources as extra
from audioknigi.services.search_relevance import search_relevance_rank


def make_card(title_html, path="/art1693"):
    return BeautifulSoup(
        f'<div><a href="{path}"><img alt="Обложка"></a>'
        f'<div><a href="{path}">{title_html}</a></div></div>',
        "html.parser",
    ).div


def test_izib_highlight_does_not_separate_case_endings():
    samples = {
        'Архив <mark>Шерлок</mark>а <b>Холмс</b>а': 'Архив Шерлока Холмса',
        'Возвращение <span>Шерлок</span>а <span>Холмс</span>а': 'Возвращение Шерлока Холмса',
        'Воспоминания о <b>Шерлок</b>е <b>Холмс</b>е': 'Воспоминания о Шерлоке Холмсе',
        'Единственная любовь <b>Шерлок</b>а <b>Холмс</b>а': 'Единственная любовь Шерлока Холмса',
        'Забытые дела <b>Шерлок</b>а <b>Холмс</b>а': 'Забытые дела Шерлока Холмса',
        'Записки о <b>Шерлок</b>е <b>Холмс</b>е': 'Записки о Шерлоке Холмсе',
        'Неизвестные приключения <b>Шерлок</b>а <b>Холмс</b>а': 'Неизвестные приключения Шерлока Холмса',
    }
    for html, expected in samples.items():
        result = extra._izib_search_card(make_card(html), 'https://izib.uk/')
        assert result is not None
        assert result.title == expected
        assert search_relevance_rank('шерлок холмс', result) < 4


def test_izib_title_punctuation_and_true_word_spaces():
    result = extra._izib_search_card(
        make_card('<span>Шерлок</span> <em>Холмс</em> . Дыхание бога'),
        'https://izib.uk/',
    )
    assert result is not None
    assert result.title == 'Шерлок Холмс. Дыхание бога'
    assert extra._izib_book_title(
        BeautifulSoup('<b>Шерлок</b> <i>Холмс</i>. Приключения', 'html.parser')
    ) == 'Шерлок Холмс. Приключения'


def test_izib_title_keeps_intentional_words_and_diacritics():
    assert extra._izib_book_title(
        BeautifulSoup('<b>Новый</b> <span>рассказ</span> о <mark>Шерлок</mark>е', 'html.parser')
    ) == 'Новый рассказ о Шерлоке'
    assert extra._izib_book_title(BeautifulSoup('L’étrange <b>affaire</b> de Holmes', 'html.parser')) == 'L’étrange affaire de Holmes'


def test_izib_book_page_title_uses_same_normalization(monkeypatch):
    class Resp:
        text = '''<h1 itemprop="name">Воспоминания о <mark>Шерлок</mark>е <mark>Холмс</mark>е</h1>
        <script>new XSPlayer({"mp3_url_prefix":"audio.example.net/",
        "tracks":[[1,"Глава",60,{},"one.mp3"]]});</script>'''
    monkeypatch.setattr(extra, '_request', lambda *a,**kw: Resp())
    book=extra.fetch_izibuk('https://izib.uk/art1693')
    assert book.title == 'Воспоминания о Шерлоке Холмсе'
    assert len(book.tracks) == 1


def test_izib_html_entities_and_markup_keep_title():
    result = extra._izib_search_card(
        make_card('Шерлок&nbsp;<b>Холмс</b>&nbsp;:&nbsp;Тайна'),
        'https://izib.uk/',
    )
    assert result is not None
    assert result.title == 'Шерлок Холмс: Тайна'


def test_izib_real_br_separates_subtitle_but_wbr_does_not_break_word():
    node = BeautifulSoup('<span>Шерлок<wbr>а Холмс<br>Дыхание бога</span>', 'html.parser').span
    assert extra._izib_book_title(node) == 'Шерлока Холмс Дыхание бога'


def test_izib_author_highlighting_keeps_word_endings():
    card = BeautifulSoup("""
    <div><a href="/art1693"><img alt="cover"></a>
    <a href="/art1693">Шерлок Холмс</a>
    <a href="/author/2">Конан <mark>Дойл</mark>а</a>
    <a href="/reader/1">Иван<mark>ов</mark>а</a></div>
    """, 'html.parser').div
    result = extra._izib_search_card(card, 'https://izib.uk/')
    assert result is not None
    assert result.author == 'Конан Дойла'
    assert result.narrator == 'Иванова'
