"""Compatibility alias. Implementation: :mod:`audioknigi.identity.metadata`.

New code should import from the implementation package. The alias preserves
module identity, public imports, monkeypatches and frozen-build discovery.
"""
import sys as _sys
from .identity import metadata as _impl
_sys.modules[__name__] = _impl
