from __future__ import annotations

"""Qt-native application event sounds.

Short MP3 cues are played with QMediaPlayer/QAudioOutput, so the Qt runtime does
not need pygame.  Windows MessageBeep remains the service/fallback cue, matching
the old user-visible behavior without the old audio dependency.
"""

import os
import queue
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QUrl, Signal, Slot, Qt
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from ..core import resource_path, safe_float

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None


EVENT_FILES = {
    "download_start": "download_in_progress.mp3",
    "download_complete": "download_complete.mp3",
    "error": "error.mp3",
    "link_pasted": "link_pasted.mp3",
    "queue_item_added": "queue_item_added.mp3",
    "search_complete": "search_complete.mp3",
    "queue_complete": "queue_complete.mp3",
    "queue_started": "queue_started.mp3",
    "download_cancelled": "download_cancelled.mp3",
    "download_resumed": "download_resumed.mp3",
    "download_paused": "download_paused.mp3",
    "book_not_found": "book_not_found.mp3",
    "book_found": "book_found.mp3",
    "update_available": "update_available.mp3",
    "recovery_started": "recovery_started.mp3",
    "files_already_downloaded": "files_already_downloaded.mp3",
    "narration_changed": "narration_changed.mp3",
}
SYSTEM_SOUND_ROLES = {
    "download_start": "ok", "download_complete": "asterisk", "error": "hand",
    "link_pasted": "ok", "queue_item_added": "ok", "search_complete": "asterisk",
    "queue_complete": "asterisk", "queue_started": "ok", "download_cancelled": "exclamation",
    "download_resumed": "ok", "download_paused": "exclamation", "book_not_found": "exclamation",
    "book_found": "asterisk", "update_available": "asterisk", "recovery_started": "asterisk",
    "files_already_downloaded": "asterisk", "narration_changed": "ok", "app_ready": "asterisk",
    "attention": "exclamation", "completed_files_missing": "exclamation",
}
SYSTEM_ONLY_EVENTS = frozenset({"app_ready", "attention", "completed_files_missing"})
SUPPORTED_SOUND_EVENTS = frozenset(EVENT_FILES) | SYSTEM_ONLY_EVENTS
_MAX_CACHED_MEDIA_PLAYERS = 3


class QtEventSoundManager(QObject):
    _queued_play = Signal(str, bool)

    def __init__(self, parent=None, *, enabled=True, volume=1.0, language="ru"):
        super().__init__(parent)
        self.enabled = bool(enabled)
        self.volume = self._clamp(volume)
        self.language = self._lang(language)
        self._queued_play.connect(self._play_queued, Qt.ConnectionType.QueuedConnection)
        # Keep one player per cue. QMediaPlayer.setSource() is asynchronous on
        # Windows; rapidly swapping a single player's source can poison the
        # multimedia pipeline when two UI events arrive close together.
        self._players: dict[str, tuple[QMediaPlayer, QAudioOutput]] = {}
        self._player_order: list[str] = []
        self._pending_media_callbacks: dict[str, object] = {}
        # MessageBeep can block on some Windows/RDP audio stacks. A dedicated
        # daemon worker keeps it completely outside the Qt GUI thread and cannot
        # keep interpreter shutdown alive.
        self._system_sound_queue: queue.Queue[int | None] = queue.Queue(maxsize=8)
        self._system_shutdown = threading.Event()
        self._system_thread: threading.Thread | None = None
        if winsound is not None and os.name == "nt":
            self._system_thread = threading.Thread(
                target=self._system_sound_worker,
                name="qt-system-sound",
                daemon=True,
            )
            self._system_thread.start()

    @staticmethod
    def _clamp(value) -> float:
        return max(0.0, min(1.0, safe_float(value, 1.0)))

    @staticmethod
    def _lang(value) -> str:
        raw = str(value or "ru").strip().lower().replace("_", "-")
        return raw.split("-", 1)[0] or "ru"

    def configure(self, *, enabled=None, volume=None, language=None):
        if enabled is not None:
            self.enabled = bool(enabled)
        if volume is not None:
            self.volume = self._clamp(volume)
            for _player, output in self._players.values():
                output.setVolume(self.volume)
        if language is not None:
            new_language = self._lang(language)
            if new_language != self.language:
                self._stop_players()
                self.language = new_language

    def _path(self, event: str) -> Path | None:
        filename = EVENT_FILES.get(event)
        if not filename:
            return None
        if self.language != "ru":
            localized = resource_path("assets", "sounds", self.language, filename)
            if localized.is_file():
                return localized
        path = resource_path("assets", "sounds", filename)
        return path if path.is_file() else None

    @staticmethod
    def _system_flag(event: str):
        if winsound is None:
            return None
        role = SYSTEM_SOUND_ROLES.get(event, "ok")
        names = {
            "ok": "MB_OK", "asterisk": "MB_ICONASTERISK", "exclamation": "MB_ICONEXCLAMATION",
            "hand": "MB_ICONHAND", "question": "MB_ICONQUESTION",
        }
        return getattr(winsound, names.get(role, "MB_OK"), getattr(winsound, "MB_OK", 0))

    def _system_sound_worker(self) -> None:
        while True:
            try:
                flag = self._system_sound_queue.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                if flag is None:
                    return
                if winsound is not None:
                    winsound.MessageBeep(flag)
            except Exception:
                pass
            finally:
                try:
                    self._system_sound_queue.task_done()
                except ValueError:
                    pass

    def play_system(self, event: str = "app_ready") -> bool:
        if winsound is None or os.name != "nt" or self._system_shutdown.is_set():
            return False
        try:
            self._system_sound_queue.put_nowait(self._system_flag(event))
            return True
        except queue.Full:
            # UI cues are advisory. Dropping one is safer than blocking the GUI.
            return False
        except Exception:
            return False

    @Slot(str, bool)
    def _play_queued(self, event: str, force: bool) -> None:
        self.play(event, force=force)

    def _stop_media_players(self, *, except_key: str | None = None) -> None:
        """Keep event cues on one logical audio channel.

        A separate QMediaPlayer is retained per cue because changing a player's
        source rapidly can be unreliable on Windows.  Playback itself is still
        exclusive: a new UI cue stops every older cue before it starts.  This
        prevents an error sound from overlapping a retry/download-start cue and
        prevents closely spaced UI events from talking over each other.
        """
        for key, (player, _output) in self._players.items():
            if except_key is not None and key == except_key:
                continue
            try:
                player.stop()
            except RuntimeError:
                pass

    def _retire_player(self, key: str) -> None:
        pair = self._players.pop(key, None)
        try:
            self._player_order.remove(key)
        except ValueError:
            pass
        if pair is None:
            return
        player, output = pair
        pending = self._pending_media_callbacks.pop(key, None)
        if pending is not None:
            try:
                player.mediaStatusChanged.disconnect(pending)
            except (RuntimeError, TypeError):
                pass
        try:
            player.stop()
            player.setSource(QUrl())
        except Exception:
            pass
        try:
            player.setAudioOutput(None)
        except RuntimeError:
            pass
        try:
            player.deleteLater()
        except RuntimeError:
            pass
        try:
            output.deleteLater()
        except RuntimeError:
            pass

    def _touch_player(self, key: str) -> None:
        try:
            self._player_order.remove(key)
        except ValueError:
            pass
        self._player_order.append(key)

    def play(self, event: str, *, force=False) -> bool:
        event = str(event or "")
        if QThread.currentThread() != self.thread():
            self._queued_play.emit(event, bool(force))
            return True
        if event not in SUPPORTED_SOUND_EVENTS or (not self.enabled and not force):
            return False
        if event in SYSTEM_ONLY_EVENTS:
            self._stop_media_players()
            return self.play_system(event)
        path = self._path(event)
        if path is None:
            self._stop_media_players()
            return self.play_system(event)
        try:
            key = str(path.resolve())
            self._stop_media_players(except_key=key)
            pair = self._players.get(key)
            if pair is None:
                while len(self._players) >= _MAX_CACHED_MEDIA_PLAYERS and self._player_order:
                    self._retire_player(self._player_order[0])
                player = QMediaPlayer(self)
                output = QAudioOutput(self)
                output.setVolume(self.volume)
                player.setAudioOutput(output)
                player.setSource(QUrl.fromLocalFile(key))
                pair = (player, output)
                self._players[key] = pair
            self._touch_player(key)
            if pair is not None:
                player, _output = pair
                _output.setVolume(self.volume)
                # Re-triggering the same cue restarts it instead of layering it.
                try:
                    player.stop()
                except RuntimeError:
                    pass
                if player.position() > 0:
                    player.setPosition(0)

            loading_states = {
                QMediaPlayer.MediaStatus.NoMedia,
                QMediaPlayer.MediaStatus.LoadingMedia,
            }
            if player.mediaStatus() not in loading_states:
                player.play()
                return True

            # QMediaPlayer.setSource() is asynchronous on Windows.  Defer the
            # first play until the backend confirms that media is loaded instead
            # of relying on an immediate play() call that some WMF/RDP stacks drop.
            old_pending = self._pending_media_callbacks.pop(key, None)
            if old_pending is not None:
                try:
                    player.mediaStatusChanged.disconnect(old_pending)
                except (RuntimeError, TypeError):
                    pass

            def play_when_loaded(status, *, media_player=player, media_key=key, cue=event):
                if status not in (
                    QMediaPlayer.MediaStatus.LoadedMedia,
                    QMediaPlayer.MediaStatus.BufferedMedia,
                    QMediaPlayer.MediaStatus.InvalidMedia,
                ):
                    return
                callback = self._pending_media_callbacks.pop(media_key, None)
                if callback is not None:
                    try:
                        media_player.mediaStatusChanged.disconnect(callback)
                    except (RuntimeError, TypeError):
                        pass
                if status == QMediaPlayer.MediaStatus.InvalidMedia:
                    # Do not cache a permanently invalid QMediaPlayer. Retire it
                    # so the next occurrence can construct a fresh backend object.
                    self._retire_player(media_key)
                    self.play_system(cue)
                    return
                try:
                    media_player.play()
                except RuntimeError:
                    self.play_system(cue)

            self._pending_media_callbacks[key] = play_when_loaded
            player.mediaStatusChanged.connect(play_when_loaded)
            return True
        except Exception:
            return self.play_system(event)

    def _stop_players(self):
        for key, (player, output) in list(self._players.items()):
            pending = self._pending_media_callbacks.pop(key, None)
            if pending is not None:
                try:
                    player.mediaStatusChanged.disconnect(pending)
                except (RuntimeError, TypeError):
                    pass
            try:
                player.stop()
                player.setSource(QUrl())
            except Exception:
                pass
            try:
                player.setAudioOutput(None)
            except RuntimeError:
                pass
            try:
                player.deleteLater()
            except RuntimeError:
                pass
            try:
                output.deleteLater()
            except RuntimeError:
                pass
        self._players.clear()
        self._player_order.clear()
        self._pending_media_callbacks.clear()

    def shutdown(self):
        self._stop_players()
        self._system_shutdown.set()
        # Drop stale advisory cues and balance Queue.unfinished_tasks before
        # placing the sentinel. This keeps shutdown deterministic even for tests
        # or callers that use Queue.join().
        while True:
            try:
                self._system_sound_queue.get_nowait()
            except queue.Empty:
                break
            else:
                try:
                    self._system_sound_queue.task_done()
                except ValueError:
                    pass
        try:
            self._system_sound_queue.put_nowait(None)
        except Exception:
            pass
        thread = self._system_thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            # Keep shutdown bounded: MessageBeep can block briefly on broken RDP/
            # audio stacks, but a self-test must not leak an otherwise idle worker.
            thread.join(timeout=0.75)
        if thread is not None and not thread.is_alive():
            self._system_thread = None


__all__ = ["QtEventSoundManager", "EVENT_FILES", "SUPPORTED_SOUND_EVENTS", "SYSTEM_ONLY_EVENTS"]
