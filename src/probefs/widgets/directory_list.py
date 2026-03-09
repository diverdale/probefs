"""DirectoryList — scrollable flat list of directory entries for parent and current panes."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import ListView, ListItem, Label


class DirectoryList(Widget, can_focus=True):

    class EntryHighlighted(Message):
        """Posted when the user moves the cursor to a new entry."""
        def __init__(self, entry: dict) -> None:
            self.entry = entry
            super().__init__()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._entries: list[dict] = []

    def compose(self) -> ComposeResult:
        yield ListView()

    def set_entries(self, entries: list[dict]) -> None:
        """Replace list contents. Called from MainScreen message handler (main thread)."""
        self._entries = entries
        lv = self.query_one(ListView)
        lv.clear()
        for entry in entries:
            name = entry.get("name", "")
            # Show basename only, not full path (fsspec returns full paths)
            display_name = name.split("/")[-1] if "/" in name else name
            suffix = "/" if entry.get("type") == "directory" else ""
            lv.append(ListItem(Label(display_name + suffix)))

    def move_cursor_down(self) -> None:
        """Move ListView selection down by one."""
        lv = self.query_one(ListView)
        lv.action_cursor_down()

    def move_cursor_up(self) -> None:
        """Move ListView selection up by one."""
        lv = self.query_one(ListView)
        lv.action_cursor_up()

    def get_highlighted_entry(self) -> dict | None:
        """Return the currently highlighted entry dict, or None if list is empty."""
        lv = self.query_one(ListView)
        if lv.index is not None and 0 <= lv.index < len(self._entries):
            return self._entries[lv.index]
        return None

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Convert ListView.Highlighted to our domain message."""
        event.stop()  # Don't bubble raw ListView events outside this widget
        if event.item is not None and event.list_view.index is not None:
            idx = event.list_view.index
            if 0 <= idx < len(self._entries):
                self.post_message(self.EntryHighlighted(self._entries[idx]))
