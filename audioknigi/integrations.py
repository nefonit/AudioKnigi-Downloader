from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from .core import get_http_session


@dataclass(slots=True)
class AudiobookshelfConfig:
    enabled: bool = False
    server_url: str = ""
    api_key: str = ""
    library_id: str = ""


def _base(url: str) -> str:
    """Normalize an Audiobookshelf base URL.

    Ordinary home-server addresses are often entered without a scheme. In that
    case use http:// rather than letting requests fail later with MissingSchema.
    Only http/https are accepted.
    """
    value = str(url or "").strip().rstrip("/")
    if not value:
        return ""
    if "://" not in value:
        value = "http://" + value
    parsed = urlparse(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Адрес Audiobookshelf должен быть HTTP/HTTPS URL, например http://192.168.1.10:13378")
    return value


def audiobookshelf_get_libraries(server_url: str, api_key: str, timeout: float = 15.0):
    base = _base(server_url)
    if not base or not api_key:
        raise ValueError("Нужны адрес Audiobookshelf и API key.")
    try:
        response = get_http_session().get(
            f"{base}/api/libraries",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.exceptions.SSLError as exc:
        raise RuntimeError(
            "Audiobookshelf использует недоверенный HTTPS-сертификат. "
            "Установите доверенный сертификат или используйте HTTP только в защищённой локальной сети."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status = getattr(exc.response, "status_code", None)
        if status == 401:
            raise RuntimeError("Неверный API key Audiobookshelf (HTTP 401).") from exc
        raise RuntimeError(f"Audiobookshelf вернул HTTP {status or 'ошибку'}.") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Не удалось подключиться к Audiobookshelf: {exc}") from exc
    try:
        data = response.json()
    except (ValueError, requests.exceptions.JSONDecodeError) as exc:
        raise RuntimeError(
            "Audiobookshelf вернул ответ не в формате JSON. Проверьте адрес сервера, reverse proxy и авторизацию."
        ) from exc
    return data.get("libraries", []) if isinstance(data, dict) else []


def audiobookshelf_scan(server_url: str, api_key: str, library_id: str, timeout: float = 120.0):
    base = _base(server_url)
    library_id = str(library_id or "").strip()
    if not base or not api_key or not library_id:
        raise ValueError("Не заполнены Audiobookshelf URL / API key / Library ID.")
    try:
        response = get_http_session().post(
            f"{base}/api/libraries/{library_id}/scan",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.exceptions.SSLError as exc:
        raise RuntimeError(
            "Audiobookshelf использует недоверенный HTTPS-сертификат. "
            "Установите доверенный сертификат или используйте HTTP только в защищённой локальной сети."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status = getattr(exc.response, "status_code", None)
        if status == 401:
            raise RuntimeError("Неверный API key Audiobookshelf (HTTP 401).") from exc
        raise RuntimeError(f"Audiobookshelf вернул HTTP {status or 'ошибку'} при запуске сканирования.") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Не удалось подключиться к Audiobookshelf: {exc}") from exc
    return True
