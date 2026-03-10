"""DirectoryList — multi-column DataTable display of directory entries.

Uses DataTable(cursor_type="row") instead of ListView so each entry can
display five Rich Text columns: name/icon, permissions, size, date, owner.

Public API:
  - EntryHighlighted message class
  - set_entries(entries, show_hidden=False, sort_mode="name_asc") -> int
  - set_filter(text: str) -> int
  - reapply(show_hidden: bool, sort_mode: str) -> int
  - move_cursor_up() / move_cursor_down()
  - get_highlighted_entry() -> dict | None
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable

from probefs.config import load_config
from probefs.icons.base import IconSet
from probefs.icons.factory import load_icon_set
from probefs.rendering.columns import build_row


class DirectoryList(Widget, can_focus=True):

    class EntryHighlighted(Message):
        """Posted when the cursor moves to a new entry."""
        def __init__(self, entry: dict) -> None:
            self.entry = entry
            super().__init__()

        @property
        def control(self) -> "DirectoryList":
            return self._sender  # type: ignore[return-value]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._all_entries: list[dict] = []    # raw from fs.ls — never filtered
        self._visible_entries: list[dict] = []  # filtered + sorted — drives DataTable
        self._filter_text: str = ""
        self._sort_mode: str = "name_asc"
        self._show_hidden: bool = False
        self._icon_set: IconSet = load_icon_set(load_config())

    def compose(self) -> ComposeResult:
        yield DataTable(cursor_type="row", show_header=False, show_cursor=True)

    def on_mount(self) -> None:
        dt = self.query_one(DataTable)
        dt.add_column("name")           # flexible width (no fixed width = fills remaining space)
        dt.add_column("perm", width=10)
        dt.add_column("size", width=8)
        dt.add_column("date", width=12)
        dt.add_column("owner", width=10)

    def set_entries(
        self,
        entries: list[dict],
        show_hidden: bool = False,
        sort_mode: str = "name_asc",
    ) -> int:
        """Replace list contents. Resets filter. Returns visible item count.

        Called from MainScreen on main thread after directory load.
        Filtering, hidden-toggle, and sorting all happen here via _apply().
        """
        self._all_entries = entries
        self._filter_text = ""
        self._sort_mode = sort_mode
        self._show_hidden = show_hidden
        return self._apply()

    def set_filter(self, text: str) -> int:
        """Update filter text and re-render. Returns visible item count."""
        self._filter_text = text
        return self._apply()

    def reapply(self, show_hidden: bool, sort_mode: str) -> int:
        """Update hidden/sort params and re-render. Returns visible item count."""
        self._show_hidden = show_hidden
        self._sort_mode = sort_mode
        return self._apply()

    def _apply(self) -> int:
        """Filter + sort _all_entries, repopulate DataTable. Returns visible count."""
        # Step 1: hidden filter
        entries = [
            e for e in self._all_entries
            if self._show_hidden or not _is_hidden(e)
        ]
        # Step 2: text filter (case-insensitive substring on basename)
        if self._filter_text:
            needle = self._filter_text.lower()
            entries = [e for e in entries if needle in _basename(e).lower()]
        # Step 3: sort (dirs always float to top)
        entries = _sort_entries(entries, self._sort_mode)

        self._visible_entries = entries
        dt = self.query_one(DataTable)
        dt.clear(columns=False)
        for entry in self._visible_entries:
            row = build_row(entry, self._icon_set)
            dt.add_row(*row)
        return len(self._visible_entries)

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
        if idx is not None and 0 <= idx < len(self._visible_entries):
            return self._visible_entries[idx]
        return None

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Convert DataTable.RowHighlighted to EntryHighlighted domain message."""
        event.stop()
        idx = event.cursor_row
        if 0 <= idx < len(self._visible_entries):
            self.post_message(self.EntryHighlighted(self._visible_entries[idx]))


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _basename(entry: dict) -> str:
    """Return the basename of an entry's path."""
    name = entry.get("name", "")
    return name.split("/")[-1] if "/" in name else name


def _is_hidden(entry: dict) -> bool:
    """Return True if entry basename starts with '.'."""
    return _basename(entry).startswith(".")


def _sort_entries(entries: list[dict], sort_mode: str) -> list[dict]:
    """Sort entries with directories floating to the top.

    name_asc/name_desc — alphabetical by basename (case-insensitive).
    size_desc — largest files first; directories sorted by name.
    date_desc — most recently modified first (dirs + files together).
    """
    dirs = [e for e in entries if e.get("type") == "directory"]
    files = [e for e in entries if e.get("type") != "directory"]

    def name_key(e: dict) -> str:
        return _basename(e).lower()

    def size_key(e: dict) -> int:
        return e.get("size", 0) or 0

    def date_key(e: dict) -> float:
        import datetime as _dt
        m = e.get("mtime", 0.0)
        if isinstance(m, _dt.datetime):
            return m.timestamp()
        return float(m) if m else 0.0

    if sort_mode == "name_asc":
        dirs.sort(key=name_key)
        files.sort(key=name_key)
    elif sort_mode == "name_desc":
        dirs.sort(key=name_key, reverse=True)
        files.sort(key=name_key, reverse=True)
    elif sort_mode == "size_desc":
        dirs.sort(key=name_key)           # dirs: alphabetical
        files.sort(key=size_key, reverse=True)
    elif sort_mode == "date_desc":
        dirs.sort(key=date_key, reverse=True)
        files.sort(key=date_key, reverse=True)
    else:
        dirs.sort(key=name_key)
        files.sort(key=name_key)

    return dirs + files
