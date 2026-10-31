"""Offline checks for new external sources: no live downloads or credentials."""
import json
import threading
from urllib.parse import urlparse

import pytest

from audioknigi.core import Cancelled, SiteStructureChanged
from audioknigi.providers import provider_for_key, provider_for_url, registered_providers
from audioknigi.providers import extra_sources as extra
from audioknigi.services.book_analysis_service import BookAnalysisService, AnalysisOptions
from audioknigi.sources import is_supported_url, source_key, normalize_supported_url


class Response:
    def __init__(self, payload):
        self.payload = payload
        self.text = payload if isinstance(payload, str) else json.dumps(payload)

    def json(self):
        return self.payload


@pytest.fixture
def fake_web(monkeypatch):
    docs = {}
    def get(url, *, cancel_event=None, json_payload=None, params=None):
        if cancel_event and cancel_event.is_set():
            raise Cancelled('cancelled')
        key = urlparse(url).path
        if json_payload is not None:
            key += ':' + str(json_payload.get('operationName', 'search'))
        if key not in docs:
            raise AssertionError('unexpected request ' + key)
        return Response(docs[key])
    monkeypatch.setattr(extra, '_request', get)
    return docs


@pytest.mark.parametrize('url,key', [
    ('izib.uk/art144511','izibuk'),
    ('www.yakniga.org/author-slug/book-slug','yakniga'),
    ('https://www.uknig.com/books/123-foo?utm=1','uknig'),
    ('https://archive.org/details/test_librivox#foo','librivox'),
])
def test_new_url_identity_and_normalization(url,key):
    assert source_key(url) == key
    assert is_supported_url(url)
    assert provider_for_url(url).key == key
    assert normalize_supported_url(url).startswith('https://')


@pytest.mark.parametrize('url',[ 'https://archive.org/download/something/a.mp3',
    'https://evil-archive.org/details/abc', 'https://yakniga.org/search',
    'https://izib.uk/search', 'https://uknig.com/books/',
    'https://archive.org/details/', 'https://yakniga.org/'])
def test_new_unsupported_urls(url):
    assert not is_supported_url(url)


def test_izibuk_book_tracks(fake_web):
    fake_web['/art/demo'] = '''<h1>Demo</h1><span itemprop="name">Образец</span>
     <a href="/author/test">Иван</a><a href="/reader/some">Пётр</a>
     <script>var player = new XSPlayer({"mp3_url_prefix":"cdn.example.net/mp3","tracks":[
     [0,"Часть 1",31,0,"1.mp3"],[1,"Часть 2",42,0,"2.mp3"]]});</script>'''
    book = extra.fetch_izibuk('https://izib.uk/art/demo')
    assert book.title == 'Образец' and book.author == 'Иван'
    assert book.tracks[1].file == 'https://cdn.example.net/mp3/2.mp3'
    assert book.tracks[1].duration == 42
    assert [t.index for t in book.tracks] == [1, 2]


def test_yakniga_book_and_search(fake_web):
    fake_web['/graphql:getBook'] = {'data': {'book': {'title':'Test', 'authorName':'Name',
        'authorAlias':'author','aliasName':'book','readers':[{'name':'Voice'}], 'isBiblio':False,
        'chapters':{'collection':[{'name':'one','fileUrl':'/files/1.mp3','duration':100},
                                  {'name':'two','fileUrl':'https://cdn.test/2.mp3','duration':200}]}}}}
    fake_web['/author/book'] = '<div class="page__description page__description-hide">Описание тестовой книги.</div>'
    book = extra.fetch_yakniga('https://yakniga.org/author/book')
    assert book.narrator == 'Voice'
    assert book.description == 'Описание тестовой книги.'
    assert book.tracks[0].file == 'https://yakniga.org/files/1.mp3'
    assert book.tracks[1].duration == 200
    fake_web['/graphql:None'] = {'data': {'search': [
        {'title':'One','authorAlias':'a','aliasName':'b','authorName':'John','isBiblio':False},
        {'title':'Private','authorAlias':'a','aliasName':'c','isBiblio':True}]}}
    assert [r.url for r in extra.search_yakniga('some')] == ['https://yakniga.org/a/b']


def test_yakniga_restricted(fake_web):
    fake_web['/graphql:getBook'] = {'data': {'book': {'title':'Private', 'isBiblio':True}}}
    with pytest.raises(RuntimeError, match='лицензии'):
        extra.fetch_yakniga('https://yakniga.org/author/book')


def test_uknig_book(fake_web):
    fake_web['/books/demo'] = '''<h1 itemprop="name">Book</h1>
    <script>createPlayer("/player/demo.json")</script>'''
    fake_web['/player/demo.json'] = [{'title':'First','file':'https://cdn.example/f.mp3 or https://other/f.mp3'}]
    book = extra.fetch_uknig('https://uknig.com/books/demo')
    assert len(book.tracks) == 1
    assert book.tracks[0].file == 'https://cdn.example/f.mp3'


def test_uknig_licensed(fake_web):
    fake_web['/books/demo'] = '<h1>Licensed</h1>'
    with pytest.raises(RuntimeError, match='лицензионная'):
        extra.fetch_uknig('https://uknig.com/books/demo')


def test_librivox_fetch_select_format_and_search(fake_web):
    fake_web['/metadata/example'] = {'metadata':{'title':'Old Book','creator':['A. Author'],
        'description':'<p>Public domain</p>','collection':['other','librivoxaudio']},
        'files':[{'name':'chap 1.mp3','format':'128Kbps MP3','length':'60.5','title':'Chap 1'},
                 {'name':'chap 2.mp3','format':'128Kbps MP3','length':'78'},
                 {'name':'duplicate.mp3','format':'VBR MP3','length':'60'},
                 {'name':'cover.jpg','format':'JPEG'}]}
    book = extra.fetch_librivox('https://archive.org/details/example')
    assert book.author == 'A. Author' and book.description == 'Public domain'
    assert len(book.tracks) == 2
    assert book.tracks[0].file == 'https://archive.org/download/example/chap%201.mp3'
    fake_web['/advancedsearch.php'] = {'response': {'docs': [
        {'title':'Old Book','creator':'A. Author','identifier':'example'}]}}
    assert extra.search_librivox('Old')[0].url == 'https://archive.org/details/example'


def test_librivox_rejects_unrelated_archived_item(fake_web):
    fake_web['/metadata/example'] = {'metadata':{'title':'News','collection':'other'}, 'files': []}
    with pytest.raises(SiteStructureChanged, match='коллекцию LibriVox'):
        extra.fetch_librivox('https://archive.org/details/example')


def test_cancellation_stops_work(fake_web):
    event = threading.Event()
    event.set()
    with pytest.raises(Cancelled):
        extra.fetch_izibuk('https://izib.uk/art/demo', cancel_event=event)


def test_headless_analyzer_routes_to_provider_without_browser(monkeypatch):
    from audioknigi.providers.registry import provider_for_key
    provider = provider_for_key('librivox')
    book = extra._meta_book('https://archive.org/details/example', title='An Example',
        tracks=[extra._track(1,'First','https://archive.org/download/example/one.mp3', 'https://archive.org/')])
    monkeypatch.setattr(type(provider), 'fetch_book', lambda self, url, *, cancel_event=None: book)
    analyzer = BookAnalysisService(options=AnalysisOptions(fetch_cover=False))
    monkeypatch.setattr(analyzer, '_populate_missing_track_durations', lambda b: 0)
    out = analyzer.analyze('https://archive.org/details/example')
    assert out.title == 'An Example' and len(out.tracks) == 1


def test_uknig_full_description_is_book_paragraph_only(fake_web):
    html = '''<html><h1 itemprop="name">Гарри Поттер и Кубок Огня</h1>
    <div class="description"><p>Гарри Поттеру предстоит четвёртый год обучения
    в Школе чародейства и волшебства "Хогвартс". <br>Новые заклинания,
    новые зелья, новые учителя… <br> Всё, как обычно, но на школу внезапно
    обрушивается потрясающее событие: Турнир Трёх Волшебников.</p></div>
    <section><div class="description">Входит в серию Гарри Поттер</div></section>
    <script>createPlayer("/player/test.json")</script></html>'''
    fake_web['/books/678270'] = html
    fake_web['/player/test.json'] = [{'title': '1', 'file': 'https://cdn.example/1.mp3'}]
    book = extra.fetch_uknig('https://uknig.com/books/678270')
    assert book.description.startswith('Гарри Поттеру предстоит четвёртый год')
    assert 'Турнир Трёх Волшебников' in book.description
    assert 'Входит в серию' not in book.description
    assert 'Новые заклинания, новые зелья' in book.description


def test_librivox_official_catalogue_used_when_archive_empty(fake_web):
    fake_web['/advancedsearch.php'] = {'response': {'docs': []}}
    fake_web['/api/feed/audiobooks'] = {'books': [
        {'title': 'The Adventures of Sherlock Holmes',
         'url_iarchive': 'http://archive.org/details/sherlock_holmes_librivox',
         'authors': [{'first_name': 'Arthur Conan', 'last_name': 'Doyle'}]},
    ]}
    results = extra.search_librivox('Sherlock Holmes')
    assert len(results) == 1
    assert results[0].url == 'https://archive.org/details/sherlock_holmes_librivox'
    assert results[0].author == 'Arthur Conan Doyle'


def test_librivox_official_catalogue_author_lookup_and_safe_links(monkeypatch):
    calls = []
    def fake_request(url, *, cancel_event=None, params=None, json_payload=None):
        calls.append((url, params))
        if 'advancedsearch' in url:
            return Response({'response': {'docs': []}})
        if params.get('title'):
            return Response({'books': [{'title': 'Bad target',
                                        'url_iarchive': 'https://evil.example/details/x'}]})
        return Response({'books': [{'title': 'Public domain recording',
                                    'url_iarchive': '',
                                    'url_zip_file': 'https://archive.org/download/verified_id/book.zip'}]})
    monkeypatch.setattr(extra, '_request', fake_request)
    results = extra.search_librivox('Doyle')
    assert [r.url for r in results] == ['https://archive.org/details/verified_id']
    assert any(p and p.get('author') == 'Doyle' for _, p in calls)


def test_librivox_official_catalogue_network_failure_keeps_empty_archive(monkeypatch):
    import requests
    def fake_request(url, *, cancel_event=None, params=None, json_payload=None):
        if 'advancedsearch' in url:
            return Response({'response': {'docs': []}})
        raise requests.exceptions.ConnectTimeout('network down')
    monkeypatch.setattr(extra, '_request', fake_request)
    assert extra.search_librivox('not found') == []


def test_yakniga_analysis_uses_graphql_duration_without_18_sec_ffprobe(monkeypatch):
    from audioknigi.models import Book
    adapter = provider_for_key('yakniga')
    assert adapter
    book = extra._meta_book('https://yakniga.org/author/book', title='Book',
                             tracks=[extra._track(1, 'part1', 'https://cdn.example/p1.mp3', 'https://yakniga.org/')])
    monkeypatch.setattr(type(adapter), 'fetch_book', lambda self, url, *, cancel_event=None: book)
    analyzer = BookAnalysisService(options=AnalysisOptions(fetch_cover=False))
    def forbidden(_book):
        raise AssertionError('Yakniga must not launch ffprobe in analysis')
    monkeypatch.setattr(analyzer, '_populate_missing_track_durations', forbidden)
    assert analyzer.analyze('https://yakniga.org/author/book') is book
    assert book.tracks[0].duration is None


def test_librivox_diagnostic_uses_disclosed_public_domain_example():
    from audioknigi.services.source_health_service import _probe_search
    class Provider:
        key = 'librivox'
        display_name = 'archive.org'
        def search(self, term):
            assert term == 'Sherlock Holmes'
            return [object()]
    item = _probe_search(Provider(), 'Поттер')
    assert item.reachable
    assert item.search_results == 1
    assert 'Sherlock Holmes' in item.search_endpoint


def test_librivox_regular_search_term_is_never_rewritten():
    from audioknigi.services.source_health_service import _probe_search
    class Provider:
        key = 'librivox'
        display_name = 'archive.org'
        def search(self, term):
            assert term == 'Doyle'
            return []
    item = _probe_search(Provider(), 'Doyle')
    assert item.reachable and item.search_results == 0
    assert 'Sherlock Holmes' not in item.search_endpoint
