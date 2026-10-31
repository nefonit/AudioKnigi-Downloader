"""Experimental Akniga.org source adapter.

The website serves chapter timelines through a same-origin AJAX book endpoint
and audio through a time-limited HLS manifest. We use the *site's own browser*
to obtain its currently played media URL, rather than copying private keys or
maintaining a custom decryption routine. No account/purchase/DRM bypass.

This module requires live-site validation. Akniga explicitly does not offer
ordinary file exports outside its website. Use for authorized audio only.
"""
from __future__ import annotations

import html
import json
import re
import threading
from urllib.parse import urljoin, urlsplit

from ..core import Cancelled, SiteStructureChanged, USER_AGENT, parse_time_seconds
from ..models import Book, Track
from ..network_dns import (
    DNS_MODE_AUTO, current_dns_mode, user_proxy_enabled, launch_playwright_chromium,
)
from ..logging_utils import app_logger

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

_BID_RE = re.compile(r'\bdata-bid\s*=\s*["\'](\d+)["\']', re.I)
_KEY_RE = re.compile(r'''LIVESTREET_SECURITY_KEY\s*=\s*['"]([^'"]+)['"]''')
_META_RE = re.compile(r'<meta\s+[^>]*>', re.I)
_ATTR_RE = re.compile(r'''([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')''')


def _meta_value(page_html: str, *names: str) -> str:
    for tag in _META_RE.findall(page_html or ""):
        attrs = {k.lower(): html.unescape(v or q or "") for k, v, q in _ATTR_RE.findall(tag)}
        if attrs.get("property", "").lower() in names or attrs.get("name", "").lower() in names:
            return attrs.get("content", "").strip()
    return ""


def _clean(text) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(text or ""))).strip()


# Search-engine metadata on Akniga is not the book synopsis.  It often starts
# with "Аудиокнига «...», читает ... Слушайте бесплатно онлайн." and can be
# truncated. Prefer the visible Description section, then clean the metadata.
_SEO_INTRO_RE = re.compile(
    r"^Аудиокнига\s+[«\"'„]?.{1,220}?(?:[»\"'“])?\s*,?\s*"
    r"читает\s+[^.!?]{1,150}\.\s*Слушайте\s+бесплатно\s+онлайн[.!?]?\s*",
    re.I,
)


def _strip_akniga_seo(text: str) -> str:
    value = _clean(text)
    # Prefix removal is intentionally anchored: ordinary prose after the
    # promotional sentence is kept verbatim, and prose containing the same
    # words later is never modified.
    return _SEO_INTRO_RE.sub("", value, count=1).strip()


def _description_from_page(page_html: str) -> str:
    """Extract the *book* synopsis, never neighbouring series/reader widgets.

    Akniga reuses ``description__article-main`` for several blocks on some
    book pages. A long text block without an ``Описание`` label is **not**
    proof that it is the synopsis. Prefer an explicitly labelled description
    and only use weak, unlabelled matches when there is no better source.
    """
    from bs4 import BeautifulSoup, Tag

    soup = BeautifulSoup(page_html or "", "html.parser")
    for unwanted in soup.select("script, style, noscript, template"):
        unwanted.decompose()

    caption_selector = ".content__main__book--item--caption"

    def is_description_label(text: str) -> bool:
        return _clean(text).casefold().rstrip(" :：") == "описание"

    def readable(node) -> str:
        if not isinstance(node, Tag):
            return ""
        value = _strip_akniga_seo(node.get_text(" ", strip=True))
        return re.sub(r"^Описание\s*(?::|[–—])?\s+", "", value, count=1, flags=re.I).strip()

    # On compilations such as "Мифы Ктулху" the "Содержание" list is INSIDE
    # the very same description__article-main element as the synopsis. Its
    # content belongs to a different field, not the book annotation. Do not
    # trim at words appearing naturally inside prose: only standalone section
    # labels and headings end a synopsis.
    tail_headings = {
        "содержание", "оглавление", "поддержать исполнителя",
        "поделиться аудиокнигой", "другие озвучки", "другие книги серии",
        "входит в подборку", "другие книги", "комментарии",
    }

    def synopsis_from_node(el) -> str:
        # Work with a clone: deleting a heading must not mutate the original
        # DOM, which is also inspected by the fallback extractors.
        copy = BeautifulSoup(str(el), "html.parser")
        for caption in copy.select(caption_selector):
            caption.decompose()
        selected = copy.select_one(el.name) if isinstance(el, Tag) else None
        if selected is None:
            return ""
        # Iterate textual nodes in document order, stopping as soon as a new
        # section starts, even when its heading is merely <b>Содержание</b> or
        # bare text separated by <br> rather than a sibling article element.
        # Splitting before _clean() also preserves the original paragraphs.
        parts = []
        for node in selected.strings:
            raw = str(node or "").strip()
            if not raw:
                continue
            # Text nodes can include literal line breaks from the page HTML.
            lines = raw.splitlines()
            end_section = False
            for line in lines:
                piece = _clean(line)
                if not piece:
                    continue
                if piece.casefold().rstrip(" :：") in tail_headings:
                    end_section = True
                    break
                parts.append(piece)
            if end_section:
                break
        value = _strip_akniga_seo(" ".join(parts))
        value = re.sub(r"^Описание\s*(?::|[–—])?\s+", "", value, count=1, flags=re.I).strip()
        if len(value) < 20 or value.casefold().startswith((
            "входит в подборку", "другие озвучки", "другие книги серии",
            "другие книги", "поддержать исполнителя", "добавлено ",
        )):
            return ""
        return value

    def linked_label(el) -> bool:
        # Some older pages place the label directly *before* the body.
        for sibling in el.previous_siblings:
            if not isinstance(sibling, Tag):
                continue
            return sibling.select_one(caption_selector) is not None and any(
                is_description_label(x.get_text(" ", strip=True))
                for x in sibling.select(caption_selector)
            ) or is_description_label(sibling.get_text(" ", strip=True))
        return False

    # Tier 1: a captioned book synopsis. A collection/series block can use
    # the same CSS class but it has no such caption (or a different caption).
    bodies = soup.select(".description__article-main")
    for el in bodies:
        labels = el.select(caption_selector)
        if any(is_description_label(x.get_text(" ", strip=True)) for x in labels):
            value = synopsis_from_node(el)
            if value:
                return value
    for el in bodies:
        if not el.select(caption_selector) and linked_label(el):
            value = synopsis_from_node(el)
            if value:
                return value

    # Tier 2: other explicit book-description selectors. Do not inspect a
    # generic itemprop or an unlabelled article until after heading matching.
    for selector in (
        "#book-description", ".book-description", ".book__description",
        ".book_description", ".book-description-text", ".book__annotation",
        ".book-annotation", ".book-desc", ".book-info__description",
    ):
        for el in soup.select(selector):
            value = synopsis_from_node(el)
            if value:
                return value

    # Tier 3: explicitly marked textual heading followed by its prose.
    # Stop at the next caption/section heading to avoid swallowing the series,
    # recommendations, author information or comments.
    for string in soup.find_all(string=lambda item: bool(item and is_description_label(item))):
        label = string.parent
        if not isinstance(label, Tag):
            continue
        for parent in (label, label.parent):
            if not isinstance(parent, Tag):
                continue
            parts = []
            for sibling in parent.next_siblings:
                if not isinstance(sibling, Tag):
                    continue
                if sibling.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                    break
                if sibling.select_one(caption_selector) is not None:
                    break
                value = readable(sibling)
                if value.casefold().startswith((
                    "добавлено ", "комментарии", "рейтинг", "похожие книги",
                    "другие озвучки", "другие книги серии", "другие книги",
                    "поддержать исполнителя", "входит в подборку",
                )):
                    break
                if value and not is_description_label(value):
                    parts.append(value)
                if sum(len(part) for part in parts) >= 8000:
                    break
            collected = _clean(" ".join(parts))
            if len(collected) >= 20:
                return collected

    # Tier 4: a legacy unlabelled description block. Only trust it if there
    # is exactly one such candidate; otherwise use metadata, not an arbitrary
    # series/reader widget. This preserves compatibility with older Akniga.
    unlabelled = [el for el in bodies if not el.select(caption_selector)]
    if len(bodies) == 1 and len(unlabelled) == 1:
        value = synopsis_from_node(unlabelled[0])
        if value:
            return value

    for el in soup.select("[itemprop='description'], .book__text, .book-text"):
        value = synopsis_from_node(el)
        if value:
            return value
    return ""


def _akniga_description(page_html: str) -> str:
    visible = _description_from_page(page_html)
    if visible:
        return visible
    fallback = _strip_akniga_seo(_meta_value(page_html, "og:description", "description"))
    # Metadata describing a collection is not a synopsis, either.
    return "" if fallback.casefold().startswith("входит в подборку") else fallback


def _parse_api_book(url: str, page_html: str, payload: dict, playlist_url: str) -> Book:
    """Pure book decoder. Timeline offsets refer to the same HLS source."""
    if not isinstance(payload, dict):
        raise SiteStructureChanged("Akniga: AJAX ответ не является объектом.")
    raw_items = payload.get("items", [])
    if isinstance(raw_items, str):
        try:
            raw_items = json.loads(raw_items)
        except (ValueError, TypeError) as exc:
            raise SiteStructureChanged("Akniga: неверный формат списка глав.") from exc
    if not isinstance(raw_items, list):
        raise SiteStructureChanged("Akniga: отсутствует список глав.")

    title = _clean(payload.get("titleonly") or _meta_value(page_html, "og:title"))
    if not title:
        raise SiteStructureChanged("Akniga: не удалось получить название книги.")
    tracks = []
    for idx, item in enumerate(raw_items, 1):
        if not isinstance(item, dict):
            continue
        start = parse_time_seconds(item.get("time_from_start"))
        end = parse_time_seconds(item.get("time_finish"))
        if start is None or end is None or end <= start:
            # Never fabricate chapter boundaries: bad offsets would create
            # wrong files and unsafe resume state.
            raise SiteStructureChanged(f"Akniga: некорректное время главы {idx}.")
        name = _clean(item.get("title")) or f"Глава {idx}"
        tracks.append(Track(
            index=idx, title=name, file=playlist_url,
            start=start, end=end, duration=end-start,
        ))
    if not tracks:
        raise SiteStructureChanged("Akniga: не обнаружено ни одной главы.")
    # Offsets must be coherent with one continuous HLS timeline.
    for prev, curr in zip(tracks, tracks[1:]):
        if curr.start < prev.start:
            raise SiteStructureChanged("Akniga: главы расположены не по времени.")

    return Book(
        url=url, title=title, author=_clean(payload.get("author")),
        narrator=_clean(payload.get("reader") or payload.get("performer")),
        cover_url=urljoin(url, _meta_value(page_html, "og:image")),
        description=_akniga_description(page_html),
        playlist_url=playlist_url, tracks=tracks,
    )


def _is_hls_url(url: str) -> bool:
    try:
        parsed = urlsplit(str(url or ""))
        return parsed.scheme == "https" and parsed.path.lower().endswith(".m3u8") and bool(parsed.hostname)
    except (ValueError, TypeError):
        return False


def _api_data(page, bid: str, key: str) -> dict:
    """Use same-origin AJAX; session cookies stay within the active browser."""
    # Credentials stay with the website. The page's normal AJAX API performs
    # authorization; the source does not attempt to unlock restricted books.
    return page.evaluate("""async ({bid, key}) => {
      async function post(path, params) {
        const response = await fetch(path, {
          method: 'POST', credentials: 'same-origin',
          headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest'},
          body: new URLSearchParams(params)
        });
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return await response.json();
      }
      const tokenResponse = await post('/ajax/player/token', {
        security_ls_key: key, bid, ts: String(Date.now())
      });
      if (!tokenResponse || !tokenResponse.token) throw new Error('no token');
      return await post('/ajax/b/' + encodeURIComponent(bid), {
        security_ls_key: key, bid, token: tokenResponse.token, hls: 'true'
      });
    }""", {"bid": bid, "key": key})


def _find_hls(page, payload: dict, found: list[str], cancel_event: threading.Event | None) -> str:
    # Prefer the live site's own player helper when public in the page.
    # Never bundle a reverse-engineered/decryption script or hard-coded keys.
    hres = payload.get("hres") if isinstance(payload, dict) else None
    if hres:
        try:
            candidate = page.evaluate("""(value) => {
                try {
                    return typeof plh !== 'undefined' && typeof plh.getHres === 'function'
                        ? plh.getHres(value) : null;
                } catch (_) { return null; }
            }""", hres)
            if isinstance(candidate, str) and _is_hls_url(candidate):
                return candidate
        except Exception:
            pass

    # Ordinary playback can ask the browser for an HLS manifest. Capture
    # network requests only: do not copy or persist any stream credentials.
    selectors = [
        'button[aria-label*="Воспроиз"]', 'button[aria-label*="Play"]',
        '[data-action="play"]', '[data-play]',
        '.player__play', '.player-play', '.btn-play',
        'button[class*="play"]', '[class*="player"] [class*="play"]',
    ]
    for selector in selectors:
        if found:
            break
        try:
            loc = page.locator(selector).first
            if loc.count() and loc.is_visible():
                loc.click(timeout=1200)
        except Exception:
            continue
    try:
        page.evaluate("""() => {
            const audio = document.querySelector('audio, video');
            if (audio && audio.paused) audio.play().catch(() => {});
        }""")
    except Exception:
        pass
    for _ in range(40):
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled("Операция отменена пользователем")
        if found:
            return found[-1]
        page.wait_for_timeout(250)
    raise SiteStructureChanged(
        "Akniga: не удалось обнаружить HLS-плейлист во время воспроизведения. "
        "Возможно, структура плеера изменилась или доступ к книге ограничен."
    )


def _is_proxy_tunnel_error(exc: BaseException) -> bool:
    """Recognize a failed local proxy tunnel, not an HTTP/application error."""
    message = str(exc)
    return any(token in message for token in (
        "ERR_TUNNEL_CONNECTION_FAILED", "ERR_PROXY_CONNECTION_FAILED",
        "ERR_NO_SUPPORTED_PROXIES",
    ))


def _is_navigation_connection_error(exc: BaseException) -> bool:
    """Page navigation TCP/DNS failures eligible for one auto-DNS fallback.

    A page's HTTP status, blocked resource, site script or audio-player error
    must never trigger a re-analysis. Do not match the generic Playwright
    'Timeout' (which can be DOM load delay, not a failed connection).
    """
    message = str(exc)
    return "Page.goto:" in message and any(code in message for code in (
        "net::ERR_CONNECTION_TIMED_OUT", "net::ERR_NAME_NOT_RESOLVED",
        "net::ERR_CONNECTION_RESET", "net::ERR_CONNECTION_CLOSED",
        "net::ERR_CONNECTION_REFUSED", "net::ERR_ADDRESS_UNREACHABLE",
    ))


def _fetch_using_browser(playwright, url: str, cancel_event, *, use_system_dns: bool) -> Book:
    """One complete attempt: always close the context and browser on failure."""
    browser = launch_playwright_chromium(
        playwright.chromium, use_system_dns=use_system_dns,
    )
    try:
        context = browser.new_context(user_agent=USER_AGENT, locale="ru-RU")
        try:
            page = context.new_page()
            found: list[str] = []

            def on_request(request):
                address = request.url
                if _is_hls_url(address) and address not in found:
                    found.append(address)

            page.on("request", on_request)
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if cancel_event is not None and cancel_event.is_set():
                raise Cancelled("Операция отменена пользователем")
            page_html = page.content()
            bid_match = _BID_RE.search(page_html)
            key_match = _KEY_RE.search(page_html)
            if not bid_match or not key_match:
                raise SiteStructureChanged(
                    "Akniga: в HTML отсутствуют идентификатор книги или ключ AJAX-запроса."
                )
            try:
                payload = _api_data(page, bid_match.group(1), key_match.group(1))
            except Exception as exc:
                raise SiteStructureChanged(
                    "Akniga: сайт не вернул данные глав через AJAX (возможны ограничения доступа)."
                ) from exc
            playlist_url = _find_hls(page, payload, found, cancel_event)
            return _parse_api_book(url, page_html, payload, playlist_url)
        finally:
            context.close()
    finally:
        browser.close()


def fetch_book(url: str, *, cancel_event: threading.Event | None = None) -> Book:
    """Fetch a book with chapter boundaries and a fresh HLS manifest URL."""
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Операция отменена пользователем")
    if sync_playwright is None:
        raise RuntimeError("Для Akniga необходимо установить Playwright и Chromium.")

    with sync_playwright() as playwright:
        try:
            return _fetch_using_browser(
                playwright, url, cancel_event, use_system_dns=False,
            )
        except Exception as exc:
            if (not (_is_proxy_tunnel_error(exc) or _is_navigation_connection_error(exc))
                    or current_dns_mode() != DNS_MODE_AUTO
                    or user_proxy_enabled()
                    or (cancel_event is not None and cancel_event.is_set())):
                raise
            # The app's Cloudflare DNS mode 'auto' explicitly permits a
            # fallback to the OS resolver; do not alter the global DNS mode.
            # Do not log the full Playwright exception: it may contain the
            # user's book URL, signed URLs or other private request data.
            app_logger.warning(
                "Akniga Playwright page connection failed; "
                "one system-DNS retry (error_type=%s)", type(exc).__name__,
            )
            try:
                return _fetch_using_browser(
                    playwright, url, cancel_event, use_system_dns=True,
                )
            except Exception as retry_exc:
                if (_is_proxy_tunnel_error(retry_exc)
                        or _is_navigation_connection_error(retry_exc)):
                    raise RuntimeError(
                        "Akniga: страницу не удалось открыть ни через встроенный "
                        "DNS-мост, ни через системное подключение. Проверьте "
                        "доступность сайта в Edge, настройки сети и Cloudflare One."
                    ) from retry_exc
                raise
