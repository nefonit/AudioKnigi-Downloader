"""Offline contract checks for the experimental Akniga provider."""
import pytest

from audioknigi.akniga import _is_hls_url, _parse_api_book
from audioknigi.core import SiteStructureChanged
from audioknigi.providers import provider_for_url
from audioknigi.sources import is_supported_url, normalize_supported_url, source_key

URL = "https://akniga.org/glubina-pogruzhenie-76-e"
HLS = "https://h7.akniga.club/b/123/pl.m3u8?res=test&expires=1999999999"


def test_akniga_source_url_and_provider():
    assert is_supported_url(URL)
    assert source_key(URL) == "akniga"
    assert provider_for_url(URL).key == "akniga"
    assert normalize_supported_url("www.akniga.org/glubina-pogruzhenie-76-e/?t=3") == URL
    assert not is_supported_url("https://akniga.org/page/faq/")
    assert not is_supported_url("https://akniga.org/search/")
    assert not is_supported_url("https://akniga.org.evil.test/glubina-pogruzhenie-76-e")


def test_hls_detection():
    assert _is_hls_url(HLS)
    assert not _is_hls_url("https://cdn.example.test/a.mp3")
    assert not _is_hls_url("file:///tmp/pl.m3u8")


def test_parse_akniga_chapters_without_fake_media_urls():
    payload = {
        "titleonly": "Глубина. Погружение 76-е",
        "author": "Том Флетчер",
        "items": '[{"title":"00. intro","time_from_start":0,"time_finish":98},'
                 '{"title":"01. Вид","time_from_start":98,"time_finish":1697}]',
    }
    page = '<meta content="/cover.jpg" property="og:image">'
    book = _parse_api_book(URL, page, payload, HLS)
    assert book.title == payload["titleonly"]
    assert book.cover_url == "https://akniga.org/cover.jpg"
    assert [t.title for t in book.tracks] == ["00. intro", "01. Вид"]
    assert [t.duration for t in book.tracks] == [98.0, 1599.0]
    assert [t.file for t in book.tracks] == [HLS, HLS]


def test_parse_refuses_bad_timeline():
    payload = {"titleonly": "test", "items": [{"title":"a", "time_from_start":15, "time_finish":5}]}
    with pytest.raises(SiteStructureChanged):
        _parse_api_book(URL, "", payload, HLS)
