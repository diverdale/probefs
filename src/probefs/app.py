"""ProbeFSApp — Textual application entry point for probefs."""
from __future__ import annotations

from textual.app import App
from textual.binding import Binding

from probefs.screens.main import MainScreen


class ProbeFSApp(App):
    """Three-pane keyboard-driven file browser."""

    CSS_PATH = "probefs.tcss"

    SCREENS = {"main": MainScreen}

    BINDINGS = [
        Binding("j", "screen.cursor_down", "Down", priority=True, show=False),
        Binding("down", "screen.cursor_down", "Down", priority=True, show=False),
        Binding("k", "screen.cursor_up", "Up", priority=True, show=False),
        Binding("up", "screen.cursor_up", "Up", priority=True, show=False),
        Binding("l", "screen.enter_dir", "Enter dir", priority=True, show=False),
        Binding("enter", "screen.enter_dir", "Enter dir", priority=True, show=False),
        Binding("h", "screen.leave_dir", "Leave dir", priority=True, show=False),
        Binding("backspace", "screen.leave_dir", "Leave dir", priority=True, show=False),
        Binding("ctrl+c", "quit", "Quit", priority=True, show=False),
    ]

    def on_mount(self) -> None:
        """Push main screen on launch."""
        self.push_screen("main")


def main() -> None:
    """Entry point for `uv run probefs` and `probefs.app:main`."""
    ProbeFSApp().run()
