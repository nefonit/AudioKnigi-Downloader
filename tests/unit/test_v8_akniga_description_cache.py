"""Pure offline regression coverage for Akniga synopsis and HLS resume."""
from pathlib import Path
import pytest
from audioknigi.akniga import _akniga_description, _parse_api_book
from audioknigi.download import hls_parallel
from audioknigi.core import Cancelled

URL = 'https://akniga.org/kozhin-oleg-snegurochka'
HLS = 'https://cdn.example.org/stream.m3u8?expires=5000&signature=test'
PAYLOAD = {'titleonly': 'Снегурочка', 'items': [
    {'title': 'Снегурочка', 'time_from_start': 0, 'time_finish': 2600}
]}
SEO = ('Аудиокнига «Снегурочка», читает Князев Владимир. '
       'Слушайте бесплатно онлайн. Рассказ-победитель первого в истории DARKER '
       'литературного конкурса «Чёртова дюжина».')
SYNOPSIS = ('Рассказ-победитель первого в истории DARKER литературного конкурса '
            '«Чёртова дюжина». Этнографическая экспедиция попадает в полузаброшенную '
            'деревню Маррь. Но реальность может оказаться гораздо страшнее сказки…')


def test_description_prefers_full_visible_annotation_over_truncated_seo_meta():
    page = f'''<html><head><meta name="description" content="{SEO}"></head><body>
    <h2>Описание</h2><div><p>{SYNOPSIS}</p></div><h2>Комментарии</h2>
    </body></html>'''
    book = _parse_api_book(URL, page, PAYLOAD, HLS)
    assert book.description == SYNOPSIS
    assert not book.description.startswith('Аудиокнига')
    assert 'Этнографическая экспедиция' in book.description


def test_description_accepts_structured_block_with_heading():
    page = f'''<div class="book__description"><h3>Описание</h3><p>{SYNOPSIS}</p></div>'''
    assert _akniga_description(page) == SYNOPSIS


def test_description_removes_seo_prefix_from_fallback_but_keeps_prose():
    page = f'<meta content="{SEO}" property="og:description">'
    assert _akniga_description(page).startswith('Рассказ-победитель')
    assert 'Слушайте бесплатно' not in _akniga_description(page)



def test_description_joins_paragraphs_until_next_heading():
    page = ("<h2>Описание</h2><p>Экспедиция входит в деревню Маррь, "
            "где давно никто не бывал.</p><p>Местные жители хранят страшную тайну.</p>"
            "<h2>Комментарии</h2><p>Это комментарий, а не описание.</p>")
    value = _akniga_description(page)
    assert "Экспедиция входит" in value
    assert "Местные жители" in value
    assert "Это комментарий" not in value

def test_description_does_not_modify_real_intro():
    text = 'На окраине деревни все шептались: слушайте бесплатно онлайн рассказы детей.'
    assert _akniga_description(f'<meta name="description" content="{text}">') == text


# Real Akniga markup provided by a user: the book description coexists with
# a collection banner in the same page. Collection metadata is not synopsis.
FULL_SNEG = (
    "Рассказ-победитель первого в истории DARKER литературного конкурса «Чёртова дюжина». "
    "Этнографическая экспедиция попадает в полузаброшенную деревню Маррь, "
    "связанную с первыми упоминаниями легенды о Снегурочке. "
    "Но реальность может оказаться гораздо страшнее привычной всем сказки…"
)
COLLECTION = "Входит в подборку В деревне явно творится какая-то хрень 16 аудиокниг"


def test_akniga_user_book_block_beats_collection_membership_and_seo():
    markup = f'''<html><head><meta name="description" content="{SEO}"></head><body>
    <div itemprop="description">{COLLECTION}</div>
    <div class="description__article-main">
      <div class="content__main__book--item--caption">Описание</div>
      {FULL_SNEG}
    </div>
    </body></html>'''
    book = _parse_api_book(URL, markup, PAYLOAD, HLS)
    assert book.description == FULL_SNEG
    assert "Входит в подборку" not in book.description
    assert "Слушайте бесплатно" not in book.description


def test_akniga_current_description_container_removes_caption_not_prose():
    html = f'''<div class="description__article-main">
      <div class="content__main__book--item--caption">Описание</div>
      <p> {FULL_SNEG} </p>
    </div>'''
    assert _akniga_description(html) == FULL_SNEG


def test_akniga_collection_banner_not_accepted_as_book_synopsis():
    markup = f'''<div itemprop="description">{COLLECTION}</div>
    <meta name="description" content="{SEO}">'''
    assert _akniga_description(markup).startswith("Рассказ-победитель")


def test_akniga_collection_only_metadata_does_not_become_synopsis():
    assert _akniga_description(f'<meta name="description" content="{COLLECTION}">') == ""


def test_akniga_disambiguates_multiple_captioned_blocks():
    markup = f'''<div class="description__article-main">
      <div class="content__main__book--item--caption">Подборка</div>{COLLECTION}</div>
      <div class="description__article-main">
      <div class="content__main__book--item--caption">Описание</div>{FULL_SNEG}</div>'''
    assert _akniga_description(markup) == FULL_SNEG


PLAYLIST = b'#EXTM3U\n#EXT-X-VERSION:3\n#EXTINF:4.0,\nfirst.ts\n#EXTINF:4.0,\nsecond.ts\n#EXT-X-ENDLIST\n'


def test_cache_reuses_completed_segment_after_cancel(monkeypatch, tmp_path):
    monkeypatch.setattr(hls_parallel, '_get_bytes', lambda *_a, **_kw: PLAYLIST)
    calls = []
    should_cancel = [True]
    def download(index, url, dest, *_args, **_kwargs):
        calls.append(index)
        if index == 1 and should_cancel[0]:
            raise Cancelled('user cancelled')
        dest.write_bytes(f'segment {index}'.encode())
        return index, dest.stat().st_size
    monkeypatch.setattr(hls_parallel, '_download_segment', download)
    cache = tmp_path / 'persistent'
    with pytest.raises(Cancelled):
        hls_parallel.stage_hls_vod(HLS, tmp_path / 'stage1', referer='',
            user_agent='test', check_cancel=lambda: None,
            on_progress=lambda *_: None, max_workers=1, segment_cache_dir=cache)
    assert calls == [0, 1]
    should_cancel[0] = False
    result = hls_parallel.stage_hls_vod(HLS, tmp_path / 'stage2', referer='',
        user_agent='test', check_cancel=lambda: None,
        on_progress=lambda *_: None, max_workers=1, segment_cache_dir=cache)
    assert result.is_file()
    assert calls == [0, 1, 1]  # first segment reused; second downloaded
    assert (tmp_path / 'stage2' / 'seq000000.ts').read_bytes() == b'segment 0'
    assert all('expires=5000' not in str(path) for path in cache.rglob('*'))


def test_cache_rejects_modified_segments_and_changed_playlist(monkeypatch, tmp_path):
    payload = [PLAYLIST]
    monkeypatch.setattr(hls_parallel, '_get_bytes', lambda *_a, **_kw: payload[0])
    calls = []
    def download(index, url, dest, *_a, **_kw):
        calls.append(index)
        dest.write_bytes(f'valid {index}'.encode())
        return index, dest.stat().st_size
    monkeypatch.setattr(hls_parallel, '_download_segment', download)
    cache = tmp_path / 'cache'
    def stage(n):
        return hls_parallel.stage_hls_vod(HLS, tmp_path / f's{n}', referer='',
            user_agent='test', check_cancel=lambda: None,
            on_progress=lambda *_: None, max_workers=1, segment_cache_dir=cache)
    stage(1)
    segment = next(cache.glob('*/seq000000.ts'))
    segment.write_bytes(b'corrupt')
    stage(2)
    assert calls.count(0) == 2
    assert calls.count(1) == 1
    payload[0] = PLAYLIST.replace(b'#EXT-X-VERSION:3', b'#EXT-X-VERSION:4')
    stage(3)
    assert calls.count(0) == 3
    assert calls.count(1) == 2
