"""PreviewPane — right pane stub.

Phase 1: displays entry name and type as plain text.
Phase 6: will render syntax-highlighted file content and directory listings.
The message routing infrastructure is wired from Phase 1 so Phase 6 requires
only handler body changes, not architectural changes.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static


class PreviewPane(Widget):

    class CursorChanged(Message):
        """Posted by MainScreen when the cursor moves to a new entry."""
        def __init__(self, entry: dict) -> None:
            self.entry = entry
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Static("", id="preview-content")

    def show_entry(self, entry: dict) -> None:
        """Update preview for the given entry. Phase 1: shows name and type."""
        name = entry.get("name", "").split("/")[-1]
        entry_type = entry.get("type", "unknown")
        self.query_one("#preview-content", Static).update(
            f"{name}\n[dim]{entry_type}[/dim]"
        )

    def on_preview_pane_cursor_changed(self, event: CursorChanged) -> None:
        """Handle cursor change — update preview display."""
        self.show_entry(event.entry)
