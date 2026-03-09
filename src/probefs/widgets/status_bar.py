"""StatusBar — single-line docked widget showing filesystem context.

Displays four fields:
  - path: the current working directory
  - sort_mode: active sort label (e.g. "name ↑")
  - item_count: number of items in the current directory
  - free_space: available disk space (e.g. "42.3 GB free")

Wired by MainScreen: updated after every DirectoryLoaded message and
cursor change. Uses Textual reactive attributes + watch_ pattern so
Label widgets update automatically when attributes are set from outside.

Layout: four Labels in a Horizontal. Path is left-aligned and expands
to fill available space. Sort, count and space are right-aligned fixed widths.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    """One-line status bar showing current path, sort mode, item count, and free space."""

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
    StatusBar #sb-sort {
        width: 10;
        color: $accent;
        text-align: right;
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
    sort_mode: reactive[str] = reactive("name ↑")
    item_count: reactive[int] = reactive(0)
    free_space: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Label("", id="sb-path")
        yield Label("", id="sb-sort")
        yield Label("", id="sb-count")
        yield Label("", id="sb-space")

    def watch_path(self, value: str) -> None:
        self.query_one("#sb-path", Label).update(value)

    def watch_sort_mode(self, value: str) -> None:
        self.query_one("#sb-sort", Label).update(value)

    def watch_item_count(self, value: int) -> None:
        label = f"{value} items" if not self._filter_active else f"{value} matched"
        self.query_one("#sb-count", Label).update(label)

    def watch_free_space(self, value: str) -> None:
        self.query_one("#sb-space", Label).update(value)

    # Filter-active flag: when True, item count label says "matched" instead of "items"
    _filter_active: bool = False

    def set_filter_active(self, active: bool) -> None:
        """Toggle the filter-active state (affects item_count label wording)."""
        self._filter_active = active
        # Re-trigger watch to update label wording
        self.watch_item_count(self.item_count)
