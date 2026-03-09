"""StatusBar — single-line docked widget showing filesystem context.

Displays three fields:
  - path: the current working directory
  - item_count: number of items in the current directory
  - free_space: available disk space (e.g. "42.3 GB free")

Wired by MainScreen: updated after every DirectoryLoaded message and
cursor change. Uses Textual reactive attributes + watch_ pattern so
Label widgets update automatically when attributes are set from outside.

Layout: three Labels in a Horizontal. Path is left-aligned and expands
to fill available space. Count and space are right-aligned fixed widths.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    """One-line status bar showing current path, item count, and free space."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $panel-darken-1;
        layout: horizontal;
        padding: 0 1;
    }
    StatusBar #sb-path {
        width: 1fr;
        color: $text;
    }
    StatusBar #sb-count {
        width: 12;
        color: $text-muted;
        text-align: right;
    }
    StatusBar #sb-space {
        width: 16;
        color: $text-muted;
        text-align: right;
    }
    """

    path: reactive[str] = reactive("")
    item_count: reactive[int] = reactive(0)
    free_space: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("", id="sb-path")
            yield Label("", id="sb-count")
            yield Label("", id="sb-space")

    def watch_path(self, value: str) -> None:
        self.query_one("#sb-path", Label).update(value)

    def watch_item_count(self, value: int) -> None:
        self.query_one("#sb-count", Label).update(f"{value} items")

    def watch_free_space(self, value: str) -> None:
        self.query_one("#sb-space", Label).update(value)
