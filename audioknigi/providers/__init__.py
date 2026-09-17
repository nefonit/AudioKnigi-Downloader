"""Source-provider abstraction and built-in provider registry."""
from .base import SourceProvider
from .registry import provider_for_key, provider_for_url, registered_providers

__all__ = ["SourceProvider", "provider_for_key", "provider_for_url", "registered_providers"]
