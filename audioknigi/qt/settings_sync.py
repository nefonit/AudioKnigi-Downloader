from __future__ import annotations

from collections.abc import Mapping

from ..core import DEFAULT_OUTPUT, safe_int


class SettingsSyncMixin:
    """Synchronize persisted settings into already-created Qt controls.

    Kept separate from the main window so the 4k+ line orchestration class can
    continue to shrink without changing widget ownership or signal wiring.
    """
    def _apply_settings_to_qt_controls(self):
        data = self.settings if isinstance(self.settings, Mapping) else {}
        if hasattr(self, "output_edit"):
            self.output_edit.setText(str(data.get("output_dir", DEFAULT_OUTPUT) or DEFAULT_OUTPUT))
        mappings = (
            ("theme_combo", data.get("theme", "system")),
            ("naming_combo", data.get("naming_mode", "number")),
            ("audio_preset_combo", data.get("audio_preset", "copy")),
            ("normalization_combo", data.get("normalization_mode", "off")),
            ("segment_count_combo", str(data.get("segment_count") or "auto")),
            ("segment_threshold_combo", safe_int(data.get("segment_threshold_mb", 16), 16)),
            ("auto_chunk_combo", safe_int(data.get("auto_chunk_min_kbytes_per_sec", 256), 256)),
        )
        for attr, value in mappings:
            self._set_combo_data(getattr(self, attr, None), value)
        if hasattr(self, "scale_spin"):
            self.scale_spin.setValue(max(80, min(200, safe_int(data.get("scale", 100), 100))))
        if hasattr(self, "event_sound_volume_slider"):
            self.event_sound_volume_slider.setValue(max(0, min(100, safe_int(data.get("event_sound_volume", 100), 100))))
        if hasattr(self, "language_combo"):
            self._set_combo_data(self.language_combo, data.get("language", "ru"))
        if hasattr(self, "ui_mode_combo"):
            self._set_combo_data(self.ui_mode_combo, data.get("ui_mode", "easy"))
        if hasattr(self, "bandwidth_spin"):
            try:
                self.bandwidth_spin.setValue(max(0.0, float(data.get("bandwidth_limit", 0.0) or 0.0)))
            except (TypeError, ValueError):
                self.bandwidth_spin.setValue(0.0)
        checks = (
            ("embed_tags_check", "embed_tags", True),
            ("sidecars_check", "save_sidecars", True),
            ("delete_source_check", "delete_source", True),
            ("playwright_check", "playwright_fallback_enabled", True),
            ("clipboard_auto_check", "clipboard_auto", True),
            ("parallel_single_source_check", "parallel_single_source", False),
            ("use_templates_check", "use_templates", False),
            ("abs_enabled_check", "abs_enabled", False),
            ("minimize_to_tray_check", "minimize_to_tray", True),
            ("event_sounds_check", "event_sounds_enabled", True),
            ("large_mode_check", "large_mode", False),
            ("hide_source_check", "hide_source", False),
        )
        for attr, key, default in checks:
            widget = getattr(self, attr, None)
            if widget is not None:
                widget.setChecked(bool(data.get(key, default)))
        texts = (
            ("folder_template_edit", "folder_template", "{Book_Title}"),
            ("track_template_edit", "track_template", "{Track_Number}.mp3"),
            ("abs_url_edit", "abs_url", ""),
            ("abs_api_key_edit", "abs_api_key", ""),
            ("abs_library_id_edit", "abs_library_id", ""),
        )
        for attr, key, default in texts:
            widget = getattr(self, attr, None)
            if widget is not None:
                widget.setText(str(data.get(key, default) or default))
        if hasattr(self, "player_volume_slider"):
            self.player_volume_slider.setValue(max(0, min(100, safe_int(data.get("player_volume", 80), 80))))
        if hasattr(self, "player_rate_combo"):
            try:
                rate = float(data.get("player_rate", 1.0) or 1.0)
            except (TypeError, ValueError):
                rate = 1.0
            self._set_combo_data(self.player_rate_combo, rate)
        if hasattr(self, "easy_output_edit"):
            self.easy_output_edit.setText(str(data.get("output_dir", DEFAULT_OUTPUT) or DEFAULT_OUTPUT))
        if hasattr(self, "book_output_edit"):
            self.book_output_edit.setText(str(data.get("output_dir", DEFAULT_OUTPUT) or DEFAULT_OUTPUT))
        audio = str(data.get("audio_preset", "copy") or "copy")
        norm = str(data.get("normalization_mode", "off") or "off")
        inferred_quality = "phone" if audio == "64k_mono" else ("normalize" if norm == "two_pass" else "standard")
        explicit_quality = str(data.get("quality_preset", "") or "").strip()
        quality = explicit_quality if explicit_quality in {"standard", "phone", "normalize"} else inferred_quality
        if hasattr(self, "quality_combo"):
            self._set_combo_data(self.quality_combo, quality)
        if hasattr(self, "easy_quality_combo"):
            self._set_combo_data(self.easy_quality_combo, quality)
        self._apply_large_mode()
        self._apply_source_visibility()


__all__ = ["SettingsSyncMixin"]
