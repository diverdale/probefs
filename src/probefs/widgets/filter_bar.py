"""FilterBar — one-line overlay filter widget for live filename filtering.

Displayed at bottom (same dock as Footer). MainScreen swaps Footer/FilterBar
visibility so they never overlap. Escape deactivates and restores Footer.
Enter keeps filter active and closes the bar input (filter persists in the list).
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class FilterBar(Widget, can_focus=True):
    """One-line filter bar docked at bottom. Hidden by default."""

    DEFAULT_CSS = """
    FilterBar {
        height: 1;
        dock: bottom;
        display: none;
        layout: horizontal;
        background: $panel-darken-1;
        padding: 0 1;
    }
    FilterBar #filter-prompt {
        width: auto;
        color: $warning;
    }
    FilterBar #filter-text {
        width: 1fr;
        color: $text;
    }
    FilterBar #filter-hint {
        width: auto;
        color: $text-muted;
    }
    """

    _text: reactive[str] = reactive("")

    class FilterChanged(Message):
        """Posted on every keystroke with current filter text."""
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class FilterCleared(Message):
        """Posted when Escape is pressed — filter should be removed."""

    class FilterSubmitted(Message):
        """Posted when Enter is pressed — keep filter active, close bar."""
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Label("/ ", id="filter-prompt")
        yield Label("", id="filter-text")
        yield Label("  Esc cancel  Enter keep", id="filter-hint")

    def activate(self) -> None:
        """Show bar, clear text, take focus."""
        self._text = ""
        self.display = True
        self.focus()

    def deactivate(self) -> None:
        """Hide bar and post FilterCleared."""
        self.display = False
        self.post_message(self.FilterCleared())

    def watch__text(self, value: str) -> None:
        """Update display label with text + block cursor."""
        self.query_one("#filter-text", Label).update(value + "█")

    def on_key(self, event) -> None:
        """Handle keystrokes directly — keeps FilterBar at 1-line height."""
        key = event.key
        if key == "escape":
            event.stop()
            self.deactivate()
        elif key == "enter":
            event.stop()
            text = self._text
            self.display = False
            self.post_message(self.FilterSubmitted(text))
        elif key == "backspace":
            event.stop()
            self._text = self._text[:-1]
            self.post_message(self.FilterChanged(self._text))
        elif event.character and event.character.isprintable():
            event.stop()
            self._text += event.character
            self.post_message(self.FilterChanged(self._text))
