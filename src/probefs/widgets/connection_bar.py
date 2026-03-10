"""ConnectionBar — SFTP connection form widget.

Two visual states managed via ContentSwitcher:
  "form"   — editable fields (host, port, user, auth, secret) + Connect button
  "status" — single line showing user@host:port + Disconnect button

Posts ConnectRequested when Connect is clicked.
Posts DisconnectRequested when Disconnect is clicked.
If profiles exist in ~/.probefs/sftp_hosts.yaml, a Select widget lets the
user pre-fill the form from a saved profile.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, ContentSwitcher, Input, Label, Select

from probefs.config import load_sftp_hosts


class ConnectionBar(Widget):
    """SFTP connection form. Switches between form and connected-status views."""

    DEFAULT_CSS = """
    ConnectionBar {
        height: auto;
        background: $panel;
        border-bottom: solid $primary;
        padding: 0 1;
    }
    ConnectionBar ContentSwitcher {
        height: auto;
    }
    ConnectionBar Vertical {
        height: auto;
    }
    ConnectionBar Horizontal {
        height: auto;
        width: 100%;
        align: left middle;
        padding: 0 0 0 0;
    }
    ConnectionBar Label.field-label {
        width: auto;
        padding: 0 1 0 0;
        color: $text-muted;
    }
    ConnectionBar Input {
        height: 1;
        border: none;
        padding: 0;
        background: $surface;
        width: 20;
        margin: 0 1 0 0;
    }
    ConnectionBar #port-input {
        width: 6;
    }
    ConnectionBar Select {
        width: 18;
        height: 1;
        margin: 0 1 0 0;
    }
    ConnectionBar Select SelectCurrent {
        border: none !important;
        padding: 0 1;
        height: 1;
    }
    ConnectionBar Button {
        height: 1;
        min-width: 12;
        margin: 0 0 0 1;
        border: none;
    }
    ConnectionBar #conn-status {
        height: 1;
        layout: horizontal;
        align: left middle;
    }
    ConnectionBar #status-label {
        width: 1fr;
        color: $success;
    }
    """

    class ConnectRequested(Message):
        """Posted when the user clicks Connect."""
        def __init__(self, host: str, port: int, username: str,
                     auth: str, secret: str) -> None:
            self.host = host
            self.port = port
            self.username = username
            self.auth = auth          # "password" or "key"
            self.secret = secret      # password text OR key file path
            super().__init__()

    class DisconnectRequested(Message):
        """Posted when the user clicks Disconnect."""

    def __init__(self, initial_host: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._initial_host = initial_host or ""

    def compose(self) -> ComposeResult:
        profiles = load_sftp_hosts()
        profile_options = [(p["name"], p["name"]) for p in profiles]

        with ContentSwitcher(initial="conn-form"):
            with Vertical(id="conn-form"):
                with Horizontal():
                    yield Label("Host", classes="field-label")
                    yield Input(self._initial_host, placeholder="hostname or IP",
                                id="host-input")
                    yield Label("Port", classes="field-label")
                    yield Input("22", placeholder="22", id="port-input")
                    yield Label("User", classes="field-label")
                    yield Input("", placeholder="username", id="user-input")
                    if profile_options:
                        yield Select(
                            [(name, name) for name, _ in profile_options],
                            prompt="Profiles...",
                            id="profile-select",
                            allow_blank=True,
                        )
                    yield Button("Connect", variant="primary", id="btn-connect")
                with Horizontal():
                    yield Label("Auth", classes="field-label")
                    yield Select(
                        [("Password", "password"), ("SSH Key", "key")],
                        value="password",
                        id="auth-select",
                        allow_blank=False,
                    )
                    yield Label("Pass / Key path", classes="field-label",
                                id="secret-label")
                    yield Input("", placeholder="password or ~/.ssh/id_rsa",
                                password=True, id="secret-input")
            with Horizontal(id="conn-status"):
                yield Label("", id="status-label")
                yield Button("Disconnect", variant="warning", id="btn-disconnect")

    def set_connected(self, host: str, port: int, username: str) -> None:
        """Switch to connected status view."""
        self.query_one("#status-label", Label).update(
            f"[bold $success]✓[/]  {username}@{host}:{port}"
        )
        self.query_one(ContentSwitcher).current = "conn-status"

    def set_disconnected(self) -> None:
        """Switch back to form view."""
        self.query_one(ContentSwitcher).current = "conn-form"
        self.query_one("#secret-input", Input).value = ""   # clear password

    def get_form_values(self) -> tuple[str, int, str, str, str]:
        """Return (host, port, username, auth, secret) from the form."""
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "btn-connect":
            host, port, username, auth, secret = self.get_form_values()
            if host and username:
                self.post_message(
                    self.ConnectRequested(host, port, username, auth, secret)
                )
        elif event.button.id == "btn-disconnect":
            self.post_message(self.DisconnectRequested())

    def on_select_changed(self, event: Select.Changed) -> None:
        event.stop()
        if event.select.id == "profile-select" and event.value is not Select.BLANK:
            # Pre-fill form from saved profile
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
                    auth_sel = self.query_one("#auth-select", Select)
                    auth_sel.value = "key"
                    secret_inp = self.query_one("#secret-input", Input)
                    secret_inp.password = False
                    secret_inp.value = key_path
        elif event.select.id == "auth-select":
            # Toggle password masking based on auth type
            secret_inp = self.query_one("#secret-input", Input)
            secret_inp.password = (event.value == "password")
            secret_inp.placeholder = (
                "password" if event.value == "password" else "~/.ssh/id_rsa"
            )
            secret_inp.value = ""
