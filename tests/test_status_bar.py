"""Tests for the reworked 2-line instrument StatusBar."""
from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Label

from probefs.widgets.status_bar import StatusBar


class _Harness(App):
    def compose(self) -> ComposeResult:
        yield StatusBar()


@pytest.mark.asyncio
async def test_status_bar_renders_gauge_and_breakdown() -> None:
    app = _Harness()
    async with app.run_test():
        sb = app.query_one(StatusBar)
        sb.set_sort("name ↑")
        sb.set_counts(total=10, dirs=3, files=7)
        sb.set_disk(total=1000, free=360)
        sb.set_hidden(False)
        sb.set_filter_active(False)

        lamps = str(app.query_one("#sb-lamps", Label).render())
        breakdown = str(app.query_one("#sb-breakdown", Label).render())
        gauge = str(app.query_one("#sb-gauge", Label).render())

        assert "name ↑" in lamps
        assert "hidden" in lamps
        assert "3" in breakdown and "7" in breakdown
        assert "DISK" in gauge
        assert "%" in gauge


@pytest.mark.asyncio
async def test_status_bar_filter_active_breakdown() -> None:
    app = _Harness()
    async with app.run_test():
        sb = app.query_one(StatusBar)
        sb.set_counts(total=4, dirs=0, files=4)
        sb.set_filter_active(True)
        breakdown = str(app.query_one("#sb-breakdown", Label).render())
        assert "matched" in breakdown
