from pathlib import Path

import pytest
from audioknigi.models import Book, QueueItem, Track
from audioknigi.queue_manager import QueueMixin


def test_settings_sliders_opt_in_to_direct_track_click():
    text = Path('audioknigi/ui/settings_tab.py').read_text(encoding='utf-8')
    assert text.count('jump_on_click=True') >= 2


def test_slider_wrapper_has_direct_click_handler():
    text = Path('audioknigi/ui_kit.py').read_text(encoding='utf-8')
    assert 'def _jump_to_clicked_position' in text
    assert 'self.set(value)' in text
    assert 'return "break"' in text


class QueueHost(QueueMixin):
    def __init__(self, items):
        self.queue_items = list(items)


def test_finished_queue_item_stays_done_when_files_exist(tmp_path):
    mp3 = tmp_path / '01.mp3'
    mp3.write_bytes(b'ok')
    item = QueueItem(
        url='https://example.test/book',
        title='Книга',
        status='Готово',
        status_code='done',
        output_folder=str(tmp_path),
        completed_files=[str(mp3)],
    )
    host = QueueHost([item])
    assert host._revalidate_finished_queue_files() is False
    assert item.status == 'Готово'
    assert item.status_code == 'done'


def test_finished_queue_item_returns_to_pending_when_file_was_deleted(tmp_path):
    missing = tmp_path / '01.mp3'
    item = QueueItem(
        url='https://example.test/book',
        title='Книга',
        status='Готово',
        status_code='done',
        output_folder=str(tmp_path),
        completed_files=[str(missing)],
        last_error='old',
        transient=True,
    )
    host = QueueHost([item])
    assert host._revalidate_finished_queue_files() is True
    assert item.status == 'Ожидает'
    assert item.status_code == 'pending'
    assert item.last_error == ''
    assert item.transient is False


def test_finished_queue_item_returns_to_pending_for_zero_byte_file(tmp_path):
    empty = tmp_path / '01.mp3'
    empty.write_bytes(b'')
    item = QueueItem(
        url='https://example.test/book',
        status='Готово',
        status_code='done',
        output_folder=str(tmp_path),
        completed_files=[str(empty)],
    )
    host = QueueHost([item])
    assert host._revalidate_finished_queue_files() is True
    assert item.status_code == 'pending'


def test_queue_completion_snapshot_records_selected_non_skipped_mp3s(tmp_path):
    item = QueueItem(url='https://example.test/book')
    book = Book(
        url=item.url,
        title='Книга',
        tracks=[
            Track(index=1, file='u1', title='Один'),
            Track(index=2, file='u2', title='Два'),
            Track(index=3, file='u3', title='Три'),
        ],
    )
    host = QueueHost([item])
    host.runtime_use_templates = False
    host.runtime_naming_mode = 'number'
    host._track_filename = lambda _book, track: f'{track.index:02d}.mp3'
    host._remember_queue_outputs(item, book, [1, 2, 3], [2], tmp_path)
    assert item.output_folder == str(tmp_path)
    assert item.completed_files == [str(tmp_path / '01.mp3'), str(tmp_path / '03.mp3')]

def test_real_ttk_slider_track_click_jumps_to_clicked_value():
    import tkinter as tk
    from audioknigi.ui_kit import CTkSlider

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('Tk display is not available')
    try:
        root.geometry('600x140')
        value = tk.DoubleVar(value=0)
        slider = CTkSlider(
            root,
            from_=0,
            to=100,
            number_of_steps=100,
            jump_on_click=True,
            variable=value,
        )
        slider.pack(fill='x', padx=20, pady=35)
        root.update_idletasks()
        x, y = slider.coords(50)
        assert 'slider' not in str(slider.identify(x, y)).lower()
        slider.event_generate('<ButtonPress-1>', x=int(x), y=int(y))
        root.update()
        assert value.get() == pytest.approx(50.0, abs=0.6)
    finally:
        root.destroy()
