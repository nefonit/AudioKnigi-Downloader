"""Validate HTTP range responses before accepting existing partial audio bytes.

These helpers are independent of I/O, Qt, HTTP sessions and file operations.
"""

from __future__ import annotations

import re


def is_complete_partial_after_416(existing_size: int, content_range: str) -> bool:
    """Recognize an already-complete partial after the server answers HTTP 416.

    Keep compatibility with observed CDN headers: `bytes */N`,
    `bytes 0-(N-1)/N`, and bare `/N`. The caller alone performs the final
    atomic rename, and all mismatched/unknown totals require a fresh request.
    """
    if existing_size <= 0:
        return False
    match = re.search(
        r"(?:bytes\s+)?(?:\*|\d+\s*-\s*\d+)?\s*/\s*(\d+)\s*$",
        content_range or "",
        re.I,
    )
    return bool(match and existing_size == int(match.group(1)))


def validate_resumed_206(existing_size: int, content_range: str) -> None:
    """Fail before writing if a resumed 206 response starts at a wrong offset.

    An ordinary 200 response can restart from zero; a 206 response may only be
    appended when Content-Range proves it starts at the end of the local .part.
    Accept optional whitespace around the slash, as some CDNs emit it.
    """
    if existing_size <= 0:
        return

    value = str(content_range or "").strip()
    match = re.match(
        r"(?i)^bytes\s+(\d+)-(\d+)\s*/\s*(\d+|\*)\s*$",
        value,
    )
    valid = False
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        total = match.group(3)
        valid = start == existing_size and end >= start
        if total != "*":
            valid = valid and end < int(total)
    if not valid:
        raise RuntimeError(
            f"Некорректный Content-Range при докачке с байта {existing_size}: {value}"
        )
