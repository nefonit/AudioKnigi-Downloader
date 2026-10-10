"""Download-domain exceptions shared by the headless engine and UI."""

from ..core import safe_int


def _normalized_track_indices(values):
    return sorted({
        index
        for value in (values or [])
        if not isinstance(value, bool)
        if (index := safe_int(value, -1)) >= 0
    })


class MissingMediaSourceError(RuntimeError):
    """HTTP 404/410 tied to one concrete media source and its book parts."""
    def __init__(self, message, *, source_url="", track_indices=None):
        super().__init__(message)
        self.source_url = str(source_url or "")
        self.track_indices = _normalized_track_indices(track_indices)

class MissingSelectedTracksError(RuntimeError):
    """Selected parts disappeared from a refreshed public playlist."""
    def __init__(self, track_indices):
        self.track_indices = _normalized_track_indices(track_indices)
        shown = ", ".join(str(x) for x in self.track_indices[:12])
        extra = f" (и ещё {len(self.track_indices) - 12})" if len(self.track_indices) > 12 else ""
        super().__init__("После обновления плейлиста исчезли выбранные части: " + shown + extra)

class SharedSourceTimelineError(RuntimeError):
    """A shared local audio source does not contain media near the playlist end."""
    def __init__(self, issue):
        normalized = dict(issue or {})
        raw_indices = normalized.get("track_indices")
        if raw_indices is None and "track_index" in normalized:
            raw_indices = [normalized.get("track_index")]
        normalized["track_indices"] = _normalized_track_indices(raw_indices)
        self.issue = normalized
        super().__init__("Скачанный общий аудиофайл не покрывает все таймкоды плейлиста.")

class RangeUnsupported(RuntimeError):
    pass

__all__ = ["MissingMediaSourceError", "MissingSelectedTracksError", "SharedSourceTimelineError", "RangeUnsupported"]
