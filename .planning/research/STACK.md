# Stack Research

**Domain:** Python TUI file browser (ranger-style, three-pane)
**Researched:** 2026-03-09
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.10+ | Runtime | Target baseline; asyncssh 2.x requires 3.10+, typing improvements available, match-statement syntax clean for keybinding dispatch |
| Textual | 8.0.2 | TUI framework | Industry standard for interactive Python TUIs in 2026; async-native, CSS theming (TCSS), built-in Worker API for non-blocking file ops, Pilot testing API, custom keymap API in stable releases |
| Rich | 14.3.3 | Syntax highlighting, text rendering | Textual's underlying rendering engine; use directly for preview pane syntax highlighting via `rich.syntax.Syntax.from_path()` |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruamel.yaml | 0.19.1 | YAML config read/write | All YAML config (theme files, keymap overrides, user settings); use over PyYAML because it preserves comments and supports YAML 1.2 — critical when users hand-edit theme files |
| platformdirs | 4.9.4 | XDG/platform config paths | Resolves `~/.config/probefs/`, `~/.local/share/probefs/` on Linux and correct equivalents on macOS/Windows; always use over hardcoded paths |
| send2trash | 2.1.0 | Safe file deletion | Sends to OS trash instead of permanent unlink; required for any delete operation in a file browser targeting server admins who make mistakes |
| watchdog | 6.0.0 | Filesystem event monitoring | Live directory refresh when external processes add/remove files; use `Observer` with Textual Worker so events post to UI thread safely |
| asyncssh | 2.22.0 | SFTP support (future milestone) | Async-native SSH/SFTP; integrate at architecture boundaries now (abstract filesystem interface), implement in a later milestone; do not use paramiko for new code |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | 0.10.9 | Package/project manager, build frontend | Replace pip/poetry/virtualenv; `uv init --package`, `uv build`, `uv publish`; 10-100x faster than pip; standard in 2026 |
| pytest | 9.0.2 | Test runner | Standard; pair with pytest-asyncio for Textual async tests |
| pytest-asyncio | 1.1.0 | Async test support | Required for testing Textual apps; decorate async tests with `@pytest.mark.asyncio` or configure `asyncio_mode = "auto"` in pyproject.toml |
| pytest-textual-snapshot | 1.1.0 | Visual regression testing | Captures SVG screenshots of Textual app states; compare across commits to catch layout/theme regressions; run once to generate baseline |
| ruff | latest | Linting + formatting | Replaces flake8 + black + isort in one fast tool; configure in pyproject.toml |
| mypy | latest | Static type checking | Textual's widget API is fully typed; mypy catches widget composition errors at dev time, not runtime |

## Installation

```bash
# Initialize project
uv init --package probefs
cd probefs

# Core runtime dependencies
uv add textual rich ruamel.yaml platformdirs send2trash watchdog

# SFTP (add when implementing SFTP milestone)
# uv add asyncssh

# Dev dependencies
uv add --dev pytest pytest-asyncio pytest-textual-snapshot ruff mypy
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Textual | urwid | If targeting Python 2 or needing an extremely minimal dependency footprint on embedded Linux; urwid is effectively unmaintained for new feature development |
| Textual | curses (stdlib) | Never for new application development; curses requires manual screen management with no layout system, no widget reuse, no CSS theming |
| ruamel.yaml | PyYAML | Only if you never allow users to edit config files by hand; PyYAML destroys comments on round-trip and parses `yes`/`no` as booleans by default (a footgun for config files) |
| send2trash | `os.unlink()` / `shutil.rmtree()` | Only for truly temporary/generated files that users don't care about recovering; never for user-initiated delete actions |
| watchdog | inotify (Linux-only) | Only if Linux-exclusive deployment is guaranteed and you need lower overhead; watchdog abstracts platform differences for macOS kqueue + Linux inotify + Windows ReadDirectoryChangesW |
| asyncssh | paramiko | Only for legacy codebases already on paramiko; asyncssh is async-native and faster for concurrent transfers; paramiko is synchronous and requires thread wrapping |
| uv | poetry | If the team already has a heavy Poetry investment; uv builds on pyproject.toml/PEP 621 and is compatible with Hatchling as build backend |
| platformdirs | hardcoded `~/.config/` | Never; breaks on macOS (`~/Library/Application Support`) and Windows (`%APPDATA%`) |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| PyYAML | Parses `yes`/`no`/`on`/`off` as booleans in YAML 1.1 mode; nukes comments on round-trip write; stuck on YAML 1.1 standard from 2005 | ruamel.yaml |
| python-magic (libmagic) | Requires system-level `libmagic` native library; adds a C dependency that breaks on minimal server installs and Homebrew formula packaging | stdlib `mimetypes.guess_type()` for preview MIME detection; acceptable for a file browser where extensions are the primary signal |
| curses | No layout system, no widget abstraction, manual screen buffer management; TUI apps built on curses require full rewrites to evolve | Textual |
| urwid | Unmaintained for new features; no async support; lacks CSS theming; requires manual layout code | Textual |
| Poetry | Slower than uv; adds overhead with lock file format incompatibilities; being displaced by uv in 2025-2026 ecosystem | uv |
| paramiko | Synchronous SSH/SFTP; needs thread wrapping inside Textual workers; higher complexity for SFTP milestone integration | asyncssh |
| Directly importing `os.path` | `pathlib.Path` provides the same surface with cleaner API and safer path composition; `os.path` is the pre-3.4 pattern | `pathlib.Path` throughout |

## Stack Patterns by Variant

**For icon rendering (Nerd Fonts vs ASCII fallback):**
- Do not rely on automatic Nerd Font detection — no reliable cross-terminal API exists
- Use a runtime probe at startup: attempt to render a known Nerd Font glyph (U+E000 range) and read terminal response, OR default to ASCII and expose a `PROBEFS_ICONS=nerd|ascii|auto` environment variable
- Fallback to ASCII box-drawing characters by default; let users opt into Nerd Fonts explicitly via config or env var
- Store icon sets as a dict mapping MIME category → glyph string; swap the entire dict based on the detected/configured mode

**For theme distribution (GitHub-based registry):**
- Store community themes as YAML files in a dedicated GitHub repository (e.g., `probefs-themes`)
- Theme install: `probefs theme install <name>` fetches raw YAML via HTTPS (use `httpx` or stdlib `urllib.request`), validates schema with ruamel.yaml, writes to `platformdirs.user_data_dir()/themes/`
- Do not bundle more than 2-3 built-in themes; keep the binary small and let users pull what they want

**For keybinding overrides:**
- Use Textual's native keymap API (`App.set_keymap()`, `Binding(id=...)`) — this was added to stable in a 2024 release and is the correct surface for user-local overrides
- Load user keymap YAML at `on_mount` and call `self.set_keymap(parsed_dict)`; no need for custom event routing

**For SFTP architecture (future milestone):**
- Define an abstract `FileSystemProvider` protocol now (using `typing.Protocol`)
- `LocalProvider` uses `pathlib` + `shutil`; `SFTPProvider` implements the same interface via asyncssh
- The three-pane layout never directly calls `pathlib` — it calls `self.fs.listdir()`, `self.fs.read()`, etc.
- This prevents SFTP from requiring a pane-level rewrite when implemented

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| textual 8.0.2 | rich >=14.2.0 | Textual pins rich >=14.2.0 in its own dependencies; rich 14.3.3 satisfies this |
| textual 8.0.2 | Python 3.9–3.14 | Target Python 3.10+ for asyncssh compat, but Textual itself supports 3.9 |
| asyncssh 2.22.0 | Python >=3.10 | Hard lower bound; this is why the project targets Python 3.10+ |
| asyncssh 2.22.0 | cryptography >=39.0 | Auto-installed as a dependency; no manual pinning needed |
| ruamel.yaml 0.19.1 | Python 3.x | Version 0.19.0+ dropped the optional C extension (ruamel.yaml.clib) — pure Python install, no compilation needed |
| pytest-asyncio 1.1.0 | pytest >=9.0 | pytest 9 required; pair with `asyncio_mode = "auto"` in pyproject.toml to avoid per-test decorator noise |
| watchdog 6.0.0 | Python >=3.9 | Apache 2.0 license; inotify on Linux, kqueue on macOS, ReadDirectoryChangesW on Windows |

## Packaging and Distribution

```toml
# pyproject.toml (minimal)
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "probefs"
requires-python = ">=3.10"
dependencies = [
    "textual>=8.0.0",
    "rich>=14.2.0",
    "ruamel.yaml>=0.19.0",
    "platformdirs>=4.0.0",
    "send2trash>=2.0.0",
    "watchdog>=6.0.0",
]

[project.scripts]
probefs = "probefs.cli:main"
```

**PyPI:** `uv publish` after `uv build` — primary distribution channel.

**pipx:** Users install with `pipx install probefs`; pipx is available via Homebrew and handles the isolated venv automatically.

**Homebrew tap:** Create `homebrew-probefs` GitHub repo with a Ruby formula that calls `pipx install probefs` or uses Python resource declarations. Third-party tap, not homebrew-core (core requires significant usage threshold).

## Sources

- PyPI textual 8.0.2 — https://pypi.org/pypi/textual/json (verified 2026-03-09)
- PyPI rich 14.3.3 — https://pypi.org/pypi/rich/json (verified 2026-03-09)
- PyPI ruamel.yaml 0.19.1 — https://pypi.org/pypi/ruamel.yaml/json (verified 2026-03-09)
- PyPI platformdirs 4.9.4 — https://pypi.org/pypi/platformdirs/json (verified 2026-03-09)
- PyPI send2trash 2.1.0 — https://pypi.org/pypi/Send2Trash/json (verified 2026-03-09)
- PyPI watchdog 6.0.0 — https://pypi.org/pypi/watchdog/json (verified 2026-03-09)
- PyPI asyncssh 2.22.0 — https://pypi.org/pypi/asyncssh/json (verified 2026-03-09)
- PyPI uv 0.10.9 — https://pypi.org/pypi/uv/json (verified 2026-03-09)
- PyPI pytest 9.0.2 — https://pypi.org/pypi/pytest/json (verified 2026-03-09)
- PyPI pytest-asyncio 1.1.0 — https://pypi.org/pypi/pytest-asyncio/json (verified 2026-03-09)
- PyPI pytest-textual-snapshot 1.1.0 — https://pypi.org/pypi/pytest-textual-snapshot/json (verified 2026-03-09)
- Textual theming guide — https://textual.textualize.io/guide/design/ (verified 2026-03-09)
- Textual testing guide — https://textual.textualize.io/guide/testing/ (verified 2026-03-09)
- Textual keybinding/keymap docs — https://textual.textualize.io/api/binding/ (verified via WebSearch 2026-03-09)
- ruamel.yaml vs PyYAML analysis — https://medium.com/top-python-libraries/why-ruamel-yaml-should-be-your-python-yaml-library-of-choice-81bc17891147 (MEDIUM confidence — WebSearch, corroborated by PyPI changelogs)
- Python packaging 2026 state — https://learn.repoforge.io/posts/the-state-of-python-packaging-in-2026/ (MEDIUM confidence — WebSearch)
- Nerd Fonts detection discussion — https://github.com/ryanoasis/nerd-fonts/discussions/829 (MEDIUM confidence — official repo discussion)

---
*Stack research for: Python TUI file browser (probefs)*
*Researched: 2026-03-09*
