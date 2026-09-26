from __future__ import annotations

from pathlib import Path

from audioknigi.providers import audioknigi_search

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_advanced_empty_book_state_owns_spare_vertical_space() -> None:
    pages = src("audioknigi/qt/main_window_pages.py")
    assert "intro.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)" in pages
    assert "url_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)" in pages
    assert "self.book_empty_state.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)" in pages
    assert "layout.addWidget(self.book_empty_state, 1)" in pages
    # After analysis the chapter table takes over the elastic workspace.
    assert "layout.addWidget(self.track_table, 1)" in pages


def test_easy_and_advanced_universal_inputs_are_wired_bidirectionally() -> None:
    main = src("audioknigi/qt/main_window.py")
    settings = src("audioknigi/qt/mixins/settings.py")
    assert "self._syncing_book_inputs = False" in main
    assert "self._wire_book_input_sync()" in main
    assert "def _wire_book_input_sync(self):" in settings
    assert 'for name in ("book_url_edit", "easy_input", "search_edit")' in settings
    assert "def _sync_book_input_text(self, source, text: str):" in settings
    assert "edit.setText(text)" in settings


def test_audioknigi_annotation_uses_real_synopsis_not_page_chrome() -> None:
    html = """
    <html><body>
      <div class="shortstory">
        <p>Тут можно слушать бесплатно Демченко Антон - Боярич. Исполнитель: Карпов Дмитрий,
        Жанр: Фантастика. Так же Вы можете слушать полную версию онлайн или прочесть
        краткое содержание, предисловие (аннотацию), описание и ознакомиться с отзывами.</p>
        <p>14 часов 32 минуты 26052</p>
        <p>Слушать эту аудиокнигу в приложении</p>
        <p>Добавляйте книги в android приложение Audiotales прямо с сайта.</p>
        <p>Автор:</p><p>Демченко Антон</p>
        <p>Исполнитель:</p><p>Карпов Дмитрий</p>
        <p>Серия:</p><p>Воздушный стрелок (1)</p>
        <p>Добавлено:</p><p>18.09.2019</p>
        <p>Жанры</p><p>Фэнтези Технофэнтези</p>
        <p>Характеристики</p><p>Приключенческое Психологическое</p>
        <h2>Демченко Антон - Боярич краткое содержание</h2>
        <p>Демченко Антон - Боярич - описание и краткое содержание,
        исполнитель: Карпов Дмитрий, слушайте бесплатно онлайн на сайте электронной
        библиотеки AudioKnigi.com.ua</p>
        <p>Говорят, жить надо так, чтобы после смерти боги предложили тебе повторить.
        Случай и воля древнего божества занесли героя в тело подростка.</p>
        <h2>Демченко Антон - Боярич слушать онлайн бесплатно</h2>
        <p>Плеер, скачать, отзывы и другая техническая информация.</p>
      </div>
    </body></html>
    """
    value = audioknigi_search._audioknigi_description_from_html(
        html, title="Боярич", author="Демченко Антон"
    )
    assert value.startswith("Говорят, жить надо так")
    assert "Случай и воля" in value
    folded = value.casefold()
    assert "audioknigi.com.ua" not in folded
    assert "исполнитель:" not in folded
    assert "добавлено:" not in folded
    assert "audiotales" not in folded
    assert "плеер" not in folded


def test_audioknigi_intro_phrase_does_not_start_annotation_capture() -> None:
    html = """
    <article class="shortstory">
      <p>Тут можно слушать бесплатно Книга. Также можно прочесть краткое содержание,
      предисловие, описание и отзывы.</p>
      <p>Автор: Автор Тестовый</p>
      <p>Исполнитель: Чтец Тестовый</p>
      <p>Добавлено: 24.09.2026</p>
      <h2>Автор Тестовый - Книга краткое содержание</h2>
      <p>Автор Тестовый - Книга - описание и краткое содержание, исполнитель:
      Чтец Тестовый, слушайте бесплатно онлайн на сайте электронной библиотеки
      AudioKnigi.com.ua</p>
      <p>Это настоящая аннотация книги без сведений о плеере и каталоге.</p>
      <h2>Автор Тестовый - Книга отзывы</h2>
      <p>Комментарий пользователя.</p>
    </article>
    """
    value = audioknigi_search._audioknigi_description_from_html(
        html, title="Книга", author="Автор Тестовый"
    )
    assert value == "Это настоящая аннотация книги без сведений о плеере и каталоге."


def test_audioknigi_semantic_fallback_still_accepts_clean_description() -> None:
    html = """
    <div class="book-description">
      Чистая аннотация о героях, конфликте и событиях произведения.
    </div>
    """
    value = audioknigi_search._audioknigi_description_from_html(
        html, title="Книга", author="Автор"
    )
    assert value == "Чистая аннотация о героях, конфликте и событиях произведения."
