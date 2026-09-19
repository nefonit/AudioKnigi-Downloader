from __future__ import annotations

import threading

from audioknigi.knigavuhe import _hydrate_search_result_titles, _knigavuhe_matches_query
from audioknigi.models import SearchResult
from audioknigi.providers import audioknigi_search
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService


def test_knigavuhe_strict_relevance_rejects_reported_unrelated_books() -> None:
    query = "Крыса"
    assert _knigavuhe_matches_query(
        SearchResult(title="Крысы в стенах", author="Говард Филлипс Лавкрафт",
                     narrator="VartKes", url="https://knigavuhe.org/book/rats/",
                     source="knigavuhe.org"),
        query,
    )
    for title in ("Крауч Энд", "Дворец грез", "Кому жить на Руси хорошо"):
        assert not _knigavuhe_matches_query(
            SearchResult(title=title, author="Другой автор", narrator="Другой чтец",
                         url=f"https://knigavuhe.org/book/{title}/", source="knigavuhe.org"),
            query,
        )


def test_knigavuhe_hydration_applies_final_query_filter_without_network_when_metadata_complete() -> None:
    items = [
        SearchResult(title="Крысы в стенах", author="Лавкрафт", narrator="VartKes",
                     url="https://knigavuhe.org/book/rats/", source="knigavuhe.org"),
        SearchResult(title="Крауч Энд", author="Стивен Кинг", narrator="Чтец",
                     url="https://knigavuhe.org/book/crouch-end/", source="knigavuhe.org"),
        SearchResult(title="Дворец грез", author="Автор", narrator="Чтец",
                     url="https://knigavuhe.org/book/palace/", source="knigavuhe.org"),
        SearchResult(title="Кому жить на Руси хорошо", author="Некрасов", narrator="Чтец",
                     url="https://knigavuhe.org/book/rus/", source="knigavuhe.org"),
    ]
    filtered = _hydrate_search_result_titles(items, "Крыса")
    assert [item.title for item in filtered] == ["Крысы в стенах"]


class _Response:
    def __init__(self, html: str):
        self.content = html.encode("utf-8")
        self.text = html
        self.url = "https://audioknigi.com.ua/audio-test"

    def raise_for_status(self):
        return None


class _Session:
    def __init__(self, html: str):
        self.html = html

    def get(self, *args, **kwargs):
        return _Response(self.html)


def test_audioknigi_page_metadata_keeps_coauthor_out_of_title_and_merges_authors() -> None:
    html = "<html><title>Бурносова Татьяна - Тоннельная крыса</title></html>"
    source = SearchResult(
        title="Тоннельная крыса",
        author="Бурносова Татьяна",
        url="https://audioknigi.com.ua/audio-test",
        source="audioknigi.com.ua",
    )
    result = audioknigi_search._audioknigi_page_metadata(
        source,
        session_factory=lambda: _Session(html),
        metadata_extractor=lambda _html, _fallback: (
            "Бурносова Татьяна - Тоннельная крыса",
            "Бурносов Юрий",
            "",
        ),
        extended_metadata_extractor=lambda _html: ("", "Чтец", "", ""),
    )
    assert result.title == "Тоннельная крыса"
    assert "Бурносова Татьяна" in result.author
    assert "Бурносов Юрий" in result.author


def test_audioknigi_author_merging_deduplicates_reordered_same_person() -> None:
    merged = audioknigi_search._merge_author_names(
        "Юрий Бурносов", "Бурносов Юрий", "Татьяна Бурносова"
    )
    assert merged.count("Юрий") == 1
    assert "Татьяна Бурносова" in merged


def test_direct_audioknigi_analysis_does_not_invent_unverified_author_prefix() -> None:
    html = """
    <title>Гарри Поттер — Философский камень</title>
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"AudioBook",
     "name":"Гарри Поттер — Философский камень",
     "author":{"@type":"Person","name":"Джоан Роулинг"},
     "description":"Настоящая аннотация книги."}
    </script>
    <div class="book-description">Настоящая аннотация книги о событиях романа.</div>
    """
    service = BookAnalysisService(
        cancel_event=threading.Event(),
        options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False),
    )
    book = service._parse_playlist_data(
        url="https://audioknigi.com.ua/audio-test",
        html_text=html,
        page_title="",
        playlist_url="https://audioknigi.com.ua/list.pl.txt",
        playlist_text='[{"file":"https://cdn.example/1.mp3","title":"Глава 1"}]',
    )
    assert book.title == "Гарри Поттер — Философский камень"
    assert book.author == "Джоан Роулинг"
