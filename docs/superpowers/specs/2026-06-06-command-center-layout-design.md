# Command-Center Layout — Design Spec

**Date:** 2026-06-06
**Status:** Approved (pending spec review)

## Goal

Restyle the probefs main screen as an "instrument panel" / control-surface
without changing the three-pane miller-columns navigation model. Surface
telemetry the FAL already exposes (disk usage, item counts, per-file metadata)
and frame the UI as a cockpit.

Scope decisions (locked during brainstorming):

- **Tier:** Instrument panel (cockpit chrome + live telemetry). No structural
  side-rail (that was the rejected "full cockpit" tier).
- **Framing:** Single outer frame — one bordered container, panes divided by
  thin vertical rules, each pane gets a colored title header row.
- **Instruments:** all four — disk gauge, indicator lamps, preview metadata
  readout, live clock.
- **Gauge color by fullness:** green < 70%, yellow < 90%, red ≥ 90%.
- **ASCII fallback:** config toggle `cockpit_ascii`, default off.

This is the new default look — there is no on/off switch for the cockpit itself
(only the `cockpit_ascii` glyph toggle).

## Layout

```
┌─ probefs ──────────────────────────────  dale@host · 14:32:07 ┐  HeaderBar
│  ~ › dev › probefs                                            │
├──────────────┬───────────────────────┬───────────────────────┤  rule
│ PARENT       │ probefs             ◆ │ PREVIEW · CLAUDE.md    │  pane titles
│   …list…     │   …list…              │ ┌ 1.8K rw-r--r-- dale ┐│  preview meta
│              │                       │ │ …content…           ││
├──────────────┴───────────────────────┴───────────────────────┤  rule
│ ● LOCAL   ◐ name↑   ○ hidden   ◌ filter      10 ▸ 3 d · 7 f   │  StatusBar L1
│ DISK [██████████████░░░░░░] 64%  ·  704.2 G free               │  StatusBar L2
├───────────────────────────────────────────────────────────────┤
│ j/k move  l open  h back  …                                    │  Footer
└───────────────────────────────────────────────────────────────┘
```

### Structure

`MainScreen.compose` wraps the existing content in one outer `Vertical`
(`#cockpit`, accent border) containing, top to bottom:

1. `HeaderBar` (`#header-bar`) — `border-bottom` provides the rule under the breadcrumb.
2. `Horizontal` (`#panes`) — the three panes; vertical `border-right` rules between them (as today).
3. `StatusBar` (`#status-bar`) — `border-top` provides the rule above the lamps; height 2.

`FilterBar` and `Footer` remain where they are. The outer `Vertical`'s border
draws the full box; inner section rules come from per-section border edges.

### Active pane

On the main screen the **current pane is always the active pane** — the parent
pane is display-only context and is never navigated directly. So the accent
treatment (accent-colored title row + `◆` marker) is applied statically to
`#pane-current`. No focus-change tracking is required. (This differs from the
SFTP screen, which has Tab-switchable active panes; that screen is out of scope.)

## Components

### HeaderBar (new — `widgets/header_bar.py`)

- Left: app name `probefs` + breadcrumb of cwd, `›`-separated, home collapsed to `~`.
- Right: `user@host` + live clock `HH:MM:SS`.
- Reactive `path: str` drives the breadcrumb (set from `MainScreen` on every load).
- Clock: `set_interval(1.0, self._tick)` updating a `time`-derived reactive.
- `user@host`: `getpass.getuser()` + `socket.gethostname()`. These are process
  identity, not filesystem I/O, so they do not belong in the FAL and are called
  directly in the widget. Reflects the local machine (main screen is always local).

### StatusBar (reworked — `widgets/status_bar.py`)

Grows from 1 to 2 lines. The path field is removed (now owned by the header).

- **Line 1:** indicator lamps (left) + item breakdown (right).
  - Lamps: connection (`LOCAL`), sort (current sort label), hidden, filter.
    Lit = active (themed accent/success), unlit = `$text-muted`.
  - Breakdown: `<total> ▸ <dirs> d · <files> f`.
- **Line 2:** disk gauge — `DISK [████░░] <pct>% · <free> free`, bar color by fullness.

New reactives / setters: `sort_mode`, `total_count`, `dir_count`, `file_count`,
`disk_total`, `disk_free`, `show_hidden`, `filter_active`, `connection_label`.

### PreviewPane (changed — `widgets/preview_pane.py`)

- Adds a metadata header Label (`#preview-header`) above the `ContentSwitcher`.
- `show_entry(entry)` sets the header from the entry dict before dispatching the
  content load: `name · size · perms · owner · mtime` (directories show item
  intent appropriately, e.g. size shown as `-`).
- Reuses `rendering/metadata.py` (`human_size`, `format_mtime`, `uid_to_name`)
  and `stat.filemode(mode)`.

### DirectoryList (changed — `widgets/directory_list.py`)

- `compose` yields a pane-title Label above the existing `DataTable`.
- `set_title(text)` and `set_active(bool)` control the title row + accent.
- A method to report visible dir/file counts (drawn from `_visible_entries`),
  consumed by `MainScreen` for the breakdown.

## FAL change

`ProbeFS.disk_usage(path)` currently returns free bytes only. Change it to
return total/used/free (all available from `shutil.disk_usage`). Return a small
named structure (e.g. `DiskUsage(total, used, free)` namedtuple) for clarity.

Callers updated: `MainScreen._load_panes` and the `DirectoryLoaded` message
(which currently carries `free_space: int`) — extend to carry total + free.

## Glyphs, theming, config

- **Colors:** theme tokens only (`$primary`, `$accent`, `$success`, `$warning`,
  `$text-muted`, `$panel`). No hardcoded colors. Cell/glyph coloring uses Rich
  `Text` style strings, per the existing rendering convention.
- **Gauge color tiers:** green (`$success`) < 70%, yellow (`$warning`) < 90%,
  red (`$error`) ≥ 90%.
- **Glyph set:** Unicode geometric/block characters by default
  (`● ◐ ○ ◌ █ ░ › ◆`). These are not Nerd Font glyphs and render in modern
  terminals. Config toggle `cockpit_ascii: true` (default off) swaps to
  ASCII-safe equivalents: gauge `[##--]`, lamps `[*]`/`[ ]`, chevron `>`,
  marker `*`. Read via `config.get("cockpit_ascii", False)`; malformed/missing
  config falls back to off, consistent with the config-never-crashes rule.

## Pure helpers (new — `rendering/cockpit.py`)

Formatting logic lives in pure, app-free functions so it is unit-testable with
plain inputs (matching the codebase's module-level-helper pattern):

- `build_breadcrumb(path: str, home: str) -> str`
- `build_gauge(used: int, total: int, *, ascii: bool) -> tuple[Text, str]`
  (bar renderable + color tier)
- `build_lamps(state, *, ascii: bool) -> Text`
- `build_preview_meta(entry: dict) -> str`
- `gauge_color_tier(pct: float) -> str` (green/yellow/red selection)

Widgets stay thin and call these.

## Testing

- **Unit (pure, no app):** breadcrumb formatting incl. `~` collapse and root;
  gauge bar fill + color tier at 0/69/70/89/90/100%; ASCII vs Unicode glyph
  selection; lamp line for each state combination; preview-meta formatting for
  file vs directory; `ProbeFS.disk_usage` returns total ≥ free > 0 on a real path.
- **Integration (`run_test`):** header shows the breadcrumb for the launch dir;
  status line 2 shows a gauge; preview header shows metadata for the highlighted
  entry; `#pane-current` carries the active class/marker.
- **Snapshot (optional):** `pytest-textual-snapshot` capture of the new layout.

## Files touched

- New: `widgets/header_bar.py`, `rendering/cockpit.py`
- Changed: `widgets/status_bar.py`, `widgets/preview_pane.py`,
  `widgets/directory_list.py`, `screens/main.py`, `fs/probe_fs.py`,
  `probefs.tcss`
- Config: read `cockpit_ascii` (no writer; documented in `probefs.yaml.example`)
- Tests: new unit + integration test files

## Out of scope

- Left side-rail (bookmarks / mounts / recent) — the rejected "full cockpit" tier.
- SFTP screen restyling — it has its own active-pane model; can follow later.
- Making the cockpit itself toggleable on/off.
```
