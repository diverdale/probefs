# probefs

## What This Is

A modern TUI file browser built with Python and Textual, designed for server administrators who need to navigate and manage file systems visually over SSH. probefs combines the fluid three-pane navigation of ranger/yazi with a rich theming system, custom icon support, and a user-configurable keybinding layer.

## Core Value

A fast, beautiful, keyboard-driven file browser that feels at home in any terminal — local or remote — with a theming ecosystem that makes it yours.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Three-pane file navigation (parent dir | current dir | preview pane), ranger-style
- [ ] File operations via hotkeys: rename, copy, move, delete, create file/dir
- [ ] File preview in right pane (text files, directory listings)
- [ ] Color theming via YAML/JSON config files with live reload
- [ ] Built-in theme collection (light, dark, and a few curated extras)
- [ ] Theme file format with metadata (name, author, description) for sharing
- [ ] GitHub-based theme registry (curated awesome-list style index)
- [ ] Theme install/manage commands (install from GitHub, list, switch)
- [ ] Icon themes with Nerd Font glyphs + ASCII fallback, auto-detected
- [ ] User-local keybinding overrides via config file
- [ ] Distribution via PyPI, pipx, and Homebrew

### Out of Scope

- SFTP/remote filesystem interface — future milestone; architect for clean extension
- Plugin framework — deferred; keybinding customization covers v1 extensibility needs
- Vim-style command mode (`:rename`, etc.) — future consideration after v1
- XML theme format — explicitly rejected; YAML/JSON only
- GUI theme editor inside the TUI — v2; config file is source of truth for v1

## Context

- Built with Python + Textual (https://textual.textualize.io/)
- Target users: server administrators, developers comfortable in the terminal
- Navigation feel: lf/yazi — modern, fast, minimal, extensible
- Nerd Fonts are common in developer terminals but not guaranteed on servers; ASCII fallback is important for SSH contexts
- Theme sharing inspired by iTerm2's community color scheme ecosystem but using YAML/JSON instead of XML
- Architecture must accommodate future SFTP transport layer without major refactoring

## Constraints

- **Tech Stack**: Python + Textual — core framework, no alternatives
- **Python Version**: Target Python 3.10+ for modern type hints and match statements
- **No XML**: Theme/config files are YAML or TOML/JSON only
- **Terminal compatibility**: Must work in standard SSH terminal environments (no special terminal features required beyond color support)
- **Distribution**: PyPI package + pipx-friendly + Homebrew formula for macOS

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Three-pane layout (ranger-style) | Matches mental model of navigating directory trees; preview pane adds context | — Pending |
| YAML/JSON for themes (not XML) | Human-readable, widely supported, avoids iTerm2 XML pain | — Pending |
| GitHub-based theme registry (awesome-list style) | Decentralized, no backend to maintain, community-driven | — Pending |
| Nerd Fonts + ASCII auto-detect | Works great when available, degrades gracefully on bare servers | — Pending |
| Skip plugins v1, support user keybindings | Scope control; keybindings cover the main customization need | — Pending |
| SFTP deferred but architecturally planned | Server admin use case is core motivation; filesystem abstraction layer needed | — Pending |

---
*Last updated: 2026-03-09 after initialization*
