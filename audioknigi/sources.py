"""Legacy import path for :mod:`audioknigi.providers.source_urls`.

Use the new package in new code. Static import preserves PyInstaller's module
graph, monkeypatching and class identity across legacy and new import paths.
"""
import sys as _sys
from .providers import source_urls as _implementation

_sys.modules[__name__] = _implementation
