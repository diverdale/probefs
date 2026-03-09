"""ASCIIIconSet — default icon set using ASCII symbols and Rich color strings.

No configuration required. Safe for all terminal environments including SSH.
"""
from __future__ import annotations

from .base import IconSet


class ASCIIIconSet(IconSet):
    """Default icon set using plain ASCII symbols.

    Works in every terminal environment without special font support.
    This is the fallback for all other icon sets.
    """

    _ICONS: dict[str, str] = {
        "directory": "/",
        "file": " ",
        "executable": "*",
        "symlink": "@",
        "broken_symlink": "!",
        "archive": "#",
        "image": "%",
    }

    _COLORS: dict[str, str] = {
        "directory": "bold blue",
        "executable": "bold green",
        "symlink": "cyan",
        "broken_symlink": "bold red",
        "archive": "yellow",
        "image": "magenta",
        "file": "default",
    }

    def get_icon(self, category: str) -> str:
        """Return ASCII icon for the given file category."""
        return self._ICONS.get(category, " ")

    def get_color(self, category: str) -> str:
        """Return Rich color style string for the given file category."""
        return self._COLORS.get(category, "default")
