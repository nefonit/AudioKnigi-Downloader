from __future__ import annotations

from collections.abc import MutableMapping

import os
import re
import time
from pathlib import Path

from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget,
)

from ..core import DEFAULT_OUTPUT, fmt_time, load_json, safe_int
from ..models import Book, cover_cache_bytes
from .accessibility import announce, configure_accessible
from .player_controller import QtPlayerController


class PlayerUiMixin:
    """Player-tab construction, local-book discovery and playback actions."""

    def _build_player_tab(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(18, 14, 18, 14)
        outer.addStretch(1)
        center = QHBoxLayout()
        center.addStretch(1)
        card = QWidget(page)
        card.setObjectName("playerCard")
        card.setMaximumWidth(980)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        hero = QHBoxLayout()
        self.player_cover_label = QLabel("♫\n" + self._l("Нет обложки"))
        self.player_cover_label.setObjectName("coverPlaceholder")
        self.player_cover_label.setFixedSize(260, 260)
        self.player_cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_cover_label.setScaledContents(True)
        configure_accessible(self.player_cover_label, name="Обложка воспроизводимой книги", identifier="player_cover")
        hero.addWidget(self.player_cover_label)

        info = QVBoxLayout()
        self.player_book_title_label = QLabel(self._l("Аудиофайл не выбран"))
        self.player_book_title_label.setObjectName("playerTitle")
        self.player_book_title_label.setWordWrap(True)
        self.player_book_meta_label = QLabel(self._l("Откройте папку книги или отдельный аудиофайл."))
        self.player_book_meta_label.setObjectName("secondaryText")
        self.player_book_meta_label.setWordWrap(True)
        info.addWidget(self.player_book_title_label)
        info.addWidget(self.player_book_meta_label)
        self.player_file_label = QLabel(self._l("Аудиофайл не выбран."))
        self.player_file_label.setWordWrap(True)
        self.player_file_label.setObjectName("secondaryText")
        configure_accessible(self.player_file_label, name="Текущий аудиофайл", identifier="player_file")
        info.addWidget(self.player_file_label)
        open_row = QHBoxLayout()
        self.player_open_button = QPushButton(self._l("Открыть папку с книгой…"))
        self.player_open_button.setProperty("role", "primary")
        configure_accessible(self.player_open_button, name="Открыть папку с аудиокнигой", identifier="player_open_book")
        self.player_open_button.clicked.connect(self.open_book_folder_dialog)
        self.player_open_file_button = QPushButton(self._l("Открыть отдельный файл…"))
        configure_accessible(self.player_open_file_button, name="Открыть отдельный аудиофайл", identifier="player_open_file")
        self.player_open_file_button.clicked.connect(self.open_audio_file)
        open_row.addWidget(self.player_open_button)
        open_row.addWidget(self.player_open_file_button)
        open_row.addStretch(1)
        info.addLayout(open_row)

        chapter_label = QLabel(self._l("Главы книги"))
        chapter_label.setObjectName("sectionTitle")
        info.addWidget(chapter_label)
        self.player_chapter_list = QListWidget()
        self.player_chapter_list.setObjectName("playerChapters")
        self.player_chapter_list.setMinimumHeight(120)
        self.player_chapter_list.setWordWrap(True)
        self.player_chapter_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        configure_accessible(self.player_chapter_list, name="Главы текущей книги", identifier="player_chapters")
        self.player_chapter_list.itemActivated.connect(self._player_chapter_activated)
        self.player_chapter_list.itemClicked.connect(self._player_chapter_activated)
        self._set_player_chapter_placeholder()
        info.addWidget(self.player_chapter_list, 1)
        hero.addLayout(info, 1)
        card_layout.addLayout(hero)

        transport = QHBoxLayout()
        self.player_back_button = QPushButton(self._l("−30 с"))
        self.player_play_button = QPushButton(self._l("▶ Воспроизвести"))
        self.player_play_button.setProperty("role", "primary")
        self.player_play_button.setMinimumHeight(44)
        self.player_play_button.setMinimumWidth(180)
        self.player_forward_button = QPushButton(self._l("+30 с"))
        self.player_stop_button = QPushButton(self._l("Стоп"))
        self.player_restart_button = QPushButton(self._l("С начала"))
        for w in (self.player_back_button, self.player_play_button, self.player_forward_button, self.player_stop_button, self.player_restart_button):
            w.setEnabled(False)
        configure_accessible(self.player_back_button, name="Назад на 30 секунд", identifier="player_back_30")
        configure_accessible(self.player_play_button, name="Воспроизвести или поставить на паузу", identifier="player_play_pause")
        configure_accessible(self.player_forward_button, name="Вперёд на 30 секунд", identifier="player_forward_30")
        configure_accessible(self.player_stop_button, name="Остановить воспроизведение", identifier="player_stop")
        configure_accessible(self.player_restart_button, name="Перейти в начало аудиофайла", identifier="player_restart")
        self.player_back_button.clicked.connect(lambda: self._player_seek_relative(-30))
        self.player_play_button.clicked.connect(self._player_toggle)
        self.player_forward_button.clicked.connect(lambda: self._player_seek_relative(30))
        self.player_stop_button.clicked.connect(self._player_stop)
        self.player_restart_button.clicked.connect(self._player_restart)
        transport.addStretch(1)
        transport.addWidget(self.player_back_button)
        transport.addWidget(self.player_play_button)
        transport.addWidget(self.player_forward_button)
        transport.addWidget(self.player_stop_button)
        transport.addWidget(self.player_restart_button)
        transport.addStretch(1)
        card_layout.addLayout(transport)

        self.player_seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.player_seek_slider.setRange(0, 1)
        self.player_seek_slider.setSingleStep(5)
        self.player_seek_slider.setPageStep(30)
        self.player_seek_slider.setEnabled(False)
        configure_accessible(self.player_seek_slider, name="Позиция воспроизведения", identifier="player_seek")
        self.player_seek_slider.sliderPressed.connect(self._player_seek_pressed)
        self.player_seek_slider.sliderReleased.connect(self._player_seek_released)
        self.player_seek_slider.valueChanged.connect(self._player_seek_preview)
        self.player_time_label = QLabel("00:00 / 00:00")
        configure_accessible(self.player_time_label, name="Время воспроизведения", identifier="player_time")
        seek_row = QHBoxLayout()
        seek_row.addWidget(self.player_seek_slider, 1)
        seek_row.addWidget(self.player_time_label)
        card_layout.addLayout(seek_row)

        audio_row = QHBoxLayout()
        volume_label = QLabel(self._l("Громкость:"))
        self.player_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.player_volume_slider.setRange(0, 100)
        self.player_volume_slider.setSingleStep(5)
        self.player_volume_slider.setPageStep(10)
        self.player_volume_slider.setValue(max(0, min(100, safe_int(self.settings.get("player_volume", 80), 80))))
        configure_accessible(self.player_volume_slider, name="Громкость плеера", identifier="player_volume")
        volume_label.setBuddy(self.player_volume_slider)
        self.player_volume_value_label = QLabel(f"{self.player_volume_slider.value()}%")
        self.player_volume_value_label.setMinimumWidth(42)
        self.player_volume_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        configure_accessible(self.player_volume_value_label, name=self._l("Текущая громкость плеера"), identifier="player_volume_value")
        self.player_volume_slider.valueChanged.connect(self._player_volume_changed)
        self.player_volume_slider.sliderMoved.connect(self._on_player_volume_slider_moved)
        rate_label = QLabel(self._l("Скорость:"))
        self.player_rate_combo = QComboBox()
        for rate in (0.75, 1.0, 1.25, 1.5, 1.75, 2.0):
            self.player_rate_combo.addItem(f"{rate:g}×", rate)
        try:
            saved_rate = float(self.settings.get("player_rate", 1.0) or 1.0)
        except (TypeError, ValueError):
            saved_rate = 1.0
        rate_index = min(range(self.player_rate_combo.count()), key=lambda index: abs(float(self.player_rate_combo.itemData(index)) - saved_rate))
        self.player_rate_combo.setCurrentIndex(rate_index)
        configure_accessible(self.player_rate_combo, name="Скорость воспроизведения", identifier="player_rate")
        rate_label.setBuddy(self.player_rate_combo)
        self.player_rate_combo.currentIndexChanged.connect(self._player_rate_changed)
        audio_row.addWidget(volume_label)
        audio_row.addWidget(self.player_volume_slider, 1)
        audio_row.addWidget(self.player_volume_value_label)
        audio_row.addSpacing(18)
        audio_row.addWidget(rate_label)
        audio_row.addWidget(self.player_rate_combo)
        card_layout.addLayout(audio_row)

        self.player_status_label = QLabel(self._l("Плеер готов. Выберите файл или скачанную часть книги."))
        self.player_status_label.setObjectName("secondaryText")
        self.player_status_label.setWordWrap(True)
        configure_accessible(self.player_status_label, name="Состояние плеера", identifier="player_status")
        card_layout.addWidget(self.player_status_label)

        center.addWidget(card)
        center.addStretch(1)
        outer.addLayout(center)
        outer.addStretch(1)
        return page

    @Slot()
    def _player_seek_relative(self, seconds: int):
        if self.player_controller is None or not self.player_controller.has_source():
            return
        target_seconds = max(0, int(self.player_seek_slider.value()) + int(seconds))
        self.player_controller.seek(target_seconds * 1000)

    def _set_player_chapter_placeholder(self, text: str | None = None) -> None:
        if not hasattr(self, "player_chapter_list"):
            return
        if text is None:
            text = self._l("Список глав появится\nпосле открытия книги")
        self.player_chapter_list.clear()
        item = QListWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.player_chapter_list.addItem(item)

    @Slot(QListWidgetItem)
    def _player_chapter_activated(self, item):
        if item is None:
            return
        path_text = str(item.data(Qt.ItemDataRole.UserRole) or "").strip()
        if path_text:
            path = Path(path_text).expanduser()
            if path.is_file():
                # QListWidget can emit itemClicked and itemActivated for one
                # quick double-click/activation sequence. Preserve convenient
                # single-click playback while suppressing an immediate duplicate
                # load of the same chapter.
                try:
                    activation_key = str(path.resolve())
                except OSError:
                    activation_key = str(path)
                now = time.monotonic()
                previous = getattr(self, "_last_player_chapter_activation", None)
                if previous and previous[0] == activation_key and now - previous[1] < 0.45:
                    return
                self._last_player_chapter_activation = (activation_key, now)
                controller = getattr(self, "player_controller", None)
                current = getattr(controller, "current_path", None) if controller is not None else None
                if current is not None:
                    try:
                        if current.resolve() == path.resolve():
                            return
                    except OSError:
                        if current == path:
                            return
                files = list(getattr(self, "_player_book_files", []) or [])
                if path in files:
                    self._load_player_file(
                        path, autoplay=True, preserve_folder_context=True, activate_ui=False
                    )
                else:
                    self.load_book_folder(path.parent, start_file=path, autoplay=True)

    def _refresh_player_context(self, book: Book | None = None) -> None:
        if not hasattr(self, "player_chapter_list"):
            return
        current_path = None
        if self.player_controller is not None and self.player_controller.current_path is not None:
            try:
                current_path = self.player_controller.current_path.resolve()
            except Exception:
                current_path = self.player_controller.current_path
        candidates = [book, self.current_book, self.last_completed_book]
        chosen = None
        if current_path is not None:
            for candidate in candidates:
                if candidate is None:
                    continue
                for track in list(getattr(candidate, "tracks", []) or []):
                    local = str(getattr(track, "local_path", "") or "").strip()
                    if not local:
                        continue
                    try:
                        if Path(local).expanduser().resolve() == current_path:
                            chosen = candidate
                            break
                    except Exception:
                        pass
                if chosen is not None:
                    break
        if chosen is None and current_path is None:
            chosen = next((candidate for candidate in candidates if candidate is not None), None)

        self.player_cover_label.setPixmap(QPixmap())
        self.player_cover_label.setText("♫\n" + self._l("Нет обложки"))
        self._set_player_chapter_placeholder()
        if chosen is None:
            if current_path is not None:
                self.player_book_title_label.setText(current_path.stem)
                self.player_book_meta_label.setText(self._l("Локальный аудиофайл"))
            else:
                self.player_book_title_label.setText(self._l("Аудиофайл не выбран"))
                self.player_book_meta_label.setText(self._l("Откройте скачанную часть книги или любой аудиофайл."))
            return

        self.player_book_title_label.setText(str(chosen.title or self._l("Без названия")))
        meta = []
        if chosen.author:
            meta.append(self._l("Автор: {value}", value=chosen.author))
        if chosen.narrator:
            meta.append(self._l("Чтец: {value}", value=chosen.narrator))
        self.player_book_meta_label.setText(" • ".join(meta) if meta else self._l("Аудиокнига"))
        cover = cover_cache_bytes(getattr(chosen, "cover_cache", None))
        if cover:
            pix = QPixmap()
            if pix.loadFromData(cover):
                self.player_cover_label.setPixmap(pix)
                self.player_cover_label.setText("")
        tracks = list(getattr(chosen, "tracks", []) or [])
        if tracks:
            self.player_chapter_list.clear()
        else:
            self._set_player_chapter_placeholder(self._l("Для этой аудиокниги список глав пока недоступен"))
        current_row = -1
        local_book_files = []
        for row, track in enumerate(tracks):
            title = str(getattr(track, "title", "") or f"Часть {getattr(track, 'index', row + 1)}")
            item = QListWidgetItem(f"{int(getattr(track, 'index', row + 1)):02d}. {title}")
            local_text = str(getattr(track, "local_path", "") or "").strip()
            local = Path(local_text).expanduser() if local_text else None
            if local is not None and local.is_file():
                local_book_files.append(local)
                item.setData(Qt.ItemDataRole.UserRole, str(local))
                if current_path is not None:
                    try:
                        if local.resolve() == current_path:
                            current_row = row
                    except Exception:
                        pass
            else:
                item.setToolTip(self._l("Эта глава ещё не скачана"))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.player_chapter_list.addItem(item)
        self._player_book_files = local_book_files
        if current_row >= 0:
            self.player_chapter_list.setCurrentRow(current_row)

    def _init_player(self):
        self._player_seek_active = False
        self.player_controller = QtPlayerController(parent=self)
        self.player_controller.sourceChanged.connect(self._player_source_changed)
        self.player_controller.positionChanged.connect(self._player_position_changed)
        self.player_controller.durationChanged.connect(self._player_duration_changed)
        self.player_controller.playbackStateChanged.connect(self._player_state_changed)
        self.player_controller.seekableChanged.connect(self._player_seekable_changed)
        self.player_controller.message.connect(self._player_message)
        self.player_controller.error.connect(self._player_error)
        self.player_controller.completed.connect(self._player_completed)
        self.player_controller.set_volume(self.player_volume_slider.value())
        self.player_controller.set_rate(float(self.player_rate_combo.currentData() or 1.0))
        self._player_state_changed("stopped")

    def _selected_track(self):
        selection_model = self.track_table.selectionModel()
        if selection_model is None:
            return None
        rows = selection_model.selectedRows()
        if rows:
            return self.track_model.track_at(rows[0].row())
        current = self.track_table.currentIndex()
        return self.track_model.track_at(current.row()) if current.isValid() else None

    @Slot()
    def _update_selected_track_player_button(self, *_args):
        track = self._selected_track()
        path = Path(str(getattr(track, "local_path", "") or "")).expanduser() if track is not None else None
        self.play_selected_track_button.setEnabled(bool(path and path.is_file()))

    @Slot()
    def play_selected_track(self):
        track = self._selected_track()
        if track is None:
            self.set_status("Сначала выберите часть книги.", assertive=True)
            return
        path_text = str(getattr(track, "local_path", "") or "").strip()
        path = Path(path_text).expanduser() if path_text else None
        if path is None or not path.is_file():
            self._show_message(
                QMessageBox.Icon.Information,
                self._l("Файл не найден"),
                self._l(
                    "У выбранной части пока нет доступного локального файла. Сначала скачайте её "
                    "или откройте готовый аудиофайл на вкладке «Плеер»."
                ),
            )
            self.set_status("Локальный файл выбранной части пока недоступен.", assertive=True)
            return
        self.load_book_folder(path.parent, start_file=path, autoplay=True)

    @Slot()
    def open_book_folder_dialog(self):
        edit = getattr(self, "output_edit", None)
        start = (edit.text().strip() if edit is not None else "") or str(DEFAULT_OUTPUT)
        folder = QFileDialog.getExistingDirectory(self, self._l("Выберите папку с аудиокнигой"), start)
        if folder:
            self.load_book_folder(Path(folder), autoplay=True)

    @Slot()
    def open_audio_file(self):
        edit = getattr(self, "output_edit", None)
        start = (edit.text().strip() if edit is not None else "") or str(DEFAULT_OUTPUT)
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            self._l("Открыть аудиофайл"),
            start,
            self._l("Аудиофайлы (*.mp3 *.ogg *.wav *.flac *.m4a *.aac *.opus);;Все файлы (*)"),
        )
        if file_path:
            path = Path(file_path)
            self.load_book_folder(path.parent, start_file=path, autoplay=True)

    @staticmethod
    def _player_natural_sort_key(path: Path):
        return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", path.name)]

    def _player_audio_files(self, folder: Path) -> list[Path]:
        extensions = {".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".m4b"}
        try:
            files = [
                item for item in folder.iterdir()
                if item.is_file()
                and item.suffix.casefold() in extensions
                and not item.name.casefold().startswith(("_source", "_repair"))
            ]
        except OSError:
            return []
        return sorted(files, key=self._player_natural_sort_key)

    def _player_folder_metadata(self, folder: Path) -> dict:
        payload = load_json(folder / "metadata.json", {})
        return payload if isinstance(payload, dict) else {}

    def _player_folder_cover(self, folder: Path) -> Path | None:
        wanted = ("cover.jpg", "cover.jpeg", "cover.png", "folder.jpg", "folder.png", "front.jpg", "front.png")
        try:
            by_name = {item.name.casefold(): item for item in folder.iterdir() if item.is_file()}
        except OSError:
            return None
        for name in wanted:
            candidate = by_name.get(name)
            if candidate is not None:
                return candidate
        return None

    def load_book_folder(self, folder: Path, start_file: Path | None = None, *, autoplay: bool = True):
        folder = Path(folder).expanduser()
        files = self._player_audio_files(folder)
        if not files:
            self.set_status("В выбранной папке нет поддерживаемых аудиофайлов.", assertive=True)
            return
        resolved = {}
        for index, file_path in enumerate(files):
            try:
                resolved[file_path.resolve()] = index
            except OSError:
                resolved[file_path] = index
        target = files[0]
        if start_file is not None:
            start_file = Path(start_file).expanduser()
            try:
                start_key = start_file.resolve()
            except OSError:
                start_key = start_file
            if start_key in resolved:
                target = files[resolved[start_key]]

        self._player_book_folder = folder
        self._player_book_files = files
        metadata = self._player_folder_metadata(folder)
        self._player_local_metadata = metadata
        self.player_book_title_label.setText(str(metadata.get("title") or folder.name or target.stem))
        meta = []
        author = str(metadata.get("author") or "").strip()
        narrator = str(metadata.get("narrator") or "").strip()
        if author:
            meta.append(self._l("Автор: {value}", value=author))
        if narrator:
            meta.append(self._l("Чтец: {value}", value=narrator))
        self.player_book_meta_label.setText(
            " • ".join(meta)
            if meta
            else self._l("{count} глав(ы) • {folder}", count=len(files), folder=folder.name)
        )

        self.player_cover_label.setPixmap(QPixmap())
        cover_path = self._player_folder_cover(folder)
        if cover_path is not None:
            pix = QPixmap(str(cover_path))
            if not pix.isNull():
                self.player_cover_label.setPixmap(pix)
                self.player_cover_label.setText("")
            else:
                self.player_cover_label.setText("♫\n" + self._l("Нет обложки"))
        else:
            self.player_cover_label.setText("♫\n" + self._l("Нет обложки"))

        self.player_chapter_list.clear()
        target_row = 0
        chapter_titles = {}
        for row in list(metadata.get("tracks", []) or []):
            if isinstance(row, dict):
                try:
                    chapter_titles[int(row.get("index"))] = str(row.get("title") or "").strip()
                except (TypeError, ValueError):
                    pass
        for idx, file_path in enumerate(files):
            chapter_title = chapter_titles.get(idx + 1) or file_path.stem
            item = QListWidgetItem(f"{idx + 1:02d}. {chapter_title}")
            item.setData(Qt.ItemDataRole.UserRole, str(file_path))
            item.setToolTip(str(file_path))
            self.player_chapter_list.addItem(item)
            if file_path == target:
                target_row = idx
        self.player_chapter_list.setCurrentRow(target_row)
        self._load_player_file(target, autoplay=autoplay, preserve_folder_context=True)

    def _load_player_file(
        self, path: Path, *, autoplay: bool, preserve_folder_context: bool = False, activate_ui: bool = True
    ):
        controller = self.player_controller
        if controller is None:
            return
        if not preserve_folder_context:
            self._player_book_folder = None
            self._player_book_files = []
            self._player_local_metadata = {}
        try:
            resume = controller.load(path, autoplay=autoplay)
        except Exception as exc:
            self._player_error(str(exc))
            return
        if activate_ui:
            self.tabs.setCurrentIndex(self.TAB_PLAYER)
            self.player_play_button.setFocus(Qt.FocusReason.OtherFocusReason)
        if resume >= 3.0:
            self.player_status_label.setText(self._l("Продолжение с {time}.", time=fmt_time(resume)))
            self.set_status(f"Плеер: продолжаю {path.name} с {fmt_time(resume)}.")
        else:
            self.player_status_label.setText(self._l("Загружен файл: {name}", name=path.name))
            self.set_status(f"Плеер: загружен {path.name}.")

    @staticmethod
    def _player_path_identity(path: Path) -> str:
        try:
            value = str(Path(path).expanduser().resolve())
        except (OSError, RuntimeError, ValueError):
            value = str(Path(path).expanduser())
        value = value.replace("\\", "/")
        return value.casefold() if os.name == "nt" else value

    def _player_switch_chapter(self, delta: int) -> None:
        files = list(getattr(self, "_player_book_files", []) or [])
        controller = getattr(self, "player_controller", None)
        current = getattr(controller, "current_path", None) if controller is not None else None
        if not files or current is None:
            return
        current_key = self._player_path_identity(current)
        current_index = next(
            (index for index, candidate in enumerate(files) if self._player_path_identity(candidate) == current_key),
            0,
        )
        target_index = max(0, min(len(files) - 1, current_index + int(delta)))
        if target_index == current_index:
            return
        target = files[target_index]
        self._select_player_chapter_path(target)
        self._load_player_file(target, autoplay=True, preserve_folder_context=True, activate_ui=False)

    def media_play_pause(self) -> None:
        self._player_toggle()

    def media_next_track(self) -> None:
        self._player_switch_chapter(1)

    def media_previous_track(self) -> None:
        self._player_switch_chapter(-1)

    @Slot()
    def _player_toggle(self):
        if self.player_controller is not None:
            self.player_controller.toggle_play_pause()

    @Slot()
    def _player_stop(self):
        if self.player_controller is not None:
            self.player_controller.stop()
            self.set_status("Воспроизведение остановлено. Позиция сохранена.")

    @Slot()
    def _player_restart(self):
        if self.player_controller is None or not self.player_controller.has_source():
            return
        self.player_controller.seek(0)
        self.player_controller.play()
        self.set_status("Воспроизведение с начала.")

    @Slot()
    def _player_seek_pressed(self):
        self._player_seek_active = True

    @Slot()
    def _player_seek_released(self):
        self._player_seek_active = False
        if self.player_controller is not None:
            self.player_controller.seek(self.player_seek_slider.value() * 1000)
        self.set_status(f"Позиция: {fmt_time(self.player_seek_slider.value())}.")

    @Slot(int)
    def _player_seek_preview(self, value: int):
        # Always reflect the slider value. Keyboard changes do not emit
        # sliderPressed/sliderReleased, so limiting this to mouse dragging made
        # the time label stale for screen-reader/keyboard users.
        self.player_time_label.setText(
            f"{fmt_time(value)} / {fmt_time(self.player_seek_slider.maximum())}"
        )
        # Keyboard slider actions also need to seek immediately. Programmatic
        # playback updates are signal-blocked in _player_position_changed, while
        # mouse dragging remains deferred until sliderReleased.
        if (
            not getattr(self, "_player_seek_active", False)
            and self.player_seek_slider.hasFocus()
            and self.player_controller is not None
            and self.player_controller.has_source()
        ):
            self.player_controller.seek(int(value) * 1000)

    @Slot(int)
    def _on_player_volume_slider_moved(self, value: int):
        tooltip_fn = getattr(self, "_show_volume_tooltip", None)
        if callable(tooltip_fn):
            tooltip_fn(self.player_volume_slider, value)

    @Slot(int)
    def _player_volume_changed(self, value: int):
        percent = max(0, min(100, int(value)))
        if hasattr(self, "player_volume_value_label"):
            self.player_volume_value_label.setText(f"{percent}%")
        if isinstance(getattr(self, "settings", None), MutableMapping):
            self.settings["player_volume"] = percent
        if self.player_controller is not None:
            self.player_controller.set_volume(percent)

    @Slot(int)
    def _player_rate_changed(self, _index: int):
        rate = float(self.player_rate_combo.currentData() or 1.0)
        if isinstance(getattr(self, "settings", None), MutableMapping):
            self.settings["player_rate"] = rate
        if self.player_controller is not None:
            self.player_controller.set_rate(rate)
            self.player_status_label.setText(self._l("Скорость воспроизведения: {rate}×", rate=f"{rate:g}"))
            self.player_rate_combo.setAccessibleDescription(self._l("Текущая скорость {rate}×", rate=f"{rate:g}"))
            if self.player_rate_combo.hasFocus():
                announce(self.player_rate_combo, self._l("Скорость {rate}×", rate=f"{rate:g}"))

    def _select_player_chapter_path(self, path: Path) -> None:
        try:
            wanted = path.resolve()
        except OSError:
            wanted = path
        for row in range(self.player_chapter_list.count()):
            item = self.player_chapter_list.item(row)
            value = str(item.data(Qt.ItemDataRole.UserRole) or "").strip() if item is not None else ""
            if not value:
                continue
            candidate = Path(value).expanduser()
            try:
                candidate_key = candidate.resolve()
            except OSError:
                candidate_key = candidate
            if candidate_key == wanted:
                self.player_chapter_list.setCurrentRow(row)
                return

    @Slot(str)
    def _player_source_changed(self, file_path: str):
        media_filter = getattr(self, "_media_key_filter", None)
        if media_filter is not None:
            media_filter.set_global_enabled(bool(str(file_path or "").strip()))
        path = Path(file_path)
        self.player_file_label.setText(self._l("Файл: {name}", name=path.name))
        self.player_play_button.setEnabled(True)
        self.player_restart_button.setEnabled(True)
        self.player_back_button.setEnabled(True)
        self.player_forward_button.setEnabled(True)
        files = list(getattr(self, "_player_book_files", []) or [])
        if files:
            self._select_player_chapter_path(path)
        else:
            self._refresh_player_context()

    @Slot(int, int)
    def _player_position_changed(self, position: int, duration: int):
        if not getattr(self, "_player_seek_active", False):
            self.player_seek_slider.blockSignals(True)
            position_seconds = max(0, int(round(position / 1000.0)))
            self.player_seek_slider.setValue(min(position_seconds, max(1, self.player_seek_slider.maximum())))
            self.player_seek_slider.blockSignals(False)
        position_seconds = max(0, int(round(position / 1000.0)))
        duration_seconds = max(0, int(round(duration / 1000.0)))
        self.player_seek_slider.setAccessibleDescription(
            self._l("Текущая позиция {position} секунд из {duration} секунд", position=position_seconds, duration=duration_seconds)
        )
        self.player_time_label.setAccessibleDescription(
            self._l("{position} секунд из {duration} секунд", position=position_seconds, duration=duration_seconds)
        )
        self.player_time_label.setText(f"{fmt_time(position / 1000.0)} / {fmt_time(duration / 1000.0)}")

    @Slot(int)
    def _player_duration_changed(self, duration: int):
        duration = max(0, int(duration))
        duration_seconds = max(0, int(round(duration / 1000.0)))
        self.player_seek_slider.setRange(0, max(1, duration_seconds))
        self.player_seek_slider.setEnabled(duration_seconds > 0)

    @Slot(bool)
    def _player_seekable_changed(self, seekable: bool):
        self.player_seek_slider.setEnabled(bool(seekable) and self.player_seek_slider.maximum() > 1)

    @Slot(str)
    def _player_state_changed(self, state: str):
        has_source = self.player_controller is not None and self.player_controller.has_source()
        playing = state == "playing"
        paused = state == "paused"
        self.player_play_button.setEnabled(has_source)
        self.player_play_button.setText(self._l("Пауза") if playing else self._l("▶ Воспроизвести"))
        self.player_play_button.setAccessibleName(self._l("Пауза воспроизведения") if playing else self._l("Воспроизвести"))
        self.player_stop_button.setEnabled(has_source and (playing or paused))
        self.player_restart_button.setEnabled(has_source)
        self.player_back_button.setEnabled(has_source)
        self.player_forward_button.setEnabled(has_source)
        if playing:
            self.player_status_label.setText(self._l("Воспроизведение."))
        elif paused:
            self.player_status_label.setText(self._l("Пауза. Позиция сохранена."))

    @Slot(str)
    def _player_message(self, message: str):
        if message:
            message = self._rt(message)
            self.player_status_label.setText(message)
            self.set_status(message)

    @Slot(str)
    def _player_error(self, message: str):
        text = self._rt(str(message or "Ошибка воспроизведения"))
        self.player_status_label.setText(self._l("Ошибка: ") + text)
        self.set_status(self._l("Ошибка плеера: ") + text, assertive=True)
        self._show_message(QMessageBox.Icon.Critical, self._l("Ошибка плеера"), text)

    @Slot(str)
    def _player_completed(self, file_path: str):
        path = Path(file_path)
        files = list(getattr(self, "_player_book_files", []) or [])
        if files:
            try:
                current_key = path.resolve()
            except OSError:
                current_key = path
            for index, candidate in enumerate(files):
                try:
                    candidate_key = candidate.resolve()
                except OSError:
                    candidate_key = candidate
                if candidate_key == current_key and index + 1 < len(files):
                    next_path = files[index + 1]
                    self._select_player_chapter_path(next_path)
                    self._load_player_file(
                        next_path, autoplay=True, preserve_folder_context=True, activate_ui=False
                    )
                    self.player_status_label.setText(self._l("Следующая глава: {name}", name=next_path.stem))
                    self.set_status(f"Плеер: следующая глава — {next_path.stem}.")
                    return
        name = path.name
        self.player_status_label.setText(self._l("Книга завершена: {name}", name=name))
        self.set_status(f"Воспроизведение книги завершено: {name}", assertive=True)


__all__ = ["PlayerUiMixin"]
