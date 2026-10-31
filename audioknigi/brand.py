"""Compatibility alias. Implementation: :mod:`audioknigi.identity.brand`.

New code should import from the implementation package. The alias preserves
module identity, public imports, monkeypatches and frozen-build discovery.
"""
import sys as _sys
from .identity import brand as _impl
_sys.modules[__name__] = _impl
