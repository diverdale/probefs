"""SFTPScreen — dual-pane local↔remote file transfer screen.

Layout:
  Status bar (top) — shows connection state; press c to (re)connect
  Horizontal split:
    Left:  local DirectoryList (always active, remembers cwd from MainScreen)
    Right: remote DirectoryList (disabled until connected)
  SFTPStatusBar (bottom) — shows both paths and item counts
  Footer

Active pane (local or remote) is indicated by a highlighted column border.
Tab switches the active pane. j/k/l/h navigate the active pane.
y transfers the highlighted item to the other pane's current directory.
c opens the connect dialog. Escape returns to the main screen.
"""
from __future__ import annotations

import shutil
from pathlib import PurePosixPath

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label

from probefs.config import save_sftp_host
from probefs.core.file_manager import FileManagerCore
from probefs.fs.probe_fs import ProbeFS
from probefs.widgets.directory_list import DirectoryList


class SFTPScreen(Screen):
    """Dual-pane local ↔ remote SFTP file transfer screen."""

    DEFAULT_CSS = """
    SFTPScreen #conn-status-bar {
        height: 1;
        background: $panel;
        border-bottom: solid $primary;
        padding: 0 1;
        color: $text-muted;
    }
    SFTPScreen #dual-panes {
        height: 1fr;
    }
    SFTPScreen .pane-col {
        width: 1fr;
        border: solid $panel;
    }
    SFTPScreen .pane-col.active-col {
        border: solid $primary;
    }
    SFTPScreen .pane-header {
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
        width: 100%;
    }
    SFTPScreen #sftp-status {
        height: 1;
        background: $panel-darken-1;
        layout: horizontal;
        padding: 0 1;
    }
    SFTPScreen #sftp-status Label {
        width: 1fr;
        color: $text-muted;
    }
    SFTPScreen #remote-col DirectoryList {
        opacity: 0.4;
    }
    SFTPScreen #remote-col.connected DirectoryList {
        opacity: 1.0;
    }
    """

    BINDINGS = [
        ("tab", "switch_pane", "Switch pane"),
        ("c", "connect", "Connect"),
        ("y", "transfer", "Transfer"),
        ("escape", "leave", "Back"),
    ]

    # App-level bindings that don't apply to SFTPScreen.
    _BLOCKED_ACTIONS = frozenset({
        "copy", "move", "delete", "rename", "new_file", "new_dir",
        "toggle_hidden", "sort", "filter", "goto", "copy_path",
        "open_default", "shell", "about", "help", "sftp",
    })

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        if action in self._BLOCKED_ACTIONS:
            return False
        return True

    def __init__(self, local_cwd: str | None = None,
                 connect_to: str | None = None) -> None:
        super().__init__()
        self._local_start = local_cwd
        self._connect_to = connect_to
        self._active_pane: str = "local"
        self._local_core: FileManagerCore | None = None
        self._remote_core: FileManagerCore | None = None
        self._connected: bool = False

    def compose(self) -> ComposeResult:
        yield Label("Not connected  ·  press c to connect",
                    id="conn-status-bar")
        with Horizontal(id="dual-panes"):
            with Vertical(id="local-col", classes="pane-col active-col"):
                yield Label("LOCAL", classes="pane-header", id="local-header")
                yield DirectoryList(id="pane-local")
            with Vertical(id="remote-col", classes="pane-col"):
                yield Label("REMOTE  (not connected)", classes="pane-header",
                            id="remote-header")
                yield DirectoryList(id="pane-remote")
        with Horizontal(id="sftp-status"):
            yield Label("", id="status-local")
            yield Label("", id="status-remote")
        yield Footer()

    def on_mount(self) -> None:
        local_fs = ProbeFS()
        start = self._local_start or local_fs.home()
        self._local_core = FileManagerCore(local_fs, start_path=start)
        self._load_local()
        # Auto-open connect dialog after first render
        self.call_after_refresh(self.action_connect)

    # ── Directory loading workers ─────────────────────────────────────────

    @work(thread=True, exclusive=False, exit_on_error=False)
    def _load_local(self) -> None:
        assert self._local_core is not None
        try:
            entries = self._local_core.fs.ls(self._local_core.cwd, detail=True)
        except Exception as exc:
            self.app.notify(f"Local error: {exc}", severity="error")
            return
        self.app.call_from_thread(self._apply_local, entries)

    def _apply_local(self, entries: list[dict]) -> None:
        assert self._local_core is not None
        pane = self.query_one("#pane-local", DirectoryList)
        count = pane.set_entries(entries, show_hidden=self._local_core.show_hidden,
                                 sort_mode=self._local_core.sort_mode)
        self.query_one("#local-header", Label).update(
            f"LOCAL  {self._local_core.cwd}"
        )
        self.query_one("#status-local", Label).update(
            f"local: {self._local_core.cwd}  ·  {count} items"
        )

    @work(thread=True, exclusive=False, exit_on_error=False)
    def _load_remote(self) -> None:
        assert self._remote_core is not None
        try:
            entries = self._remote_core.fs.ls(self._remote_core.cwd, detail=True)
        except Exception as exc:
            self.app.notify(f"Remote error: {exc}", severity="error")
            return
        self.app.call_from_thread(self._apply_remote, entries)

    def _apply_remote(self, entries: list[dict]) -> None:
        assert self._remote_core is not None
        pane = self.query_one("#pane-remote", DirectoryList)
        count = pane.set_entries(entries, show_hidden=self._remote_core.show_hidden,
                                 sort_mode=self._remote_core.sort_mode)
        self.query_one("#remote-header", Label).update(
            f"REMOTE  {self._remote_core.cwd}"
        )
        self.query_one("#status-remote", Label).update(
            f"remote: {self._remote_core.cwd}  ·  {count} items"
        )

    # ── Connection ────────────────────────────────────────────────────────

    def action_connect(self) -> None:
        """Open the SFTP connection dialog."""
        from probefs.widgets.dialogs import ConnectDialog
        self.app.push_screen(
            ConnectDialog(initial_host=self._connect_to or ""),
            self._on_connect_dialog,
        )

    def _on_connect_dialog(self, result: dict | None) -> None:
        if result is None:
            return
        self.app.notify("Connecting…", timeout=10)
        key_path = result["secret"] if result["auth"] == "key" else ""
        self._do_connect(
            result["host"], result["port"], result["username"],
            result["auth"], result["secret"], key_path,
        )

    @work(thread=True, exit_on_error=False)
    def _do_connect(self, host: str, port: int, username: str,
                    auth: str, secret: str, key_path: str) -> None:
        """Worker: establish SFTP connection and list remote home."""
        kwargs: dict = {"host": host, "port": port, "username": username}
        if auth == "key":
            import os
            kwargs["key_filename"] = os.path.expanduser(secret)
        else:
            kwargs["password"] = secret

        try:
            remote_fs = ProbeFS(protocol="sftp", **kwargs)
            remote_home = remote_fs.home()
            remote_fs.ls(remote_home, detail=True)
        except Exception as exc:
            self.app.call_from_thread(
                self.app.notify, f"Connection failed: {exc}", severity="error"
            )
            return

        self.app.call_from_thread(
            self._on_connected, host, port, username, remote_fs, remote_home, key_path
        )

    def _on_connected(self, host: str, port: int, username: str,
                      remote_fs: ProbeFS, remote_home: str,
                      key_path: str) -> None:
        """Main-thread: finalize connection, update UI, save profile."""
        self._remote_core = FileManagerCore(remote_fs, start_path=remote_home)
        self._connected = True

        self.query_one("#conn-status-bar", Label).update(
            f"[bold $success]✓[/]  {username}@{host}:{port}"
            f"  ·  tab switch pane  ·  c reconnect"
        )
        self.query_one("#remote-col").add_class("connected")
        save_sftp_host(host, port, username, key_path)

        self.app.notify(f"Connected to {username}@{host}", timeout=3)
        self._load_remote()

    def _disconnect(self) -> None:
        self._connected = False
        self._remote_core = None
        self.query_one("#conn-status-bar", Label).update(
            "Not connected  ·  press c to connect"
        )
        self.query_one("#remote-col").remove_class("connected")
        self.query_one("#pane-remote", DirectoryList).set_entries([])
        self.query_one("#remote-header", Label).update("REMOTE  (not connected)")
        self.query_one("#status-remote", Label).update("")
        self._active_pane = "local"
        self._refresh_active_border()

    # ── Navigation ────────────────────────────────────────────────────────

    def on_directory_list_entry_highlighted(
        self, event: DirectoryList.EntryHighlighted
    ) -> None:
        event.stop()

    def action_switch_pane(self) -> None:
        if not self._connected:
            return
        self._active_pane = "remote" if self._active_pane == "local" else "local"
        self._refresh_active_border()
        self.query_one(f"#pane-{self._active_pane}", DirectoryList).focus()

    def _refresh_active_border(self) -> None:
        self.query_one("#local-col").set_class(self._active_pane == "local",
                                               "active-col")
        self.query_one("#remote-col").set_class(self._active_pane == "remote",
                                                "active-col")

    def action_cursor_down(self) -> None:
        self.query_one(f"#pane-{self._active_pane}", DirectoryList).move_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one(f"#pane-{self._active_pane}", DirectoryList).move_cursor_up()

    def action_enter_dir(self) -> None:
        core = self._local_core if self._active_pane == "local" else self._remote_core
        if core is None:
            return
        pane = self.query_one(f"#pane-{self._active_pane}", DirectoryList)
        entry = pane.get_highlighted_entry()
        if entry is None or entry.get("type") != "directory":
            return
        name = entry.get("name", "")
        basename = name.split("/")[-1] if "/" in name else name
        core.descend(basename)
        if self._active_pane == "local":
            self._load_local()
        else:
            self._load_remote()

    def action_leave_dir(self) -> None:
        core = self._local_core if self._active_pane == "local" else self._remote_core
        if core is None:
            return
        core.ascend()
        if self._active_pane == "local":
            self._load_local()
        else:
            self._load_remote()

    # ── Transfer ──────────────────────────────────────────────────────────

    def action_transfer(self) -> None:
        """Copy highlighted item from active pane to the other pane."""
        if not self._connected:
            self.app.notify("Not connected — press c to connect",
                            severity="warning")
            return

        if self._active_pane == "local":
            src_core = self._local_core
            dst_core = self._remote_core
            direction = "upload"
        else:
            src_core = self._remote_core
            dst_core = self._local_core
            direction = "download"

        if src_core is None or dst_core is None:
            return

        pane = self.query_one(f"#pane-{self._active_pane}", DirectoryList)
        entry = pane.get_highlighted_entry()
        if entry is None:
            return

        src_path = entry.get("name", "")
        dst_dir = dst_core.cwd
        basename = src_path.split("/")[-1] if "/" in src_path else src_path
        dst_path = str(PurePosixPath(dst_dir) / basename)

        if entry.get("type") == "directory":
            self.app.notify("Directory transfer not yet supported",
                            severity="warning")
            return

        self.app.notify(f"{direction.capitalize()}ing {basename}…", timeout=30)
        self._do_transfer(src_core.fs, src_path, dst_core.fs, dst_path, direction)

    @work(thread=True, exit_on_error=False)
    def _do_transfer(self, src_fs: ProbeFS, src_path: str,
                     dst_fs: ProbeFS, dst_path: str, direction: str) -> None:
        """Worker: stream file between two filesystems."""
        try:
            with src_fs.open_read(src_path) as src:
                with dst_fs.open_write(dst_path) as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
        except Exception as exc:
            self.app.notify(f"Transfer failed: {exc}", severity="error")
            return
        basename = src_path.split("/")[-1] if "/" in src_path else src_path
        self.app.notify(f"{direction.capitalize()}ed {basename}")
        if direction == "upload":
            self.app.call_from_thread(self._load_remote)
        else:
            self.app.call_from_thread(self._load_local)

    # ── Exit ─────────────────────────────────────────────────────────────

    def action_leave(self) -> None:
        """Return to main screen, dropping the SFTP connection."""
        self.app.pop_screen()
