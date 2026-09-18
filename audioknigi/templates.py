from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

from .core import safe_name

SUPPORTED_TOKENS = (
    "Output_Dir", "Author", "Book_Title", "Year", "Genre",
    "Track_Number", "Track_Title", "Narrator",
)
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wav"}
_TOKEN_RE = re.compile(r"\{([A-Za-z0-9_]+)\}")


def _field(obj, name: str, default=None):
    """Read a model or compatibility mapping without assuming either shape."""
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _safe_track_index(track) -> int:
    if isinstance(track, (int, str)) and not isinstance(track, bool):
        try:
            return int(track)
        except (TypeError, ValueError):
            pass
    try:
        raw = _field(track, "index", 0)
        return int(raw if raw is not None else 0)
    except (AttributeError, TypeError, ValueError):
        return 0




def track_number_width(book, minimum: int = 2) -> int:
    """Width needed for lexicographically sortable track numbers.

    Books with 100+ parts use 001..130 rather than 01..130, so ordinary
    filename sorting in Explorer and simple players preserves playback order.
    """
    try:
        tracks = list(_field(book, "tracks", []) or [])
    except Exception:
        tracks = []
    indexes = [_safe_track_index(track) for track in tracks]
    maximum = max(indexes, default=0)
    return max(int(minimum), len(str(maximum if maximum > 0 else 0)))

def template_values(book, track=None, output_dir=None, *, language: str = "ru") -> dict[str, str]:
    # ``language`` is retained for source/API compatibility with older callers.
    # Filesystem identity is deliberately language-neutral, so it is not used.
    _ = language
    track_number = ""
    track_title = ""
    if track is not None:
        idx = _safe_track_index(track)
        width = track_number_width(book)
        track_number = f"{idx:0{width}d}"
        raw_title = _field(track, "title", "")
        # A missing per-track title must remain unique. Falling back to the book
        # title makes templates such as {Track_Title}.mp3 overwrite every part.
        track_title = f"track-{track_number}" if raw_title is None or str(raw_title) == "" else str(raw_title)
    raw_year = _field(book, "year", "")
    return {
        "Output_Dir": str(output_dir or ""),
        # Path identity must stay stable when the UI language changes.
        "Author": str(_field(book, "author", "") or "Без автора"),
        "Book_Title": str(_field(book, "title", "") or "audiobook"),
        "Year": "" if raw_year is None else str(raw_year),
        "Genre": str(_field(book, "genre", "") or ""),
        "Narrator": str(_field(book, "narrator", "") or ""),
        "Track_Number": track_number,
        "Track_Title": track_title,
    }


def render_text_template(template: str, values: dict[str, str]) -> str:
    # Resolve placeholders while they still belong to the *template*.  Never run
    # a placeholder-removal regex after inserting user/book data: a real title
    # such as "Альбом {Remix}" must keep its braces intact.
    raw_template = str(template or "")
    values_ci = {str(key).casefold(): value for key, value in values.items()}

    def replace_token(match: re.Match[str]) -> str:
        key = match.group(1).casefold()
        return str(values_ci[key]) if key in values_ci else match.group(0)

    result = _TOKEN_RE.sub(replace_token, raw_template)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def render_folder(base_dir: str | Path, template: str, book, *, create: bool = True, language: str = "ru") -> Path:
    base = Path(base_dir).expanduser()
    values = template_values(book, output_dir="", language=language)
    # Keep separators authored by the user in the template, but never let a
    # slash/backslash contained in book metadata silently create directories.
    folder_values = {}
    for key, value in values.items():
        raw_value = str(value or "")
        folder_values[key] = safe_name(raw_value) if raw_value else ""
    raw = render_text_template(template or "{Book_Title}", folder_values).strip("/\\ ")
    parts = [p for p in re.split(r"[/\\]+", raw) if p and p not in (".", "..")]
    safe_parts = [sp for p in parts if (sp := safe_name(p))]
    fallback_title = safe_name(str(_field(book, "title", "") or "audiobook")) or "audiobook"
    folder = base.joinpath(*safe_parts) if safe_parts else base / fallback_title
    if create:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


def _strip_literal_template_extension(template: str) -> str:
    """Remove only an extension literally authored in the template itself.

    This deliberately runs *before* substituting title/author values, so a track
    title ending in '.m4a' is treated as data rather than mistaken for a format
    directive.
    """
    lowered = template.lower()
    for candidate in sorted(AUDIO_EXTENSIONS, key=len, reverse=True):
        if lowered.endswith(candidate):
            return template[:-len(candidate)]
    return template


def render_track_filename(template: str, book, track, ext: str = ".mp3", *, language: str = "ru") -> str:
    ext = str(ext or ".mp3")
    if not ext.startswith("."):
        ext = "." + ext
    ext = ext.lower()

    source_template = str(template or "{Track_Number}")
    source_template = _strip_literal_template_extension(source_template)
    values = template_values(book, track=track, language=language)
    raw = render_text_template(source_template, values)
    raw = safe_name(raw) or f"{_safe_track_index(track):0{track_number_width(book)}d}"
    # PlayerJS metadata sometimes already contains the source media extension.
    # The output format owns the final suffix, so replace a trailing known audio
    # extension instead of producing names such as chapter.m4a.mp3.
    lowered_raw = raw.lower()
    for candidate in sorted(AUDIO_EXTENSIONS, key=len, reverse=True):
        if lowered_raw.endswith(candidate):
            raw = raw[:-len(candidate)]
            break
    raw = raw.rstrip(" .") or f"{_safe_track_index(track):0{track_number_width(book)}d}"
    return raw + ext
