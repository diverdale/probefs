# probefs

**A fast, beautiful, keyboard-driven TUI file browser built with Python and Textual.**
Navigate your filesystem at the speed of thought — no mouse required.

![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Framework](https://img.shields.io/badge/built%20with-Textual-purple)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  probefs                                                                │
├──────────────────┬──────────────────────┬──────────────────────────────┤
│  PARENT          │  CURRENT             │  PREVIEW                     │
│                  │                      │                              │
│  ..              │  > Documents/        │  # README.md                 │
│  home/           │    Downloads/        │                              │
│  etc/            │    Music/            │  Welcome to probefs.         │
│  usr/            │    Pictures/         │  A keyboard-driven TUI       │
│  var/            │    Videos/           │  file browser built with     │
│                  │    README.md         │  Python and Textual.         │
│                  │    .bashrc           │                              │
│                  │    .gitconfig        │  Navigate fast. No mouse.    │
│                  │                      │                              │
├──────────────────┴──────────────────────┴──────────────────────────────┤
│  ~/home/user  •  8 items  •  42.3 GB free                              │
├─────────────────────────────────────────────────────────────────────────┤
│  j/k move  l/Enter open  h/Back up  y copy  p move  d trash  ? help   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Features

- **Three-pane miller columns** — parent context, active directory, and live preview side-by-side
- **Vim-style navigation** — `j`/`k` to move, `l` to enter, `h` to go up
- **Syntax-highlighted previews** — powered by Pygments, auto-detected from file extension
- **Directory previews** — right pane lists directory contents when a folder is selected
- **Full file operations** — copy, move, rename, delete, new file, new directory
- **Safe deletes** — `d` sends to OS Trash, never permanent deletion
- **Toggle hidden files** — `.` key shows/hides dotfiles instantly
- **Nerd Fonts icons** — optional glyph icons with `icons: nerd` in config (falls back to ASCII)
- **Configurable themes** — three built-ins plus a full custom theme YAML schema
- **Rebindable keys** — override any action's keybinding in your config file
- **Status bar** — always shows current path, item count, and free disk space
- **Zero mouse required** — every operation reachable from the keyboard

---

## Requirements

- Python >= 3.10
- Any modern terminal (kitty, iTerm2, Ghostty, Windows Terminal, GNOME Terminal, etc.)

---

## Installation

### From PyPI (recommended)

```sh
pip install probefs
```

Or with [uv](https://github.com/astral-sh/uv) (installs as an isolated tool):

```sh
uv tool install probefs
```

### From source (development)

```sh
git clone https://github.com/yourusername/probefs.git
cd probefs
uv sync
uv run probefs
```

---

## Quick Start

```sh
probefs
```

That's it. probefs opens in your current directory.

---

## Key Bindings

| Key | Action |
|-----|--------|
| `j` / `↓` | Move cursor down |
| `k` / `↑` | Move cursor up |
| `l` / `Enter` | Enter directory / open |
| `h` / `Backspace` | Go up to parent directory |
| `.` | Toggle hidden files (dotfiles) |
| `y` | Copy selected item |
| `p` | Move selected item |
| `d` | Delete (send to Trash) |
| `r` | Rename selected item |
| `n` | New file in current directory |
| `Ctrl+N` | New directory in current directory |
| `q` / `Ctrl+C` | Quit |

---

## Configuration

probefs reads `~/.probefs/probefs.yaml` on startup. The file and directory are created automatically on first launch. For a fully commented reference, see [`probefs.yaml.example`](probefs.yaml.example) in this repo.

```yaml
# ~/.probefs/probefs.yaml

theme: probefs-dark          # built-in theme name
theme_file: ~/mytheme.yaml   # path to a custom theme YAML (overrides theme:)

icons: nerd                  # nerd (requires Nerd Fonts) | ascii (default)

keybindings:
  probefs.cursor_down: "j"   # override a default key
```

Invalid configuration is silently ignored; probefs will never crash on startup due to a bad config file.

---

## Themes

Three themes are built in:

| Theme name | Style |
|---|---|
| `probefs-dark` | Dark background, blue/teal accents (default) |
| `probefs-light` | Light background, high-contrast |
| `probefs-tokyo-night` | Tokyo Night color palette |

Activate a theme in your config:

```yaml
theme: probefs-tokyo-night
```

---

## Custom Themes

Drop a `.yaml` file into `~/.probefs/themes/` and probefs picks it up automatically on next launch. Activate it by name:

```yaml
theme: my-theme
```

Or point `theme_file` directly at any YAML file:

```yaml
theme_file: ~/my-probefs-theme.yaml
```

Full theme schema:

```yaml
name: my-theme           # required
dark: true               # true = dark background variant

# Core colors (all accept CSS hex, rgb(), or named colors)
primary:    "#5B8DD9"
secondary:  "#2D4A8A"
background: "#1C2023"
surface:    "#252B2E"
panel:      "#1E2528"
foreground: "#E0E0E0"
warning:    "#FFB86C"
error:      "#FF5555"
success:    "#50FA7B"
accent:     "#8BE9FD"

# Optional metadata (informational only, not used at runtime)
author:      "Your Name"
description: "My custom theme"
version:     "1.0.0"
```

Only `name` and `primary` are required. All other color fields are optional and fall back to theme defaults.

---

## Icons

By default probefs uses plain ASCII symbols that work in any terminal. If your terminal uses a [Nerd Fonts](https://www.nerdfonts.com/) patched font, enable glyph icons:

```yaml
icons: nerd
```

| Setting | Icons used |
|---------|------------|
| `ascii` (default) | `/` dirs, space files — works everywhere including SSH |
| `nerd` | Unicode glyphs from Nerd Fonts (requires patched font) |

> Auto-detection is not possible over SSH, so Nerd Fonts must be explicitly enabled.

---

## Keybinding Overrides

Override any action's key in `~/.probefs/probefs.yaml`:

```yaml
keybindings:
  probefs.cursor_down: "j,ctrl+j"   # multiple keys: comma-separated
  probefs.cursor_up:   "k"
  probefs.quit:        "q"
```

An override **replaces** all defaults for that action. To keep an existing key and add a new one, list both:

```yaml
keybindings:
  probefs.enter_dir: "l,enter,space"   # l, Enter, and Space all enter a directory
```

> Note: chord/sequence bindings (e.g. `gg`) are not supported. No conflict detection is performed — if two actions share a key, last registration wins.

---

## Documentation

Full reference: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

---

## License

MIT — see [LICENSE](LICENSE) for details.
