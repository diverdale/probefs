"""Rich Text row builder for the DataTable in DirectoryList.

build_row() is the single place where an fsspec entry dict is converted
into displayable cells. All coloring uses Rich Text style strings — never
TCSS (Pitfall 7 from research: Rich Text styles and TCSS are independent;
TCSS cannot target individual DataTable cell text).
"""
from __future__ import annotations

import stat

from rich.text import Text

from probefs.icons.base import IconSet
from probefs.rendering.metadata import (
    format_mtime,
    get_category,
    human_size,
    uid_to_name,
)


def build_row(
    entry: dict, icon_set: IconSet, fs=None
) -> tuple[Text, Text, Text, Text, Text]:
    """Convert an fsspec entry dict to a tuple of Rich Text cells for DataTable.

    Returns (name_cell, perms_cell, size_cell, date_cell, owner_cell).
    All coloring uses Rich Text style strings — never TCSS (Pitfall 7 from research).

    Args:
        entry: fsspec entry dict with keys: name, mode, size, mtime, uid, islink, destination
        icon_set: IconSet instance providing get_icon() and get_color() for the category
        fs: Optional ProbeFS for FAL-safe broken symlink detection
    """
    name = entry.get("name", "")
    basename = name.split("/")[-1] if "/" in name else name
    mode = entry.get("mode", 0)
    size = entry.get("size", 0)
    mtime = entry.get("mtime")
    uid = entry.get("uid", 0)
    islink = entry.get("islink", False)
    destination = entry.get("destination", "")

    category = get_category(entry, fs)
    icon = icon_set.get_icon(category)
    color = icon_set.get_color(category)

    # Name cell: icon + name + optional symlink arrow
    name_cell = Text()
    name_cell.append(icon + " ", style="dim")
    name_cell.append(basename, style=color)
    if islink and destination:
        name_cell.append(f" -> {destination}", style="dim cyan")

    # Permissions: stat.filemode() handles all mode bits correctly (setuid, sticky, etc.)
    perms_cell = Text(stat.filemode(mode), style="dim")

    # Size: right-justified, cyan
    size_cell = Text(human_size(size), style="cyan", justify="right")

    # Date: dim
    date_cell = Text(format_mtime(mtime), style="dim")

    # Owner: dim, with fallback for unknown UIDs
    owner_cell = Text(uid_to_name(uid), style="dim")

    return name_cell, perms_cell, size_cell, date_cell, owner_cell
