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


def load_all_builtin_themes() -> list[Theme]:
    """Load all built-in probefs themes from package data.

    Uses importlib.resources.files() to locate YAML files in the
    probefs.themes sub-package — works whether installed as a wheel,
    editable install, or zip import.

    Raises:
        ThemeValidationError: If a built-in theme file is malformed
            (should never happen in release builds).
    """
    themes: list[Theme] = []
    pkg = ilr.files("probefs.themes")
    for fname in _BUILTIN_FILES:
        content = pkg.joinpath(fname).read_text(encoding="utf-8")
        theme = ThemeLoader.load_from_string(content, source_label=fname)
        themes.append(theme)
    return themes
