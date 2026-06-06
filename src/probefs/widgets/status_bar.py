"""StatusBar — two-line instrument readout docked at the bottom of MainScreen.

Line 1: indicator lamps (connection · sort · hidden · filter) on the left,
        item breakdown (total ▸ dirs · files) on the right.
Line 2: disk-usage gauge (DISK [████░░] 64% · 704.2 G free), colored by fullness.

The current path now lives in the HeaderBar, not here. State is set by
MainScreen via the set_* methods after each DirectoryLoaded message and on
sort/hidden/filter changes; each setter refreshes the affected line.
"""
from __future__ import annotations

from rich.text import Text

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Label

from probefs.config import load_config
from probefs.rendering.cockpit import build_gauge, build_lamps
from probefs.rendering.metadata import human_size


class StatusBar(Widget):
    """Two-line cockpit status readout: lamps + breakdown, and a disk gauge."""

    DEFAULT_CSS = """
    StatusBar {
        height: 2;
        background: $panel-darken-1;
        padding: 0 1;
    }
    StatusBar #sb-row1 {
        height: 1;
    }
    StatusBar #sb-lamps {
        width: 1fr;
    }
    StatusBar #sb-breakdown {
        width: auto;
        color: $text-muted;
        text-align: right;
    }
    StatusBar #sb-gauge {
        height: 1;
        width: 100%;
    }
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._ascii: bool = bool(load_config().get("cockpit_ascii", False))
        self._connection: str = "LOCAL"
        self._sort_label: str = "name ↑"
        self._hidden: bool = False
        self._filter_active: bool = False
        self._total: int = 0
        self._dirs: int = 0
        self._files: int = 0
        self._disk_total: int = 0
        self._disk_free: int = 0

    def compose(self) -> ComposeResult:
        with Horizontal(id="sb-row1"):
            yield Label("", id="sb-lamps")
            yield Label("", id="sb-breakdown")
        yield Label("", id="sb-gauge")

    # -- public setters (called by MainScreen) -------------------------------

    def set_connection(self, label: str) -> None:
        self._connection = label
        self._refresh_lamps()

    def set_sort(self, label: str) -> None:
        self._sort_label = label
        self._refresh_lamps()

    def set_hidden(self, hidden: bool) -> None:
        self._hidden = hidden
        self._refresh_lamps()

    def set_filter_active(self, active: bool) -> None:
        self._filter_active = active
        self._refresh_lamps()
        self._refresh_breakdown()

    def set_counts(self, total: int, dirs: int, files: int) -> None:
        self._total, self._dirs, self._files = total, dirs, files
        self._refresh_breakdown()

    def set_disk(self, total: int, free: int) -> None:
        self._disk_total, self._disk_free = total, free
        self._refresh_gauge()

    # -- line builders -------------------------------------------------------

    def _refresh_lamps(self) -> None:
        lamps = build_lamps(
            connection=self._connection,
            sort_label=self._sort_label,
            hidden=self._hidden,
            filter_active=self._filter_active,
            ascii=self._ascii,
        )
        self.query_one("#sb-lamps", Label).update(lamps)

    def _refresh_breakdown(self) -> None:
        if self._filter_active:
            text = f"{self._total} matched"
        else:
            arrow = ">" if self._ascii else "▸"
            text = f"{self._total} {arrow} {self._dirs} d · {self._files} f"
        self.query_one("#sb-breakdown", Label).update(text)

    def _refresh_gauge(self) -> None:
        used = max(0, self._disk_total - self._disk_free)
        gauge = build_gauge(used, self._disk_total, ascii=self._ascii)
        line = Text("DISK ", style="dim")
        line.append_text(gauge)
        if self._disk_total > 0:
            line.append(f"  ·  {human_size(self._disk_free).strip()} free", style="dim")
        self.query_one("#sb-gauge", Label).update(line)
