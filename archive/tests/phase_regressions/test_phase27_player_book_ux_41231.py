from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "\n".join((ROOT / "audioknigi" / "qt" / name).read_text(encoding="utf-8") for name in ("main_window.py", "main_window_pages.py"))
PLAYER = (ROOT / "audioknigi" / "qt" / "player_mixin.py").read_text(encoding="utf-8")
SPEED = (ROOT / "audioknigi/qt/speed_graph.py").read_text(encoding="utf-8")
THEME = (ROOT / "audioknigi/qt/theme.py").read_text(encoding="utf-8")


def test_settings_save_is_persistent_footer_outside_category_stack():
    assert 'footer.setObjectName("settingsFooter")' in MAIN
    assert 'self.save_settings_button = QPushButton(self._l("Сохранить настройки"))' in MAIN
    assert 'page_layout.addWidget(footer)' in MAIN
    assert 'maintenance = group(integration_layout, self._l("Резервная копия"))' in MAIN
    assert 'QWidget#settingsFooter' in THEME


def test_player_chapter_placeholder_wraps_without_horizontal_scroll():
    assert 'self.player_chapter_list.setWordWrap(True)' in PLAYER
    assert 'ScrollBarAlwaysOff' in PLAYER
    assert 'Список глав появится\\nпосле открытия книги' in PLAYER


def test_player_can_open_folder_or_file_and_build_local_book():
    assert 'def open_book_folder_dialog(self):' in PLAYER
    assert 'def load_book_folder(self, folder: Path, start_file: Path | None = None' in PLAYER
    assert 'def _player_audio_files(self, folder: Path) -> list[Path]:' in PLAYER
    assert '".m4b"' in PLAYER
    assert 'startswith(("_source", "_repair_source"))' in PLAYER
    assert 'self.player_open_button = QPushButton(self._l("Открыть папку с книгой…"))' in PLAYER
    assert 'self.player_open_file_button = QPushButton(self._l("Открыть отдельный файл…"))' in PLAYER


def test_player_folder_loads_cover_metadata_and_natural_chapters():
    assert 'def _player_natural_sort_key(path: Path):' in PLAYER
    assert 'load_json(folder / "metadata.json", {})' in PLAYER
    assert 'def _player_folder_cover(self, folder: Path) -> Path | None:' in PLAYER
    assert 'self.player_chapter_list.addItem(item)' in PLAYER


def test_end_of_media_advances_to_next_local_chapter():
    block = PLAYER.split('def _player_completed(self, file_path: str):', 1)[1]
    assert 'index + 1 < len(files)' in block
    assert 'activate_ui=False' in block


def test_history_and_easy_listen_load_whole_folder():
    assert 'def history_listen(self):' in MAIN
    assert 'self.load_book_folder(folder, autoplay=True)' in MAIN
    listen_block = MAIN.split('def listen_last_completed_book(self):', 1)[1].split('def _wire_live_accessibility_feedback', 1)[0]
    assert 'self.load_book_folder(folder, autoplay=True)' in listen_block


def test_speed_graph_is_compact_until_transfer_starts():
    assert 'self.setFixedHeight(40)' in SPEED
    assert 'self._expanded_height = 72' in SPEED
    assert 'if value > 0.0' in SPEED
