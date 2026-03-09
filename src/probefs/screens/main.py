"""MainScreen — Three-pane file browser screen.

Composes DirectoryList (parent), DirectoryList (current), and PreviewPane.
Directory loading is always done inside @work(thread=True) workers — never
on the main thread — so the UI stays responsive during slow I/O.
"""
from __future__ import annotations

from pathlib import PurePosixPath

from textual import work
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import Screen
from textual.containers import Horizontal

from probefs.core.file_manager import FileManagerCore
from probefs.fs.probe_fs import ProbeFS
from probefs.widgets.dialogs import ConfirmDialog, InputDialog
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
        pane.set_entries(message.entries, show_hidden=self.core.show_hidden)

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

    def action_toggle_hidden(self) -> None:
        """Toggle hidden dotfile visibility. '.' key binding."""
        self.core.show_hidden = not self.core.show_hidden
        # No disk re-read — set_entries filters from the already-loaded _entries.
        # Re-trigger _load_panes to reload fresh (entries are already cached in
        # memory by the OS so this is fast; no actual disk I/O bottleneck).
        self._load_panes()

    # -- File operation actions (Phase 5) --
    # Pattern: action method collects input via modal, then fires a named @work worker.
    # Workers run in threads; all main-thread calls use call_from_thread.

    def _get_highlighted_path(self) -> str | None:
        """Return the full path of the highlighted entry, or None if pane is empty."""
        entry = self.query_one("#pane-current", DirectoryList).get_highlighted_entry()
        if entry is None:
            return None
        return entry.get("name", "")

    def action_copy(self) -> None:
        """Copy highlighted entry to a user-supplied destination path."""
        src = self._get_highlighted_path()
        if not src:
            return
        basename = src.split("/")[-1] if "/" in src else src
        initial = str(PurePosixPath(self.core.cwd) / basename)

        def _on_dst(dst: str | None) -> None:
            if dst:
                self._do_copy(src, dst)

        self.app.push_screen(
            InputDialog(f"Copy '{basename}' to:", initial_value=initial),
            _on_dst,
        )

    @work(thread=True, exit_on_error=False)
    def _do_copy(self, src: str, dst: str) -> None:
        try:
            self.core.fs.copy(src, dst)
        except FileExistsError:
            self.app.notify("Destination already exists", severity="warning")
            return
        except OSError as exc:
            self.app.notify(f"Copy failed: {exc}", severity="error")
            return
        self.app.notify("Copied")
        self.call_from_thread(self._load_panes)

    def action_move(self) -> None:
        """Move highlighted entry to a user-supplied destination path."""
        src = self._get_highlighted_path()
        if not src:
            return
        basename = src.split("/")[-1] if "/" in src else src
        initial = str(PurePosixPath(self.core.cwd) / basename)

        def _on_dst(dst: str | None) -> None:
            if dst:
                self._do_move(src, dst)

        self.app.push_screen(
            InputDialog(f"Move '{basename}' to:", initial_value=initial),
            _on_dst,
        )

    @work(thread=True, exit_on_error=False)
    def _do_move(self, src: str, dst: str) -> None:
        try:
            self.core.fs.move(src, dst)
        except FileExistsError as exc:
            self.app.notify(str(exc), severity="warning")
            return
        except (OSError, Exception) as exc:
            self.app.notify(f"Move failed: {exc}", severity="error")
            return
        self.app.notify("Moved")
        self.call_from_thread(self._load_panes)

    def action_delete(self) -> None:
        """Send highlighted entry to OS Trash after confirmation."""
        path = self._get_highlighted_path()
        if not path:
            return
        name = path.split("/")[-1] if "/" in path else path

        def _on_confirmed(confirmed: bool | None) -> None:
            if confirmed:
                self._do_trash(path)

        self.app.push_screen(
            ConfirmDialog(f"Send '{name}' to Trash?"),
            _on_confirmed,
        )

    @work(thread=True, exit_on_error=False)
    def _do_trash(self, path: str) -> None:
        try:
            self.core.fs.trash(path)
        except OSError as exc:
            self.app.notify(f"Could not trash: {exc}", severity="error")
            return
        self.app.notify("Moved to Trash")
        self.call_from_thread(self._load_panes)

    def action_rename(self) -> None:
        """Rename highlighted entry in-place via InputDialog."""
        path = self._get_highlighted_path()
        if not path:
            return
        current_name = path.split("/")[-1] if "/" in path else path

        def _on_new_name(new_name: str | None) -> None:
            if new_name and new_name != current_name:
                self._do_rename(path, new_name)

        self.app.push_screen(
            InputDialog("Rename to:", initial_value=current_name),
            _on_new_name,
        )

    @work(thread=True, exit_on_error=False)
    def _do_rename(self, path: str, new_name: str) -> None:
        try:
            self.core.fs.rename(path, new_name)
        except FileExistsError:
            self.app.notify(f"'{new_name}' already exists", severity="warning")
            return
        except OSError as exc:
            self.app.notify(f"Rename failed: {exc}", severity="error")
            return
        self.app.notify(f"Renamed to '{new_name}'")
        self.call_from_thread(self._load_panes)

    def action_new_file(self) -> None:
        """Create a new empty file in the current directory."""
        def _on_name(name: str | None) -> None:
            if name:
                path = str(PurePosixPath(self.core.cwd) / name)
                self._do_new_file(path)

        self.app.push_screen(
            InputDialog("New file name:"),
            _on_name,
        )

    @work(thread=True, exit_on_error=False)
    def _do_new_file(self, path: str) -> None:
        try:
            self.core.fs.new_file(path)
        except FileExistsError:
            name = path.split("/")[-1] if "/" in path else path
            self.app.notify(f"'{name}' already exists", severity="warning")
            return
        except OSError as exc:
            self.app.notify(f"Could not create file: {exc}", severity="error")
            return
        name = path.split("/")[-1] if "/" in path else path
        self.app.notify(f"Created '{name}'")
        self.call_from_thread(self._load_panes)

    def action_new_dir(self) -> None:
        """Create a new directory in the current directory."""
        def _on_name(name: str | None) -> None:
            if name:
                path = str(PurePosixPath(self.core.cwd) / name)
                self._do_new_dir(path)

        self.app.push_screen(
            InputDialog("New directory name:"),
            _on_name,
        )

    @work(thread=True, exit_on_error=False)
    def _do_new_dir(self, path: str) -> None:
        try:
            self.core.fs.new_dir(path)
        except FileExistsError:
            name = path.split("/")[-1] if "/" in path else path
            self.app.notify(f"'{name}' already exists", severity="warning")
            return
        except OSError as exc:
            self.app.notify(f"Could not create directory: {exc}", severity="error")
            return
        name = path.split("/")[-1] if "/" in path else path
        self.app.notify(f"Created directory '{name}'")
        self.call_from_thread(self._load_panes)
