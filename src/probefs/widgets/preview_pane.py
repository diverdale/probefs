"""PreviewPane — right pane with two-mode display.

Mode 1 (file): syntax-highlighted text preview using Rich Syntax + Static.
Mode 2 (directory): file listing using DirectoryList (same widget as left panes).

ContentSwitcher toggles between the two modes without mounting/unmounting.
File reads happen in a @work(thread=True, exclusive=True) worker — exclusive=True
cancels in-flight loads when the cursor moves quickly (race-condition safe).

Message routing: MainScreen posts PreviewPane.CursorChanged(entry) to this widget.
The handler calls show_entry() which dispatches to the correct worker based on type.
This is identical to the Phase 1 interface — MainScreen.py requires no changes.
"""
from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import ContentSwitcher, Static
from textual.worker import get_current_worker

from probefs.widgets.directory_list import DirectoryList

# Truncation notice appended when file exceeds MAX_PREVIEW_BYTES
_TRUNCATION_NOTICE = "\n\n[dim]--- preview truncated at 512 KB ---[/dim]"


class PreviewPane(Widget):
    """Right pane: shows syntax-highlighted file preview or directory listing."""

    class CursorChanged(Message):
        """Posted by MainScreen when the cursor moves to a new entry."""
        def __init__(self, entry: dict) -> None:
            self.entry = entry
            super().__init__()

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial="preview-file"):
            yield Static("", id="preview-file", markup=True)
            yield DirectoryList(id="preview-dir")

    def show_entry(self, entry: dict) -> None:
        """Dispatch preview update based on entry type. Called from CursorChanged handler."""
        entry_type = entry.get("type", "unknown")
        path = entry.get("name", "")
        if entry_type == "directory":
            self._load_dir_preview(path)
        else:
            self._load_file_preview(path)

    @work(thread=True, exclusive=True, exit_on_error=False)
    def _load_file_preview(self, path: str) -> None:
        """Worker: read file via ProbeFS.read_text(), build Rich Syntax, switch to file mode."""
        from rich.syntax import Syntax
        from probefs.fs.probe_fs import MAX_PREVIEW_BYTES

        worker = get_current_worker()

        # self.screen is the MainScreen this widget is mounted inside.
        # Reading .core.fs is safe from a thread — it's set in on_mount before
        # any worker can run, and is never reassigned after that.
        fs = self.screen.core.fs  # type: ignore[attr-defined]

        truncated = False
        try:
            text = fs.read_text(path)
        except ValueError as exc:
            # Binary file detected — show informative message
            if worker.is_cancelled:
                return
            self.app.call_from_thread(self._show_file_content, f"[dim]{exc}[/dim]", is_markup=True)
            return
        except (OSError, PermissionError) as exc:
            if worker.is_cancelled:
                return
            self.app.call_from_thread(self._show_file_content, f"[dim]Cannot read: {exc}[/dim]", is_markup=True)
            return

        # Check if content was capped (file larger than max_bytes)
        import os
        try:
            file_size = os.path.getsize(path)
            if file_size > MAX_PREVIEW_BYTES:
                truncated = True
        except OSError:
            pass

        if worker.is_cancelled:
            return

        # Build Rich Syntax renderable
        # Use 'ansi_dark' theme — respects terminal color scheme (no hardcoded 24-bit colors)
        # Syntax auto-detects lexer from path extension via Pygments; falls back to 'default'
        import pathlib
        extension = pathlib.Path(path).suffix.lstrip(".")
        lexer = extension if extension else "text"
        try:
            syntax = Syntax(
                text,
                lexer=lexer,
                theme="ansi_dark",
                line_numbers=True,
                word_wrap=False,
                indent_guides=False,
            )
        except Exception:
            # Unknown lexer — fall back to plain text
            syntax = Syntax(text, lexer="text", theme="ansi_dark", line_numbers=True)

        if worker.is_cancelled:
            return

        self.app.call_from_thread(self._show_syntax, syntax, truncated)

    def _show_syntax(self, syntax: object, truncated: bool) -> None:
        """Main-thread: switch to file mode, update Static with Rich Syntax renderable."""
        switcher = self.query_one(ContentSwitcher)
        switcher.current = "preview-file"
        static = self.query_one("#preview-file", Static)
        static.update(syntax)
        if truncated:
            # Append truncation notice as a second update — appending text after a Syntax
            # renderable is not directly possible, so we compose a Group renderable.
            from rich.console import Group
            from rich.text import Text
            notice = Text("\n--- preview truncated at 512 KB ---", style="dim")
            static.update(Group(syntax, notice))

    def _show_file_content(self, markup_text: str, *, is_markup: bool = True) -> None:
        """Main-thread: switch to file mode, show plain markup text (error/binary messages)."""
        switcher = self.query_one(ContentSwitcher)
        switcher.current = "preview-file"
        self.query_one("#preview-file", Static).update(markup_text)

    @work(thread=True, exclusive=True, exit_on_error=False)
    def _load_dir_preview(self, path: str) -> None:
        """Worker: list directory contents, post to preview-dir DirectoryList."""
        worker = get_current_worker()
        fs = self.screen.core.fs  # type: ignore[attr-defined]
        try:
            entries = fs.ls(path, detail=True)
        except (OSError, PermissionError) as exc:
            if worker.is_cancelled:
                return
            self.app.call_from_thread(self._show_file_content, f"[dim]Cannot read directory: {exc}[/dim]", is_markup=True)
            return

        if worker.is_cancelled:
            return

        self.app.call_from_thread(self._show_dir_entries, entries, self.screen.core.show_hidden)

    def _show_dir_entries(self, entries: list[dict], show_hidden: bool) -> None:
        """Main-thread: switch to directory mode, populate DirectoryList."""
        switcher = self.query_one(ContentSwitcher)
        switcher.current = "preview-dir"
        dir_list = self.query_one("#preview-dir", DirectoryList)
        dir_list.set_entries(entries, show_hidden=show_hidden)

    def on_preview_pane_cursor_changed(self, event: CursorChanged) -> None:
        """Handle cursor change — dispatch to correct worker based on entry type."""
        self.show_entry(event.entry)
