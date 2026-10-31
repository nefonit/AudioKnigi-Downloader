"""Small, dependency-free brand system for the desktop UI.

The app keeps branding separate from widget implementation so the same wording
can be reused by the Qt UI, onboarding, help windows and future installers.
"""
from __future__ import annotations

BRAND_NAME = "AudioKnigi"
PRODUCT_NAME = "Downloader"
DISPLAY_NAME = f"{BRAND_NAME} {PRODUCT_NAME}"
BRAND_TAGLINE = "Аудиокниги без лишних шагов"
BRAND_PROMISE = "Скачивайте, храните и слушайте в одном приложении"
SOURCE_HOST = "audioknigi.com.ua / knigavuhe.org / poleknig.com"

AUTHOR_NAME = "Едуард Саратовцев"
AUTHOR_EMAIL = "serioussem39@gmail.com"
AUTHOR_GITHUB_URL = "https://github.com/nefonit"
PROJECT_URL = "https://github.com/nefonit/AudioKnigi-Downloader"
COPYRIGHT_YEAR = 2026

FONT_FAMILY = "Segoe UI"


def version_label(version: str) -> str:
    raw = str(version or "").strip()
    if not raw:
        return ""
    return raw if raw.lower().startswith("v") else f"v{raw}"


__all__ = [
    "BRAND_NAME", "PRODUCT_NAME", "DISPLAY_NAME", "BRAND_TAGLINE",
    "BRAND_PROMISE", "SOURCE_HOST", "FONT_FAMILY", "version_label",
    "AUTHOR_NAME", "AUTHOR_EMAIL", "AUTHOR_GITHUB_URL", "PROJECT_URL", "COPYRIGHT_YEAR",
]
