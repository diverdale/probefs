"""Tests for the pure cockpit/instrument formatting helpers."""
from __future__ import annotations

import pytest

from probefs.rendering.cockpit import (
    build_breadcrumb,
    build_gauge,
    build_lamps,
    build_preview_meta,
    gauge_color_tier,
)


# ---------------------------------------------------------------------------
# build_breadcrumb
# ---------------------------------------------------------------------------


def test_breadcrumb_collapses_home() -> None:
    assert build_breadcrumb("/home/dale/dev/probefs", "/home/dale") == "~ › dev › probefs"


def test_breadcrumb_home_itself() -> None:
    assert build_breadcrumb("/home/dale", "/home/dale") == "~"


def test_breadcrumb_root() -> None:
    assert build_breadcrumb("/", "/home/dale") == "/"


def test_breadcrumb_absolute_non_home() -> None:
    assert build_breadcrumb("/usr/bin", "/home/dale") == "/ › usr › bin"


def test_breadcrumb_ascii_separator() -> None:
    assert build_breadcrumb("/usr/bin", "/home/dale", ascii=True) == "/ > usr > bin"


# ---------------------------------------------------------------------------
# gauge_color_tier
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "pct,expected",
    [(0, "green"), (69, "green"), (70, "yellow"), (89, "yellow"), (90, "red"), (100, "red")],
)
def test_gauge_color_tier(pct: float, expected: str) -> None:
    assert gauge_color_tier(pct) == expected


# ---------------------------------------------------------------------------
# build_gauge
# ---------------------------------------------------------------------------


def test_gauge_half_full() -> None:
    g = build_gauge(used=50, total=100, width=10)
    assert g.plain == "[█████░░░░░] 50%"


def test_gauge_ascii() -> None:
    g = build_gauge(used=50, total=100, width=10, ascii=True)
    assert g.plain == "[#####-----] 50%"


def test_gauge_zero_total_is_safe() -> None:
    g = build_gauge(used=0, total=0, width=10)
    assert g.plain == "[░░░░░░░░░░] 0%"


def test_gauge_full() -> None:
    g = build_gauge(used=100, total=100, width=10)
    assert g.plain == "[██████████] 100%"


# ---------------------------------------------------------------------------
# build_lamps
# ---------------------------------------------------------------------------


def test_lamps_contains_all_fields() -> None:
    text = build_lamps(
        connection="LOCAL", sort_label="name↑", hidden=False, filter_active=False
    ).plain
    assert "LOCAL" in text
    assert "name↑" in text
    assert "hidden" in text
    assert "filter" in text


def test_lamps_lit_glyph_when_active() -> None:
    on = build_lamps(connection="LOCAL", sort_label="name↑", hidden=True, filter_active=True).plain
    off = build_lamps(connection="LOCAL", sort_label="name↑", hidden=False, filter_active=False).plain
    assert "●" in on
    assert "○" in off


def test_lamps_ascii() -> None:
    text = build_lamps(
        connection="LOCAL", sort_label="name↑", hidden=True, filter_active=False, ascii=True
    ).plain
    assert "[*]" in text  # hidden is on
    assert "[ ]" in text  # filter is off


# ---------------------------------------------------------------------------
# build_preview_meta
# ---------------------------------------------------------------------------


def test_preview_meta_file() -> None:
    entry = {
        "name": "/a/CLAUDE.md",
        "type": "file",
        "size": 1843,
        "mode": 0o100644,
        "uid": 0,
        "mtime": 0,
    }
    meta = build_preview_meta(entry)
    assert meta.startswith("CLAUDE.md")
    assert "1.8K" in meta or "1.8 K" in meta
    assert "rw-r--r--" in meta


def test_preview_meta_directory_shows_dash_size() -> None:
    entry = {"name": "/a/docs", "type": "directory", "mode": 0o040755, "uid": 0, "mtime": 0}
    meta = build_preview_meta(entry)
    assert meta.startswith("docs")
    assert " · - · " in meta


# ---------------------------------------------------------------------------
# HeaderBar widget (integration)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_header_bar_shows_breadcrumb() -> None:
    from textual.app import App, ComposeResult
    from textual.widgets import Label
    from probefs.widgets.header_bar import HeaderBar

    class _Harness(App):
        def compose(self) -> ComposeResult:
            yield HeaderBar()

    app = _Harness()
    async with app.run_test():
        hdr = app.query_one(HeaderBar)
        hdr.path = "/home/dale/dev/probefs"
        left = hdr.query_one("#hdr-left", Label)
        assert "probefs" in str(left.render())
        right = hdr.query_one("#hdr-right", Label)
        assert "@" in str(right.render())  # user@host


# ---------------------------------------------------------------------------
# PreviewPane metadata header (integration)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_pane_header_shows_meta() -> None:
    from textual.app import App, ComposeResult
    from textual.widgets import Label
    from probefs.widgets.preview_pane import PreviewPane

    class _Harness(App):
        def compose(self) -> ComposeResult:
            yield PreviewPane()

    app = _Harness()
    async with app.run_test():
        pane = app.query_one(PreviewPane)
        pane.update_meta({"name": "/a/CLAUDE.md", "type": "file", "size": 1843,
                          "mode": 0o100644, "uid": 0, "mtime": 0})
        header = str(app.query_one("#preview-header", Label).render())
        assert "CLAUDE.md" in header
        assert "rw-r--r--" in header


# ---------------------------------------------------------------------------
# Full-app cockpit smoke test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cockpit_chrome_renders_in_app(tmp_path, monkeypatch) -> None:
    """The real app shows the breadcrumb, disk gauge, and an active current pane."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "file.txt").write_text("hi")
    monkeypatch.chdir(tmp_path)

    from textual.widgets import Label
    from probefs.app import ProbeFSApp
    from probefs.widgets.directory_list import DirectoryList

    app = ProbeFSApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        scr = app.screen
        header = str(scr.query_one("#hdr-left", Label).render())
        assert "probefs" in header
        gauge = str(scr.query_one("#sb-gauge", Label).render())
        assert "DISK" in gauge and "%" in gauge
        assert scr.query_one("#pane-current", DirectoryList).has_class("active")
        assert not scr.query_one("#pane-parent", DirectoryList).has_class("active")
