"""IconSet abstract base class — strategy interface for icon/color selection."""
from __future__ import annotations

from abc import ABC, abstractmethod


class IconSet(ABC):
    """Abstract base class for file type icon and color strategies.

    Implementations provide icons and Rich color strings for each file category.

    Categories: "directory", "file", "executable", "symlink",
                "broken_symlink", "archive", "image"
    """

    @abstractmethod
    def get_icon(self, category: str) -> str:
        """Return the icon string for the given file category."""
        ...

    @abstractmethod
    def get_color(self, category: str) -> str:
        """Return the Rich color style string for the given file category."""
        ...
