from __future__ import annotations

from pathlib import Path

from audioknigi.providers import audioknigi_search

ROOT = Path(__file__).resolve().parents[2]


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_audioknigi_multi_author_prefix_is_removed_from_title() -> None:
    value = "Бурносов Юрий, Бурносова Татьяна - Тоннельная крыса"
    title, authors = audioknigi_search._split_multi_author_prefix(value)
    assert title == "Тоннельная крыса"
    assert authors == "Бурносов Юрий, Бурносова Татьяна"
    assert audioknigi_search._split_audioknigi_title(value) == (title, authors)


def test_multi_author_split_does_not_treat_ordinary_dash_title_as_multi_author() -> None:
    value = "Гарри Поттер — Философский камень"
    assert audioknigi_search._split_multi_author_prefix(value) == (value, "")


def test_audioknigi_page_hydration_merges_multi_author_prefix_with_structured_author() -> None:
    class Response:
        url = "https://audioknigi.com.ua/audio-test"
        text = ""
        content = (
            "<html><title>Бурносов Юрий, Бурносова Татьяна - Тоннельная крыса</title></html>"
        ).encode("utf-8")
        def raise_for_status(self):
            return None

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    result = audioknigi_search.SearchResult(
        title="Бурносов Юрий, Бурносова Татьяна - Тоннельная крыса",
        author="",
        url="https://audioknigi.com.ua/audio-test",
        source="audioknigi.com.ua",
    )
    hydrated = audioknigi_search._audioknigi_page_metadata(
        result,
        session_factory=Session,
        metadata_extractor=lambda _html, _fallback: (
            "Бурносова Татьяна - Тоннельная крыса",
            "Бурносов Юрий",
            "",
        ),
        extended_metadata_extractor=lambda _html: ("", "Чтец", "", ""),
    )
    assert hydrated.title == "Тоннельная крыса"
    assert "Бурносов Юрий" in hydrated.author
    assert "Бурносова Татьяна" in hydrated.author


def test_direct_audioknigi_analysis_imports_multi_author_normalizer() -> None:
    source = src("audioknigi/services/book_analysis_service.py")
    assert "_split_multi_author_prefix as _split_audioknigi_multi_author_prefix" in source
    assert "_merge_author_names as _merge_audioknigi_authors" in source
    assert "visible_title, visible_authors = _split_audioknigi_multi_author_prefix(title)" in source
    assert "metadata_book_title, metadata_prefix_authors = _split_audioknigi_multi_author_prefix(metadata_title)" in source


def test_visual_keyboard_focus_ring_covers_both_easy_and_advanced_controls() -> None:
    theme = src("audioknigi/qt/theme.py")
    required = (
        "QPushButton:focus",
        "QLineEdit:focus",
        "QComboBox:focus",
        "QPlainTextEdit:focus",
        "QTableView:focus",
        "QListWidget:focus",
        "QCheckBox:focus",
        "QSlider:focus",
        "QTabBar:focus",
    )
    for selector in required:
        assert selector in theme
    assert "3px solid #ffb000" in theme
    assert "2px solid #ffb000" in theme


def test_easy_mode_has_explicit_tab_chain_and_text_views_do_not_trap_tab() -> None:
    main = src("audioknigi/qt/main_window.py")
    pages = src("audioknigi/qt/main_window_pages.py")
    assert "def _configure_keyboard_tab_order" in main
    assert "QWidget.setTabOrder(current, following)" in main
    for identifier in (
        "self.easy_input", "self.easy_paste_button", "self.easy_action_button",
        "self.easy_quality_combo", "self.easy_output_edit", "self.easy_folder_button",
        "self.easy_download_button", "self.easy_search_table", "self.easy_narration_combo",
        "self.easy_description", "self.easy_open_listen_button", "self.easy_another_button",
        "self.tabs",
    ):
        assert identifier in main
    assert "self.easy_description.setTabChangesFocus(True)" in main
    assert "self.session_log.setTabChangesFocus(True)" in pages


def test_accessibility_audit_covers_easy_dynamic_reader_controls() -> None:
    audit = src("audioknigi/qt/accessibility_audit.py")
    required = audit.split("REQUIRED_ACCESSIBLE_IDS = (", 1)[1].split(")\n\n", 1)[0]
    focusable = audit.split("FOCUSABLE_ACCESSIBLE_IDS = (", 1)[1].split(")\n\n", 1)[0]
    for identifier in ("easy_narration_variant", "easy_book_description"):
        assert f'"{identifier}"' in required
        assert f'"{identifier}"' in focusable
