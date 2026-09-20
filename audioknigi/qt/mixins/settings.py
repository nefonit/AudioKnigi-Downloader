from __future__ import annotations

from PySide6.QtCore import QThread, QTimer, Slot, Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from ...brand import DISPLAY_NAME
from ...metadata import APP_VERSION
from ...core import DEFAULT_OUTPUT, safe_int
from ...config.settings import AppSettings, normalize_settings, save_app_settings
from ..theme import THEMES, apply_theme
from ..workers import AudiobookshelfWorker as _AudiobookshelfWorker

class SettingsUiMixin:
    """Settings behavior for :class:`AudioKnigiQtWindow`."""

    def _wire_output_dir_sync(self):
        if hasattr(self, "easy_quality_combo"):
            self.easy_quality_combo.currentIndexChanged.connect(self._easy_quality_preset_changed)
        edits = [
            getattr(self, name, None)
            for name in ("output_edit", "book_output_edit", "easy_output_edit")
        ]
        for edit in (item for item in edits if item is not None):
            edit.textChanged.connect(lambda text, source=edit: self._sync_output_dir_text(source, text))

    @Slot(int)
    def _easy_quality_preset_changed(self, _index: int):
        if getattr(self, "_syncing_quality", False):
            return
        preset = str(self.easy_quality_combo.currentData() or "standard")
        self._syncing_quality = True
        try:
            self._set_combo_data(self.quality_combo, preset)
            self._quality_preset_changed(self.quality_combo.currentIndex())
        finally:
            self._syncing_quality = False

    def _sync_output_dir_text(self, source, text: str):
        if getattr(self, "_syncing_output_dirs", False):
            return
        self._syncing_output_dirs = True
        try:
            edits = [
                getattr(self, name, None)
                for name in ("output_edit", "book_output_edit", "easy_output_edit")
            ]
            for edit in (item for item in edits if item is not None):
                if edit is not source and edit.text() != text:
                    edit.setText(text)
        finally:
            self._syncing_output_dirs = False
        self._schedule_unfinished_refresh()

    def _schedule_unfinished_refresh(self) -> None:
        timer = getattr(self, "_unfinished_refresh_timer", None)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(300)
            timer.timeout.connect(self._refresh_unfinished)
            self._unfinished_refresh_timer = timer
        timer.start()

    def _choose_output_dir(self, _checked=False, *, target=None):
        edit = target or getattr(self, "output_edit", None) or getattr(self, "easy_output_edit", None)
        start = edit.text().strip() if edit is not None else str(self.settings.get("output_dir", DEFAULT_OUTPUT))
        selected = QFileDialog.getExistingDirectory(self, self._l("Папка для аудиокниг"), start or str(DEFAULT_OUTPUT))
        if selected:
            if edit is not None:
                # textChanged synchronizes all three fields and schedules one
                # debounced unfinished-download scan. Avoid an immediate second
                # scan here, which is expensive on NAS/external drives.
                edit.setText(selected)

    def _preview_theme(self):
        theme = self.theme_combo.currentData() or "system"
        apply_theme(QApplication.instance(), theme)

    def _apply_saved_theme(self):
        theme = str(self.settings.get("theme", "system") or "system").lower()
        apply_theme(QApplication.instance(), theme if theme in THEMES else "system")

    def _set_combo_data(self, widget, value):
        if widget is None:
            return
        index = widget.findData(value)
        if index >= 0:
            widget.setCurrentIndex(index)

    @Slot(int)
    def _quality_preset_changed(self, _index: int):
        preset = self.quality_combo.currentData() if hasattr(self, "quality_combo") else "standard"
        if hasattr(self, "easy_quality_combo") and not getattr(self, "_syncing_quality", False):
            self._syncing_quality = True
            try:
                self._set_combo_data(self.easy_quality_combo, preset)
            finally:
                self._syncing_quality = False
        if not hasattr(self, "audio_preset_combo") or not hasattr(self, "normalization_combo"):
            return
        if preset == "phone":
            self._set_combo_data(self.audio_preset_combo, "64k_mono")
            self._set_combo_data(self.normalization_combo, "off")
        elif preset == "normalize":
            self._set_combo_data(self.audio_preset_combo, "128k_stereo")
            self._set_combo_data(self.normalization_combo, "two_pass")
        else:
            self._set_combo_data(self.audio_preset_combo, "copy")
            self._set_combo_data(self.normalization_combo, "off")

    def _settings_from_ui(self) -> dict:
        updated = dict(self.settings or {})
        output_dir = self.output_edit.text().strip() or str(DEFAULT_OUTPUT)
        quality_preset = self.quality_combo.currentData() or "standard"
        audio_preset = self.audio_preset_combo.currentData() or "copy"
        normalization_mode = self.normalization_combo.currentData() or "off"
        if self.current_ui_mode() == "easy":
            output_dir = self.easy_output_edit.text().strip() or output_dir
            # Changing the Easy quality combo already synchronizes the advanced
            # audio/normalization controls in _easy_quality_preset_changed().
            # Merely saving unrelated settings in Easy mode must not erase a
            # previously configured custom advanced audio profile.
            quality_preset = self.easy_quality_combo.currentData() or quality_preset
        updated.update({
            "output_dir": output_dir,
            "theme": self.theme_combo.currentData() or "system",
            "scale": int(self.scale_spin.value()),
            "player_volume": int(self.player_volume_slider.value()),
            "player_rate": float(self.player_rate_combo.currentData() or 1.0),
            "minimize_to_tray": bool(self.minimize_to_tray_check.isChecked()),
            "naming_mode": self.naming_combo.currentData() or "number",
            "audio_preset": audio_preset,
            "normalization_mode": normalization_mode,
            "normalize_audio": normalization_mode != "off",
            "embed_tags": bool(self.embed_tags_check.isChecked()),
            "save_sidecars": bool(self.sidecars_check.isChecked()),
            "delete_source": bool(self.delete_source_check.isChecked()),
            "playwright_fallback_enabled": bool(self.playwright_check.isChecked()),
            "clipboard_auto": bool(self.clipboard_auto_check.isChecked()),
            "parallel_single_source": bool(self.parallel_single_source_check.isChecked()),
            "segment_count": self.segment_count_combo.currentData() or "auto",
            "segment_threshold_mb": max(1, safe_int(self.segment_threshold_combo.currentData(), 16)),
            "auto_chunk_min_kbytes_per_sec": max(1, safe_int(self.auto_chunk_combo.currentData(), 256)),
            "bandwidth_limit": float(self.bandwidth_spin.value()),
            "use_templates": bool(self.use_templates_check.isChecked()),
            "folder_template": self.folder_template_edit.text().strip() or "{Book_Title}",
            "track_template": self.track_template_edit.text().strip() or "{Track_Number}.mp3",
            "abs_enabled": bool(self.abs_enabled_check.isChecked()),
            "abs_url": self.abs_url_edit.text().strip(),
            "abs_api_key": self.abs_api_key_edit.text().strip(),
            "abs_library_id": self.abs_library_id_edit.text().strip(),
            "quality_preset": quality_preset,
            "language": self.language_combo.currentData() or self.language,
            "ui_mode": self.current_ui_mode(),
            "event_sounds_enabled": bool(self.event_sounds_check.isChecked()),
            "event_sound_volume": int(self.event_sound_volume_slider.value()),
            "large_mode": bool(self.large_mode_check.isChecked()),
            "hide_source": bool(self.hide_source_check.isChecked()),
        })
        return updated

    @Slot()
    def preview_event_sound(self):
        """Play a real packaged event cue, not the Windows MessageBeep fallback."""
        played = self.event_sound_manager.play_media_only("search_complete", force=True)
        if played:
            self.set_status(self._l("Проверка встроенного звука события."))
        else:
            self.set_status(self._l("Не удалось воспроизвести встроенный звук события."), assertive=True)

    @Slot()
    def preview_system_sound(self):
        """Play the native Windows system notification cue."""
        played = self.event_sound_manager.play_system("app_ready")
        if played:
            self.set_status(self._l("Проверка системного звука Windows."))
        else:
            self.set_status(self._l("Системный звук Windows недоступен."), assertive=True)

    def _save_settings(self, _checked: bool = False, *, silent: bool = False):
        updated = self._settings_from_ui()
        updated = normalize_settings(updated)
        if save_app_settings(updated):
            self.settings = AppSettings.from_mapping(updated)
            self.language = str(updated.get("language", self.language) or self.language)
            self.event_sound_manager.configure(
                enabled=bool(updated.get("event_sounds_enabled", True)),
                volume=float(updated.get("event_sound_volume", 100) or 100) / 100.0,
                language=self.language,
            )
            self.set_ui_mode(str(updated.get("ui_mode", self.current_ui_mode()) or "easy"), persist=False)
            self._apply_large_mode()
            self._apply_source_visibility()
            self._refresh_unfinished()
            if not silent:
                self.set_status("Настройки сохранены. Масштаб применится после перезапуска приложения.")
            return True
        if not silent:
            self.set_status("Не удалось сохранить настройки.", assertive=True)
        return False

    @Slot()
    def test_audiobookshelf(self):
        if self._abs_thread is not None and self._abs_thread.isRunning():
            self.set_status("Проверка Audiobookshelf уже выполняется.")
            return
        url = self.abs_url_edit.text().strip()
        key = self.abs_api_key_edit.text().strip()
        if not url or not key:
            self.set_status("Для проверки нужны адрес Audiobookshelf и API key.", assertive=True)
            return
        self.abs_test_button.setEnabled(False)
        self.set_status("Проверяю соединение с Audiobookshelf…")
        thread = QThread(self)
        worker = _AudiobookshelfWorker(url, key)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._worker_ui_relay.audiobookshelf_finished, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._worker_ui_relay.audiobookshelf_thread_finished, Qt.ConnectionType.QueuedConnection)
        thread.finished.connect(thread.deleteLater)
        self._abs_thread = thread
        self._abs_worker = worker
        thread.start()

    @Slot(object)
    def _audiobookshelf_finished(self, result):
        kind, payload = result
        self.abs_test_button.setEnabled(True)
        if kind == "error":
            self.set_status("Audiobookshelf недоступен: " + str(payload), assertive=True)
            self._show_message(QMessageBox.Icon.Critical, "Audiobookshelf", str(payload))
            return
        libraries = payload if isinstance(payload, list) else []
        lines = []
        for item in libraries[:20]:
            if isinstance(item, dict):
                lines.append(f"{item.get('name', '—')} — {item.get('id', '')}")
        text = self._l("Соединение успешно.")
        if lines:
            text += "\n\n" + self._l("Библиотеки:") + "\n" + "\n".join(lines)
        self._show_message(QMessageBox.Icon.Information, "Audiobookshelf", text)
        self.set_status(f"Audiobookshelf доступен. Библиотек: {len(libraries)}.", assertive=True)

    @Slot()
    def _clear_abs_thread(self):
        self._abs_thread = None
        self._abs_worker = None
        if hasattr(self, "abs_test_button"):
            self.abs_test_button.setEnabled(True)

    def _show_about(self):
        self._show_message(
            QMessageBox.Icon.Information,
            "О программе",
            f"{DISPLAY_NAME} {APP_VERSION}\n\n"
            + self._l("Загрузчик аудиокниг с поиском, очередью, историей, встроенным плеером и поддержкой экранных дикторов.")
            + "\n\n"
            + self._l("Поддерживаемые источники: audioknigi.com.ua, knigavuhe.org и poleknig.com."),
        )


__all__ = ["SettingsUiMixin"]
