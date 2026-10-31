"""Compatibility alias. Implementation: :mod:`audioknigi.diagnostics.crash_report`.

New code should import from the implementation package. The alias preserves
module identity, public imports, monkeypatches and frozen-build discovery.
"""
import sys as _sys
from .diagnostics import crash_report as _impl
_sys.modules[__name__] = _impl
