"""Regression tests: Akniga's series and narrator widgets are not a synopsis.

The affected URL is https://akniga.org/lavkraft-govard-uzhas-danvicha .
These HTML examples model competing visible article blocks (offline); they do
not claim to be an exact saved copy of the remote page.
"""

from audioknigi.akniga import _akniga_description, _parse_api_book

BOOK_URL = "https://akniga.org/lavkraft-govard-uzhas-danvicha"
SYNOPSIS = (
    "Второго февраля 1913 года у Лавинии Уэйтли родился сын Уилбер. "
    "Дальнейшие происшествия в деревне стали началом кошмара."
)
SERIES = "Другие книги серии Тёмные аллеи 2.2 - Ктулху и аколиты " + " | ".join(
    f"Глава из серии {n}" for n in range(18)
)
OTHER_NARRATORS = "Другие озвучки: Зайцев Андрей, VartKes. " * 3


def test_dunwich_captioned_synopsis_beats_unlabelled_series_before_it():
    markup = f'''<html><head><meta property="og:description" content="Слушать Ужас Данвича"></head><body>
      <div class="description__article-main">{SERIES}</div>
      <div class="description__article-main"><div class="content__main__book--item--caption">
          Другие озвучки</div>{OTHER_NARRATORS}</div>
      <div class="description__article-main">
        <div class="content__main__book--item--caption">Описание</div>
        {SYNOPSIS}
      </div></body></html>'''
    payload = {"titleonly": "Ужас Данвича", "items": [
        {"title": "Ужас Данвича - 01", "time_from_start": 0, "time_finish": 600},
    ]}
    book = _parse_api_book(BOOK_URL, markup, payload, "https://cdn.example.test/source.m3u8")
    assert book.description == SYNOPSIS
    assert "Другие озвучки" not in book.description
    assert "Другие книги серии" not in book.description


def test_dunwich_caption_sibling_beats_unlabelled_other_readings():
    markup = f'''<section><div class="description__article-main">{OTHER_NARRATORS}</div>
       <div class="content__main__book--item--caption">Описание</div>
       <div class="description__article-main">{SYNOPSIS}</div></section>'''
    assert _akniga_description(markup) == SYNOPSIS


def test_no_labeled_description_returns_seo_instead_of_unlabelled_series():
    markup = f'''<head><meta property="og:description" content="{SYNOPSIS}"></head>
      <div class="description__article-main">{SERIES}</div>
      <div class="description__article-main">{OTHER_NARRATORS}</div>'''
    assert _akniga_description(markup) == SYNOPSIS


def test_single_legacy_unlabelled_synopsis_is_still_accepted():
    assert _akniga_description(f'<div class="description__article-main">{SYNOPSIS}</div>') == SYNOPSIS


def test_prevent_generic_itemprop_series_from_overwriting_labeled_synopsis():
    markup = f'''<div itemprop="description">{SERIES}</div>
    <div class="description__article-main">
       <div class="content__main__book--item--caption">Описание</div>{SYNOPSIS}
    </div>'''
    assert _akniga_description(markup) == SYNOPSIS
