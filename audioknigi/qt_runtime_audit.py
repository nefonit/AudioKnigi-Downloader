"""Compatibility alias. Implementation: :mod:`audioknigi.qt.runtime_audit`.

New code should import from the implementation package. The alias preserves
module identity, public imports, monkeypatches and frozen-build discovery.
"""
import sys as _sys
from .qt import runtime_audit as _impl
_sys.modules[__name__] = _impl
