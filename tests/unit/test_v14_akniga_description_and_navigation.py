"""Regression against user-reported Akniga pages and browser navigation errors."""
from contextlib import contextmanager
from types import SimpleNamespace
import pytest
from audioknigi import akniga

URL = "https://akniga.org/lavkraft-govard-mify-ktulhu"
INTRO = (
    "Эти рассказы и повести — очень разные. События, описанные в них, происходят "
    "в самых разных местах — от далекого будущего и нашего времени, до глубокого "
    "прошлого, когда человек только зарождался, от далеких планет до маленьких "
    "американских захолустных городков, вплоть до средневековых замков. "
    "Эти рассказы очень разные в плане сюжета — одни из них напоминают легенды "
    "и притчи, другие — повествования самых разных людей о необычных и ужасных "
    "событиях, которые происходят с ними. Оптимистичные и наводящие печаль и "
    "безысходность, светлые и темные, порой — философские, порой — почти "
    "приключенческие. И все же их объединяет одно — все они принадлежат перу "
    "Говарда Филипса Лавкрафта, гениального американского писателя, обладавшего "
    "поистине уникальным воображением и создавшего эти небольшие литературные шедевры."
)
CONTENTS = "Говард Лавкрафт — Безымянный город. Говард Лавкрафт — Дагон"

@pytest.mark.parametrize("tail", [
    f"<br><br><b>Содержание</b><br>{CONTENTS}",
    f"<br><br>Содержание<br>{CONTENTS}",
    f"<p><strong>Содержание</strong></p><ol><li>{CONTENTS}</li></ol>",
    f"\nСодержание\n{CONTENTS}",
])
def test_myths_synopsis_does_not_swallow_table_of_contents(tail):
    html = f"""<html><head><meta property="og:description" content="Promo"></head>
    <div class="description__article-main">
    <div class="content__main__book--item--caption">Описание</div>
    <p>{INTRO}</p>{tail}</div></html>"""
    assert akniga._akniga_description(html) == INTRO


def test_ordinary_word_contents_does_not_truncate_prose():
    text = "Содержание этой истории раскрывается постепенно, когда герой приходит в деревню."
    html = f'<div class="description__article-main"><div class="content__main__book--item--caption">Описание</div>{text}</div>'
    assert akniga._akniga_description(html) == text


@pytest.mark.parametrize("mode,expected", [("auto", [False, True]), ("cloudflare", [False])])
def test_navigation_timeout_auto_only_falls_back_to_system_dns(monkeypatch, mode, expected):
    attempts = []
    closed = []
    class Page:
        def on(self, *args): pass
        def goto(self, url, **kwargs):
            if not attempts[-1]:
                raise RuntimeError('Page.goto: net::ERR_CONNECTION_TIMED_OUT at ' + url)
        def content(self):
            return '<section data-bid="123"></section><script>LIVESTREET_SECURITY_KEY = "abc"</script>'
    class Ctx:
        def new_page(self): return Page()
        def close(self): closed.append('context')
    class Browser:
        def new_context(self, **kwargs): return Ctx()
        def close(self): closed.append('browser')
    def launch(browser, *, use_system_dns=False):
        attempts.append(use_system_dns)
        return Browser()
    @contextmanager
    def playwright(): yield SimpleNamespace(chromium=object())
    monkeypatch.setattr(akniga, 'sync_playwright', playwright)
    monkeypatch.setattr(akniga, 'launch_playwright_chromium', launch)
    monkeypatch.setattr(akniga, 'current_dns_mode', lambda: mode)
    monkeypatch.setattr(akniga, 'user_proxy_enabled', lambda: False)
    monkeypatch.setattr(akniga, '_api_data', lambda *args: {'items': []})
    monkeypatch.setattr(akniga, '_find_hls', lambda *args: 'https://media.example.test/book.m3u8')
    monkeypatch.setattr(akniga, '_parse_api_book', lambda *args: 'book')
    if mode == 'auto':
        assert akniga.fetch_book(URL) == 'book'
    else:
        with pytest.raises(RuntimeError, match='ERR_CONNECTION_TIMED_OUT'):
            akniga.fetch_book(URL)
    assert attempts == expected
    assert closed == ['context', 'browser'] * len(expected)


def test_double_navigation_timeout_raises_safe_message(monkeypatch):
    @contextmanager
    def playwright(): yield SimpleNamespace(chromium=object())
    monkeypatch.setattr(akniga, 'sync_playwright', playwright)
    monkeypatch.setattr(akniga, 'current_dns_mode', lambda: 'auto')
    monkeypatch.setattr(akniga, 'user_proxy_enabled', lambda: False)
    monkeypatch.setattr(akniga, '_fetch_using_browser', lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError('Page.goto: net::ERR_CONNECTION_TIMED_OUT at https://akniga.org/private?token=secret')))
    with pytest.raises(RuntimeError, match='Akniga: страницу не удалось открыть') as err:
        akniga.fetch_book(URL)
    assert 'token=secret' not in str(err.value)


def test_app_errors_do_not_trigger_network_retry():
    assert not akniga._is_navigation_connection_error(RuntimeError('Page.goto: Timeout 30000ms exceeded'))
    assert not akniga._is_navigation_connection_error(RuntimeError('Page.goto: HTTP 403 Forbidden'))
    assert not akniga._is_navigation_connection_error(RuntimeError('Page.evaluate: net::ERR_CONNECTION_TIMED_OUT'))
