"""YAMLIconSet — loads icons and colors from a user-supplied YAML file.

Falls back to ASCIIIconSet for any category not defined in the YAML file.
YAML format: top-level 'icons' and 'colors' dicts keyed by category name.
"""
from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from .ascii_set import ASCIIIconSet
from .base import IconSet


class YAMLIconSet(IconSet):
    """Icon set loaded from a YAML theme file.

    YAML file must have 'icons' and/or 'colors' dicts at the top level.
    Missing categories fall back to ASCIIIconSet defaults.

    Example YAML structure::

        icons:
          directory: "/"
          file: " "
        colors:
          directory: "bold blue"
          file: "default"
    """

    def __init__(self, theme_path: str) -> None:
        yaml = YAML()
        data = yaml.load(Path(theme_path))
        self._icons: dict = data.get("icons", {}) if data else {}
        self._colors: dict = data.get("colors", {}) if data else {}
        self._fallback = ASCIIIconSet()

    def get_icon(self, category: str) -> str:
        """Return icon from YAML, falling back to ASCIIIconSet for missing categories."""
        return self._icons.get(category) or self._fallback.get_icon(category)

    def get_color(self, category: str) -> str:
        """Return color from YAML, falling back to ASCIIIconSet for missing categories."""
        return self._colors.get(category) or self._fallback.get_color(category)
