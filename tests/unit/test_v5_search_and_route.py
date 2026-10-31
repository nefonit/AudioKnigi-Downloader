"""V5 regressions: catalogue extraction, truthful search diagnostic, fast TCP fallback."""
from __future__ import annotations

import socket
import threading
from dataclasses import dataclass

import pytest

from audioknigi.core import Cancelled, SiteStructureChanged
from audioknigi.providers import extra_sources as extra
from audioknigi.providers.adapters import AKnigaProvider, IzibukProvider
from audioknigi.providers.base import SourceProvider
from audioknigi.services import source_health_service as health
from audioknigi import network_dns as nd


class Response:
    def __init__(self, text):
        self.text = text


def fake_soup_pages(monkeypatch, pages):
    requested=[]
    def _get(url, *, cancel_event=None, **kwargs):
        requested.append(url)
        for key, markup in pages.items():
            if key in url:
                return Response(markup)
        raise AssertionError(f'unexpected page: {url}')
    monkeypatch.setattr(extra, '_request', _get)
    return requested


def test_akniga_real_provider_search_and_metadata(monkeypatch):
    pages = {'page1': '''<div class="content__main__articles">
       <div class="content__main__articles--item">
        <div class="article--cover"><a href="/doil-artur-delo"><img alt="Дойл Артур – Горбун"></a></div>
        <span class="link__action--author"><a href="/author/1">Дойл Артур</a>
        <a href="/performer/7">Сушков</a></span>
       </div>
       <div class="content__main__articles--item">
        <div class="article--cover"><a href="/preview-foo"><img alt="Превью"></a></div>
        <div class="caption__article-preview">Фрагмент</div>
       </div>
       <div class="content__main__articles--item"><a href="https://evil.example/bad-1">external</a></div>
       </div>''',
       'page2': '<div class="content__main__articles"></div>'}
    requested=fake_soup_pages(monkeypatch,pages)
    results=AKnigaProvider().search('Горбун')
    assert len(results)==1
    assert results[0].title=='Горбун'
    assert results[0].author=='Дойл Артур'
    assert results[0].narrator=='Сушков'
    assert results[0].source=='akniga.org'
    assert results[0].url=='https://akniga.org/doil-artur-delo'
    assert 'page1/?q=' in requested[0]
    assert len(requested)==2


def test_akniga_empty_is_distinguished_from_unrecognized_layout(monkeypatch):
    fake_soup_pages(monkeypatch, {'page1':'<div class="content__main__articles"></div>'})
    assert extra.search_akniga('Невозможный запрос')==[]
    fake_soup_pages(monkeypatch, {'page1':'<html><title>Обслуживание</title></html>'})
    with pytest.raises(SiteStructureChanged,match='область результатов'):
        extra.search_akniga('Невозможный запрос')


def test_akniga_cancelled_before_network(monkeypatch):
    event=threading.Event();event.set()
    monkeypatch.setattr(extra, '_request', lambda *a,**k: pytest.fail('must not request'))
    with pytest.raises(Cancelled):
        extra.search_akniga('Горбун',cancel_event=event)


def test_izib_card_uses_text_title_not_cover_and_deduplicates(monkeypatch):
    pages={'p=1': '''<section id="books_list"><div class="grid">
     <div><a href="/art001"><img alt="Книга на обложке"></a>
      <div><a href="/art001">Правильное название</a></div>
      <a href="/author/11">Автор 1</a><a href="/reader/22">Чтец 1</a></div>
     <div><a href="/art002"><img alt="Книга 2"></a>
      <div><a href="/art002">Книга 2</a></div></div>
     </div></section>''',
     'p=2': '<section id="books_list"><div></div></section>'}
    requested=fake_soup_pages(monkeypatch,pages)
    rows=IzibukProvider().search('автор')
    assert [r.title for r in rows]==['Правильное название','Книга 2']
    assert rows[0].author=='Автор 1'
    assert rows[0].narrator=='Чтец 1'
    assert rows[0].url=='https://izib.uk/art001'
    assert len(requested)==2


def test_izib_unknown_html_is_error_not_empty(monkeypatch):
    fake_soup_pages(monkeypatch,{'p=1':'<html>Browser challenge</html>'})
    with pytest.raises(SiteStructureChanged,match='область результатов'):
        extra.search_izibuk('Поттер')


def test_search_diagnostic_distinguishes_unsupported_empty_error(monkeypatch):
    class Unimplemented(SourceProvider):
        key='stub';display_name='Stub'
        def supports_url(self,url): return False
        def canonicalize_url(self,url):return url
        def fetch_book(self,url,*,cancel_event=None):raise NotImplementedError
    @dataclass
    class Blank:
        key: str='blank';display_name: str='Blank'
        def search(self, query):return []
    @dataclass
    class Broken:
        key: str='broken';display_name: str='Broken'
        def search(self, query):raise TimeoutError('https://secret.example/?token=private')
    from audioknigi import providers
    monkeypatch.setattr(providers,'registered_providers',lambda:(Unimplemented(),Blank(),Broken()))
    rows=health.check_source_search('Поттер').items
    assert not rows[0].search_supported and not rows[0].reachable
    assert rows[0].error=='Поиск не поддерживается'
    assert rows[1].search_supported and rows[1].reachable and rows[1].search_results==0
    assert rows[2].search_supported and not rows[2].reachable and 'тайм-аут' in rows[2].error
    assert 'private' not in rows[2].error


def test_cached_system_ip_skips_failing_cloudflare_ip(monkeypatch):
    nd.configure_dns_mode('auto')
    with nd._CACHE_LOCK:nd._ROUTE_HINTS.clear()
    monkeypatch.setattr(nd,'_resolve',lambda *a:('192.0.2.1',))
    monkeypatch.setattr(nd,'_system_addresses',lambda *a:('192.0.2.2',))
    tried=[]
    class Connected:
        def getpeername(self):return ('192.0.2.2',443)
        def close(self):pass
    def connect(target, timeout=None):
        tried.append(target[0])
        if target[0]=='192.0.2.1':raise TimeoutError('cloudflare ip blocked')
        return Connected()
    monkeypatch.setattr(nd,'_ORIGINAL_CREATE_CONNECTION',connect)
    try:
        _,first=nd._connect_target_with_info('example.org',443,timeout=3.5)
        assert first['dns_provider']=='system (TCP fallback)'
        assert tried==['192.0.2.1','192.0.2.2']
        tried.clear()
        _,second=nd._connect_target_with_info('example.org',443,timeout=3.5)
        assert tried==['192.0.2.2']
        assert second['fallback_status']=='cached_system_route_success'
        nd.configure_dns_mode('cloudflare')
        assert not nd._ROUTE_HINTS
    finally:
        nd.configure_dns_mode('auto')
        with nd._CACHE_LOCK:nd._ROUTE_HINTS.clear()
