from __future__ import annotations

"""Localization facade.

Stable message IDs live in ``locales/messages.json``.  Russian source literals
from older UI code are isolated in ``legacy_literals.json`` so new code can use
IDs without growing another phase-specific Python dictionary.
"""

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)
_LOCALE_DIR = Path(__file__).with_name("locales")


def _read_json(name: str, default: Any):
    try:
        value = json.loads((_LOCALE_DIR / name).read_text(encoding="utf-8"))
        return value
    except (OSError, ValueError, TypeError):
        _logger.exception("Failed to load locale catalog: %s", name)
        return default


LANGUAGES: dict[str, str] = _read_json(
    "languages.json", {"ru": "Русский", "uk": "Українська", "de": "Deutsch", "en": "English"}
)
STRINGS: dict[str, dict[str, str]] = _read_json("messages.json", {"ru": {}})
_PHASE29_LITERAL_TRANSLATIONS: dict[str, dict[str, str]] = _read_json("legacy_literals.json", {})
_PHASE29_RUNTIME_EXACT: dict[str, dict[str, str]] = _read_json("runtime_exact.json", {})
_PHASE29_RUNTIME_PREFIXES: dict[str, dict[str, str]] = _read_json("runtime_prefixes.json", {})
def _normalize_runtime_regex_catalog(value: Any) -> tuple[tuple[str, dict[str, str]], ...]:
    """Return only well-formed runtime regex rows from an external locale catalog."""
    if not isinstance(value, list):
        return ()
    rows: list[tuple[str, dict[str, str]]] = []
    for item in value:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        pattern, variants = item[0], item[1]
        if not isinstance(pattern, str) or not isinstance(variants, dict):
            continue
        rows.append((pattern, variants))
    return tuple(rows)


_PHASE29_RUNTIME_REGEX = _normalize_runtime_regex_catalog(_read_json("runtime_regex.json", []))

# Compatibility name retained for regression tooling.  Accessibility literals
# are now part of the external locale catalog rather than a future-phase block.
_PHASE39_ACCESSIBILITY_LITERAL_TRANSLATIONS = _PHASE29_LITERAL_TRANSLATIONS

_LITERAL_TEMPLATE_EXAMPLES = {
    "Доступно: {Author} {Book_Title} {Year} {Genre} {Narrator} {Track_Number} {Track_Title}",
}


def _language(code: str) -> str:
    return code if code in STRINGS else "ru"


def tr(language: str, key: str, **kwargs) -> str:
    """Translate a stable message ID such as ``status_downloading``."""
    language = _language(language)
    value = STRINGS.get(language, {}).get(key, STRINGS.get("ru", {}).get(key, key))
    if not kwargs:
        return str(value)
    try:
        return str(value).format(**kwargs)
    except Exception as exc:
        _logger.warning("i18n formatting failed: language=%s key=%s error=%s", language, key, exc)
        return str(value)


def message(language: str, message_id: str, **kwargs) -> str:
    """Preferred stable-ID localization API for new code."""
    return tr(language, message_id, **kwargs)


def ui_text(language: str, russian_text: str, **kwargs) -> str:
    """Compatibility translator for legacy Russian source literals."""
    language = _language(language)
    source = str(russian_text)
    if language == "ru":
        value = source
    else:
        value = _PHASE29_LITERAL_TRANSLATIONS.get(language, {}).get(source)
        if value is None:
            exact_entry = _PHASE29_RUNTIME_EXACT.get(source)
            value = exact_entry.get(language) if isinstance(exact_entry, dict) else None
        if value is None:
            value = source
    if source in _LITERAL_TEMPLATE_EXAMPLES or not kwargs:
        return value
    try:
        return value.format(**kwargs)
    except Exception:
        return value


@lru_cache(maxsize=512)
def _compiled_runtime_pattern(pattern: str):
    return re.compile(pattern, re.DOTALL)


def localize_runtime_text(language: str, text: str) -> str:
    language = _language(language)
    raw = str(text or "")
    if language == "ru" or not raw:
        return raw
    for pattern, variants in _PHASE29_RUNTIME_REGEX:
        match = _compiled_runtime_pattern(pattern).match(raw)
        if match:
            template = variants.get(language)
            if template:
                try:
                    return template.format(*match.groups())
                except Exception:
                    pass
    exact_entry = _PHASE29_RUNTIME_EXACT.get(raw)
    if isinstance(exact_entry, dict):
        translated = exact_entry.get(language)
        if translated is not None:
            return translated
    for prefix, variants in _PHASE29_RUNTIME_PREFIXES.items():
        if raw.startswith(prefix):
            return variants.get(language, prefix) + raw[len(prefix):]
    literal = _PHASE29_LITERAL_TRANSLATIONS.get(language, {}).get(raw)
    return literal if literal is not None else raw


__all__ = ["LANGUAGES", "STRINGS", "tr", "message", "ui_text", "localize_runtime_text"]
