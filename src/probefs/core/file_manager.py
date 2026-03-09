"""FileManagerCore — Navigation state machine.

Holds current working directory (cwd) and cursor position.
All state transitions are pure path arithmetic — no filesystem I/O
occurs inside descend() or ascend(). Workers on the screen call
fs.ls() separately after receiving a navigation event.
"""
from __future__ import annotations

from pathlib import PurePosixPath

from probefs.fs.probe_fs import ProbeFS


SORT_MODES = ("name_asc", "name_desc", "size_desc", "date_desc")

SORT_LABELS: dict[str, str] = {
    "name_asc":  "name ↑",
    "name_desc": "name ↓",
    "size_desc": "size ↓",
    "date_desc": "date ↓",
}


class FileManagerCore:
    """Navigation state machine for probefs.

    Attributes:
        fs: ProbeFS instance for worker access (not called during navigation).
        cwd: Current working directory as an absolute path string.
        cursor_index: Index of the highlighted entry in the current pane.
    """

    def __init__(self, fs: ProbeFS, start_path: str) -> None:
        self.fs = fs
        self.cwd: str = start_path
        self.cursor_index: int = 0
        self.show_hidden: bool = False
        self.sort_mode: str = "name_asc"

    def next_sort_mode(self) -> str:
        """Cycle to the next sort mode and return it."""
        idx = SORT_MODES.index(self.sort_mode)
        self.sort_mode = SORT_MODES[(idx + 1) % len(SORT_MODES)]
        return self.sort_mode

    @property
    def parent_path(self) -> str:
        """Parent of cwd as a string. Returns '/' when already at root."""
        parent = PurePosixPath(self.cwd).parent
        return str(parent)

    def descend(self, entry_name: str) -> str:
        """Navigate into a child directory.

        Sets cwd to cwd/entry_name and resets cursor_index to 0.
        No filesystem I/O is performed.

        Args:
            entry_name: Name of the child directory entry to enter.

        Returns:
            The new cwd as a string.
        """
        self.cwd = str(PurePosixPath(self.cwd) / entry_name)
        self.cursor_index = 0
        return self.cwd

    def ascend(self) -> str:
        """Navigate to the parent directory.

        Sets cwd to parent_path and resets cursor_index to 0.
        At the filesystem root ('/'), this is a no-op for cwd but still
        resets cursor_index to 0. No filesystem I/O is performed.

        Returns:
            The new cwd as a string.
        """
        parent = self.parent_path
        if parent != self.cwd:  # At root, parent == cwd == "/"
            self.cwd = parent
        self.cursor_index = 0
        return self.cwd
