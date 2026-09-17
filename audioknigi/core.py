import html as html_lib
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Mapping
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .metadata import APP_VERSION as _APP_VERSION, DISPLAY_NAME

# Public compatibility export for acceptance/build integrations. New code should
# import version metadata from audioknigi.metadata directly.
APP_VERSION = _APP_VERSION
APP_TITLE = DISPLAY_NAME
DEFAULT_OUTPUT = Path.home() / "Documents" / "AudioKnigi"
DEFAULT_UI_SCALE = 100
UI_SCALE_MIGRATION_KEY = "ui_scale_default_100_migrated"
LEGACY_AUTOMATIC_UI_SCALE = 125

if os.name == "nt":
    APP_DIR = Path(os.getenv("APPDATA") or Path.home()) / "AudioKnigiDownloader"
else:
    APP_DIR = Path.home() / ".audioknigi_downloader"

SETTINGS_FILE = APP_DIR / "settings.json"
HISTORY_FILE = APP_DIR / "history.json"
COOKIE_FILE = APP_DIR / "session_cookies.json"
SESSION_PROFILE_FILE = APP_DIR / "session_profile.json"
PLAYER_POSITIONS_FILE = APP_DIR / "player_positions.json"
CRASH_REPORT_FILE = APP_DIR / "last_crash_report.txt"
SESSION_STATE_FILE = APP_DIR / "session_state.json"

# Current/recent desktop Chrome majors as of 2026-09-12.
USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36",
)
USER_AGENT = USER_AGENTS[0]
RETRY_STATUS_CODES = (429, 500, 502, 503, 504)
_HTTP_LOCAL = threading.local()
_HTTP_PROFILE_LOCK = threading.RLock()
_HTTP_PROFILE_GENERATION = 0
_JSON_LOCK = threading.RLock()

def safe_float(value, default=0.0):
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        result = float(default)
    if math.isfinite(result):
        return result
    try:
        fallback = float(default)
    except (TypeError, ValueError, OverflowError):
        fallback = 0.0
    return fallback if math.isfinite(fallback) else 0.0


NORMALIZATION_MODES = frozenset({"off", "single", "two_pass"})

def safe_normalization_mode(value, default="off") -> str:
    """Return a supported loudness-normalization mode.

    ``single`` is the legacy one-pass loudnorm mode and remains intentionally
    supported for settings migrated from older releases. Unknown/corrupt values
    fall back to a known mode rather than leaking into worker state.
    """
    fallback = str(default or "off").strip().lower()
    if fallback not in NORMALIZATION_MODES:
        fallback = "off"
    mode = str(value or fallback).strip().lower()
    return mode if mode in NORMALIZATION_MODES else fallback

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return int(default)


def migrate_ui_scale_settings(settings):
    """Migrate the legacy automatic 125% UI scale to the new 100% default once.

    Releases before 4.12.3 could persist 125% even when the user had not
    explicitly chosen an enlarged interface.  Merely changing
    ``DEFAULT_UI_SCALE`` therefore does not help existing profiles: their old
    ``settings.json`` keeps overriding the new default.

    The marker is stored for every profile.  This is important because after
    the one-time migration a user is free to select 125% manually, and that
    explicit choice must be preserved on every later restart.
    """
    source = dict(settings) if isinstance(settings, Mapping) else {}
    data = dict(source)
    if bool(data.get(UI_SCALE_MIGRATION_KEY, False)):
        return data, False

    if safe_int(data.get("scale", DEFAULT_UI_SCALE), DEFAULT_UI_SCALE) == LEGACY_AUTOMATIC_UI_SCALE:
        data["scale"] = DEFAULT_UI_SCALE
    data[UI_SCALE_MIGRATION_KEY] = True
    return data, data != source


WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def resource_path(*parts: str) -> Path:
    """Return a resource path in source mode or inside a PyInstaller bundle."""
    meipass = getattr(sys, "_MEIPASS", None)
    base = Path(meipass) if meipass else Path(__file__).resolve().parent.parent
    return base.joinpath(*parts)


_EXECUTABLE_CACHE = {}
_EXECUTABLE_CACHE_LOCK = threading.Lock()


def hidden_subprocess_kwargs(platform_name=None):
    """Return subprocess options that suppress console windows on Windows.

    FFmpeg and FFprobe are console-subsystem executables.  When AudioKnigi is
    started with pythonw.exe or from a PyInstaller ``--windowed`` build, a
    child media process can otherwise flash a console window above the GUI.
    ``CREATE_NO_WINDOW`` is the primary protection; STARTUPINFO/SW_HIDE is kept
    as a compatible fallback for Windows Python builds/wrappers that do not
    expose that creation flag.  Other platforms receive an empty mapping.
    """
    current = os.name if platform_name is None else str(platform_name)
    if current != "nt":
        return {}

    options = {}
    creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0)
    if creationflags:
        options["creationflags"] = creationflags

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= int(getattr(subprocess, "STARTF_USESHOWWINDOW", 1) or 1)
        # SW_HIDE == 0.  ``subprocess`` does not expose SW_HIDE on every Python
        # build, so zero is the correct portable fallback.
        startupinfo.wShowWindow = int(getattr(subprocess, "SW_HIDE", 0) or 0)
        options["startupinfo"] = startupinfo
    except Exception:
        pass
    return options


def _media_tool_works(path: str) -> bool:
    """Return True when an FFmpeg-family executable really starts.

    Chocolatey exposes small shim executables in ``chocolatey\\bin``.  They
    work only while they remain in the Chocolatey environment.  A PyInstaller
    one-file build used to copy such a shim into ``_MEI...``; the detached shim
    then exited with 0xFFFFFFFF and no stderr.  A lightweight ``-version`` probe
    lets us reject a broken bundled shim and fall back to a working system tool.
    """
    try:
        completed = subprocess.run(
            [str(path), "-hide_banner", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=12,
            shell=False,
            check=False,
            **hidden_subprocess_kwargs(),
        )
        return completed.returncode == 0
    except Exception:
        return False


def resolve_executable(name: str):
    """Find a usable external tool or PyInstaller-bundled binary.

    FFmpeg/FFprobe candidates are validated once per process before being used.
    This protects portable builds from accidentally bundled package-manager
    shims while keeping normal executables fast through a small cache.
    """
    raw_name = str(name or "").strip()
    if not raw_name:
        return None
    filename = raw_name + ".exe" if os.name == "nt" and not raw_name.lower().endswith(".exe") else raw_name
    tool_key = Path(filename).stem.lower()
    validate_media = tool_key in {"ffmpeg", "ffprobe"}
    meipass = str(getattr(sys, "_MEIPASS", "") or "")
    try:
        exe_dir = str(Path(sys.executable).resolve().parent)
    except Exception:
        exe_dir = ""
    path_env = os.environ.get("PATH", "")
    cache_key = (raw_name.lower(), meipass, exe_dir, path_env)

    with _EXECUTABLE_CACHE_LOCK:
        if cache_key in _EXECUTABLE_CACHE:
            return _EXECUTABLE_CACHE[cache_key]

    candidates = []
    if meipass:
        candidates.append(Path(meipass) / filename)
    if exe_dir:
        candidates.append(Path(exe_dir) / filename)
    system_path = shutil.which(raw_name)
    if system_path:
        candidates.append(Path(system_path))

    result = None
    seen = set()
    for candidate in candidates:
        try:
            key = os.path.normcase(os.path.abspath(str(candidate)))
            if key in seen:
                continue
            seen.add(key)
            if candidate.is_file():
                candidate_text = str(candidate)
                if validate_media and not _media_tool_works(candidate_text):
                    continue
                result = candidate_text
                break
        except Exception:
            continue

    with _EXECUTABLE_CACHE_LOCK:
        _EXECUTABLE_CACHE[cache_key] = result
    return result

def safe_name(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", str(name))
    name = re.sub(r"\s+", " ", name).strip(". ")
    if not name:
        return "audiobook"
    stem = name.split(".", 1)[0].upper()
    if stem in WINDOWS_RESERVED:
        name = "_" + name
    return name[:180].rstrip(". ") or "audiobook"

def parse_time_seconds(value):
    """Convert numeric or HH:MM:SS/MM:SS playlist values to seconds.

    PlayerJS playlists are not fully consistent between books: some expose
    numeric seconds, while others use a clock string.  Invalid/empty values
    deliberately return ``None`` so callers can fall back to measured audio.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            number = float(value)
        except Exception:
            return None
        return number if number >= 0 and math.isfinite(number) else None

    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text.replace(",", "."))
        return number if number >= 0 and math.isfinite(number) else None
    except (TypeError, ValueError):
        pass

    parts = text.split(":")
    if len(parts) not in (2, 3):
        return None
    try:
        nums = [float(part.strip().replace(",", ".")) for part in parts]
    except (TypeError, ValueError):
        return None
    if any(number < 0 or not math.isfinite(number) for number in nums):
        return None
    if len(nums) == 2:
        minutes, seconds = nums
        total = minutes * 60.0 + seconds
    else:
        hours, minutes, seconds = nums
        total = hours * 3600.0 + minutes * 60.0 + seconds
    return total if math.isfinite(total) else None


def effective_track_duration(track):
    """Best known duration without changing source-cut semantics on Track."""
    duration = parse_time_seconds(getattr(track, "duration", None))
    if duration is not None and duration > 0:
        return duration

    start = parse_time_seconds(getattr(track, "start", None))
    end = parse_time_seconds(getattr(track, "end", None))
    if start is not None and end is not None and end > start:
        return end - start

    actual = parse_time_seconds(getattr(track, "actual_duration", None))
    if actual is not None and actual > 0:
        return actual
    return None


def display_track_timeline(tracks):
    """Return display-only (start, end, duration) values for track rows.

    ``Track.start``/``Track.end`` are source trimming coordinates and must not
    be overwritten merely to make the UI prettier.  When a playlist contains
    one MP3 per chapter it commonly omits those coordinates; in that case the
    table shows a cumulative audiobook timeline using the known/measured
    chapter duration instead.
    """
    rows = []
    cursor = 0.0
    for track in tracks:
        duration = effective_track_duration(track)
        raw_start = parse_time_seconds(getattr(track, "start", None))
        raw_end = parse_time_seconds(getattr(track, "end", None))

        if raw_start is not None or raw_end is not None:
            start = raw_start
            end = raw_end
            if start is None and end is not None and duration is not None:
                start = max(0.0, end - duration)
            if start is None:
                start = cursor if duration is not None else None
            if end is None and start is not None and duration is not None:
                end = start + duration
        elif duration is not None:
            start = cursor
            end = cursor + duration
        else:
            start = end = None

        rows.append((start, end, duration))
        if end is not None:
            cursor = max(cursor, float(end))
        elif duration is not None:
            cursor += float(duration)
    return rows


def fmt_time(seconds):
    try:
        seconds = int(float(seconds))
    except Exception:
        return "—"
    seconds = max(0, seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def fmt_size(size):
    try:
        size = int(size)
    except Exception:
        return "—"
    if size <= 0:
        return "—"
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return "—"

def fmt_eta(seconds):
    try:
        value = float(seconds)
        if not math.isfinite(value):
            return "—"
        seconds = max(0, int(value))
    except Exception:
        return "—"
    return fmt_time(seconds)

def load_json(path, default):
    """Read one JSON file consistently with in-process atomic writers."""
    with _JSON_LOCK:
        try:
            target = Path(path)
            if target.exists():
                return json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default

def save_json(path, data, *, raise_errors=False):
    """Atomically write JSON and serialize concurrent writers.

    Returns ``True`` on success and ``False`` on a best-effort write failure.
    Critical workflows (backup restore, explicit exports/settings migrations)
    may pass ``raise_errors=True`` so the UI never reports success when the
    filesystem rejected the write.
    """
    target = Path(path)
    temp_path = None
    with _JSON_LOCK:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(data, ensure_ascii=False, indent=2)
            temp_path = target.with_name(
                f".{target.name}.{os.getpid()}.{threading.get_ident()}.tmp"
            )
            temp_path.write_text(payload, encoding="utf-8")
            os.replace(temp_path, target)
            return True
        except Exception:
            try:
                if temp_path is not None and temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass
            if raise_errors:
                raise
            return False

def valid_site_url(url):
    # Keep URL policy in the dedicated source-normalization module while
    # avoiding an eager import in the low-level HTTP module.
    from .sources import is_supported_url
    return is_supported_url(url)


def _unescape_json_strings(value):
    if isinstance(value, str):
        return html_lib.unescape(value)
    if isinstance(value, list):
        return [_unescape_json_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: _unescape_json_strings(item) for key, item in value.items()}
    return value


def _first_json_ld(html_text):
    blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text or "", re.I | re.S)
    items = []
    for block in blocks:
        try:
            # JSON-LD is JSON first. Unescaping entities before json.loads can turn
            # a harmless ``&quot;`` inside a JSON string into a syntax-breaking
            # quote. Decode entities only after the JSON structure is parsed.
            data = _unescape_json_strings(json.loads(block.strip()))
        except Exception:
            continue
        if isinstance(data, list):
            items.extend(data)
        else:
            items.append(data)
    return items


def _walk_json(obj):
    """Iteratively walk JSON containers without consuming Python recursion depth."""
    stack = [obj]
    seen_containers = set()
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            marker = id(current)
            if marker in seen_containers:
                continue
            seen_containers.add(marker)
            yield current
            stack.extend(reversed(list(current.values())))
        elif isinstance(current, list):
            marker = id(current)
            if marker in seen_containers:
                continue
            seen_containers.add(marker)
            stack.extend(reversed(current))


def _structured_book_nodes(html_text):
    """Return JSON-LD nodes that describe a book/creative work, not site chrome."""
    candidates = []
    for root in _first_json_ld(html_text):
        for item in _walk_json(root):
            if not isinstance(item, dict):
                continue
            raw_type = item.get("@type", "")
            types = raw_type if isinstance(raw_type, list) else [raw_type]
            normalized_types = {
                str(value).strip().casefold().rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]
                for value in types
            }
            if normalized_types.intersection({"book", "audiobook", "creativework"}):
                candidates.append(item)
    return candidates


def extract_extended_metadata_from_html(html):
    description = ""
    narrator = ""
    genre = ""
    year = ""
    # Only read extended fields from the actual Book/AudioBook/CreativeWork
    # node. Arbitrary JSON-LD commonly contains WebSite/Organization objects
    # with their own description and genre-like fields.
    for item in _structured_book_nodes(html):
        if not description and item.get("description"):
            description = re.sub(r"<[^>]+>", " ", str(item.get("description")))
            description = re.sub(r"\s+", " ", html_lib.unescape(description)).strip()
        if not genre and item.get("genre"):
            value = item.get("genre")
            genre = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
        if not year:
            value = item.get("datePublished") or item.get("dateCreated")
            if value:
                m = re.search(r"(19|20)\d{2}", str(value))
                if m:
                    year = m.group(0)
        if not narrator:
            value = item.get("readBy") or item.get("narrator")
            if isinstance(value, dict):
                narrator = str(value.get("name") or "")
            elif isinstance(value, list):
                names = []
                for x in value:
                    if isinstance(x, dict):
                        names.append(str(x.get("name") or ""))
                    elif x:
                        names.append(str(x))
                narrator = ", ".join(x for x in names if x)
            elif value:
                narrator = str(value)
    if not narrator:
        # AudioKnigi summary text commonly uses
        # ``Исполнитель: Имя, Жанр: ...`` in one text node.  A greedy
        # ``[^<]+`` capture used to leak ``, Жанр:`` into the Reader column.
        # Stop at the next known metadata label or markup boundary instead.
        m = re.search(
            r'(?:Диктор|Читает|Исполнитель)\s*[:—-]\s*'
            r'([^<\n\r]{1,160}?)'
            r'(?=\s*(?:,\s*)?(?:Жанр|Серия|Добавлено|Автор|Год|Краткое содержание|Описание)\s*:|[<\n\r]|$)',
            html or "",
            re.I,
        )
        if m:
            narrator = re.sub(r"\s+", " ", html_lib.unescape(m.group(1))).strip(" \t,;:–—-")
    if narrator:
        narrator = re.split(
            r"\s*,?\s*(?:Жанр|Серия|Добавлено|Автор|Год|Краткое содержание|Описание)\s*:",
            str(narrator),
            maxsplit=1,
            flags=re.I,
        )[0].strip(" \t,;:–—-")
    return description, narrator, genre, year

def _structured_book_metadata(html_text):
    """Best-effort title/author from JSON-LD book metadata only.

    Avoid scanning arbitrary JavaScript for a generic ``name`` key: pages often
    contain unrelated objects such as {"name": "button_close"}.
    """
    candidates = _structured_book_nodes(html_text)
    if not candidates:
        return "", ""
    node = candidates[0]
    title = str(node.get("name") or node.get("headline") or "").strip()
    author_value = node.get("author")
    if isinstance(author_value, dict):
        author = str(author_value.get("name") or "").strip()
    elif isinstance(author_value, list):
        names = []
        for value in author_value:
            if isinstance(value, dict):
                value = value.get("name")
            if value:
                names.append(str(value).strip())
        author = ", ".join(name for name in names if name)
    else:
        author = str(author_value or "").strip()
    return html_lib.unescape(title), html_lib.unescape(author)


def extract_metadata_from_html(html, fallback_title=""):
    html_text = html or ""
    title = fallback_title
    author = ""
    cover_url = ""

    m = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        html_text, re.I,
    )
    if not m:
        m = re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            html_text, re.I,
        )
    if m:
        cover_url = html_lib.unescape(m.group(1).replace("\\/", "/"))

    structured_title, structured_author = _structured_book_metadata(html_text)
    if structured_author:
        author = structured_author
    else:
        author_match = re.search(
            r'["\']author["\']\s*:\s*["\']([^"\']+)["\']', html_text, re.I,
        )
        if author_match:
            author = html_lib.unescape(author_match.group(1).strip())

    if structured_title:
        title = structured_title
    else:
        title_match = re.search(
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
            html_text, re.I,
        )
        if not title_match:
            title_match = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
                html_text, re.I,
            )
        if title_match:
            candidate = html_lib.unescape(title_match.group(1)).strip()
            if candidate:
                title = candidate
        elif not str(title or "").strip():
            html_title = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
            if html_title:
                candidate = re.sub(r"\s+", " ", html_lib.unescape(html_title.group(1))).strip()
                if candidate:
                    title = candidate

    return title, author, cover_url

def _load_persisted_profile():
    data = load_json(SESSION_PROFILE_FILE, {})
    return data if isinstance(data, dict) else {}


def load_browser_context_profile() -> tuple[dict[str, str], list[dict]]:
    """Return persisted browser headers/cookies in Playwright-compatible form.

    HTTP workers and browser fallbacks must share the same Cloudflare/session
    identity.  Keep this adapter in core so site modules do not read profile
    JSON files independently or drift on expiry handling.
    """
    profile = _load_persisted_profile()
    raw_headers = profile.get("headers") if isinstance(profile.get("headers"), dict) else {}
    headers: dict[str, str] = {}
    for name in ("User-Agent", "Accept-Language", "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform"):
        value = raw_headers.get(name)
        if value:
            headers[name] = str(value)

    raw_cookies = load_json(COOKIE_FILE, [])
    cookies: list[dict] = []
    now = time.time()
    if isinstance(raw_cookies, list):
        for item in raw_cookies:
            if not isinstance(item, dict) or not item.get("name") or not item.get("domain"):
                continue
            try:
                expires = float(item.get("expires", -1))
            except (TypeError, ValueError, OverflowError):
                expires = -1
            if expires > 0 and expires <= now:
                continue
            cookie = {
                "name": str(item.get("name") or ""),
                "value": str(item.get("value") or ""),
                "domain": str(item.get("domain") or ""),
                "path": str(item.get("path") or "/"),
                "secure": bool(item.get("secure", False)),
            }
            if expires > 0:
                cookie["expires"] = expires
            cookies.append(cookie)
    return headers, cookies


def build_http_session():
    """Retry-enabled session. Each worker gets its own pool and persisted browser profile."""
    session = requests.Session()
    # Do not allow HTTP(S)_PROXY / ALL_PROXY environment variables to bypass
    # the application's Cloudflare-only resolver. Playwright has its own local
    # Cloudflare-resolving proxy; Python requests connect directly after DoH.
    session.trust_env = False
    retry = Retry(
        total=4,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.6,
        status_forcelist=RETRY_STATUS_CODES,
        allowed_methods=frozenset(("GET", "HEAD")),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=32, pool_block=False)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    profile = _load_persisted_profile()
    persisted_headers = profile.get("headers") if isinstance(profile.get("headers"), dict) else {}
    session.headers.update({
        "User-Agent": str(persisted_headers.get("User-Agent") or random.choice(USER_AGENTS)),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": str(persisted_headers.get("Accept-Language") or "ru-RU,ru;q=0.9,en;q=0.7"),
        "Connection": "keep-alive",
    })
    for name in ("sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform"):
        value = persisted_headers.get(name)
        if value:
            session.headers[name] = str(value)
    _load_persisted_cookies(session)
    return session

def get_http_session():
    """Return a long-lived per-thread Session using the latest browser profile.

    The old implementation rebuilt the pool after every 24 callers, defeating
    HTTP keep-alive on chapter-heavy books. A monotonic profile generation now
    invalidates a worker session only when Playwright actually persists newer
    cookies/headers.
    """
    with _HTTP_PROFILE_LOCK:
        generation = _HTTP_PROFILE_GENERATION
    session = getattr(_HTTP_LOCAL, "session", None)
    local_generation = int(getattr(_HTTP_LOCAL, "profile_generation", -1))
    if session is None or local_generation != generation:
        if session is not None:
            try:
                session.close()
            except Exception:
                pass
        session = build_http_session()
        _HTTP_LOCAL.session = session
        _HTTP_LOCAL.profile_generation = generation
    return session


def refresh_http_session_profile() -> None:
    """Invalidate all per-thread Sessions on their next access."""
    global _HTTP_PROFILE_GENERATION
    with _HTTP_PROFILE_LOCK:
        _HTTP_PROFILE_GENERATION += 1
    # Refresh the current thread immediately; other workers refresh lazily.
    session = getattr(_HTTP_LOCAL, "session", None)
    if session is not None:
        try:
            session.close()
        except Exception:
            pass
    _HTTP_LOCAL.session = None
    _HTTP_LOCAL.profile_generation = -1

def _load_persisted_cookies(session):
    data = load_json(COOKIE_FILE, [])
    if not isinstance(data, list):
        return
    now = time.time()
    for item in data:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        expires = item.get("expires", -1)
        try:
            expires_value = float(expires)
        except Exception:
            expires_value = -1
        if expires_value > 0 and expires_value <= now:
            continue
        kwargs = {}
        if item.get("domain"):
            kwargs["domain"] = item["domain"]
        if item.get("path"):
            kwargs["path"] = item["path"]
        if expires_value > 0:
            kwargs["expires"] = int(expires_value)
        if item.get("secure"):
            kwargs["secure"] = True
        try:
            session.cookies.set(item["name"], item.get("value", ""), **kwargs)
        except Exception:
            pass

def persist_browser_session(cookies, headers=None):
    """Persist successful Playwright cookies plus the browser headers most likely tied to them."""
    cookies_provided = cookies is not None
    cleaned = []
    for item in cookies or []:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        cleaned.append({
            "name": item.get("name", ""),
            "value": item.get("value", ""),
            "domain": item.get("domain", ""),
            "path": item.get("path", "/"),
            "expires": item.get("expires", -1),
            "secure": bool(item.get("secure", False)),
        })

    safe_headers = {}
    header_source = headers if isinstance(headers, dict) else {}
    aliases = {
        "user-agent": "User-Agent",
        "accept-language": "Accept-Language",
        "sec-ch-ua": "sec-ch-ua",
        "sec-ch-ua-mobile": "sec-ch-ua-mobile",
        "sec-ch-ua-platform": "sec-ch-ua-platform",
    }
    lowered = {str(k).lower(): v for k, v in header_source.items()}
    for source_name, target_name in aliases.items():
        value = lowered.get(source_name)
        if value:
            safe_headers[target_name] = str(value)

    existing_profile = _load_persisted_profile()
    if not safe_headers and isinstance(existing_profile.get("headers"), dict):
        safe_headers = dict(existing_profile.get("headers") or {})

    if cookies_provided:
        save_json(COOKIE_FILE, cleaned)
    profile_should_refresh = bool(cookies_provided)
    if cleaned or safe_headers:
        profile_should_refresh = True
    if profile_should_refresh:
        cookies_count = len(cleaned) if cookies_provided else safe_int(existing_profile.get("cookies_saved", 0), 0)
        save_json(
            SESSION_PROFILE_FILE,
            {"headers": safe_headers, "cookies_saved": cookies_count, "saved_at": int(time.time())},
        )
        # A Session may already have been created before Playwright solved a
        # challenge. Invalidate all thread-local pools so the next request sees
        # the newly persisted cookies and matching browser headers.
        refresh_http_session_profile()


def persist_browser_cookies(cookies, headers=None):
    """Backward-compatible wrapper used by older modules/manifests.

    Some 4.x callers used the historical two-argument form.  Accepting the
    optional headers keeps restored plugins/manifests compatible while routing
    everything through the canonical session persistence path.
    """
    persist_browser_session(cookies, headers=headers)

class Cancelled(Exception):
    pass


class SiteStructureChanged(RuntimeError):
    """Raised when the site responds normally but expected player/playlist markup disappeared."""
    pass
