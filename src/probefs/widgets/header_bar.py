"""HeaderBar — top cockpit bar: app name + breadcrumb, user@host + live clock.

Left side shows the app name and a chevron breadcrumb of the current path
(home collapsed to '~'). Right side shows 'user@host · HH:MM:SS' with a clock
that ticks once a second.

The breadcrumb path is driven by MainScreen via the reactive `path` attribute.
user@host reflects the local machine (the main screen is always local); these
are process identity (getpass/socket), not filesystem I/O, so they do not go
through the FAL.
"""
from __future__ import annotations

import datetime
import getpass
import os
import socket

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

from probefs.config import load_config
from probefs.rendering.cockpit import build_breadcrumb


class HeaderBar(Widget):
    """Top instrument-panel bar with breadcrumb and live clock."""

    DEFAULT_CSS = """
    HeaderBar {
        height: 1;
        background: $panel-darken-1;
    }
    HeaderBar #hdr-row {
        height: 1;
        padding: 0 1;
    }
    HeaderBar #hdr-left {
        width: 1fr;
        color: $text;
    }
    HeaderBar #hdr-right {
        width: auto;
        color: $text-muted;
        text-align: right;
    }
    """

    path: reactive[str] = reactive("")
    clock: reactive[str] = reactive("")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._ascii: bool = bool(load_config().get("cockpit_ascii", False))
        self._home: str = os.path.expanduser("~")
        self._userhost: str = f"{getpass.getuser()}@{socket.gethostname()}"

    def compose(self) -> ComposeResult:
        with Horizontal(id="hdr-row"):
            yield Label("", id="hdr-left")
            yield Label("", id="hdr-right")

    def on_mount(self) -> None:
        self._tick()
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        self.clock = datetime.datetime.now().strftime("%H:%M:%S")

    def watch_path(self, value: str) -> None:
        crumb = build_breadcrumb(value, self._home, ascii=self._ascii) if value else ""
        sep = " " if self._ascii else "  "
        self.query_one("#hdr-left", Label).update(f"probefs{sep}{crumb}")

    def watch_clock(self, value: str) -> None:
        self.query_one("#hdr-right", Label).update(f"{self._userhost} · {value}")
