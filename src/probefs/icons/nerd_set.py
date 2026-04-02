"""NerdIconSet — Nerd Font Unicode glyph icon set.

Requires explicit opt-in via 'icons: nerd' in config.
Nerd Fonts must be installed in the terminal for glyphs to render correctly.
Auto-detection is impossible over SSH — explicit opt-in is mandatory.
"""
from __future__ import annotations

from .base import IconSet


class NerdIconSet(IconSet):
    """Nerd Font icon set using Unicode Private Use Area codepoints.

    All icons are in the Nerd Fonts range (U+E000+).
    Requires Nerd Fonts installed and active in the terminal.
    """

    _ICONS: dict[str, str] = {
        "directory": "\uf07b",       # nf-fa-folder
        "file": "\uf15b",            # nf-fa-file
        "executable": "\uf013",      # nf-fa-cog
        "symlink": "\uf0c1",         # nf-fa-link
        "broken_symlink": "\uf127",  # nf-fa-chain_broken
        "archive": "\uf1c6",         # nf-fa-file_zip_o
        "image": "\uf1c5",           # nf-fa-file_image_o
    }

    # Colors are identical to ASCIIIconSet — same semantics, different glyphs.
    _DEFAULT_COLORS: dict[str, str] = {
        "directory": "bold blue",
        "executable": "bold green",
        "symlink": "cyan",
        "broken_symlink": "bold red",
        "archive": "yellow",
        "image": "magenta",
        "file": "default",
    }

    def __init__(self, color_overrides: dict | None = None) -> None:
        self._colors = dict(self._DEFAULT_COLORS)
        if color_overrides:
            for k, v in color_overrides.items():
                if k in self._colors:
                    self._colors[k] = str(v)

    def get_icon(self, category: str) -> str:
        """Return Nerd Font glyph for the given file category."""
        return self._ICONS.get(category, "\uf15b")  # default to file icon

    def get_color(self, category: str) -> str:
        """Return Rich color style string for the given file category."""
        return self._colors.get(category, "default")
