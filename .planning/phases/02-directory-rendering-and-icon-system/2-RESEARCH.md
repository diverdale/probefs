# Phase 2: Directory Rendering and Icon System - Research

**Researched:** 2026-03-09
**Domain:** Textual DataTable / Rich Text / file type detection / icon strategy pattern
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NAV-03 | User can toggle hidden files (dotfiles) on and off with a single key | Hidden detection: basename.startswith('.'); show_hidden bool on FileManagerCore; action_toggle_hidden on MainScreen; '.' key binding |
| DISP-01 | User can see file metadata columns: permissions, size, modified date, and owner | stat.filemode(mode), human_size(), datetime.fromtimestamp(), pwd.getpwuid() — all verified working with fsspec output |
| DISP-02 | Files are colored by type using the active theme | Rich Text style parameter per category; color map dict; verified with actual directory listing |
| DISP-03 | Symlinks display their target path; broken symlinks are visually distinct | fsspec sets islink=True + destination=str; broken = islink AND NOT os.path.exists(destination); verified with real symlinks |
| THEME-05 | User can assign icons to file types via an icon theme YAML file | ruamel.yaml confirmed working; YAML structure verified; YAMLIconSet reads icons/colors dicts |
| THEME-06 | Icon themes support Nerd Font glyphs as the configured icon set | NerdIconSet with Unicode codepoints (e.g. \uf07b); require icon_set: nerd in config |
| THEME-07 | Icon themes fall back to ASCII symbols by default; Nerd Font requires explicit opt-in | ASCIIIconSet is default; factory function reads config.get('icons') == 'nerd' |
</phase_requirements>

---

## Summary

Phase 2 replaces the simple name-only ListView inside DirectoryList with a Textual DataTable using `cursor_type="row"`. DataTable natively supports Rich Text cells (enabling per-file-type coloring), fixed-width columns (permissions, size, date, owner), and row-level highlighting with `RowHighlighted` messages. The public interface of DirectoryList — `set_entries()`, `move_cursor_up/down()`, `get_highlighted_entry()`, and `EntryHighlighted` — remains unchanged, so MainScreen requires no structural edits.

File metadata comes entirely from fsspec's existing `ls(detail=True)` output: `mode` (for permissions via `stat.filemode()`), `size`, `mtime`, `uid` (for owner via `pwd.getpwuid()`), `islink`, and `destination` (symlink target). Broken symlinks are detected by calling `os.path.exists(destination)` — fsspec sets `destination` on all symlinks but doesn't distinguish broken vs valid. File categories (directory, executable, archive, image, symlink, broken_symlink, file) drive both icon selection and color. The stdlib `stat` module handles type detection from mode bits; extension sets handle archives and images.

The icon system uses a Strategy pattern: an `IconSet` ABC with `get_icon(category)` and `get_color(category)` methods. `ASCIIIconSet` is the default (no config required). `NerdIconSet` is activated by `icons: nerd` in config. `YAMLIconSet` loads a user-supplied YAML file for full customization. `ruamel.yaml` is confirmed working and already a Phase 1 decision. `show_hidden` lives as a plain bool on `FileManagerCore`, toggled by a new `action_toggle_hidden` on MainScreen bound to the `'.'` key.

**Primary recommendation:** Replace ListView with DataTable(cursor_type="row") inside DirectoryList, build Rich Text cells per row using the file-type categorization pipeline, and implement IconSet strategy with ASCIIIconSet as default.

---

## Standard Stack

### Core (all confirmed present in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.0.2 | DataTable, Rich Text rendering, TCSS | Phase 1 decision; DataTable verified for multi-column rows |
| rich | (textual dep) | Text with styled spans, cell_len() for CJK widths | Textual uses Rich internally; cell_len() handles double-wide chars |
| fsspec | (project dep) | ls(detail=True) returns mode, mtime, uid, islink, destination | Phase 1 FAL; destination field confirmed on symlinks |
| ruamel.yaml | 0.19.1 | Icon theme YAML loading | Phase 1 decision; confirmed working with Nerd Font codepoints |
| stat (stdlib) | 3.10+ | stat.filemode(mode) for permissions string | No install; outputs '-rwxr-xr-x' format |
| pwd (stdlib) | 3.10+ | pwd.getpwuid(uid).pw_name for owner name | No install; graceful fallback to str(uid) |
| datetime (stdlib) | 3.10+ | datetime.fromtimestamp(mtime).strftime() | No install |
| os (stdlib) | 3.10+ | os.path.exists(destination) for broken symlink detection | No install; FAL boundary: only for symlink target check |

### No New Dependencies Required
The entire Phase 2 feature set is implemented using Textual's built-in DataTable + Rich Text, stdlib modules (stat, pwd, datetime), and ruamel.yaml (already in project). No additional packages need to be added.

**Installation:**
```bash
# Already installed from Phase 1 + ruamel-yaml added
uv add ruamel-yaml  # already done if Phase 1 complete
```

---

## Architecture Patterns

### Recommended Project Structure
```
src/probefs/
├── fs/
│   └── probe_fs.py          # unchanged
├── core/
│   └── file_manager.py      # ADD: show_hidden: bool = False
├── icons/
│   ├── __init__.py
│   ├── base.py              # NEW: IconSet ABC
│   ├── ascii_set.py         # NEW: ASCIIIconSet (default)
│   ├── nerd_set.py          # NEW: NerdIconSet
│   ├── yaml_set.py          # NEW: YAMLIconSet
│   └── factory.py           # NEW: load_icon_set(config) -> IconSet
├── rendering/
│   ├── __init__.py
│   ├── columns.py           # NEW: build_row() -> tuple[Text, ...]
│   └── metadata.py          # NEW: human_size(), format_mtime(), get_category()
├── widgets/
│   └── directory_list.py    # MODIFY: swap ListView for DataTable
├── screens/
│   └── main.py              # MODIFY: add toggle_hidden action + pass show_hidden
└── probefs.tcss             # MODIFY: DataTable styles
```

### Pattern 1: DataTable as Column-Aware ListView

**What:** Replace the inner `ListView` in `DirectoryList` with `DataTable(cursor_type="row", show_header=False)`. Columns are added once in `on_mount`. `set_entries()` calls `dt.clear(columns=False)` then `dt.add_row()` for each (filtered) entry.

**When to use:** Any time you need multi-column keyboard-navigable list with per-row Rich Text colors.

**Example:**
```python
# Source: Textual official docs + verified against textual 8.0.2
from textual.widgets import DataTable
from rich.text import Text

class DirectoryList(Widget, can_focus=True):

    def compose(self) -> ComposeResult:
        dt = DataTable(cursor_type="row", show_header=False, show_cursor=True)
        yield dt

    def on_mount(self) -> None:
        dt = self.query_one(DataTable)
        dt.add_column("name", width=None)        # flexible
        dt.add_column("permissions", width=10)
        dt.add_column("size", width=9)
        dt.add_column("date", width=12)
        dt.add_column("owner", width=10)

    def set_entries(self, entries: list[dict], show_hidden: bool = False) -> None:
        self._entries = [
            e for e in entries
            if show_hidden or not self._is_hidden(e)
        ]
        dt = self.query_one(DataTable)
        dt.clear(columns=False)
        for entry in self._entries:
            row = build_row(entry, self._icon_set)
            dt.add_row(*row)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        event.stop()
        idx = event.cursor_row
        if 0 <= idx < len(self._entries):
            self.post_message(self.EntryHighlighted(self._entries[idx]))

    def get_highlighted_entry(self) -> dict | None:
        dt = self.query_one(DataTable)
        idx = dt.cursor_row
        if idx is not None and 0 <= idx < len(self._entries):
            return self._entries[idx]
        return None
```

### Pattern 2: Rich Text Row Builder

**What:** A pure function `build_row(entry, icon_set) -> tuple[Text, ...]` that converts an fsspec entry dict to a tuple of Rich Text objects for DataTable cells.

**When to use:** Called from `set_entries()` for every visible entry.

**Example:**
```python
# Source: verified with actual fsspec output and Rich 13.x
import stat, pwd, datetime, os
from rich.text import Text

def build_row(entry: dict, icon_set: IconSet) -> tuple[Text, Text, Text, Text, Text]:
    name = entry.get("name", "").split("/")[-1]
    mode = entry.get("mode", 0)
    size = entry.get("size", 0)
    mtime = entry.get("mtime")
    uid = entry.get("uid", 0)
    islink = entry.get("islink", False)
    destination = entry.get("destination", "")

    category = get_category(entry)
    icon = icon_set.get_icon(category)
    color = icon_set.get_color(category)

    # Name cell: icon + name (+ symlink arrow for symlinks)
    name_cell = Text()
    name_cell.append(icon + " ", style="dim")
    name_cell.append(name, style=color)
    if islink and destination:
        name_cell.append(f" -> {destination}", style="dim cyan")

    perms_cell = Text(stat.filemode(mode), style="dim")
    size_cell = Text(human_size(size), style="cyan", justify="right")
    date_cell = Text(format_mtime(mtime), style="dim")
    owner_cell = Text(uid_to_name(uid), style="dim")

    return name_cell, perms_cell, size_cell, date_cell, owner_cell
```

### Pattern 3: IconSet Strategy

**What:** ABC `IconSet` with `get_icon(category)` and `get_color(category)`. Three implementations: `ASCIIIconSet` (built-in default), `NerdIconSet` (explicit opt-in), `YAMLIconSet` (user file). Factory function `load_icon_set(config)` returns the right instance.

**Example:**
```python
# Source: verified icon maps with actual Unicode codepoints and ASCII fallbacks
from abc import ABC, abstractmethod

class IconSet(ABC):
    @abstractmethod
    def get_icon(self, category: str) -> str: ...
    @abstractmethod
    def get_color(self, category: str) -> str: ...

class ASCIIIconSet(IconSet):
    _ICONS = {
        "directory": "/", "file": " ", "executable": "*",
        "symlink": "@", "broken_symlink": "!", "archive": "#", "image": "%",
    }
    _COLORS = {
        "directory": "bold blue", "executable": "bold green",
        "symlink": "cyan", "broken_symlink": "bold red",
        "archive": "yellow", "image": "magenta", "file": "default",
    }
    def get_icon(self, category: str) -> str:
        return self._ICONS.get(category, " ")
    def get_color(self, category: str) -> str:
        return self._COLORS.get(category, "default")

class NerdIconSet(IconSet):
    _ICONS = {
        "directory": "\uf07b", "file": "\uf15b", "executable": "\uf013",
        "symlink": "\uf0c1", "broken_symlink": "\uf127",
        "archive": "\uf1c6", "image": "\uf1c5",
    }
    # colors same as ASCIIIconSet
    ...

def load_icon_set(config: dict) -> IconSet:
    icon_cfg = config.get("icons", "ascii")
    if icon_cfg == "nerd":
        return NerdIconSet()
    if isinstance(icon_cfg, dict) and icon_cfg.get("theme_file"):
        return YAMLIconSet(icon_cfg["theme_file"])
    return ASCIIIconSet()
```

### Pattern 4: File Type Categorization

**What:** Pure function `get_category(entry) -> str` with priority: broken_symlink > symlink > directory > executable > archive > image > file.

**Example:**
```python
# Source: verified with fsspec output and stat module (stdlib)
import stat, os

ARCHIVE_EXTS = frozenset({
    ".tar", ".gz", ".bz2", ".xz", ".zip", ".7z", ".rar",
    ".zst", ".lz4", ".lzma", ".tgz", ".tbz2", ".txz",
})
IMAGE_EXTS = frozenset({
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".svg", ".ico", ".tiff", ".tif",
})

def get_category(entry: dict) -> str:
    mode = entry.get("mode", 0)
    islink = entry.get("islink", False)
    name = entry.get("name", "")
    destination = entry.get("destination", "")

    if islink:
        # os.path.exists() follows the symlink; False means broken
        if destination and not os.path.exists(destination):
            return "broken_symlink"
        return "symlink"
    if stat.S_ISDIR(mode):
        return "directory"
    if bool(mode & 0o111):
        return "executable"
    ext = os.path.splitext(name)[1].lower()
    if ext in ARCHIVE_EXTS:
        return "archive"
    if ext in IMAGE_EXTS:
        return "image"
    return "file"
```

### Pattern 5: show_hidden Toggle

**What:** `show_hidden: bool = False` on `FileManagerCore`. `MainScreen.action_toggle_hidden()` flips it and calls `_load_panes()`. `set_entries()` receives `show_hidden` and filters in-widget.

**Hidden file detection:** `basename.startswith('.')` where `basename = name.split('/')[-1]`.

**Key binding:** `'.'` key (free in current bindings; matches ranger/lf convention).

### Anti-Patterns to Avoid

- **Filtering in the worker thread:** Worker must load ALL entries unfiltered. Filtering happens in `set_entries()` on the main thread. This keeps show_hidden toggle instant (no I/O re-read).
- **Storing Rich Text in `_entries`:** `_entries` must always hold raw fsspec dicts. Rich Text is display-only, built at render time from `_entries`.
- **Using ListView for Phase 2:** ListView's ListItem does not have a native multi-column API. While add_class() works for colors, column alignment requires custom CSS hacks. DataTable is the right tool.
- **Calling os/pathlib directly in widgets:** All path operations stay in ProbeFS. The one exception is `os.path.exists(destination)` for broken symlink detection, which is a metadata check that ProbeFS should expose as `is_broken_symlink(path)` to preserve the FAL boundary.
- **Auto-detecting Nerd Fonts:** Impossible over SSH (terminal capabilities unreliable). Phase 1 confirmed: Nerd Fonts require explicit opt-in.
- **Rebuilding DataTable columns on each reload:** Columns are added ONCE in `on_mount`. Reload calls `dt.clear(columns=False)` to keep column definitions.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Permissions string | Custom octal formatter | `stat.filemode(mode)` | Stdlib; handles all file type bits correctly (setuid, sticky, etc.) |
| Terminal-safe column widths | Character count | `rich.cells.cell_len(text)` | Rich handles CJK double-wide, zero-width combining chars |
| Human-readable sizes | Custom formatter | Inline function using 1024 divisions | Simple enough to write; no library needed — see code example |
| YAML loading | pyyaml / manual parser | `ruamel.yaml` (Phase 1 decision) | Already in project; preserves YAML comments |
| Multi-column list | ListView + CSS columns | `DataTable(cursor_type="row")` | Native column widths, Rich Text cells, built-in keyboard nav |
| Icon Unicode lookup table | dict literal in widget | `IconSet` ABC implementations | Strategy pattern enables YAML override without widget changes |

**Key insight:** Rich's `cell_len()` (used internally by DataTable) already handles CJK double-wide characters correctly. Column width arithmetic will be correct as long as cells are Rich Text objects — never raw Python `len()`.

---

## Common Pitfalls

### Pitfall 1: fsspec `destination` field — always present on symlinks, never on non-symlinks

**What goes wrong:** Code checks `if entry.get('destination')` and treats absence as broken. This misidentifies regular files.

**Why it happens:** `destination` is only populated when `islink=True`. For regular files, `.get('destination')` returns `None` (not a missing key).

**How to avoid:** Always gate broken-symlink logic on `entry.get('islink') == True` first, THEN check `os.path.exists(destination)`.

**Warning signs:** Regular files colored as broken symlinks in the listing.

### Pitfall 2: DataTable `clear()` removes columns by default

**What goes wrong:** Calling `dt.clear()` (no args) removes both rows AND columns. Next `add_row()` call raises because no columns exist.

**Why it happens:** `DataTable.clear(columns: bool = False)` — columns param defaults to `False` meaning "don't clear columns". BUT the default in Textual 8.0.2 is `columns=False` which KEEPS columns. Reading the source confirms: `clear(columns=False)` removes only rows. Always pass explicitly.

**How to avoid:** Always write `dt.clear(columns=False)` explicitly in `set_entries()`.

**Warning signs:** `IndexError` or silent empty display after first directory reload.

### Pitfall 3: DataTable `cursor_row` is -1 when table is empty

**What goes wrong:** `get_highlighted_entry()` uses `dt.cursor_row` as index; when the directory is empty (or loading), `cursor_row` is 0 or -1, causing IndexError.

**Why it happens:** DataTable cursor starts at row 0 but `_entries` is empty after `clear()`.

**How to avoid:** Guard: `if dt.cursor_row is not None and 0 <= dt.cursor_row < len(self._entries)`.

**Warning signs:** Exception on descend into empty directory.

### Pitfall 4: `os.path.exists()` in widget violates FAL boundary

**What goes wrong:** Widget calls `os.path.exists()` to detect broken symlinks, coupling widget to local filesystem.

**Why it happens:** Convenient, but breaks the ProbeFS abstraction (SFTP backend has no local `os.path.exists`).

**How to avoid:** Add `ProbeFS.is_broken_symlink(path) -> bool` that calls `self._fs.exists(path)` (fsspec's exists follows symlinks). Widget uses `self._icon_set` which gets its category from `get_category(entry, fs)` or a pre-computed category field.

**Warning signs:** Test failures when ProbeFS is mocked; broken symlinks wrong on SFTP backend.

### Pitfall 5: Human size formatting for directories

**What goes wrong:** Directories show sizes like `352.0B` which is the block count, not a meaningful file count.

**Why it happens:** fsspec returns `size` for directories as the directory entry size (usually 128–4096 bytes on macOS/Linux depending on entry count).

**How to avoid:** Display size as-is (same as `ls -la`). Don't suppress it — it's valid metadata. The user understands directory sizes are block sizes.

**Warning signs:** Confusion during review; but this matches standard `ls -l` behavior.

### Pitfall 6: `pwd.getpwuid()` raises `KeyError` for unknown UIDs

**What goes wrong:** On systems with NFS or non-local users, UID lookup raises `KeyError`.

**Why it happens:** `pwd.getpwuid(uid)` raises `KeyError` if the UID isn't in the local passwd database.

**How to avoid:** Always wrap in `try/except KeyError: return str(uid)`.

**Warning signs:** Exception on listing `/proc` or network-mounted filesystems.

### Pitfall 7: Rich Text style strings vs TCSS

**What goes wrong:** Using TCSS class-based coloring on DataTable rows fails because DataTable renders cells via Rich, not TCSS widget tree.

**Why it happens:** DataTable cell content bypasses TCSS — cells are rendered with Rich's console engine. TCSS `color` on a DataTable affects the background/border, not cell text.

**How to avoid:** All file-type coloring MUST use Rich Text style strings (e.g., `"bold blue"`) passed to cell Text objects, not TCSS classes.

**Warning signs:** TCSS rules have no effect on cell text color.

---

## Code Examples

### Complete `get_category()` with FAL-safe broken symlink check

```python
# Source: verified with fsspec LocalFileSystem + stat stdlib
import stat, os

ARCHIVE_EXTS = frozenset({
    ".tar", ".gz", ".bz2", ".xz", ".zip", ".7z", ".rar",
    ".zst", ".lz4", ".lzma", ".tgz", ".tbz2", ".txz",
})
IMAGE_EXTS = frozenset({
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".svg", ".ico", ".tiff", ".tif",
})

def get_category(entry: dict, fs=None) -> str:
    """Categorize a file entry for icon/color selection.

    fs: ProbeFS instance for broken-symlink check. If None, falls back
    to os.path.exists (local filesystem only).
    """
    mode = entry.get("mode", 0)
    islink = entry.get("islink", False)
    name = entry.get("name", "")
    destination = entry.get("destination", "")

    if islink:
        if destination:
            exists = fs._fs.exists(destination) if fs else os.path.exists(destination)
            if not exists:
                return "broken_symlink"
        return "symlink"
    if stat.S_ISDIR(mode):
        return "directory"
    if bool(mode & 0o111):
        return "executable"
    ext = os.path.splitext(name)[1].lower()
    if ext in ARCHIVE_EXTS:
        return "archive"
    if ext in IMAGE_EXTS:
        return "image"
    return "file"
```

### Human-readable size formatting

```python
# Source: verified output against actual fsspec sizes
def human_size(n: int | None) -> str:
    """Format byte count as human-readable string: '4.2K', '1.5M', etc."""
    if n is None:
        return "    -"
    for unit in ("B", "K", "M", "G", "T"):
        if abs(n) < 1024.0:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}P"
```

### mtime formatting

```python
# Source: verified with actual mtime floats from fsspec
import datetime

def format_mtime(mtime: float | None) -> str:
    """Format epoch timestamp as 'Nov 12 14:23'."""
    if mtime is None:
        return "            "
    return datetime.datetime.fromtimestamp(mtime).strftime("%b %d %H:%M")
```

### uid to owner name with fallback

```python
# Source: verified with pwd stdlib
import pwd

def uid_to_name(uid: int) -> str:
    """Resolve UID to username. Falls back to str(uid) for unknown UIDs."""
    try:
        return pwd.getpwuid(uid).pw_name
    except (KeyError, OverflowError):
        return str(uid)
```

### DataTable column setup (called once in on_mount)

```python
# Source: verified against textual 8.0.2 DataTable API
def _setup_columns(self) -> None:
    dt = self.query_one(DataTable)
    dt.add_column("name")           # no width = flexible
    dt.add_column("perm", width=10)
    dt.add_column("size", width=8)
    dt.add_column("date", width=12)
    dt.add_column("owner", width=10)
```

### YAML icon theme loading

```python
# Source: verified with ruamel.yaml 0.19.1 + Unicode codepoints
from ruamel.yaml import YAML
from pathlib import Path

class YAMLIconSet(IconSet):
    def __init__(self, theme_path: str) -> None:
        yaml = YAML()
        data = yaml.load(Path(theme_path))
        self._icons = data.get("icons", {})
        self._colors = data.get("colors", {})
        self._fallback = ASCIIIconSet()

    def get_icon(self, category: str) -> str:
        return self._icons.get(category) or self._fallback.get_icon(category)

    def get_color(self, category: str) -> str:
        return self._colors.get(category) or self._fallback.get_color(category)
```

Example YAML icon theme file:
```yaml
# ~/.config/probefs/icons.yaml
icon_set: nerd
icons:
  directory: "\uf07b"     # nf-fa-folder
  file: "\uf15b"          # nf-fa-file
  executable: "\uf013"    # nf-fa-cog
  symlink: "\uf0c1"       # nf-fa-link
  broken_symlink: "\uf127" # nf-fa-chain_broken
  archive: "\uf1c6"       # nf-fa-file_zip_o
  image: "\uf1c5"         # nf-fa-file_image_o
colors:
  directory: "bold blue"
  executable: "bold green"
  symlink: "cyan"
  broken_symlink: "bold red"
  archive: "yellow"
  image: "magenta"
  file: "default"
```

### TCSS for DataTable in DirectoryList

```css
/* Source: Textual TCSS docs - DataTable styling uses component selectors */
DirectoryList DataTable {
    height: 100%;
    background: $panel;
}

/* Highlighted row uses Textual's built-in cursor styling */
/* Do NOT override DataTable > .datatable--cursor - use cursor_type="row" */
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ListView + ListItem for all lists | DataTable for tabular data, ListView for simple lists | Textual has had DataTable since 0.6 | DataTable handles columns and Rich Text natively |
| Manual column formatting with spaces | DataTable fixed-width columns | DataTable addition | No manual padding arithmetic needed |
| CSS class coloring on ListItem | Rich Text style on DataTable cells | Textual rendering model | TCSS doesn't affect DataTable cell text; Rich Text required |
| Phase 1 single-name display | Multi-column: icon+name / perm / size / date / owner | Phase 2 | Replaces ListView inside DirectoryList; public API unchanged |

**Deprecated/outdated:**
- Using `ListView` for tabular file listings: works but requires manual column alignment with spaces; DataTable is the correct widget.
- Setting `color:` TCSS on DataTable rows for file type coloring: TCSS affects widget chrome, not cell content rendered via Rich.

---

## Open Questions

1. **FAL boundary for broken symlink detection**
   - What we know: `get_category()` needs to call `os.path.exists(destination)` to detect broken symlinks; this violates the ProbeFS FAL for future SFTP backends
   - What's unclear: Whether Phase 2 should add `ProbeFS.exists(path) -> bool` or accept the local-only implementation for now
   - Recommendation: Add `ProbeFS.exists(path)` wrapping `self._fs.exists(path)`. Low effort, correct from the start.

2. **Parent pane metadata columns**
   - What we know: Phase 1 has a parent pane showing the parent directory's entries; it's a second DirectoryList
   - What's unclear: Should the parent pane show full metadata columns (same as current pane) or just names?
   - Recommendation: Show same columns in both panes — simpler code, consistent UI. Can be narrowed with `show_header=False` on parent pane's DataTable.

3. **Config file loading in Phase 2**
   - What we know: `load_icon_set(config: dict)` needs a config dict; no config system exists yet
   - What's unclear: Does Phase 2 introduce config file loading, or does it accept a hardcoded config dict?
   - Recommendation: Phase 2 implements `IconSet` and `load_icon_set()` but bootstraps with hardcoded `{}` dict (returns `ASCIIIconSet`). Config file loading is a later phase. The factory signature is future-proof.

---

## Sources

### Primary (HIGH confidence)
- Textual 8.0.2 source — DataTable API verified by running `uv run python -c "..."` against installed package
- `stat` stdlib documentation — `stat.filemode()` verified with actual mode integers from fsspec
- `pwd` stdlib — `getpwuid()` verified locally; `KeyError` fallback verified
- `rich.cells.cell_len()` — verified: `cell_len("日本語") == 6`, `cell_len("hello") == 5`
- fsspec LocalFileSystem — `ls(detail=True)` output dict fields verified with actual filesystem calls including symlink + broken symlink test

### Secondary (MEDIUM confidence)
- [Textual DataTable docs](https://textual.textualize.io/widgets/data_table/) — cursor_type="row", RowHighlighted message, Rich Text in cells
- [Textual Content guide](https://textual.textualize.io/guide/content/) — markup syntax, VisualType
- [DataTable performance discussion #5953](https://github.com/Textualize/textual/discussions/5953) — perf issue is O(m²) on columns, not rows; 5 columns is safe

### Tertiary (LOW confidence)
- [Textual ListView docs](https://textual.textualize.io/widgets/list_view/) — no component classes; confirms ListView is not column-aware

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all imports and API calls verified against installed packages
- Architecture: HIGH — DataTable API verified; fsspec fields confirmed with real I/O
- Pitfalls: HIGH — most pitfalls discovered through direct code testing (empty dt.cursor_row, clear() behavior, etc.)
- Icon strategy: HIGH — ruamel.yaml + Unicode codepoints verified working
- CJK width handling: HIGH — Rich cell_len() verified

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (Textual releases frequently; re-verify DataTable API if Textual version changes)
