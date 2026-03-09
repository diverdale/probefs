"""Reusable modal dialog widgets for file operation confirmations and input.

ALL dismiss() calls in message handlers must be called WITHOUT await.
Awaiting dismiss() from a screen's own message handler raises ScreenError.
See: Textual 8.0.2 screen.py lines 1892-1925.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


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
    ConfirmDialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._message)
            yield Button("Yes", variant="error", id="yes")
            yield Button("Cancel", variant="primary", id="cancel")

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
    InputDialog Button {
        margin: 0 1;
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
            yield Button("OK", variant="primary", id="ok")
            yield Button("Cancel", id="cancel")

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
