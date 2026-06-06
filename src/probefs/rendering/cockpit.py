"""Pure formatting helpers for the command-center / instrument-panel chrome.

Every function here is app-free and unit-testable with plain inputs, matching
the codebase's module-level-helper pattern. Coloring uses Rich `Text` style
strings — never TCSS — consistent with rendering/columns.py, because these
renderables live inside Label/Static widgets where per-glyph color is needed.

The `ascii` flag on each builder swaps Unicode glyphs for ASCII-safe ones
(driven by the `cockpit_ascii` config option) for dumb/limited terminals.
"""
from __future__ import annotations

import stat

from rich.text import Text

from probefs.rendering.metadata import format_mtime, human_size, uid_to_name

# Gauge fullness thresholds (percent).
_GAUGE_WARN = 70
_GAUGE_CRIT = 90


def build_breadcrumb(path: str, home: str, *, ascii: bool = False) -> str:
    """Format a path as a chevron breadcrumb, collapsing home to '~'.

    Examples (home=/home/dale):
        /home/dale/dev/probefs -> "~ › dev › probefs"
        /home/dale             -> "~"
        /                      -> "/"
        /usr/bin               -> "/ › usr › bin"
    """
    sep = " > " if ascii else " › "
    home_norm = home.rstrip("/") if home else ""
    if home_norm and (path == home_norm or path.startswith(home_norm + "/")):
        rest = path[len(home_norm):]
        parts = ["~"] + [p for p in rest.split("/") if p]
    else:
        parts = ["/"] + [p for p in path.split("/") if p]
    return sep.join(parts)


def gauge_color_tier(pct: float) -> str:
    """Return the Rich color for a fullness percentage: green / yellow / red."""
    if pct >= _GAUGE_CRIT:
        return "red"
    if pct >= _GAUGE_WARN:
        return "yellow"
    return "green"


def build_gauge(used: int, total: int, *, width: int = 20, ascii: bool = False) -> Text:
    """Build a colored fullness bar like '[████░░] 64%'.

    The bar is colored by fullness tier (green/yellow/red). A zero/unknown total
    is treated as 0% (empty bar) rather than raising.
    """
    if total > 0:
        ratio = max(0.0, min(1.0, used / total))
    else:
        ratio = 0.0
    pct = round(ratio * 100)
    filled = round(ratio * width)
    fill_ch, empty_ch = ("#", "-") if ascii else ("█", "░")
    color = gauge_color_tier(pct)

    bar = Text()
    bar.append("[", style="dim")
    bar.append(fill_ch * filled, style=color)
    bar.append(empty_ch * (width - filled), style="dim")
    bar.append("] ", style="dim")
    bar.append(f"{pct}%", style=color)
    return bar


def build_lamps(
    *,
    connection: str,
    sort_label: str,
    hidden: bool,
    filter_active: bool,
    ascii: bool = False,
) -> Text:
    """Build the indicator-lamp line: connection · sort · hidden · filter.

    Lit lamps use a bright style; unlit lamps are dim. Connection and sort are
    always lit (they always reflect a current value).
    """
    def lamp(label: str, lit: bool, lit_style: str) -> tuple[str, str, str]:
        if ascii:
            glyph = "[*]" if lit else "[ ]"
        else:
            glyph = "●" if lit else "○"
        style = lit_style if lit else "dim"
        return glyph, label, style

    text = Text()
    for i, (glyph, label, style) in enumerate([
        lamp(connection, True, "bold cyan"),
        lamp(sort_label, True, "bold magenta"),
        lamp("hidden", hidden, "bold green"),
        lamp("filter", filter_active, "bold green"),
    ]):
        if i:
            text.append("   ")
        text.append(glyph, style=style)
        text.append(f" {label}", style=style)
    return text


def build_preview_meta(entry: dict) -> str:
    """Build the preview-header readout: name · size · perms · owner · mtime.

    Directories show '-' for size. Empty fields are dropped.
    """
    name = entry.get("name", "")
    basename = name.split("/")[-1] if "/" in name else name
    is_dir = entry.get("type") == "directory"
    size_str = "-" if is_dir else human_size(entry.get("size", 0)).strip()
    perms = stat.filemode(entry.get("mode") or 0)
    owner = uid_to_name(entry.get("uid"))
    mtime = format_mtime(entry.get("mtime")).strip()

    parts = [basename, size_str, perms, owner, mtime]
    return " · ".join(p for p in parts if p)
