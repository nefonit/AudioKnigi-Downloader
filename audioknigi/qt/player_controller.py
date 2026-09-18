from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QApplication

from ..i18n import localize_runtime_text
from ..services.player_position_store import PlayerPositionStore


class QtPlayerController(QObject):
    """Accessible Qt Multimedia controller with legacy-compatible resume state."""

    sourceChanged = Signal(str)
    positionChanged = Signal(int, int)
    durationChanged = Signal(int)
    playbackStateChanged = Signal(str)
    seekableChanged = Signal(bool)
    message = Signal(str)
    error = Signal(str)
    completed = Signal(str)

    def __init__(self, *, store: PlayerPositionStore | None = None, parent=None) -> None:
        super().__init__(parent)
        self.store = store or PlayerPositionStore()
        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.current_path: Path | None = None
        self._pending_resume_ms = 0
        self._pending_autoplay = False
        self._resume_applied = False
        self._resume_after_stop_ms = 0
        self._at_end = False
        self._last_persisted_at = 0.0

        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.seekableChanged.connect(self._on_seekable_changed)
        self.player.errorOccurred.connect(self._on_error)

        self._save_timer = QTimer(self)
        self._save_timer.setInterval(4000)
        self._save_timer.timeout.connect(self.save_position)
        self._save_timer.start()

    def has_source(self) -> bool:
        return self.current_path is not None

    def load(self, file_path: str | Path, *, autoplay: bool = True) -> float:
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Аудиофайл не найден: {path}")

        if self.current_path is not None and self.current_path != path:
            self.save_position(force=True)

        self.current_path = path
        resume = self.store.saved_seconds(path)
        self._pending_resume_ms = max(0, int(round(resume * 1000.0)))
        self._pending_autoplay = bool(autoplay)
        self._resume_applied = False
        self._resume_after_stop_ms = 0
        self._at_end = False
        self._last_persisted_at = 0.0
        self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self.sourceChanged.emit(str(path))
        app = QApplication.instance()
        language = str(app.property("audioknigi_language") or "ru") if app is not None else "ru"
        if resume >= 3.0:
            self.message.emit(localize_runtime_text(
                language,
                f"Файл загружен. Продолжение с сохранённой позиции {int(resume)} секунд.",
            ))
        else:
            self.message.emit(localize_runtime_text(language, f"Файл загружен: {path.name}"))
        return resume

    def _apply_resume_and_autoplay(self) -> None:
        if self.current_path is None:
            return
        duration = max(0, int(self.player.duration()))
        if duration > 0 and self._pending_resume_ms >= max(0, duration - 3000):
            self._pending_resume_ms = 0
            self.store.clear(self.current_path)
        if not self._resume_applied:
            if self._pending_resume_ms > 0 and not bool(self.player.isSeekable()):
                # Windows Media Foundation can emit Loaded/Buffered before seek
                # support is ready.  Starting at zero here would lose resume.
                return
            self._resume_applied = True
            if self._pending_resume_ms > 0:
                self.player.setPosition(self._pending_resume_ms)
        if self._pending_autoplay:
            self._pending_autoplay = False
            self.player.play()

    @Slot()
    def play(self) -> None:
        if self.current_path is None:
            self.message.emit("Сначала выберите аудиофайл.")
            return
        if self._at_end or self.player.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self._at_end = False
        elif self._resume_after_stop_ms > 0 and self.player.position() < 1000:
            self.player.setPosition(self._resume_after_stop_ms)
        self._resume_after_stop_ms = 0
        self.player.play()

    @Slot()
    def pause(self) -> None:
        if self.current_path is None:
            return
        self.player.pause()
        self.save_position(force=True)

    @Slot()
    def toggle_play_pause(self) -> None:
        if self.current_path is None:
            self.message.emit("Сначала выберите аудиофайл.")
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    @Slot()
    def stop(self) -> None:
        if self.current_path is None:
            return
        position = max(0, int(self.player.position()))
        self.save_position(force=True)
        # Do not setPosition() immediately after stop(): with the FFmpeg backend
        # the asynchronous transition to StoppedState can race that seek. Keep
        # the resume point in controller state and apply it immediately before
        # the next Play instead.
        self._resume_after_stop_ms = 0 if self._at_end else (position if position >= 3000 else 0)
        self.player.stop()

    def seek(self, position_ms: int) -> None:
        if self.current_path is None:
            return
        duration = max(0, int(self.player.duration()))
        target = max(0, int(position_ms))
        if duration > 0:
            target = min(target, duration)
        self._resume_after_stop_ms = target if self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState else 0
        self._at_end = False
        self.player.setPosition(target)
        # Keyboard auto-repeat can call seek dozens of times per second. Use
        # the existing persistence throttle instead of forcing a disk write for
        # every slider step; pause/stop/shutdown still flush immediately.
        self.save_position(force=False, explicit_seconds=target / 1000.0)

    def set_volume(self, value: int) -> None:
        self.audio_output.setVolume(max(0, min(100, int(value))) / 100.0)

    def volume(self) -> int:
        return int(round(float(self.audio_output.volume()) * 100.0))

    def set_rate(self, value: float) -> None:
        self.player.setPlaybackRate(max(0.5, min(3.0, float(value))))

    def rate(self) -> float:
        return float(self.player.playbackRate())

    def save_position(self, *, force: bool = False, explicit_seconds: float | None = None) -> None:
        if self.current_path is None or not self._resume_applied or self._at_end:
            return
        now = time.monotonic()
        if not force and now - self._last_persisted_at < 3.5:
            return
        if explicit_seconds is not None:
            position_seconds = max(0.0, float(explicit_seconds))
        else:
            position_ms = max(0, int(self.player.position()))
            # QMediaPlayer resets position() to zero after Stop. Preserve the
            # controller's remembered stop position so a timer/shutdown write
            # cannot delete the resume entry that stop() just saved.
            if (
                position_ms < 1000
                and self._resume_after_stop_ms > 0
                and self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState
            ):
                position_ms = int(self._resume_after_stop_ms)
            position_seconds = position_ms / 1000.0
        duration_seconds = max(0, int(self.player.duration())) / 1000.0
        self.store.update(self.current_path, position_seconds, duration_seconds)
        self._last_persisted_at = now

    def suspend_position_persistence(self) -> None:
        """Pause periodic writes while profile files are atomically replaced."""
        self.save_position(force=True)
        self._save_timer.stop()

    def reload_position_store(self) -> None:
        self.store.reload()

    def resume_position_persistence(self) -> None:
        if not self._save_timer.isActive():
            self._save_timer.start()

    def shutdown(self) -> None:
        # Stop periodic writes first so no timer callback can race the final
        # persistence step.  Save the current position while the backend still
        # exposes it, then stop playback.
        self._save_timer.stop()
        try:
            self.save_position(force=True)
        finally:
            self.player.stop()

    @Slot(int)
    def _on_position_changed(self, position: int) -> None:
        self.positionChanged.emit(max(0, int(position)), max(0, int(self.player.duration())))

    @Slot(bool)
    def _on_seekable_changed(self, seekable: bool) -> None:
        self.seekableChanged.emit(bool(seekable))
        if seekable and self.current_path is not None and not self._resume_applied:
            self._apply_resume_and_autoplay()

    @Slot(int)
    def _on_duration_changed(self, duration: int) -> None:
        # Qt multimedia backends can emit provisional durations while loading
        # VBR/remote metadata. Never destroy a persisted resume point from this
        # provisional signal; validation happens only once media is Loaded/Buffered.
        duration = max(0, int(duration))
        self.durationChanged.emit(duration)
        self.positionChanged.emit(max(0, int(self.player.position())), duration)

    @Slot(object)
    def _on_playback_state_changed(self, state) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            name = "playing"
        elif state == QMediaPlayer.PlaybackState.PausedState:
            name = "paused"
            self.save_position(force=True)
        else:
            name = "stopped"
        self.playbackStateChanged.emit(name)

    @Slot(object)
    def _on_media_status_changed(self, status) -> None:
        if status in (
            QMediaPlayer.MediaStatus.LoadedMedia,
            QMediaPlayer.MediaStatus.BufferedMedia,
        ):
            self._apply_resume_and_autoplay()
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            path = self.current_path
            if path is not None:
                self.store.clear(path)
                self.completed.emit(str(path))
            self._pending_resume_ms = 0
            self._pending_autoplay = False
            self._resume_applied = True
            self._at_end = True
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            message = self.player.errorString() or "Qt не смог воспроизвести выбранный аудиофайл."
            self.error.emit(message)

    @Slot(object, str)
    def _on_error(self, _error, error_string: str) -> None:
        message = str(error_string or self.player.errorString() or "Ошибка воспроизведения")
        self.error.emit(message)


__all__ = ["QtPlayerController"]
