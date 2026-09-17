from __future__ import annotations

from .base import SourceProvider
from .adapters import AudioknigiProvider, KnigavuheProvider, PoleKnigProvider
from ..sources import source_key

_PROVIDERS: dict[str, SourceProvider] = {
    provider.key: provider
    for provider in (AudioknigiProvider(), KnigavuheProvider(), PoleKnigProvider())
}


def provider_for_key(key: str) -> SourceProvider | None:
    return _PROVIDERS.get(str(key or "").strip().casefold())


def provider_for_url(url: str) -> SourceProvider | None:
    return provider_for_key(source_key(url))


def registered_providers() -> tuple[SourceProvider, ...]:
    return tuple(_PROVIDERS.values())


__all__ = ["provider_for_key", "provider_for_url", "registered_providers"]
