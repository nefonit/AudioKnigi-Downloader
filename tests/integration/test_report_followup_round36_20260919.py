from __future__ import annotations

import threading
from pathlib import Path

from audioknigi.knigavuhe import _description_from_html as knigavuhe_description
from audioknigi.poleknig import _book_page_metadata as poleknig_metadata
from audioknigi.providers import audioknigi_search
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_easy_card_is_substantially_wider_and_table_keeps_adaptive_header_modes() -> None:
    source = src("audioknigi/qt/main_window.py")
    assert "card.setMinimumWidth(820)" in source
    assert "card.setMaximumWidth(1500)" in source
    assert "card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)" in source
    assert "center_row.addWidget(card, 8)" in source
    assert "easy_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)" in source
    assert 'if key in {"index", "availability", "variants", "source"}:' in source
    assert "self.easy_search_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)" in source


def test_audioknigi_title_removes_seo_suffix_and_site_url() -> None:
    clean = audioknigi_search._canonical_title
    assert clean("Крыса аудиокнига слушать онлайн https://audioknigi.com.ua/") == "Крыса"
    assert clean("Слушать онлайн аудиокнигу Крыса") == "Крыса"
    assert clean("Аудиокнига онлайн — Крыса") == "Крыса"


def test_audioknigi_author_prefix_without_dash_is_removed_from_title() -> None:
    strip = audioknigi_search._strip_author_prefix_from_title
    assert strip("Бурносов Юрий Тоннельная крыса", "Юрий Бурносов") == "Тоннельная крыса"
    assert strip("Лев Толстой - Война и мир", "Толстой Лев Николаевич") == "Война и мир"
    assert strip("Метро 2033 — Тёмные туннели", "Дмитрий Глуховский") == "Метро 2033 — Тёмные туннели"


def test_audioknigi_query_relevance_rejects_reported_unrelated_titles() -> None:
    matches = audioknigi_search._matches_query
    assert matches("Крыса", "Крыса")
    assert matches("Тоннельная крыса", "Крыса", author="Юрий Бурносов")
    assert not matches("Четыре всадника", "Крыса", author="Докинз, Харрис, Хитченс, Деннет")
    assert not matches("Большие друзья. Музыкальные сказки", "Крыса")
    assert not matches("Как удвоить объем памяти", "Крыса")


def test_audioknigi_grouping_filters_unrelated_results_even_without_metadata(monkeypatch) -> None:
    items = [
        audioknigi_search.SearchResult(title="Крыса", url="https://audioknigi.com.ua/audio-1-krysa", source="audioknigi.com.ua"),
        audioknigi_search.SearchResult(title="Четыре всадника", url="https://audioknigi.com.ua/audio-2-four", source="audioknigi.com.ua"),
        audioknigi_search.SearchResult(title="Большие друзья. Музыкальные сказки", url="https://audioknigi.com.ua/audio-3-friends", source="audioknigi.com.ua"),
    ]
    monkeypatch.setattr(audioknigi_search, "_audioknigi_page_metadata", lambda item: item)
    result = audioknigi_search._group_audioknigi_recordings(items, query="Крыса")
    assert [item.title for item in result] == ["Крыса"]


def test_audioknigi_real_annotation_beats_seo_description() -> None:
    html = """
    <html><head>
      <meta name="description" content="Крыса аудиокнига слушать онлайн https://audioknigi.com.ua/">
    </head><body>
      <div class="book-description">
        Настоящая аннотация рассказывает о герое, его конфликте и событиях книги.
      </div>
    </body></html>
    """
    value = audioknigi_search._audioknigi_description_from_html(html, title="Крыса", author="Автор")
    assert value.startswith("Настоящая аннотация")
    assert "слушать онлайн" not in value.casefold()


def test_audioknigi_analysis_normalizes_title_author_and_description() -> None:
    html = """
    <html><head>
      <title>Бурносов Юрий Тоннельная крыса аудиокнига слушать онлайн https://audioknigi.com.ua/</title>
      <script type="application/ld+json">
      {"@context":"https://schema.org","@type":"AudioBook","name":"Бурносов Юрий Тоннельная крыса аудиокнига слушать онлайн","author":{"@type":"Person","name":"Юрий Бурносов"},"description":"Слушать аудиокнигу онлайн бесплатно"}
      </script>
    </head><body>
      <div class="book-description">Содержательная аннотация о событиях романа и главных героях.</div>
    </body></html>
    """
    service = BookAnalysisService(
        cancel_event=threading.Event(),
        options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False),
    )
    book = service._parse_playlist_data(
        url="https://audioknigi.com.ua/audio-1-tonnelnaya-krysa",
        html_text=html,
        page_title="",
        playlist_url="https://audioknigi.com.ua/list.pl.txt",
        playlist_text='[{"file":"https://cdn.example/1.mp3","title":"Глава 1"}]',
    )
    assert book.title == "Тоннельная крыса"
    assert book.author == "Юрий Бурносов"
    assert book.description.startswith("Содержательная аннотация")


def test_knigavuhe_annotation_prefers_visible_description_and_rejects_seo_meta() -> None:
    html = """
    <meta name="description" content="Крыса слушать аудиокнигу бесплатно на knigavuhe.org">
    <div class="book__description">Настоящая аннотация Knigavuhe с описанием сюжета книги.</div>
    """
    assert knigavuhe_description(html).startswith("Настоящая аннотация Knigavuhe")
    seo_only = '<meta name="description" content="Крыса слушать аудиокнигу бесплатно на knigavuhe.org">'
    assert knigavuhe_description(seo_only) == ""


def test_poleknig_annotation_contract_still_prefers_visible_synopsis() -> None:
    html = """
    <head><meta name="description" content="Скачать аудиокнигу Крыса бесплатно и слушать онлайн"></head>
    <body><h1>Крыса</h1><a href="/authors/1">Автор</a>
    <div class="book-description">Реальная аннотация с содержательным описанием сюжета и героя.</div></body>
    """
    meta = poleknig_metadata(html, "https://poleknig.com/books/1")
    assert meta["description"].startswith("Реальная аннотация")


def test_both_ui_modes_render_the_same_book_description_field() -> None:
    source = src("audioknigi/qt/mixins/analysis_download.py")
    assert 'self.book_description.setText(str(book.description or self._l("Описание отсутствует.")))' in source
    assert 'easy_description = str(book.description or "").strip()' in source
    assert "self.easy_description.setPlainText(easy_description)" in source
