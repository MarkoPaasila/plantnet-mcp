"""Hermes plugin entry at repo root — delegates to the implementation package."""

import sys
from pathlib import Path

# Hermes loads this file as a directory plugin (not via pip entry points).
# Ensure the repo root is on sys.path so the sibling package imports.
_root = Path(__file__).resolve().parent
_root_str = str(_root)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

from hermes_plantnet_plugin import register, __version__

__all__ = ["register", "__version__"]
