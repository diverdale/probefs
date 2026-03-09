"""load_icon_set() factory — returns the appropriate IconSet based on config.

Config key 'icons':
  absent or 'ascii'          -> ASCIIIconSet() (default, no config required)
  'nerd'                     -> NerdIconSet() (requires explicit opt-in per THEME-07)
  dict with 'theme_file' key -> YAMLIconSet(config['icons']['theme_file'])
"""
from __future__ import annotations

from .ascii_set import ASCIIIconSet
from .base import IconSet
from .nerd_set import NerdIconSet
from .yaml_set import YAMLIconSet


def load_icon_set(config: dict) -> IconSet:
    """Return the appropriate IconSet based on config.

    Args:
        config: Application config dict. Inspects the 'icons' key.

    Returns:
        An IconSet instance appropriate for the given config.
    """
    icon_cfg = config.get("icons", "ascii")
    if icon_cfg == "nerd":
        return NerdIconSet()
    if isinstance(icon_cfg, dict) and icon_cfg.get("theme_file"):
        return YAMLIconSet(icon_cfg["theme_file"])
    return ASCIIIconSet()
