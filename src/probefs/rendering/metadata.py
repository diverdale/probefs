"""File categorization and metadata formatting utilities.

These are pure functions that form the foundation of the rendering pipeline.
get_category() drives both icon selection and color assignment.
The helper functions populate the four metadata columns in the DataTable.

FAL boundary note: get_category() accepts an optional ProbeFS instance (fs)
for broken-symlink detection. When fs is provided, it calls fs._fs.exists()
(fsspec's exists, which follows symlinks). When fs is None it falls back to
os.path.exists (local filesystem only). Widgets pass fs; standalone callers
and tests don't need to.
"""
from __future__ import annotations

import datetime
import os
import pwd
import stat

# ---------------------------------------------------------------------------
# Extension sets (module-level, exported)
# ---------------------------------------------------------------------------

ARCHIVE_EXTS: frozenset[str] = frozenset({
    ".tar", ".gz", ".bz2", ".xz", ".zip", ".7z", ".rar",
    ".zst", ".lz4", ".lzma", ".tgz", ".tbz2", ".txz",
})

IMAGE_EXTS: frozenset[str] = frozenset({
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".svg", ".ico", ".tiff", ".tif",
})


# ---------------------------------------------------------------------------
# get_category
# ---------------------------------------------------------------------------

def get_category(entry: dict, fs=None) -> str:
    """Categorize a file entry for icon/color selection.

    Priority order: broken_symlink > symlink > directory > executable > archive > image > file

    Args:
        entry: fsspec entry dict with keys: islink, destination, mode, name
        fs: ProbeFS instance for broken-symlink check. If None, falls back to
            os.path.exists (local filesystem only).

    Returns:
        One of: 'broken_symlink', 'symlink', 'directory', 'executable',
                'archive', 'image', 'file'
    """
    mode = entry.get("mode", 0)
    islink = entry.get("islink", False)
    name = entry.get("name", "")
    destination = entry.get("destination", "")

    # Gate ALL symlink logic on islink first (Pitfall 1 from research:
    # never check destination without confirming islink=True first).
    if islink:
        if destination:
            exists = fs._fs.exists(destination) if fs is not None else os.path.exists(destination)
            if not exists:
                return "broken_symlink"
        return "symlink"

    if entry.get("type") == "directory" or stat.S_ISDIR(mode):
        return "directory"

    if bool(mode & 0o111):
        return "executable"

    # Extension-based categorization — use last component of path for name
    basename = name.split("/")[-1]
    ext = os.path.splitext(basename)[1].lower()
    if ext in ARCHIVE_EXTS:
        return "archive"
    if ext in IMAGE_EXTS:
        return "image"

    return "file"


# ---------------------------------------------------------------------------
# human_size
# ---------------------------------------------------------------------------

def human_size(n: int | None) -> str:
    """Format byte count as human-readable string.

    Returns '4.2K', '1.5M', '    -' for None, etc.
    Column-aligned: None returns 5-char '    -'.
    """
    if n is None:
        return "    -"
    value = float(n)
    for unit in ("B", "K", "M", "G", "T"):
        if abs(value) < 1024.0:
            return f"{value:.1f}{unit}"
        value /= 1024.0
    return f"{value:.1f}P"


# ---------------------------------------------------------------------------
# format_mtime
# ---------------------------------------------------------------------------

def format_mtime(mtime) -> str:
    """Format mtime as 'Nov 12 14:23' (12 chars).

    Accepts a float epoch timestamp (local fs) or a datetime object (SFTP).
    Returns 12 spaces for None — keeps column alignment when mtime is missing.
    """
    if mtime is None:
        return "            "  # 12 spaces — matches column width
    if isinstance(mtime, datetime.datetime):
        return mtime.strftime("%b %d %H:%M")
    try:
        return datetime.datetime.fromtimestamp(float(mtime)).strftime("%b %d %H:%M")
    except (OSError, OverflowError, ValueError, TypeError):
        return "            "


# ---------------------------------------------------------------------------
# uid_to_name
# ---------------------------------------------------------------------------

def uid_to_name(uid) -> str:
    """Resolve UID to username. Falls back to str(uid) for unknown UIDs.

    Accepts int or None (SFTP entries may omit uid).
    """
    if uid is None:
        return ""
    try:
        return pwd.getpwuid(int(uid)).pw_name
    except (KeyError, OverflowError, ValueError, TypeError):
        return str(uid)
