from __future__ import annotations

import json
from pathlib import Path

from audioknigi.core import extract_metadata_from_html
from audioknigi.downloader import BandwidthLimiter, DownloaderMixin
from audioknigi.knigavuhe import (
    _book_page_search_metadata,
    _description_from_html,
    _extract_narration_variants,
)
from audioknigi.models import Book
from audioknigi.poleknig import _canonical_book_url, _parse_playlist_objects, _person_key
from audioknigi.qt.settings_sync import SettingsSyncMixin
from audioknigi.services.book_analysis_service import AnalysisOptions, BookAnalysisService
from audioknigi.templates import template_values


def test_bandwidth_limiter_allows_missing_cancel_event():
    limiter = BandwidthLimiter(1000)
    limiter.tokens = 0
    limiter.consume(1, None)


def test_partial_cleanup_escapes_brackets_in_filename(tmp_path: Path):
    host = DownloaderMixin()
    target = tmp_path / ".Book [Part 1].full-source"
    part = target.with_suffix(target.suffix + ".part")
    segment = part.parent / (part.name + ".seg00")
    part.write_bytes(b"partial")
    segment.write_bytes(b"segment")
    host._cleanup_partial_download(target)
    assert not part.exists()
    assert not segment.exists()


def test_filter_complex_loudnorm_is_actually_injected(tmp_path: Path):
    class Host(DownloaderMixin):
        def __init__(self):
            self.command = None

        def _run_ffmpeg_capture(self, cmd, timeout=0):
            self.command = list(cmd)
            return json.dumps({
                "input_i": "-20.0",
                "input_lra": "4.0",
                "input_tp": "-2.0",
                "input_thresh": "-30.0",
                "target_offset": "0.1",
            })

    host = Host()
    source = tmp_path / "source.mp3"
    result = host._measure_loudnorm(
        source,
        filter_complex="[0:a]anull[mix]",
        map_label="[mix]",
        extra_inputs=[source],
    )
    graph = host.command[host.command.index("-filter_complex") + 1]
    assert "loudnorm=I=-16" in graph
    assert "[audioknigi_loudnorm_measure]" in graph
    assert "measured_I=-20.0" in result


def test_json_ld_title_has_priority_over_fallback_page_title():
    html = '''<script type="application/ld+json">{"@type":"Book","name":"Clean title","author":{"name":"Author"}}</script>'''
    title, author, _cover = extract_metadata_from_html(html, "Noisy title - site suffix")
    assert title == "Clean title"
    assert author == "Author"


def test_knigavuhe_title_keeps_author_and_reader_after_listen_marker():
    html = "<title>Книга (слушать аудиокнигу онлайн) - автор Лев Толстой, читает Иван Иванов</title>"
    meta = _book_page_search_metadata(html)
    assert meta == {"title": "Книга", "author": "Лев Толстой", "narrator": "Иван Иванов"}


def test_knigavuhe_description_handles_nested_div_and_meta_attribute_order():
    assert _description_from_html('<div class="bookDescription">Первая<div>вторая</div>третья</div>') == "Первая вторая третья"
    assert _description_from_html('<meta content="Описание" name="description">') == "Описание"


def test_knigavuhe_does_not_activate_variants_from_annotation_text():
    html = '''
    <div class="bookDescription">В описании сказано: есть и другие озвучки произведения.
      <a href="/book/not-a-variant/">Похожая книга</a>
    </div>
    <h2>Рекомендации</h2>
    '''
    variants = _extract_narration_variants(html, "https://knigavuhe.org/book/current/", "Книга", "Чтец")
    assert len(variants) == 1
    assert variants[0].current is True


def test_poleknig_accepts_scheme_less_url_and_person_order():
    assert _canonical_book_url("https://poleknig.com/", "poleknig.com/books/12345") == "https://poleknig.com/books/12345"
    assert _person_key("Александр Пушкин") == _person_key("Пушкин Александр")


def test_poleknig_js_literals_true_false_null_are_parsed():
    value = "[{'file':'/audio/a.mp3','autostart':false,'duration':null}]"
    tracks = _parse_playlist_objects(value, "https://poleknig.com/books/1")
    assert len(tracks) == 1
    assert tracks[0].file == "https://poleknig.com/audio/a.mp3"


def test_settings_sync_quality_is_defined_without_advanced_combo():
    class Combo:
        pass

    class Host(SettingsSyncMixin):
        def __init__(self):
            self.settings = {"audio_preset": "64k_mono"}
            self.easy_quality_combo = Combo()
            self.values = []

        def _set_combo_data(self, combo, value):
            self.values.append((combo, value))

        def _apply_large_mode(self):
            pass

        def _apply_source_visibility(self):
            pass

    host = Host()
    host._apply_settings_to_qt_controls()
    assert host.values[-1] == (host.easy_quality_combo, "phone")


def test_relative_cover_is_canonicalized_during_headless_analysis():
    service = BookAnalysisService(options=AnalysisOptions(fetch_cover=False, fetch_remote_size=False))
    book = service._parse_playlist_data(
        url="https://audioknigi.com.ua/audio-1-book/",
        html_text='<meta property="og:image" content="/covers/one.jpg">',
        page_title="Fallback",
        playlist_url="https://audioknigi.com.ua/files/list.pl.txt",
        playlist_text='[{"file":"/audio/one.mp3","title":"1"}]',
    )
    assert book.cover_url == "https://audioknigi.com.ua/covers/one.jpg"


def test_template_unknown_author_is_localized():
    book = Book(url="https://example.invalid", title="Book", tracks=[])
    assert template_values(book, language="en")["Author"] == "Без автора"
    assert template_values(book, language="de")["Author"] == "Без автора"


def test_media_key_dedup_tracks_message_source_instead_of_time_only():
    source = Path("audioknigi/qt/media_keys.py").read_text(encoding="utf-8")
    assert "source != self._last_dispatch_source" in source
    assert 'self._dispatch(callback_name, "hotkey")' in source
    assert 'self._dispatch(callback_name, "appcommand")' in source
