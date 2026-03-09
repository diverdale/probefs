"""DirectoryList — multi-column DataTable display of directory entries.

Uses DataTable(cursor_type="row") instead of ListView so each entry can
display five Rich Text columns: name/icon, permissions, size, date, owner.

Public API (unchanged from ListView version):
  - EntryHighlighted message class
  - set_entries(entries, show_hidden=False)
  - move_cursor_up() / move_cursor_down()
  - get_highlighted_entry() -> dict | None
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable

from probefs.icons.base import IconSet
from probefs.icons.factory import load_icon_set
from probefs.rendering.columns import build_row


class DirectoryList(Widget, can_focus=True):

    class EntryHighlighted(Message):
        """Posted when the cursor moves to a new entry."""
        def __init__(self, entry: dict) -> None:
            self.entry = entry
            super().__init__()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._entries: list[dict] = []
        self._icon_set: IconSet = load_icon_set({})  # ASCIIIconSet default; no config yet
        # config loading is Phase 4; factory signature is already correct for future use

    def compose(self) -> ComposeResult:
        yield DataTable(cursor_type="row", show_header=False, show_cursor=True)

    def on_mount(self) -> None:
        dt = self.query_one(DataTable)
        dt.add_column("name")           # flexible width (no fixed width = fills remaining space)
        dt.add_column("perm", width=10)
        dt.add_column("size", width=8)
        dt.add_column("date", width=12)
        dt.add_column("owner", width=10)

    def set_entries(self, entries: list[dict], show_hidden: bool = False) -> None:
        """Replace list contents. Called from MainScreen on main thread.

        Filters hidden files (basename starts with '.') when show_hidden=False.
        Filtering happens here (not in the worker) so toggle is instant without
        re-reading disk.
        """
        self._entries = [
            e for e in entries
            if show_hidden or not _is_hidden(e)
        ]
        dt = self.query_one(DataTable)
        dt.clear(columns=False)  # MUST pass columns=False — clear() with no args removes columns (Pitfall 2)
        for entry in self._entries:
            row = build_row(entry, self._icon_set)
            dt.add_row(*row)

    def move_cursor_down(self) -> None:
        """Move DataTable cursor down by one row."""
        self.query_one(DataTable).action_cursor_down()

    def move_cursor_up(self) -> None:
        """Move DataTable cursor up by one row."""
        self.query_one(DataTable).action_cursor_up()

    def get_highlighted_entry(self) -> dict | None:
        """Return the currently highlighted entry dict, or None if list is empty."""
        dt = self.query_one(DataTable)
        idx = dt.cursor_row
        # Guard against empty table (cursor_row is 0 even when empty, Pitfall 3)
        if idx is not None and 0 <= idx < len(self._entries):
            return self._entries[idx]
        return None

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Convert DataTable.RowHighlighted to EntryHighlighted domain message."""
        event.stop()
        idx = event.cursor_row
        if 0 <= idx < len(self._entries):
            self.post_message(self.EntryHighlighted(self._entries[idx]))


def _is_hidden(entry: dict) -> bool:
    """Return True if entry basename starts with '.'."""
    name = entry.get("name", "")
    basename = name.split("/")[-1] if "/" in name else name
    return basename.startswith(".")
