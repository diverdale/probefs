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

from textual.widgets import Footer

from probefs.core.file_manager import FileManagerCore, SORT_LABELS
from probefs.fs.probe_fs import ProbeFS
from probefs.widgets.dialogs import AboutDialog, ConfirmDialog, HelpDialog, InputDialog
from probefs.widgets.directory_list import DirectoryList
from probefs.widgets.filter_bar import FilterBar
from probefs.widgets.preview_pane import PreviewPane
from probefs.widgets.status_bar import StatusBar


class DirectoryLoaded(Message):
    """Posted by _load_panes worker when a directory listing is ready."""

    def __init__(self, entries: list[dict], pane: str, free_space: int = 0) -> None:
        self.entries = entries
        self.pane = pane  # "parent" or "current"
        self.free_space = free_space  # bytes free; only populated for pane="current"
        super().__init__()


class DirectoryLoadFailed(Message):
    """Posted by _load_panes worker when a directory listing fails."""

    def __init__(self, error_message: str) -> None:
        self.error_message = error_message
        super().__init__()


class MainScreen(Screen):
    """Three-pane file browser screen: parent | current | preview."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="panes"):
            yield DirectoryList(id="pane-parent")
            yield DirectoryList(id="pane-current")
            yield PreviewPane(id="pane-preview")
        yield StatusBar(id="status-bar")
        yield FilterBar(id="filter-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize FileManagerCore and trigger initial directory load."""
        fs = ProbeFS()
        self.core = FileManagerCore(fs, start_path=fs.home())
        self._load_panes()

    @work(thread=True, exclusive=True, exit_on_error=False)
    def _load_panes(self) -> None:
        """Worker: load both parent and current directory listings in one thread.

        Also calls disk_usage() for the current directory (fast on local FS;
        result is included in DirectoryLoaded for the 'current' pane).
        """
        try:
            current_entries = self.core.fs.ls(self.core.cwd, detail=True)
            free_space = self.core.fs.disk_usage(self.core.cwd)
            self.post_message(DirectoryLoaded(current_entries, pane="current", free_space=free_space))
        except Exception as exc:
            self.post_message(DirectoryLoadFailed(str(exc)))
            return

        try:
            parent_entries = self.core.fs.ls(self.core.parent_path, detail=True)
            self.post_message(DirectoryLoaded(parent_entries, pane="parent"))
        except Exception as exc:
            self.post_message(DirectoryLoadFailed(str(exc)))

    def on_directory_loaded(self, message: DirectoryLoaded) -> None:
        """Update the appropriate pane with loaded entries. Update status bar for current pane."""
        if message.pane == "current":
            pane = self.query_one("#pane-current", DirectoryList)
            visible_count = pane.set_entries(
                message.entries,
                show_hidden=self.core.show_hidden,
                sort_mode=self.core.sort_mode,
            )
            # Update status bar: path, sort label, item count, free space
            status = self.query_one("#status-bar", StatusBar)
            status.path = self.core.cwd
            status.sort_mode = SORT_LABELS[self.core.sort_mode]
            status.item_count = visible_count
            if message.free_space > 0:
                free_gb = message.free_space / (1024 ** 3)
                status.free_space = f"{free_gb:.1f} GB free"
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

    # -- Action guard: block all screen actions while FilterBar is active --

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        """Disable all screen actions while FilterBar is visible.

        Returning False marks the binding as inactive so the key event is NOT
        consumed — it continues down the handler chain and reaches FilterBar.on_key.
        """
        try:
            fb = self.query_one("#filter-bar", FilterBar)
        except Exception:
            return True
        if fb.display:
            return False  # key passes through to FilterBar
        return True

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
        self._load_panes()

    def action_sort(self) -> None:
        """Cycle sort mode. 's' key binding."""
        new_mode = self.core.next_sort_mode()
        pane = self.query_one("#pane-current", DirectoryList)
        visible_count = pane.reapply(self.core.show_hidden, new_mode)
        status = self.query_one("#status-bar", StatusBar)
        status.sort_mode = SORT_LABELS[new_mode]
        status.item_count = visible_count

    def action_filter(self) -> None:
        """Open filter bar. '/' key binding."""
        fb = self.query_one("#filter-bar", FilterBar)
        footer = self.query_one(Footer)
        footer.display = False
        fb.activate()

    def _deactivate_filter(self) -> None:
        """Clear filter, restore Footer, refocus current pane."""
        pane = self.query_one("#pane-current", DirectoryList)
        visible_count = pane.set_filter("")
        status = self.query_one("#status-bar", StatusBar)
        status.set_filter_active(False)
        status.item_count = visible_count
        footer = self.query_one(Footer)
        footer.display = True
        self.query_one("#pane-current", DirectoryList).focus()

    def on_filter_bar_filter_changed(self, event: FilterBar.FilterChanged) -> None:
        """Live update as user types in filter bar."""
        pane = self.query_one("#pane-current", DirectoryList)
        visible_count = pane.set_filter(event.text)
        status = self.query_one("#status-bar", StatusBar)
        status.set_filter_active(bool(event.text))
        status.item_count = visible_count

    def on_filter_bar_filter_cleared(self, event: FilterBar.FilterCleared) -> None:
        """Escape pressed — remove filter, restore Footer."""
        self._deactivate_filter()

    def on_filter_bar_filter_submitted(self, event: FilterBar.FilterSubmitted) -> None:
        """Enter pressed — keep filter active, close bar, refocus pane."""
        pane = self.query_one("#pane-current", DirectoryList)
        visible_count = pane.set_filter(event.text)
        status = self.query_one("#status-bar", StatusBar)
        status.set_filter_active(bool(event.text))
        status.item_count = visible_count
        footer = self.query_one(Footer)
        footer.display = True
        pane.focus()

    # -- Navigation history --

    def action_go_back(self) -> None:
        """Navigate back in history. ctrl+o binding."""
        if self.core.go_back():
            self._load_panes()

    def action_go_forward(self) -> None:
        """Navigate forward in history. ctrl+i binding."""
        if self.core.go_forward():
            self._load_panes()

    def action_goto(self) -> None:
        """Jump to an arbitrary path via InputDialog. g binding."""
        def _on_path(path: str | None) -> None:
            if not path:
                return
            path = path.strip()
            if not self.core.fs.isdir(path):
                self.notify(f"Not a directory: {path}", severity="warning")
                return
            self.core.jump_to(path)
            self._load_panes()

        self.app.push_screen(
            InputDialog("Go to path:", initial_value=self.core.cwd, select_all=False),
            _on_path,
        )

    # -- Clipboard & launch --

    def action_copy_path(self) -> None:
        """Copy current entry's full path to clipboard. Y binding."""
        path = self._get_highlighted_path() or self.core.cwd
        try:
            self.core.fs.copy_to_clipboard(path)
            self.notify(f"Copied: {path}")
        except OSError as exc:
            self.notify(str(exc), severity="error")

    def action_open_default(self) -> None:
        """Open highlighted entry with the system default app. o binding."""
        path = self._get_highlighted_path()
        if not path:
            return
        try:
            self.core.fs.open_with_default(path)
        except OSError as exc:
            self.notify(f"Cannot open: {exc}", severity="error")

    def action_shell(self) -> None:
        """Drop to a shell in the current directory. ! binding."""
        import os
        import subprocess
        shell = os.environ.get("SHELL", "/bin/sh")
        with self.app.suspend():
            subprocess.run([shell], cwd=self.core.cwd)

    # -- Help --

    def action_help(self) -> None:
        """Show keybinding reference. ? binding."""
        self.app.push_screen(HelpDialog())

    def action_about(self) -> None:
        """Show about screen. a binding."""
        self.app.push_screen(AboutDialog())

    def action_sftp(self) -> None:
        """Open SFTP screen. ctrl+s binding."""
        from probefs.screens.sftp import SFTPScreen
        self.app.push_screen(SFTPScreen(local_cwd=self.core.cwd))

    # -- File operation actions --
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
            InputDialog(f"Copy '{basename}' to:", initial_value=initial, select_all=False),
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
        self.app.call_from_thread(self._load_panes)

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
            InputDialog(f"Move '{basename}' to:", initial_value=initial, select_all=False),
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
        self.app.call_from_thread(self._load_panes)

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
        self.app.call_from_thread(self._load_panes)

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
        self.app.call_from_thread(self._load_panes)

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
        self.app.call_from_thread(self._load_panes)

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
        self.app.call_from_thread(self._load_panes)
