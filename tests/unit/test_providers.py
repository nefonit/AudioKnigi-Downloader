from pathlib import Path

from audioknigi.providers import SourceProvider, provider_for_key, provider_for_url, registered_providers
from audioknigi.services.search_service import parse_audioknigi_results
from audioknigi.knigavuhe import _book_page_search_metadata
from audioknigi.poleknig import _tracks_from_playerjs

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures" / "providers"


def test_provider_registry_contains_all_supported_sources():
    assert {p.key for p in registered_providers()} == {"audioknigi", "knigavuhe", "poleknig"}
    assert all(isinstance(p, SourceProvider) for p in registered_providers())


def test_provider_lookup_by_url_and_canonicalization():
    provider = provider_for_url("poleknig.com/books/123-demo")
    assert provider is not None and provider.key == "poleknig"
    assert provider.canonicalize_url("poleknig.com/books/123-demo") == "https://poleknig.com/books/123"


def test_audioknigi_search_fixture():
    html = (FIX / "audioknigi_search.html").read_text(encoding="utf-8")
    results = parse_audioknigi_results(html, "https://audioknigi.com.ua/search", "Тестовая")
    assert len(results) == 1
    assert results[0].title == "Тестовая книга"


def test_knigavuhe_metadata_fixture():
    html = (FIX / "knigavuhe_book.html").read_text(encoding="utf-8")
    meta = _book_page_search_metadata(html)
    assert meta["title"] == "Тестовая книга"
    assert meta["author"] == "Иван Автор"
    assert meta["narrator"] == "Пётр Чтец"


def test_poleknig_playerjs_fixture():
    html = (FIX / "poleknig_playerjs.html").read_text(encoding="utf-8")
    tracks = _tracks_from_playerjs(html, "https://poleknig.com/books/123")
    assert [t.index for t in tracks] == [1, 2]
    assert tracks[0].title == "Глава 1"


def test_audioknigi_provider_exposes_same_search_contract(monkeypatch):
    provider = provider_for_key("audioknigi")
    assert provider is not None
    expected = []
    monkeypatch.setattr("audioknigi.providers.audioknigi_search.search_audioknigi", lambda query, cancel_event=None: expected)
    assert provider.search("test") == expected
