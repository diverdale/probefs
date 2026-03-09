"""MainScreen — Three-pane file browser screen.

Composes DirectoryList (parent), DirectoryList (current), and PreviewPane.
Directory loading is always done inside @work(thread=True) workers — never
on the main thread — so the UI stays responsive during slow I/O.
"""
from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.containers import Horizontal

from probefs.core.file_manager import FileManagerCore
from probefs.fs.probe_fs import ProbeFS
from probefs.widgets.directory_list import DirectoryList
from probefs.widgets.preview_pane import PreviewPane


class DirectoryLoaded(Message):
    """Posted by _load_panes worker when a directory listing is ready."""

    def __init__(self, entries: list[dict], pane: str) -> None:
        self.entries = entries
        self.pane = pane  # "parent" or "current"
        super().__init__()


class DirectoryLoadFailed(Message):
    """Posted by _load_panes worker when a directory listing fails."""

    def __init__(self, error_message: str) -> None:
        self.error_message = error_message
        super().__init__()


class MainScreen(Screen):
    """Three-pane file browser screen: parent | current | preview."""

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield DirectoryList(id="pane-parent")
            yield DirectoryList(id="pane-current")
            yield PreviewPane(id="pane-preview")

    def on_mount(self) -> None:
        """Initialize FileManagerCore and trigger initial directory load."""
        fs = ProbeFS()
        self.core = FileManagerCore(fs, start_path=fs.home())
        self._load_panes()

    @work(thread=True, exclusive=True, exit_on_error=False)
    def _load_panes(self) -> None:
        """Worker: load both parent and current directory listings in one thread."""
        try:
            current_entries = self.core.fs.ls(self.core.cwd, detail=True)
            self.post_message(DirectoryLoaded(current_entries, pane="current"))
        except Exception as exc:
            self.post_message(DirectoryLoadFailed(str(exc)))
            return

        try:
            parent_entries = self.core.fs.ls(self.core.parent_path, detail=True)
            self.post_message(DirectoryLoaded(parent_entries, pane="parent"))
        except Exception as exc:
            self.post_message(DirectoryLoadFailed(str(exc)))

    def on_directory_loaded(self, message: DirectoryLoaded) -> None:
        """Update the appropriate pane with loaded entries."""
        if message.pane == "current":
            pane = self.query_one("#pane-current", DirectoryList)
        else:
            pane = self.query_one("#pane-parent", DirectoryList)
        pane.set_entries(message.entries)

    def on_directory_load_failed(self, message: DirectoryLoadFailed) -> None:
        """Show error notification when directory load fails."""
        self.notify(message.error_message, severity="error")

    def on_directory_list_entry_highlighted(
        self, event: DirectoryList.EntryHighlighted
    ) -> None:
        """Handle cursor movement in current pane — update preview and trigger dir load."""
        # Only react to events from the current pane (not parent pane).
        # event.control can be None when post_message() is used directly instead
        # of the message bubbling through the widget tree.
        if event.control is None or event.control.id != "pane-current":
            return

        entry = event.entry
        # Always update preview
        preview = self.query_one("#pane-preview", PreviewPane)
        preview.post_message(PreviewPane.CursorChanged(entry))

    # -- Action methods called by ProbeFSApp bindings (namespaced "screen.*") --

    def action_cursor_down(self) -> None:
        """Move cursor down in current pane."""
        self.query_one("#pane-current", DirectoryList).move_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in current pane."""
        self.query_one("#pane-current", DirectoryList).move_cursor_up()

    def action_enter_dir(self) -> None:
        """Descend into the highlighted directory entry."""
        current_pane = self.query_one("#pane-current", DirectoryList)
        entry = current_pane.get_highlighted_entry()
        if entry is None:
            return
        if entry.get("type") != "directory":
            return
        # Extract just the basename for descend()
        name = entry.get("name", "")
        basename = name.split("/")[-1] if "/" in name else name
        self.core.descend(basename)
        self._load_panes()

    def action_leave_dir(self) -> None:
        """Ascend to the parent directory."""
        self.core.ascend()
        self._load_panes()
