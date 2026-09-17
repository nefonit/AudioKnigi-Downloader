from types import SimpleNamespace

from audioknigi.actions import ActionsMixin
from audioknigi.i18n import STRINGS, tr
from audioknigi.knigavuhe import (
    _extract_call_argument,
    _extract_narration_variants,
    parse_book_html,
    parse_search_results,
)
from audioknigi.library_visuals import LibraryVisualMixin
from audioknigi.models import SearchResult
from audioknigi.sources import is_supported_url, normalize_supported_url, source_key


def test_bookcontroller_first_argument_stops_before_second_js_argument():
    payload = '{"book":{"name":"Demo"},"playlist":[]}'
    source = f"before BookController.enter({payload}, window.playerConfig); after"
    assert _extract_call_argument(source) == payload


def test_bookcontroller_json_slash_escaping_is_left_to_json_decoder():
    payload = (
        '{"book":{"name":"Demo","authors":[{"name":"Author"}]},'
        '"playlist":[{"url":"https:\\/\\/cdn.example\\/audio\\/01.mp3","title":"1"}]}'
    )
    book = parse_book_html(
        f"<script>BookController.enter({payload}, {{mode:'x'}});</script>",
        "https://knigavuhe.org/book/demo/",
    )
    assert book.tracks[0].file == "https://cdn.example/audio/01.mp3"


def test_old_narration_layout_does_not_treat_author_as_reader():
    html = """
    <h2>Другие озвучки</h2>
    <a href="/book/other/">Demo</a>
    <a href="/author/author-name/">Имя Автора</a>
    <a href="/reader/reader-name/">Имя Чтеца</a>
    <h2>Рекомендации</h2>
    """
    variants = _extract_narration_variants(
        html,
        "https://knigavuhe.org/book/current/",
        title="Demo",
        current_narrator="Текущий Чтец",
    )
    assert len(variants) == 2
    assert variants[1].narrator == "Имя Чтеца"


def test_search_card_semantic_classes_can_move_off_div_tags():
    html = """
    <div class="bookitem">
      <a class="bookitem_name is_black" href="/book/demo/">Название книги</a>
      <span class="icon_author">Автор Книги</span>
      <span class="icon_reader">Чтец Книги</span>
    </div>
    """
    items = parse_search_results(html)
    assert len(items) == 1
    assert (items[0].title, items[0].author, items[0].narrator) == (
        "Название книги", "Автор Книги", "Чтец Книги"
    )


def test_supported_links_without_scheme_are_normalized():
    raw = "m.knigavuhe.org/book/demo/"
    assert source_key(raw) == "knigavuhe"
    assert normalize_supported_url(raw) == "https://knigavuhe.org/book/demo/"
    assert is_supported_url(raw) is True
    assert normalize_supported_url("audioknigi.com.ua/audio-demo") == "https://audioknigi.com.ua/audio-demo"


def test_search_result_keeps_mapping_compatibility():
    item = SearchResult(title="Book", author="Author", url="https://example.test/")
    assert item["title"] == "Book"
    assert item.get("author") == "Author"
    assert item.get("missing", "fallback") == "fallback"


def test_library_visual_cache_self_initializes():
    mix = LibraryVisualMixin()
    item = SimpleNamespace(cover_cache=None, url="https://example.test/book", title="Book")
    assert mix._queue_cover_photo(item) is None
    assert mix._queue_cover_images == {}


def test_capture_runtime_options_survives_partial_ui_state():
    dummy = SimpleNamespace(
        settings={},
        runtime_output_dir="C:/Books",
        runtime_output_mode="mp3",
        runtime_audio_preset="copy",
        runtime_normalization_mode="off",
        runtime_ui_mode="easy",
        _runtime_options_generation=0,
    )
    ActionsMixin._capture_runtime_options(dummy)
    assert dummy.runtime_output_dir == "C:/Books"
    assert dummy.runtime_output_mode == "mp3"
    assert dummy.runtime_normalization_mode == "off"
    assert dummy._runtime_options_generation == 1


def test_help_and_welcome_strings_exist_in_all_languages():
    required = {
        "welcome_to", "help_window_title", "help_center", "copy_error_report",
        "help_download_title", "help_download_body", "help_shortcuts_title",
    }
    for language in ("ru", "uk", "de", "en"):
        assert required <= set(STRINGS[language])
        assert "{brand}" not in tr(language, "welcome_to", brand="AudioKnigi")
    assert tr("en", "help_center") == "Help Center"
    assert tr("de", "help_window_title") == "Hilfe"
