from audioknigi.models import Book, MappingDataclass, Track
from audioknigi.templates import render_folder, render_track_filename


def test_mapping_base_serializes_safely():
    assert MappingDataclass().to_dict() == {}


def test_unknown_author_path_is_language_stable(tmp_path):
    book = Book(url="https://example.invalid", title="Book", author="")
    ru = render_folder(tmp_path, "{Author}/{Book_Title}", book, language="ru")
    en = render_folder(tmp_path, "{Author}/{Book_Title}", book, language="en")
    assert ru == en


def test_track_title_fallback_does_not_duplicate_number():
    book = Book(url="https://example.invalid", title="Book")
    track = Track(index=1, title="", file="https://example.invalid/1.mp3")
    name = render_track_filename("{Track_Number} - {Track_Title}.mp3", book, track)
    assert name != "01 - 01.mp3"
