"""Reusable modal dialog widgets for file operation confirmations and input.

ALL dismiss() calls in message handlers must be called WITHOUT await.
Awaiting dismiss() from a screen's own message handler raises ScreenError.
See: Textual 8.0.2 screen.py lines 1892-1925.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

_HELP_TEXT = """\
[bold $accent]Navigation[/]
  [bold]j / ↓[/]       Move cursor down
  [bold]k / ↑[/]       Move cursor up
  [bold]l / Enter[/]   Enter directory / open file
  [bold]h / ←[/]       Go up to parent directory
  [bold]ctrl+o[/]      Navigate back in history
  [bold]ctrl+i[/]      Navigate forward in history
  [bold]g[/]           Go to path (jump anywhere)

[bold $accent]View[/]
  [bold].[/]           Toggle hidden files (dotfiles)
  [bold]s[/]           Cycle sort mode  (name ↑ → name ↓ → size ↓ → date ↓)
  [bold]/[/]           Filter files by name  (Esc cancel · Enter keep)

[bold $accent]File Operations[/]
  [bold]y[/]           Copy selected item
  [bold]p[/]           Move selected item
  [bold]d[/]           Delete — sends to OS Trash (safe, reversible)
  [bold]r[/]           Rename selected item
  [bold]n[/]           New file in current directory
  [bold]ctrl+n[/]      New directory in current directory

[bold $accent]Clipboard & Launch[/]
  [bold]Y[/]           Copy current path to clipboard
  [bold]o[/]           Open with system default application
  [bold]![/]           Drop to shell in current directory

[bold $accent]App[/]
  [bold]?[/]           Show this help
  [bold]a[/]           About probefs
  [bold]ctrl+s[/]      Open SFTP screen
  [bold]ctrl+q[/]      Quit
  [bold]ctrl+c[/]      Quit (alternate)
"""


class ConfirmDialog(ModalScreen[bool]):
    """Confirmation modal. Returns True if confirmed, False if cancelled.

    Usage:
        def action_delete(self) -> None:
            def _on_confirmed(result: bool | None) -> None:
                if result:
                    self._do_trash(path)
            self.app.push_screen(ConfirmDialog("Send 'file.txt' to trash?"), _on_confirmed)
    """

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }
    ConfirmDialog > Vertical {
        background: $surface;
        padding: 1 2;
        width: auto;
        min-width: 40;
        max-width: 60;
        height: auto;
        border: tall $primary;
    }
    ConfirmDialog Label {
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }
    ConfirmDialog Horizontal {
        width: 100%;
        height: auto;
        align: center middle;
    }
    ConfirmDialog Button {
        width: auto;
        min-width: 10;
        margin: 0 1;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._message)
            with Horizontal():
                yield Button("Yes", variant="error", id="yes")
                yield Button("Cancel", variant="default", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # No await — calling await self.dismiss() from a message handler on the
        # same ModalScreen raises ScreenError (Textual 8.0.2 screen.py line 1898).
        self.dismiss(event.button.id == "yes")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(False)


class InputDialog(ModalScreen[str | None]):
    """Text input modal. Returns the entered string or None if cancelled.

    Supports pre-populated initial value (used for rename — shows current name).
    Enter key or OK button submits. Cancel button or Escape dismisses with None.

    Usage:
        def action_rename(self) -> None:
            def _on_name(new_name: str | None) -> None:
                if new_name:
                    self._do_rename(old_path, new_name)
            self.app.push_screen(
                InputDialog("Rename to:", initial_value="current_name.txt"),
                _on_name,
            )
    """

    DEFAULT_CSS = """
    InputDialog {
        align: center middle;
    }
    InputDialog > Vertical {
        background: $surface;
        padding: 1 2;
        width: auto;
        min-width: 50;
        max-width: 70;
        height: auto;
        border: tall $primary;
    }
    InputDialog Label {
        width: 100%;
        margin-bottom: 1;
    }
    InputDialog Input {
        width: 100%;
        margin-bottom: 1;
    }
    InputDialog Horizontal {
        width: 100%;
        height: auto;
        align: right middle;
    }
    InputDialog Button {
        width: auto;
        min-width: 10;
        margin: 0 0 0 1;
    }
    """

    def __init__(self, prompt: str, initial_value: str = "", select_all: bool = True) -> None:
        super().__init__()
        self._prompt = prompt
        self._initial = initial_value
        self._select_all = select_all

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._prompt)
            yield Input(value=self._initial, id="name-input")
            with Horizontal():
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Position cursor in pre-populated input. Select all for name entry;
        cursor at end for path entry (move/copy) so user can edit the path."""
        inp = self.query_one("#name-input", Input)
        if self._select_all:
            inp.action_select_all()
        else:
            inp.cursor_position = len(inp.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter key in the Input field submits the dialog."""
        value = event.value.strip()
        self.dismiss(value if value else None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            value = self.query_one("#name-input", Input).value.strip()
            self.dismiss(value if value else None)
        else:
            self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


_ABOUT_ART = """\
[bold $primary]  ┌─┐┬─┐┌─┐┌┐ ┌─┐┌─┐┌─┐[/]
[bold $primary]  ├─┘├┬┘│ │├┴┐├─ ├─ └─┐[/]
[bold $primary]  ┴  ┴└─└─┘└─┘└─┘┴  └─┘[/]

[dim]  a keyboard-driven TUI file browser[/]

[bold]   .---------------------------.[/]
[bold]   |[/] [dim]/home/you[/][bold]                |[/]
[bold]   |[/]   [bold $accent]> probefs/[/]  [dim]← hi :)[/][bold]   |[/]
[bold]   |[/]     [dim]Documents/[/][bold]           |[/]
[bold]   |[/]     [dim]Downloads/[/][bold]           |[/]
[bold]   |[/]     [dim]Music/[/][bold]               |[/]
[bold]   |___________________________|[/]
[bold]   | [/][dim]j[/][bold] [/][dim]k[/][bold] [/][dim]l[/][bold] [/][dim]h[/][bold] [/][dim].[/][bold] [/][dim]s[/][bold] [/][dim]/[/][bold] [/][dim]?[/][bold] [/][dim]![/][bold] [/][dim]q[/][bold]        |[/]
[bold]   '---------------------------'[/]

  [dim]Built with[/] [bold]Python[/] [dim]&[/] [bold]Textual[/]
  [dim]MIT License[/]
"""


class AboutDialog(ModalScreen[None]):
    """Silly ASCII about screen."""

    DEFAULT_CSS = """
    AboutDialog {
        align: center middle;
    }
    AboutDialog > Vertical {
        background: $surface;
        padding: 1 2;
        width: 38;
        height: auto;
        border: tall $primary;
    }
    AboutDialog Static {
        width: 100%;
    }
    AboutDialog Button {
        width: 100%;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(_ABOUT_ART, markup=True)
            yield Button("Close", variant="primary", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key in ("escape", "enter", "a"):
            self.dismiss(None)


class HelpDialog(ModalScreen[None]):
    """Full keybinding reference. Scrollable, dismissed by Escape or Close."""

    DEFAULT_CSS = """
    HelpDialog {
        align: center middle;
    }
    HelpDialog > Vertical {
        background: $surface;
        padding: 1 2;
        width: 62;
        height: 80%;
        border: tall $primary;
    }
    HelpDialog #help-title {
        text-align: center;
        width: 100%;
        color: $text;
        margin-bottom: 1;
    }
    HelpDialog VerticalScroll {
        width: 100%;
        height: 1fr;
        border: none;
    }
    HelpDialog Static {
        width: 100%;
    }
    HelpDialog Button {
        width: 100%;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("probefs — keyboard reference", id="help-title")
            with VerticalScroll():
                yield Static(_HELP_TEXT, markup=True)
            yield Button("Close", variant="primary", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key in ("escape", "enter", "question_mark"):
            self.dismiss(None)


class ConnectDialog(ModalScreen):
    """SFTP connection dialog.

    Dismisses with a dict {host, port, username, auth, secret} on Connect,
    or None if the user cancels.
    """

    DEFAULT_CSS = """
    ConnectDialog {
        align: center middle;
    }
    ConnectDialog > Vertical {
        background: $surface;
        padding: 1 2;
        width: 60;
        height: auto;
        border: tall $primary;
    }
    ConnectDialog #connect-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        color: $accent;
    }
    ConnectDialog Vertical {
        height: auto;
    }
    ConnectDialog Label.field-label {
        width: 100%;
        color: $text-muted;
        height: 1;
    }
    ConnectDialog Input {
        width: 100%;
        height: 1;
        border: none;
        padding: 0;
        background: $surface;
    }
    ConnectDialog Select {
        width: 100%;
        height: 1;
    }
    ConnectDialog Select SelectCurrent {
        border: none !important;
        padding: 0 1;
        height: 1;
    }
    ConnectDialog #row-port-user {
        height: auto;
        width: 100%;
    }
    ConnectDialog #port-col {
        width: 14;
        margin-right: 1;
    }
    ConnectDialog #user-col {
        width: 1fr;
    }
    ConnectDialog #btn-row {
        width: 100%;
        height: auto;
        align: right middle;
        margin-top: 1;
    }
    ConnectDialog Button {
        width: auto;
        min-width: 10;
        margin: 0 0 0 1;
    }
    """

    def __init__(self, initial_host: str = "") -> None:
        super().__init__()
        self._initial_host = initial_host

    def compose(self) -> ComposeResult:
        from probefs.config import load_sftp_hosts
        profiles = load_sftp_hosts()

        with Vertical():
            yield Label("SFTP Connect", id="connect-title")
            yield Label("Host", classes="field-label")
            yield Input(self._initial_host, placeholder="hostname or IP",
                        id="host-input")
            with Horizontal(id="row-port-user"):
                with Vertical(id="port-col"):
                    yield Label("Port", classes="field-label")
                    yield Input("22", placeholder="22", id="port-input")
                with Vertical(id="user-col"):
                    yield Label("User", classes="field-label")
                    yield Input("", placeholder="username", id="user-input")
            yield Label("Auth", classes="field-label")
            yield Select(
                [("Password", "password"), ("SSH Key", "key")],
                value="password",
                id="auth-select",
                allow_blank=False,
            )
            yield Label("Password", classes="field-label", id="secret-label")
            yield Input("", password=True,
                        placeholder="password or ~/.ssh/id_rsa",
                        id="secret-input")
            if profiles:
                yield Label("Saved profiles", classes="field-label")
                yield Select(
                    [(p["name"], p["name"]) for p in profiles],
                    prompt="Load a saved profile…",
                    id="profile-select",
                    allow_blank=True,
                )
            with Horizontal(id="btn-row"):
                yield Button("Connect", variant="primary", id="connect")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#host-input", Input).focus()

    def _get_values(self) -> tuple[str, int, str, str, str]:
        host = self.query_one("#host-input", Input).value.strip()
        port_str = self.query_one("#port-input", Input).value.strip()
        username = self.query_one("#user-input", Input).value.strip()
        auth_val = self.query_one("#auth-select", Select).value
        auth = str(auth_val) if auth_val is not Select.BLANK else "password"
        secret = self.query_one("#secret-input", Input).value
        try:
            port = int(port_str)
        except ValueError:
            port = 22
        return host, port, username, auth, secret

    def _submit(self) -> None:
        host, port, username, auth, secret = self._get_values()
        if not host:
            self.query_one("#host-input", Input).focus()
            return
        if not username:
            self.query_one("#user-input", Input).focus()
            return
        self.dismiss({"host": host, "port": port, "username": username,
                      "auth": auth, "secret": secret})

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "connect":
            self._submit()
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter in any field submits the form."""
        self._submit()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)

    def on_select_changed(self, event: Select.Changed) -> None:
        event.stop()
        if event.select.id == "profile-select" and event.value is not Select.BLANK:
            from probefs.config import load_sftp_hosts
            profiles = load_sftp_hosts()
            profile = next(
                (p for p in profiles if p.get("name") == event.value), None
            )
            if profile:
                self.query_one("#host-input", Input).value = str(profile.get("host", ""))
                self.query_one("#port-input", Input).value = str(profile.get("port", 22))
                self.query_one("#user-input", Input).value = str(profile.get("username", ""))
                key_path = str(profile.get("key_path", ""))
                if key_path:
                    self.query_one("#auth-select", Select).value = "key"
                    inp = self.query_one("#secret-input", Input)
                    inp.password = False
                    inp.value = key_path
        elif event.select.id == "auth-select":
            inp = self.query_one("#secret-input", Input)
            inp.password = (event.value == "password")
            inp.placeholder = (
                "password" if event.value == "password" else "~/.ssh/id_rsa"
            )
            inp.value = ""
            self.query_one("#secret-label", Label).update(
                "Password" if event.value == "password" else "Key path"
            )
