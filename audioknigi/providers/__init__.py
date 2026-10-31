"""Source-provider contracts and registry (lazy imports avoid a cycle)."""
from .base import SourceProvider

__all__ = ["SourceProvider", "provider_for_key", "provider_for_url", "registered_providers"]

def __getattr__(name):
    if name in {"provider_for_key", "provider_for_url", "registered_providers"}:
        from . import registry
        return getattr(registry, name)
    raise AttributeError(name)
