from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

AUDIOKNIGI_HOST = "audioknigi.com.ua"
KNIGAVUHE_HOST = "knigavuhe.org"
POLEKNIG_HOST = "poleknig.com"
SUPPORTED_SOURCE_HOSTS = (AUDIOKNIGI_HOST, KNIGAVUHE_HOST, POLEKNIG_HOST)

_AUDIO_BOOK_PATH_RE = re.compile(r"^/audio-\d+(?:[-/][^?#]*)?$", re.I)
_KNIGAVUHE_BOOK_PATH_RE = re.compile(r"^/book/[^/?#]+/?$", re.I)
_POLEKNIG_BOOK_PATH_RE = re.compile(r"^/books/(\d+)(?:(?:-|/)[^/?#]+)?(?:/read)?/?$", re.I)


def _parse_source_candidate(url: str):
    raw = str(url or "").strip()
    if not raw:
        return raw, None
    candidate = raw
    if "://" not in candidate:
        lowered = candidate.casefold()
        known_prefixes = (
            AUDIOKNIGI_HOST + "/",
            "www." + AUDIOKNIGI_HOST + "/",
            KNIGAVUHE_HOST + "/",
            "www." + KNIGAVUHE_HOST + "/",
            "m." + KNIGAVUHE_HOST + "/",
            POLEKNIG_HOST + "/",
            "www." + POLEKNIG_HOST + "/",
        )
        known_hosts = {
            AUDIOKNIGI_HOST,
            "www." + AUDIOKNIGI_HOST,
            KNIGAVUHE_HOST,
            "www." + KNIGAVUHE_HOST,
            "m." + KNIGAVUHE_HOST,
            POLEKNIG_HOST,
            "www." + POLEKNIG_HOST,
        }
        known_authority = re.match(r"^([^/:?#]+)(?::(\d{1,5}))?(?:[/?#]|$)", lowered)
        authority_host = known_authority.group(1) if known_authority else ""
        if lowered in known_hosts or lowered.startswith(known_prefixes) or authority_host in known_hosts:
            candidate = "https://" + candidate
    try:
        return candidate, urlparse(candidate)
    except Exception:
        return raw, None


def source_key(url: str) -> str:
    _candidate, parsed = _parse_source_candidate(url)
    if parsed is None:
        return ""
    host = (parsed.hostname or "").lower()
    if host == AUDIOKNIGI_HOST or host.endswith("." + AUDIOKNIGI_HOST):
        return "audioknigi"
    if host == KNIGAVUHE_HOST or host.endswith("." + KNIGAVUHE_HOST):
        return "knigavuhe"
    if host == POLEKNIG_HOST or host.endswith("." + POLEKNIG_HOST):
        return "poleknig"
    return ""


def source_name(url: str) -> str:
    key = source_key(url)
    known = {
        "audioknigi": "audioknigi.com.ua",
        "knigavuhe": "knigavuhe.org",
        "poleknig": "poleknig.com",
    }
    if key in known:
        return known[key]
    _candidate, parsed = _parse_source_candidate(url)
    return str(getattr(parsed, "hostname", "") or "—")


def normalize_supported_url(url: str) -> str:
    """Normalize supported source URLs to stable HTTPS book identities."""
    raw = str(url or "").strip()
    candidate, parsed = _parse_source_candidate(raw)
    if parsed is None:
        return raw
    key = source_key(candidate)
    if not key:
        return raw

    host = {
        "audioknigi": AUDIOKNIGI_HOST,
        "knigavuhe": KNIGAVUHE_HOST,
        "poleknig": POLEKNIG_HOST,
    }[key]
    netloc = host
    # Non-default explicit ports are preserved for development/test mirrors.
    # urllib.parse validates the port lazily, so malformed user input must not
    # escape as ValueError from this normalizer.
    try:
        port = parsed.port
    except ValueError:
        return ""
    if port and port not in (80, 443):
        netloc += f":{port}"
    parsed = parsed._replace(scheme="https", netloc=netloc)

    if key == "audioknigi":
        path = parsed.path or "/"
        if re.match(r"^/audio-\d+(?:[-/][^?#]*)?/?$", path, re.I):
            parsed = parsed._replace(path=path.rstrip("/") or "/", query="", fragment="")
    elif key == "knigavuhe":
        match = re.match(r"^/book/([^/?#]+)/?$", parsed.path or "", re.I)
        if match:
            parsed = parsed._replace(path=f"/book/{match.group(1)}/", query="", fragment="")
    elif key == "poleknig":
        match = re.match(r"^/books/(\d+)(?:(?:-|/)[^/?#]+)?(?:/read)?/?$", parsed.path or "", re.I)
        if match:
            # poleknig.py uses the no-trailing-slash form as its canonical ID.
            parsed = parsed._replace(path=f"/books/{match.group(1)}", query="", fragment="")
    return urlunparse(parsed)


def is_supported_url(url: str) -> bool:
    """Return True only for concrete book pages, not arbitrary pages on a known host."""
    normalized = normalize_supported_url(url)
    try:
        parsed = urlparse(normalized)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    key = source_key(normalized)
    path = parsed.path or ""
    if key == "audioknigi":
        return bool(_AUDIO_BOOK_PATH_RE.fullmatch(path))
    if key == "knigavuhe":
        return bool(_KNIGAVUHE_BOOK_PATH_RE.fullmatch(path))
    if key == "poleknig":
        return bool(_POLEKNIG_BOOK_PATH_RE.fullmatch(path))
    return False


__all__ = [
    "AUDIOKNIGI_HOST", "KNIGAVUHE_HOST", "POLEKNIG_HOST", "SUPPORTED_SOURCE_HOSTS",
    "source_key", "source_name", "normalize_supported_url", "is_supported_url",
]
