from __future__ import annotations

import importlib.resources as ilr

from probefs.theme.loader import ThemeLoader
from textual.theme import Theme

BUILTIN_THEME_NAMES: list[str] = [
    "probefs-dark",
    "probefs-light",
    "probefs-tokyo-night",
]

_BUILTIN_FILES = ("dark.yaml", "light.yaml", "tokyo-night.yaml")


def load_all_builtin_themes() -> list[tuple[Theme, dict]]:
    """Load all built-in probefs themes from package data.

    Uses importlib.resources.files() to locate YAML files in the
    probefs.themes sub-package — works whether installed as a wheel,
    editable install, or zip import.

    Returns:
        List of (Theme, file_colors) tuples. file_colors is a dict mapping
        category names to Rich color style strings (empty if not defined).

    Raises:
        ThemeValidationError: If a built-in theme file is malformed
            (should never happen in release builds).
    """
    themes: list[tuple[Theme, dict]] = []
    pkg = ilr.files("probefs.themes")
    for fname in _BUILTIN_FILES:
        content = pkg.joinpath(fname).read_text(encoding="utf-8")
        theme, file_colors = ThemeLoader.load_from_string(content, source_label=fname)
        themes.append((theme, file_colors))
    return themes
