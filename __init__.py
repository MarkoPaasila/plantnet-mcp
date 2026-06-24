"""Hermes directory-plugin entry — delegates to the implementation package."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
_root_str = str(_root)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

from hermes_plantnet_plugin import register, __version__

__all__ = ["register", "__version__"]
