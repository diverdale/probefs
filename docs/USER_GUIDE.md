# probefs User Guide

A comprehensive reference for probefs — a keyboard-driven TUI file browser built with Python and Textual.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Interface Overview](#interface-overview)
4. [Navigation](#navigation)
5. [File Preview](#file-preview)
6. [File Operations](#file-operations)
7. [Configuration](#configuration)
8. [Themes](#themes)
9. [Icons](#icons)
10. [Keybinding Customization](#keybinding-customization)
11. [Tips and Tricks](#tips-and-tricks)

---

## Introduction

probefs is a terminal-based file browser that puts the keyboard first. Inspired by vim's modal philosophy and the miller columns layout popularized by tools like ranger and lf, probefs gives you a fast, visual way to navigate your filesystem without ever touching a mouse.

The design philosophy is:

- **Keyboard-first.** Every action is reachable from a single key or key chord. The mouse is never required.
- **Vim-style movement.** If you know `hjkl`, you already know how to navigate probefs.
- **Visible context.** The three-pane layout keeps your parent directory, current directory, and a preview of the selected item on screen simultaneously — you always know where you are.
- **Safe by default.** Destructive operations (delete) go to the OS Trash, not the void.
- **No surprises.** Invalid config is ignored quietly. probefs never crashes on startup.

---

## Installation

### From PyPI

```sh
pip install probefs
```

### With uv (isolated tool install)

[uv](https://github.com/astral-sh/uv) installs probefs into its own isolated environment and puts the `probefs` binary on your PATH:

```sh
uv tool install probefs
```

### Running from source

Clone the repository and use `uv` to run directly from source:

```sh
git clone https://github.com/yourusername/probefs.git
cd probefs
uv sync
uv run probefs
```

`uv sync` installs all dependencies into a local virtual environment. `uv run probefs` executes the project entry point without needing to activate the environment manually.

---

## Interface Overview

probefs uses a three-pane miller columns layout:

```
┌──────────────────┬──────────────────────┬──────────────────────────────┐
│  PARENT          │  CURRENT             │  PREVIEW                     │
│  (read-only)     │  (active)            │                              │
│                  │                      │                              │
│  ..              │  > Documents/        │  # README.md                 │
│  home/           │    Downloads/        │                              │
│  etc/            │    Music/            │  Welcome to probefs.         │
│  usr/            │    Pictures/         │  A keyboard-driven TUI       │
│  var/            │    Videos/           │  file browser.               │
│                  │    README.md         │                              │
│                  │    .bashrc           │                              │
├──────────────────┴──────────────────────┴──────────────────────────────┤
│  ~/home/user  •  8 items  •  42.3 GB free                              │
├─────────────────────────────────────────────────────────────────────────┤
│  j/k move  l/Enter open  h/Back up  y copy  p move  d trash  q quit   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Left pane — Parent directory

Shows the contents of the directory one level above your current location. This pane is read-only and serves as a navigation context so you always know where you came from. The entry that corresponds to your current directory is highlighted.

### Middle pane — Current directory

The active, navigable pane. Your cursor lives here. Use `j`/`k` to move the cursor up and down through the listing. Press `l` or `Enter` to enter a directory or act on a file. Press `h` or `Backspace` to go up to the parent.

### Right pane — Preview

Updates live as you move the cursor in the middle pane:

- **File selected:** shows the file's contents with syntax highlighting.
- **Directory selected:** shows that directory's listing.

### Status bar

The bar below the three panes shows:

- **Current path** — the full path of the directory in the middle pane.
- **Item count** — the number of visible items in the current directory.
- **Free disk space** — the amount of free space on the filesystem where the current directory lives.

### Footer

The bar at the very bottom of the screen is a live key-hint bar showing the most common keybindings at a glance.

---

## Navigation

All navigation in probefs is modal — no modifier keys needed for movement.

| Key | Action |
|-----|--------|
| `j` or `↓` | Move cursor down one item |
| `k` or `↑` | Move cursor up one item |
| `l` or `Enter` | Enter the selected directory (moves it into the middle pane) |
| `h` or `Backspace` | Go up to the parent directory |
| `.` | Toggle display of hidden files and directories (dotfiles) |
| `q` or `Ctrl+C` | Quit probefs |

### Movement details

**Moving down and up** — `j` and `k` move the cursor one item at a time. Hold the key down to scroll through a long listing quickly. The cursor wraps at neither end; it stops at the first or last item.

**Entering a directory** — pressing `l` or `Enter` when the cursor is on a directory pushes that directory into the middle pane, the former middle pane becomes the left (parent) pane, and the preview updates for the first item in the new directory.

**Going up** — pressing `h` or `Backspace` moves up one level. The current middle directory slides into the right pane briefly, and the parent becomes the new current directory.

**Hidden files** — pressing `.` toggles dotfiles (files and directories whose names start with `.`) on and off. The toggle state persists for the lifetime of the session but is not saved between runs.

---

## File Preview

The right pane shows a preview of the item currently under the cursor.

### Files

File contents are displayed with syntax highlighting powered by [Pygments](https://pygments.org/). The language is auto-detected from the file extension (e.g. `.py` → Python, `.rs` → Rust, `.yaml` → YAML). Line numbers are shown on the left margin.

**Size limit:** Files larger than 512 KB are truncated. A notice at the bottom of the preview pane indicates when truncation has occurred.

**Binary files:** If probefs detects that a file is binary (non-text), the preview pane displays:

```
Binary file — preview unavailable
```

No attempt is made to decode or display binary content.

### PDF files

PDF files are previewed as extracted text (up to 20 pages) using `pdftotext` from [poppler](https://poppler.freedesktop.org/). Poppler is an optional system dependency — if it is not installed, the preview pane shows an install hint:

```
pdftotext not found — install poppler to enable PDF preview
  macOS:  brew install poppler
  Ubuntu: sudo apt install poppler-utils
  Fedora: sudo dnf install poppler-utils
```

### Directories

When the cursor is on a directory, the right pane shows a simple listing of that directory's contents. This lets you see what is inside a directory before entering it.

---

## File Operations

All file operations are invoked from the middle (current) pane with a single key. Each operation opens a dialog or confirmation prompt. After the operation completes, the directory listing refreshes automatically. Success and error notifications appear as brief overlays.

### Copy — `y`

Press `y` to copy the selected item.

A dialog appears with a destination path field pre-filled with the current directory path plus the item's filename. You can:

- Accept the default (copy to the same directory with the same name — effectively a duplicate).
- Change only the filename portion to copy with a new name (rename-during-copy).
- Change the directory portion to copy to a different location.

If the destination is an existing directory, the item is copied **into** that directory rather than replacing it.

### Move — `p`

Press `p` to move the selected item.

A dialog appears with a destination path field pre-filled with the current path appended to the end. Edit the path to specify where the item should be moved. The same directory semantics as copy apply: if the destination is an existing directory, the item is moved into it.

### Delete — `d`

Press `d` to delete the selected item.

A confirmation dialog asks you to confirm before anything is deleted. On confirmation, the item is sent to the **OS Trash** (macOS Trash, Windows Recycle Bin, or the freedesktop.org Trash on Linux). This is always recoverable from the Trash — probefs never performs a permanent deletion.

### Rename — `r`

Press `r` to rename the selected item.

A dialog appears with the current filename pre-filled. Edit the name in place and press `Enter` to confirm. The item is renamed within its current directory. To move an item to a different directory, use the move operation (`p`) instead.

### New file — `n`

Press `n` to create a new file in the current directory.

A dialog prompts you to enter the filename. Press `Enter` to confirm. An empty file is created at the current directory. If a file with that name already exists, an error notification is shown.

### New directory — `Ctrl+N`

Press `Ctrl+N` to create a new directory inside the current directory.

A dialog prompts you to enter the directory name. Press `Enter` to confirm. If a directory with that name already exists, an error notification is shown.

---

## Configuration

probefs reads its configuration from:

```
~/.probefs/probefs.yaml
```

The directory and config file are created automatically on first launch with all options documented inline. For a fully commented reference, see [`probefs.yaml.example`](../probefs.yaml.example) in the repository.

If the file exists but contains invalid YAML or unrecognized keys, the invalid portions are silently ignored — probefs will never crash on startup because of a bad config file.

### Full configuration reference

```yaml
# ~/.probefs/probefs.yaml

# Built-in theme name. One of: probefs-dark, probefs-light, probefs-tokyo-night
theme: probefs-dark

# Path to a custom theme YAML file.
# If set, this overrides the `theme` setting above.
theme_file: ~/my-theme.yaml

# Icon set. Options: ascii (default, works everywhere) | nerd (requires Nerd Fonts)
icons: ascii

# Keybinding overrides. Keys are action IDs; values are key strings.
# An override replaces all default keys for that action.
# Separate multiple keys with commas.
keybindings:
  probefs.cursor_down: "j"
  probefs.quit:        "q,ctrl+c"
```

### Config keys

| Key | Type | Default | Description |
|---|---|---|---|
| `theme` | string | `probefs-dark` | Name of a built-in theme |
| `theme_file` | path | _(none)_ | Path to a custom theme YAML; overrides `theme` |
| `icons` | string | `ascii` | Icon set: `ascii` or `nerd` |
| `keybindings` | map | _(see below)_ | Action ID to key string overrides |

---

## Themes

### Built-in themes

| Theme name | Style |
|---|---|
| `probefs-dark` | Dark background with blue and teal accents. The default. |
| `probefs-light` | Light background, high contrast for bright environments. |
| `probefs-tokyo-night` | Tokyo Night palette — deep blue-grey backgrounds with vivid accent colors. |

Activate a built-in theme by setting `theme` in your config:

```yaml
theme: probefs-tokyo-night
```

### Custom themes

The easiest way to create a custom theme is to drop a `.yaml` file into `~/.probefs/themes/`:

```
~/.probefs/
  themes/
    my-theme.yaml
    another-theme.yaml
```

probefs scans this directory at startup and registers every `.yaml` file it finds. Activate any of them by name in your config:

```yaml
theme: my-theme
```

Alternatively, point `theme_file` directly at any YAML file anywhere on your system:

```yaml
theme_file: ~/my-probefs-theme.yaml
```

#### Full custom theme schema

```yaml
# Required
name: my-theme        # Unique name for your theme (string, required)

# Optional — controls whether Textual uses dark or light base styling
dark: true            # true = dark variant, false = light variant

# Color fields — all accept CSS color strings:
#   hex:   "#rrggbb" or "#rgb"
#   rgb:   "rgb(r, g, b)"
#   named: "red", "cornflowerblue", etc.

primary:    "#5B8DD9"   # Primary accent (highlighted items, active borders)
secondary:  "#2D4A8A"   # Secondary accent (subdued highlights)
background: "#1C2023"   # Main terminal background
surface:    "#252B2E"   # Pane backgrounds (slightly lighter than background)
panel:      "#1E2528"   # Panel / sidebar backgrounds
foreground: "#E0E0E0"   # Default text color
warning:    "#FFB86C"   # Warning notifications and indicators
error:      "#FF5555"   # Error notifications and indicators
success:    "#50FA7B"   # Success notifications and indicators
accent:     "#8BE9FD"   # Bright accent for decorative elements

# Optional metadata — stored in the file but not used at runtime
author:      "Your Name"
description: "A brief description of the theme"
version:     "1.0.0"
```

Only `name` and `primary` are required. All other color fields are optional; unspecified fields fall back to the base theme's defaults.

#### Color role reference

| Field | Role in probefs |
|-------|----------------|
| `primary` | Active borders, focused widget outlines, dialog borders, highlighted rows |
| `secondary` | Secondary accents, subdued highlights |
| `background` | App background behind all widgets |
| `surface` | Dialog box backgrounds, input fields |
| `panel` | Directory list pane backgrounds, status bar |
| `boost` | Subtle lightening applied to focused/hovered elements over surface/panel |
| `foreground` | Default text color |
| `warning` | Warning notifications |
| `error` | Error notifications, destructive button style |
| `success` | Success notifications |
| `accent` | Highlighted text, links, secondary interactive elements |

Textual automatically derives tinted variants from each color — `$primary-lighten-1`, `$panel-darken-2`, etc. — so you only need to define the base colors and the full range is generated for free.

---

## Icons

probefs ships two icon sets. The default works in any terminal; the Nerd Fonts set adds file-type glyphs.

### Choosing an icon set

Set the `icons` key in `~/.probefs/probefs.yaml`:

```yaml
icons: nerd    # or: ascii (default)
```

| Value | Description |
|-------|-------------|
| `ascii` | Plain ASCII symbols — works in every terminal, including SSH sessions |
| `nerd` | Unicode glyphs from [Nerd Fonts](https://www.nerdfonts.com/) |

### ASCII icons (default)

| Category | Symbol |
|----------|--------|
| Directory | `/` |
| File | ` ` |
| Executable | `*` |
| Symlink | `@` |
| Broken symlink | `!` |
| Archive | `#` |
| Image | `%` |

### Nerd Fonts icons

Requires a [Nerd Fonts patched font](https://www.nerdfonts.com/font-downloads) installed and active in your terminal.

| Category | Glyph | Nerd Fonts name |
|----------|-------|-----------------|
| Directory | `\uf07b` | nf-fa-folder |
| File | `\uf15b` | nf-fa-file |
| Executable | `\uf013` | nf-fa-cog |
| Symlink | `\uf0c1` | nf-fa-link |
| Broken symlink | `\uf127` | nf-fa-chain_broken |
| Archive | `\uf1c6` | nf-fa-file_zip_o |
| Image | `\uf1c5` | nf-fa-file_image_o |

> **Note:** Auto-detection of Nerd Fonts is not possible, especially over SSH. Explicit opt-in via config is required.

---

## Keybinding Customization

### Bindable actions

| Action ID | Default keys | Description |
|---|---|---|
| `probefs.cursor_down` | `j`, `↓` | Move cursor down |
| `probefs.cursor_up` | `k`, `↑` | Move cursor up |
| `probefs.enter_dir` | `l`, `Enter` | Enter selected directory |
| `probefs.leave_dir` | `h`, `Backspace` | Go up to parent directory |
| `probefs.toggle_hidden` | `.` | Toggle hidden files |
| `probefs.quit` | `q`, `Ctrl+C` | Quit probefs |
| `probefs.copy` | `y` | Copy selected item |
| `probefs.move` | `p` | Move selected item |
| `probefs.delete` | `d` | Delete (send to Trash) |
| `probefs.rename` | `r` | Rename selected item |
| `probefs.new_file` | `n` | Create new file |
| `probefs.new_dir` | `ctrl+n` | Create new directory |

### Override semantics

An entry in `keybindings` **replaces** all default keys for that action. If you set:

```yaml
keybindings:
  probefs.cursor_down: "ctrl+j"
```

then `j` and `↓` no longer work for cursor-down — only `ctrl+j` does.

### Keeping old keys and adding new ones

To add a new key while keeping the defaults, list all keys you want (including the originals) as a comma-separated string:

```yaml
keybindings:
  probefs.cursor_down: "j,down,ctrl+j"   # j, ↓, and ctrl+j all move down
```

### Multiple keys per action

Separate multiple keys with commas, no spaces required:

```yaml
keybindings:
  probefs.enter_dir: "l,enter,space"
```

### Limitations

- **No chord/sequence support.** Bindings like `gg` or `di` are not supported. Each binding must be a single key or key with modifiers (e.g. `ctrl+n`).
- **No conflict detection.** If two actions share a key, the last one registered wins. probefs does not warn about conflicts.

---

## Tips and Tricks

### Navigate quickly

Hold `j` or `k` to scan through a long directory listing at speed. Press `l` to dive into a directory without breaking rhythm, and `h` to come back up. The three-pane layout means you always have visual context for where you are.

### Copy with rename

Press `y` to copy, then in the destination dialog edit only the **filename portion** at the end of the path. This lets you duplicate a file under a new name in one step — no need to copy first and rename second.

### Move to a different directory

Press `p` and type (or paste) the full absolute destination path in the dialog. You can move a file anywhere on your filesystem in a single operation.

### Trash vs. permanent delete

Pressing `d` always sends the item to the OS Trash — macOS Trash, Windows Recycle Bin, or the freedesktop.org Trash on Linux. Nothing probefs does is permanently irreversible. If you accidentally delete something, open your Trash and restore it.

### Seeing what's inside before entering

Before pressing `l` to enter a directory, glance at the right (preview) pane. It already shows the directory's contents so you can confirm you're going to the right place.

### Toggling dotfiles on the fly

Press `.` at any time to show or hide hidden files. This is especially useful when navigating home directories where dotfiles would otherwise clutter the listing.
