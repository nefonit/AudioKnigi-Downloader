"""Compatibility alias. Implementation: :mod:`audioknigi.connectors.audiobookshelf`.

New code should import from the implementation package. The alias preserves
module identity, public imports, monkeypatches and frozen-build discovery.
"""
import sys as _sys
from .connectors import audiobookshelf as _impl
_sys.modules[__name__] = _impl
