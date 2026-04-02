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
7. [Sort and Filter](#sort-and-filter)
8. [Clipboard and Launch](#clipboard-and-launch)
9. [SFTP Screen](#sftp-screen)
10. [Configuration](#configuration)
11. [Themes](#themes)
12. [Icons](#icons)
13. [Keybinding Customization](#keybinding-customization)
14. [Tips and Tricks](#tips-and-tricks)

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
│  ~/home/user  •  8 items  •  name↑  •  42.3 GB free                   │
├─────────────────────────────────────────────────────────────────────────┤
│  j/k move  l/Enter open  h back  ? help  ctrl+q quit                  │
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
- **Item count** — the number of visible items (or "matched" items when a filter is active).
- **Sort mode** — the current sort order (e.g. `name↑`, `size↓`).
- **Free disk space** — the amount of free space on the filesystem where the current directory lives.

### Footer

The bar at the very bottom of the screen is a live key-hint bar showing the most common keybindings at a glance. Press `?` at any time to open the full keybinding reference.

---

## Navigation

All navigation in probefs is modal — no modifier keys needed for movement.

| Key | Action |
|-----|--------|
| `j` or `↓` | Move cursor down one item |
| `k` or `↑` | Move cursor up one item |
| `l` or `Enter` | Enter the selected directory / open the selected file |
| `h` or `Backspace` | Go up to the parent directory |
| `Ctrl+O` | Navigate back in directory history |
| `Ctrl+I` | Navigate forward in directory history |
| `g` | Jump to any path via an input dialog |
| `.` | Toggle display of hidden files and directories (dotfiles) |
| `Ctrl+Q` or `Ctrl+C` | Quit probefs |

### Movement details

**Moving down and up** — `j` and `k` move the cursor one item at a time. Hold the key down to scroll through a long listing quickly. The cursor stops at the first or last item.

**Entering a directory** — pressing `l` or `Enter` when the cursor is on a directory pushes that directory into the middle pane, the former middle pane becomes the left (parent) pane, and the preview updates for the first item in the new directory.

**Going up** — pressing `h` or `Backspace` moves up one level. The parent becomes the new current directory.

**Navigation history** — every directory change is recorded. Press `Ctrl+O` to go back to the previous directory (like a browser's back button) and `Ctrl+I` to go forward again. The history is per-session and not saved between launches.

**Jump to path** — pressing `g` opens a small input dialog. Type any absolute path and press `Enter` to jump there directly.

**Hidden files** — pressing `.` toggles dotfiles on and off. The toggle state persists for the lifetime of the session but is not saved between runs.

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

### Archives (ZIP and tar)

When the cursor is on a ZIP or tar file (including `.tar.gz`, `.tar.bz2`, `.tar.xz`, `.tgz`), the right pane lists the archive's contents — file paths and sizes — without extracting the archive. No extra dependencies are needed; this uses Python's standard library.

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

## Sort and Filter

### Sort — `s`

Press `s` to cycle through four sort modes:

| Mode | Sorts by |
|------|----------|
| `name↑` | Filename A → Z (default) |
| `name↓` | Filename Z → A |
| `size↓` | File size, largest first |
| `date↓` | Last modified, newest first |

Directories are always listed before files regardless of the active sort mode. The current sort mode is shown in the status bar.

### Filter — `/`

Press `/` to open the filter bar at the bottom of the screen. Type to narrow the listing to items whose names contain the typed text (case-insensitive). The status bar updates to show how many items matched.

| Key | Action |
|-----|--------|
| Any printable character | Append to filter |
| `Backspace` | Delete last character |
| `Enter` | Keep current filter and dismiss the bar |
| `Esc` | Clear filter and dismiss the bar |

While the filter bar is open, navigation keys (`j`/`k`/`l`/`h`) and all other app shortcuts are suspended so that typing works correctly.

---

## Clipboard and Launch

### Copy path — `Y`

Press `Y` (shift+y) to copy the full absolute path of the selected item to your system clipboard. A brief notification confirms the copy.

### Open with default app — `o`

Press `o` to open the selected file with the system default application — the same program that would open if you double-clicked the file in your desktop file manager. probefs continues running in the background while the external app is open.

### Shell drop — `!`

Press `!` (shift+1) to suspend probefs and drop to an interactive shell in the current directory. Your `$SHELL` environment variable determines which shell is launched. When you exit the shell (e.g. `exit` or `Ctrl+D`), probefs resumes exactly where you left it.

---

## SFTP Screen

Press `Ctrl+S` from the main screen to open the SFTP dual-pane transfer screen. You can also launch directly into it from the command line:

```sh
probefs --sftp hostname
```

### Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Host [___________] Port [22] User [___________] [Profiles…] [Connect] │
│  Auth [Password ▼] Pass/Key path [_____________________________]       │
├──────────────────────────────────┬──────────────────────────────────────┤
│  LOCAL  /home/you                │  REMOTE  /home/you                   │
│                                  │                                       │
│  > Documents/                    │    Documents/                         │
│    Downloads/                    │    projects/                          │
│    Music/                        │    .bashrc                            │
│    README.md                     │                                       │
├──────────────────────────────────┴──────────────────────────────────────┤
│  local: /home/you  ·  4 items    remote: /home/you  ·  3 items          │
└─────────────────────────────────────────────────────────────────────────┘
```

The top bar switches between the connection form and a connected-status line once a connection is established.

### Connecting

Fill in the connection form:

| Field | Description |
|-------|-------------|
| **Host** | Hostname or IP address |
| **Port** | SSH port (default: 22) |
| **User** | SSH username |
| **Auth** | `Password` or `SSH Key` |
| **Pass / Key path** | Password text, or path to your private key (e.g. `~/.ssh/id_rsa`) |

Click **Connect** or press `Enter` from any field to initiate the connection. A notification confirms success or reports an error.

### Navigation

`Tab` switches the active pane (highlighted border). `j`/`k` move the cursor, `l` enters a directory, `h` goes up — the same as the main screen.

### Transferring files

With the cursor on a file in either pane, press `y` to transfer it to the other pane's current directory:

- **Local → Remote:** upload
- **Remote → Local:** download

A progress notification appears during the transfer. The destination pane refreshes automatically on completion.

> Directory transfer is not yet supported. Only individual files can be transferred.

### Connection profiles

On a successful connection, probefs automatically saves the host, port, username, and (if used) SSH key path to `~/.probefs/sftp_hosts.yaml`. Passwords are **never** saved.

On subsequent visits to the SFTP screen, a **Profiles** dropdown appears in the connection form. Select a saved profile to pre-fill all fields.

### SFTP keybindings

| Key | Action |
|-----|--------|
| `Tab` | Switch active pane (local / remote) |
| `j` / `k` | Move cursor in active pane |
| `l` / `Enter` | Enter directory in active pane |
| `h` / `Backspace` | Go up in active pane |
| `y` | Transfer selected file to the other pane |
| `Esc` | Disconnect and return to the main screen |

### Installing SFTP support

SFTP requires [paramiko](https://www.paramiko.org/). Install it with:

```sh
pip install "probefs[sftp]"
# or
uv tool install "probefs[sftp]"
```

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

# File listing colors — Rich style strings applied to entries in directory listings.
# Values accept any Rich-compatible style: hex colors, named colors, or styles
# like "bold #5B8DD9" or "italic cyan". All seven categories are optional;
# omitted categories fall back to the icon set's built-in defaults.
file_colors:
  directory:     "bold #5B8DD9"
  executable:    "bold #50FA7B"
  symlink:       "#8BE9FD"
  broken_symlink: "bold #FF5555"
  archive:       "#FFB86C"
  image:         "#FF79C6"
  file:          default

# Optional metadata — stored in the file but not used at runtime
author:      "Your Name"
description: "A brief description of the theme"
version:     "1.0.0"
```

Only `name` and `primary` are required. All other fields are optional; unspecified fields fall back to the base theme's defaults.

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

#### File listing color reference

The `file_colors` section controls how each entry type is colored in directory listings. Values are [Rich style strings](https://rich.readthedocs.io/en/stable/style.html) — hex colors, terminal color names, or combined styles like `"bold #5B8DD9"`.

| Category | Default (dark theme) | Description |
|----------|----------------------|-------------|
| `directory` | `bold #5B8DD9` | Directories |
| `executable` | `bold #50FA7B` | Files with execute permission |
| `symlink` | `#8BE9FD` | Symbolic links |
| `broken_symlink` | `bold #FF5555` | Symlinks pointing to a missing target |
| `archive` | `#FFB86C` | ZIP, tar, gz, and other archive formats |
| `image` | `#FF79C6` | PNG, JPG, SVG, and other image formats |
| `file` | `default` | All other files |

> **Tip:** Using hex colors (e.g. `"#5B8DD9"`) ensures consistent rendering across terminals. Named ANSI colors like `"blue"` may render differently depending on the terminal's color palette — which is why directories might appear purple in some terminals.

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
| `probefs.enter_dir` | `l`, `Enter` | Enter selected directory / open file |
| `probefs.leave_dir` | `h`, `Backspace` | Go up to parent directory |
| `probefs.go_back` | `ctrl+o` | Navigate back in history |
| `probefs.go_forward` | `ctrl+i` | Navigate forward in history |
| `probefs.goto` | `g` | Jump to any path |
| `probefs.toggle_hidden` | `.` | Toggle hidden files |
| `probefs.sort` | `s` | Cycle sort mode |
| `probefs.filter` | `/` | Open filter bar |
| `probefs.quit` | `ctrl+q`, `ctrl+c` | Quit probefs |
| `probefs.copy` | `y` | Copy selected item |
| `probefs.move` | `p` | Move selected item |
| `probefs.delete` | `d` | Delete (send to Trash) |
| `probefs.rename` | `r` | Rename selected item |
| `probefs.new_file` | `n` | Create new file |
| `probefs.new_dir` | `ctrl+n` | Create new directory |
| `probefs.copy_path` | `Y` | Copy current path to clipboard |
| `probefs.open_default` | `o` | Open with system default app |
| `probefs.shell` | `!` | Drop to shell in current directory |
| `probefs.sftp` | `ctrl+s` | Open SFTP screen |
| `probefs.help` | `?` | Show help dialog |
| `probefs.about` | `a` | Show about dialog |

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

### Filter then act

Press `/`, type a few characters to narrow the listing, then press `Enter` to keep the filter active while you perform a file operation. Press `/` and `Esc` to clear when done.

### Shell drop for bulk work

Press `!` to drop into a shell, run any commands you need (`mv`, `git`, `brew`, etc.), then `exit` to return to probefs without losing your place.

### Quit key

The quit key is `Ctrl+Q` (not `q`). This prevents accidentally closing probefs when typing in dialogs or filter bars. `Ctrl+C` also quits.
