"""Compatibility alias. Implementation: :mod:`audioknigi.localization.i18n`.

New code should import from the implementation package. The alias preserves
module identity, public imports, monkeypatches and frozen-build discovery.
"""
import sys as _sys
from .localization import i18n as _impl
_sys.modules[__name__] = _impl
