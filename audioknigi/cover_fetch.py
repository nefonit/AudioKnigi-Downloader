"""Compatibility alias. Implementation: :mod:`audioknigi.engine.cover_fetch`.

New code should import from the implementation package. The alias preserves
module identity, public imports, monkeypatches and frozen-build discovery.
"""
import sys as _sys
from .engine import cover_fetch as _impl
_sys.modules[__name__] = _impl
