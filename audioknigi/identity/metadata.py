"""Single source of truth for product identity and version metadata."""
from .brand import BRAND_NAME, DISPLAY_NAME, PRODUCT_NAME
from .version import __version__

APP_VERSION = __version__

__all__ = ["APP_VERSION", "__version__", "BRAND_NAME", "DISPLAY_NAME", "PRODUCT_NAME"]
