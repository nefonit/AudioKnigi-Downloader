from __future__ import annotations

from urllib.parse import urljoin

from ..core import Cancelled, get_http_session
from ..logging_utils import app_logger

_MAX_COVER_BYTES = 20 * 1024 * 1024


def fetch_cover_bytes(url: str, referer: str = "", *, cancel_event=None):
    """Fetch a cover as ``(bytes, mime)`` without making GUI assumptions.

    Ordinary network failures are best-effort and return ``None``. Explicit
    cancellation is never swallowed. The size cap prevents an accidental huge
    response from being retained as artwork.
    """
    raw_url = str(url or "").strip()
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url
    absolute_url = urljoin(str(referer or ""), raw_url)
    if not absolute_url or not absolute_url.lower().startswith(("http://", "https://")):
        return None
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")

    response = None
    try:
        session = get_http_session()
        headers = {"Referer": str(referer or "")} if referer else {}
        response = session.get(
            absolute_url, headers=headers, stream=True, timeout=(10, 25), allow_redirects=True
        )
        response.raise_for_status()
        try:
            declared_size = int(response.headers.get("content-length", 0) or 0)
        except (TypeError, ValueError, OverflowError):
            declared_size = 0
        if declared_size > _MAX_COVER_BYTES:
            app_logger.debug("Rejected oversized cover response: content_length=%s", declared_size)
            return None
        mime = str(response.headers.get("content-type", "image/jpeg") or "image/jpeg")
        mime = mime.split(";", 1)[0].strip() or "image/jpeg"
        generic_mime = mime.casefold() in {"application/octet-stream", "binary/octet-stream"}
        if not mime.casefold().startswith("image/") and not generic_mime:
            app_logger.debug("Rejected non-image cover response before download: content_type=%s", mime)
            return None
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if cancel_event is not None and cancel_event.is_set():
                raise Cancelled("Операция отменена пользователем")
            if not chunk:
                continue
            total += len(chunk)
            if total > _MAX_COVER_BYTES:
                return None
            chunks.append(bytes(chunk))
        payload = b"".join(chunks)
        if not payload:
            return None
        if generic_mime:
            # Some CDNs serve artwork with a generic binary content type.
            # Accept those only when the payload has a recognized image signature.
            if payload.startswith(b"\xff\xd8\xff"):
                mime = "image/jpeg"
            elif payload.startswith(b"\x89PNG\r\n\x1a\n"):
                mime = "image/png"
            elif len(payload) >= 12 and payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
                mime = "image/webp"
            elif payload.startswith((b"GIF87a", b"GIF89a")):
                mime = "image/gif"
            elif payload.startswith(b"BM"):
                mime = "image/bmp"
            else:
                app_logger.debug("Rejected unrecognized generic cover payload")
                return None
        return payload, mime
    except Cancelled:
        raise
    except Exception:
        return None
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                app_logger.debug("Could not close cover response", exc_info=True)


__all__ = ["fetch_cover_bytes"]
