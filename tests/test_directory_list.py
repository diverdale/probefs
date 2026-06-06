"""Tests for DirectoryList cursor positioning.

The parent pane must highlight the entry corresponding to the current
working directory, not always row 0. These tests cover the index-finding
logic (pure) and the widget cursor move (integration).
"""
from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.widgets import DataTable

from probefs.widgets.directory_list import DirectoryList, _index_of_basename


# ---------------------------------------------------------------------------
# Pure helper: _index_of_basename
# ---------------------------------------------------------------------------


def test_index_of_basename_finds_match() -> None:
    entries = [
        {"name": "/a/foo", "type": "directory"},
        {"name": "/a/bar", "type": "directory"},
    ]
    assert _index_of_basename(entries, "bar") == 1


def test_index_of_basename_returns_none_when_absent() -> None:
    entries = [{"name": "/a/foo", "type": "directory"}]
    assert _index_of_basename(entries, "missing") is None


def test_index_of_basename_returns_first_match() -> None:
    entries = [
        {"name": "/a/dup", "type": "directory"},
        {"name": "/b/dup", "type": "directory"},
    ]
    assert _index_of_basename(entries, "dup") == 0


def test_index_of_basename_empty_basename_returns_none() -> None:
    """Root cwd has basename '' — must not match any real entry."""
    entries = [{"name": "/a/foo", "type": "directory"}]
    assert _index_of_basename(entries, "") is None


# ---------------------------------------------------------------------------
# Widget integration: index_of + highlight_index
# ---------------------------------------------------------------------------


class _Harness(App):
    def compose(self) -> ComposeResult:
        yield DirectoryList()


@pytest.mark.asyncio
async def test_index_of_uses_visible_order() -> None:
    """index_of returns the post-sort visible row index, not the input order."""
    app = _Harness()
    async with app.run_test():
        dl = app.query_one(DirectoryList)
        # Input order is foo, bar; after name_asc sort dirs become bar(0), foo(1)
        dl.set_entries([
            {"name": "/a/foo", "type": "directory"},
            {"name": "/a/bar", "type": "directory"},
        ])
        assert dl.index_of("bar") == 0
        assert dl.index_of("foo") == 1
        assert dl.index_of("nope") is None


@pytest.mark.asyncio
async def test_highlight_index_moves_cursor() -> None:
    app = _Harness()
    async with app.run_test():
        dl = app.query_one(DirectoryList)
        dl.set_entries([
            {"name": "/a/bar", "type": "directory"},
            {"name": "/a/foo", "type": "directory"},
        ])
        dl.highlight_index(1)
        assert dl.query_one(DataTable).cursor_row == 1


# ---------------------------------------------------------------------------
# End-to-end: parent pane highlights the current directory
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parent_pane_highlights_current_dir(tmp_path, monkeypatch) -> None:
    """The parent pane cursor lands on the dir we launched inside, not row 0."""
    (tmp_path / "aaa").mkdir()
    (tmp_path / "zzz_target").mkdir()
    monkeypatch.chdir(tmp_path / "zzz_target")

    from probefs.app import ProbeFSApp

    app = ProbeFSApp()
    async with app.run_test() as pilot:
        await pilot.pause()  # let on_mount push + mount MainScreen
        await app.workers.wait_for_complete()
        await pilot.pause()  # process the DirectoryLoaded messages
        parent = app.screen.query_one("#pane-parent", DirectoryList)
        highlighted = parent.get_highlighted_entry()
        assert highlighted is not None
        assert highlighted["name"].split("/")[-1] == "zzz_target"


@pytest.mark.asyncio
async def test_ascend_highlights_child_just_left(tmp_path, monkeypatch) -> None:
    """Pressing 'h' lands the current-pane cursor on the dir we came out of."""
    (tmp_path / "aaa").mkdir()
    (tmp_path / "zzz_start").mkdir()
    monkeypatch.chdir(tmp_path / "zzz_start")

    from probefs.app import ProbeFSApp

    app = ProbeFSApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("h")  # ascend into tmp_path
        await app.workers.wait_for_complete()
        await pilot.pause()
        current = app.screen.query_one("#pane-current", DirectoryList)
        highlighted = current.get_highlighted_entry()
        assert highlighted is not None
        assert highlighted["name"].split("/")[-1] == "zzz_start"


# ---------------------------------------------------------------------------
# Pane title + active state + visible counts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_visible_counts() -> None:
    app = _Harness()
    async with app.run_test():
        dl = app.query_one(DirectoryList)
        dl.set_entries([
            {"name": "/a/d1", "type": "directory"},
            {"name": "/a/d2", "type": "directory"},
            {"name": "/a/f1", "type": "file"},
        ])
        assert dl.visible_counts() == (2, 1)


@pytest.mark.asyncio
async def test_set_title_active_marker_and_class() -> None:
    from textual.widgets import Label
    app = _Harness()
    async with app.run_test():
        dl = app.query_one(DirectoryList)
        dl.set_title("probefs", active=True)
        title = str(app.query_one("#pane-title", Label).render())
        assert "probefs" in title
        assert "◆" in title
        assert dl.has_class("active")
