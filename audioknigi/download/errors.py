"""Download-domain exceptions shared by the headless engine and UI."""

class MissingMediaSourceError(RuntimeError):
    """HTTP 404/410 tied to one concrete media source and its book parts."""
    def __init__(self, message, *, source_url="", track_indices=None):
        super().__init__(message)
        self.source_url = str(source_url or "")
        self.track_indices = sorted({int(x) for x in (track_indices or [])})

class MissingSelectedTracksError(RuntimeError):
    """Selected parts disappeared from a refreshed public playlist."""
    def __init__(self, track_indices):
        self.track_indices = sorted({int(x) for x in (track_indices or [])})
        shown = ", ".join(str(x) for x in self.track_indices[:12])
        extra = f" (и ещё {len(self.track_indices) - 12})" if len(self.track_indices) > 12 else ""
        super().__init__("После обновления плейлиста исчезли выбранные части: " + shown + extra)

class SharedSourceTimelineError(RuntimeError):
    """A shared local audio source does not contain media near the playlist end."""
    def __init__(self, issue):
        self.issue = dict(issue or {})
        super().__init__("Скачанный общий аудиофайл не покрывает все таймкоды плейлиста.")

class RangeUnsupported(RuntimeError):
    pass

__all__ = ["MissingMediaSourceError", "MissingSelectedTracksError", "SharedSourceTimelineError", "RangeUnsupported"]
