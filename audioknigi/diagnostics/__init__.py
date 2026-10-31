"""Privacy-conscious diagnostics and support-bundle helpers."""
__all__ = ["create_support_bundle", "sanitized_settings"]

def __getattr__(name):
    if name in __all__:
        from . import support_bundle
        return getattr(support_bundle, name)
    raise AttributeError(name)
