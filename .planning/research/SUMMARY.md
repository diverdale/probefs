# Project Research Summary

**Project:** probefs
**Domain:** Python TUI file manager (ranger-style three-pane, server admin focus)
**Researched:** 2026-03-09
**Confidence:** HIGH

## Executive Summary

probefs is a keyboard-driven, three-pane TUI file manager targeting server administrators and Python ecosystem users. The competitive landscape is dominated by ranger (aging Python, synchronous), yazi (Rust, fast but requires build toolchain), lf (Go, config-heavy), and nnn (C, extreme minimalism). The opportunity is a modern Python TUI file manager with first-class pipx distribution, approachable YAML theming, and safety-first file operations that none of the current leaders deliver together. The recommended stack — Python 3.10+ with Textual 8.0.2 and uv as the package manager — is the clear choice for 2026: Textual provides async-native rendering, a Worker API for non-blocking I/O, CSS theming, and a testing API. No serious alternatives exist for interactive Python TUIs.

The recommended architecture has four layers: a Textual presentation layer (three DirectoryList panes + StatusBar), a controller layer (ProbeFSApp coordinating key dispatch, theming, icons), a domain layer (FileManagerCore, FileOps, Previewer, TaskQueue), and a Filesystem Abstraction Layer (FAL) built on fsspec. The single most important architectural decision is making the FAL mandatory from day one — every file operation must flow through `ProbeFS(protocol, **kwargs)` and never call `pathlib` or `os` directly in widgets. This is what allows SFTP support to be added in a future milestone without rewriting the widget layer.

The critical risk is inherited from ranger itself: synchronous I/O on the main event loop. Yazi's primary advantage over ranger is concurrent async pane loading. probefs must use Textual's `@work(thread=True)` decorator for all filesystem calls from the very first line of navigation code — retrofitting this pattern costs as much as a rewrite. Secondary risks are: keybinding priority inversion (widget bindings stealing app-level bindings), destructive file operations without trash semantics, and YAML theme schemas that don't map to Textual's 11-color model. All three are preventable with upfront design choices, not heroic engineering.

## Key Findings

### Recommended Stack

The stack is well-settled. Textual 8.0.2 is the only viable choice for a production Python TUI in 2026 — urwid is unmaintained and curses has no layout system. Rich 14.3.3 ships as Textual's rendering engine and provides syntax highlighting for the preview pane via `rich.syntax.Syntax.from_path()`. Use `uv` as the package manager (replaces pip/poetry, 10-100x faster, 2026 standard). Use `ruamel.yaml` over PyYAML — PyYAML destroys comments on round-trip and parses `yes`/`no` as booleans, which breaks user-edited config files. The `fsspec` library is the FAL implementation; it already provides both local and SFTP backends via the same `AbstractFileSystem` interface, eliminating the need for a custom abstraction.

**Core technologies:**
- Python 3.10+: Runtime — asyncssh requires 3.10+; match-statement syntax for keybinding dispatch
- Textual 8.0.2: TUI framework — async-native, Worker API, TCSS theming, Pilot testing, keymap API
- Rich 14.3.3: Rendering/preview — Textual's underlying engine; use directly for syntax-highlighted preview pane
- fsspec: Filesystem abstraction — identical API for local and SFTP; zero widget changes when adding remote filesystems
- ruamel.yaml 0.19.1: Config/themes — preserves comments, YAML 1.2, safe for user-edited files
- platformdirs 4.9.4: Config paths — resolves XDG dirs on Linux, macOS, Windows; never hardcode `~/.config/`
- send2trash 2.1.0: Safe delete — OS trash instead of permanent unlink; required for sysadmin safety
- watchdog 6.0.0: Live directory refresh — platform-abstracted inotify/kqueue/ReadDirectoryChangesW
- uv 0.10.9: Package/project manager — `uv init --package`, `uv build`, `uv publish`

**What NOT to use:** PyYAML, paramiko (use asyncssh), curses, urwid, Poetry, `os.path` (use `pathlib`), `python-magic` (use stdlib `mimetypes`)

### Expected Features

The feature set is cross-verified against 5+ TUI file manager repositories. The three-pane Miller columns layout is the defining product identity — do not add a dual-pane mode. The differentiators that justify probefs's existence are: YAML/JSON theme system with GitHub registry (ranger and lf make theming painful), trash-by-default delete (most managers use `rm`), first-class pipx distribution, and Nerd Fonts auto-detect with explicit opt-in fallback.

**Must have (table stakes — v1):**
- Three-pane Miller columns layout with hjkl + arrow navigation
- File metadata display (permissions, size, modified date, owner)
- File type colors via YAML/JSON theme system
- Copy / move / delete / rename (single file, confirmation required)
- Multi-select with visual mode
- Create file / create directory inline
- Incremental search/filter in current directory
- Sort by name/size/date/type with asc/desc toggle
- Hidden file toggle (H key)
- Bookmarks with single-key recall
- Shell integration (cd-on-quit wrapper)
- Symlink display with target; broken symlink indication
- Status bar (path, item count, selection count, free space)
- Nerd Fonts icon themes with ASCII fallback (explicit opt-in, not auto-detect)
- User-local keybinding overrides via YAML
- Trash support (freedesktop.org spec via send2trash)
- Text file preview with syntax highlighting in right pane
- PyPI / pipx distribution

**Should have (competitive — v1.x, add after validation):**
- Bulk rename via editor (vimrename pattern) — power user differentiator
- Background task manager with progress for large copy/move operations
- Git status indicators in file listing
- GitHub theme registry with `probefs theme install <name>`

**Defer (v2+):**
- SFTP support — high complexity; architect the FAL now, implement later
- Plugin/scripting engine — shell passthrough covers the v1 use case
- Image preview — terminal-dependent, fragile in SSH/tmux; stub the interface only

**Anti-features to reject outright:**
- Built-in text editor (use $EDITOR integration)
- Built-in terminal emulator (use shell integration + `!` passthrough)
- FTP/SMB/WebDAV in v1
- Dual-pane mode (conflicts with product identity)

### Architecture Approach

The architecture is a clean four-layer design. The presentation layer contains only Textual widgets that hold no business logic — they receive reactive data downward and post Messages upward. The controller layer (`ProbeFSApp`) is a thin coordinator that mounts screens, owns global key bindings (with `priority=True`), and delegates everything else. The domain layer (`FileManagerCore`, `FileOps`, `Previewer`, `TaskQueue`) contains all business logic and is testable without a running Textual app. The FAL wraps fsspec and is the single gateway for all I/O — widgets never call `os`, `pathlib`, or `shutil` directly.

**Major components:**
1. `ProbeFSApp` (Textual App) — thin coordinator; key dispatch; mounts MainScreen; owns global bindings
2. `MainScreen` (Textual Screen) — three-pane layout composition; handles pane Messages; calls core methods
3. `DirectoryList` widget (shared for parent + current panes) — reactive entries, posts EntrySelected Message
4. `PreviewPane` widget — renders file content via Previewer; debounced worker per keypress
5. `FileManagerCore` — navigation state, selection set, clipboard, sort/filter; holds the ProbeFS instance
6. `FileOps` — async copy/move/delete/rename through FAL; dispatches to TaskQueue
7. `TaskQueue` — asyncio.Queue + Textual Worker for background ops with progress reporting
8. `ProbeFS` / FAL (fsspec wrapper) — `ls`, `stat`, `open`, `copy`, `mv`, `rm`, `mkdir`; same API for local and SFTP
9. `ThemeRegistry` — loads YAML themes, constructs `textual.Theme` objects, switches at runtime
10. `KeybindManager` — reads user YAML, calls `App.set_keymap()` on mount with `priority=True`
11. `IconResolver` — strategy pattern: `NerdIconSet` vs `ASCIIIconSet`; selected by config/env var, not detection

**Key patterns:**
- Messages-up / attributes-down: widgets never talk directly to sibling widgets
- All FS calls in `@work(thread=True)`: no blocking I/O on the main asyncio thread, ever
- Theme as data: YAML maps 1:1 to Textual's 11 base colors; `ThemeLoader` validates before `Theme` construction
- Keybinding IDs: all bindable actions have stable string IDs; user YAML references IDs, not keys

### Critical Pitfalls

1. **Synchronous I/O on the main event loop** — Use `@work(thread=True)` for every filesystem call from Phase 1. Retrofitting this after the fact costs as much as a rewrite. Ranger's primary weakness is exactly this; probefs must not inherit it.

2. **Keybinding priority inversion** — Widget-level bindings silently steal app-level bindings. Apply `priority=True` to all app-level and user-override bindings. Test every binding with focus in each of the three panes before considering any keybinding work done.

3. **Destructive file operations without safety gates** — `shutil.rmtree()` with no confirmation and no trash is a single keypress away from catastrophic loss on a server. `send2trash` must be the default delete path. Implement the confirmation modal before wiring any delete keybinding.

4. **YAML theme schema mismatch with Textual's Theme API** — Textual uses 11 named base colors with automatic shade generation. A YAML schema that does not map 1:1 to these names requires a translation layer that silently produces broken contrast. Write `ThemeLoader` with validation before writing any YAML parsing code.

5. **Nerd Font auto-detection is impossible in SSH contexts** — Font rendering happens on the client terminal, not the remote server. No reliable detection API exists. Default to ASCII; make `icons: nerd` an explicit config/env var opt-in. Every tool that has attempted detection has eventually reverted to explicit configuration.

## Implications for Roadmap

Based on the dependency graph in FEATURES.md and the pitfall-to-phase mapping in PITFALLS.md, the following phase structure is recommended:

### Phase 1: Core Scaffold and Async Architecture
**Rationale:** The async worker pattern for FS I/O is the foundational architectural decision that every subsequent phase depends on. Getting this wrong requires a full rewrite. Must be established before any real filesystem code is written.
**Delivers:** `ProbeFSApp` shell, `MainScreen` three-pane layout, `ProbeFS`/FAL on fsspec, `@work(thread=True)` pattern for all I/O, basic directory listing in all three panes, hjkl + arrow navigation
**Addresses:** Three-pane layout (table stakes), keyboard navigation (table stakes)
**Avoids:** Synchronous I/O pitfall (Pitfall 1), Ranger-style sync architecture (Pitfall 6), FAL bypass anti-pattern

### Phase 2: Directory Rendering and Icon System
**Rationale:** File type colors and icon display are foundational to the file listing experience and depend on the theme and icon subsystems. Both must be built before user-facing features are added. The `IconSet` strategy pattern must be locked in here to avoid touching every rendering site later.
**Delivers:** File metadata columns (permissions, size, date, owner), file type coloring, `IconResolver` with `NerdIconSet` and `ASCIIIconSet`, Nerd Fonts explicit opt-in via config/env var, symlink display, hidden file toggle, CJK/emoji filename width handling
**Addresses:** File metadata (table stakes), file type colors (table stakes), Nerd Fonts + ASCII fallback (table stakes and differentiator), symlink awareness (table stakes)
**Avoids:** Nerd Font auto-detection pitfall (Pitfall 2), CJK filename width trap (Performance Traps)

### Phase 3: Theme System
**Rationale:** YAML theming must be built before user-facing config is finalized, and `ThemeLoader` validation must exist before any themes are written. Icon themes are a theming subsystem — icon phase comes first, theme phase second. Theme system is a primary differentiator over ranger and lf.
**Delivers:** `ThemeRegistry`, `ThemeLoader` with validation, YAML schema mapping to Textual's 11 base colors, 2-3 built-in themes (including Dracula), runtime theme switching, TCSS using only design tokens
**Addresses:** YAML/JSON color theme system (differentiator)
**Avoids:** Theme/Textual API mismatch pitfall (Pitfall 3), hardcoded color anti-pattern (Architecture Anti-Pattern 3)

### Phase 4: Keybinding System and Config Infrastructure
**Rationale:** Keybinding architecture must be established before any user-facing bindings are documented, because retrofitting `priority=True` and `KeymapManager` breaks existing keybinding tests. Config loading (platformdirs, ruamel.yaml, Pydantic validation) underpins both the keybinding override system and all future user config.
**Delivers:** `KeybindManager`, `App.set_keymap()` integration, all app-level bindings with stable IDs and `priority=True`, user YAML override support, `config/loader.py` with Pydantic validation, XDG-correct config paths, `?` help overlay
**Addresses:** Configurable keybindings (table stakes), user-local keybinding overrides (differentiator)
**Avoids:** Keybinding priority inversion pitfall (Pitfall 4)

### Phase 5: File Operations and Safety
**Rationale:** File CRUD is table stakes but is the highest-risk phase for data loss. All safety mechanisms (send2trash, confirmation modals, destination conflict detection, symlink cycle protection) must be implemented before any destructive operation is wired to a keybinding. Multi-select must precede bulk operations.
**Delivers:** Copy, move, delete (via send2trash), rename, create file/dir; confirmation modals; multi-select with visual mode; batch operations on selection; incremental search/filter; sort controls; bookmarks; operation log
**Addresses:** Copy/move/delete/rename (table stakes), multi-select (table stakes), create file/dir (table stakes), incremental search (table stakes), sort controls (table stakes), bookmarks (table stakes), trash support (differentiator)
**Avoids:** Destructive operations without safety pitfall (Pitfall 5), symlink cycle security mistake

### Phase 6: Preview Pane and Shell Integration
**Rationale:** Preview is a distinct subsystem (Previewer with strategy pattern) that can be built independently once the three-pane layout and async worker pattern are established. Shell integration (cd-on-quit) is a low-complexity table-stakes feature that belongs here.
**Delivers:** `Previewer` with text/syntax-highlighted preview via Rich, size guard for large files, debounced preview worker, shell integration wrapper (cd-on-quit), status bar with path/count/free space
**Addresses:** Directory-aware preview pane (table stakes), text file preview (table stakes), shell integration (table stakes), status bar (table stakes)
**Avoids:** Full reactive refresh on cursor move (Performance Trap), spawning preview workers per keypress (Performance Trap), large file content in reactive state (Architecture Anti-Pattern 5)

### Phase 7: Distribution and Watchdog
**Rationale:** PyPI/pipx distribution is a core differentiator. Must be proven working on a clean install before v1 launch. Homebrew tap packaging has specific gotchas (virtualenv_install_with_resources, PEP 668) that require a dedicated phase.
**Delivers:** `pyproject.toml` with entry points, `uv build`/`uv publish` pipeline, pipx install verified, Homebrew tap formula, watchdog-based live directory refresh
**Addresses:** PyPI/pipx distribution (differentiator), live directory updates
**Avoids:** Homebrew packaging errors (integration gotcha — virtualenv, PEP 668, pinned resources)

### Phase 8: v1.x Features (Post-Validation)
**Rationale:** These features have high user value but require validation that the core is solid before investing in them. Bulk rename requires multi-select (Phase 5). Task manager with progress requires async worker infrastructure (Phase 1). Git status requires per-directory background workers with caching.
**Delivers:** Bulk rename via $EDITOR, background task manager with progress bars + cancellation, git status indicators in file listing, watchdog-based directory refresh improvements
**Addresses:** Bulk rename (differentiator), task manager (differentiator), git status (differentiator)

### Phase 9: GitHub Theme Registry (Post-Validation)
**Rationale:** Registry only makes sense once enough community themes exist to justify the fetch infrastructure. Defer until adoption data is available.
**Delivers:** `probefs theme install <name>`, registry index fetch, local theme cache, version locking
**Addresses:** GitHub theme registry (differentiator)

### Phase 10: SFTP Transport (v2)
**Rationale:** SFTP is high complexity and high value, but requires the FAL established in Phase 1 to be non-negotiable before any other FS work starts. If FAL discipline is maintained throughout Phases 1-8, adding SFTP is adding `fs/sftp.py` + connection modal — zero changes to widgets or core.
**Delivers:** `SFTPfs` via fsspec, connection modal (host/user/key), remote filesystem tab concept
**Addresses:** SFTP support (v2 feature)
**Avoids:** SFTP blocking transport (integration gotcha), paramiko in event handlers

### Phase Ordering Rationale

- Phase 1 must be first: the async worker pattern is the load-bearing architectural decision; everything else is built on it.
- Phase 2 before Phase 3: icon system is a theming subsystem; the rendering layer must exist before the theme layer manages it.
- Phase 3 before Phase 4: theme config loading uses the same config infrastructure built in Phase 4; the theme schema must be fixed before config loading is finalized.
- Phase 4 before Phase 5: keybinding IDs for all file operations must be registered with correct priority before delete/move are wired to keys.
- Phase 5 before Phase 6: multi-select (Phase 5) enables bulk operations; preview (Phase 6) is independent but depends on the async worker pattern being solid.
- Phase 7 (distribution) runs late in v1 but before launch: Homebrew packaging issues are only discoverable on a clean macOS install with no pip packages.
- Phases 8-10 are post-launch: they require user feedback to validate the correct feature investment.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 7 (Distribution):** Homebrew formula for Python apps with virtualenv is notoriously finicky; the `virtualenv_install_with_resources` + `brew update-python-resources` workflow needs a concrete working example verified against current Homebrew policy.
- **Phase 9 (Theme Registry):** GitHub-based registry design (index format, version locking, trust model) has no established standard; needs design research when the phase is planned.
- **Phase 10 (SFTP):** fsspec's `SFTPFileSystem` uses paramiko, not asyncssh. STACK.md recommends asyncssh for async-native SFTP. This conflict needs resolution at Phase 10 planning time — either use fsspec[sftp] (paramiko, run in thread worker) or switch the FAL to a custom asyncssh implementation. The architecture supports either; the decision is deferred.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Core Scaffold):** Textual async worker pattern is well-documented in official docs; `@work(thread=True)` + `call_from_thread()` is the canonical approach.
- **Phase 2 (Directory Rendering):** Standard Textual widget composition; `rich.cells.cell_len()` for column width is established.
- **Phase 3 (Theme System):** Textual's `Theme` object and `register_theme()` API is fully documented; YAML-to-Theme mapping is straightforward.
- **Phase 4 (Keybinding):** `App.set_keymap()` is the official Textual API; documented and stable.
- **Phase 5 (File Operations):** send2trash, confirmation modals, and `os.scandir()` are all well-established.
- **Phase 6 (Preview):** Rich syntax highlighting via `Syntax.from_path()` is documented; debounce pattern is standard.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All library versions verified via PyPI JSON API on 2026-03-09; alternatives evaluated against official docs |
| Features | HIGH | Cross-verified against 5+ official repos (ranger, yazi, lf, nnn, midnight commander); editorial sources corroborated |
| Architecture | HIGH | Textual patterns verified via official docs; fsspec interface verified via official docs and source; ranger source reviewed |
| Pitfalls | MEDIUM-HIGH | Textual-specific pitfalls verified via official docs and GitHub issues; SFTP and packaging pitfalls MEDIUM from official docs; Nerd Font detection HIGH from official nerd-fonts discussion |

**Overall confidence:** HIGH

### Gaps to Address

- **fsspec vs. asyncssh for SFTP transport:** STACK.md recommends asyncssh (async-native) but ARCHITECTURE.md recommends fsspec (which uses paramiko internally for SFTP). Both approaches are valid — fsspec[sftp] in a thread worker, or asyncssh with a custom FAL implementation. Resolve during Phase 10 planning. The architecture supports either without widget changes.
- **Nerd Font terminal probe feasibility:** STACK.md mentions attempting a glyph render probe as one option; PITFALLS.md conclusively recommends against it. PITFALLS.md wins — explicit opt-in is the correct approach. No gap in the recommendation, but the STACK.md language should not lead implementers toward the probe approach.
- **Theme registry index format:** No established standard for a GitHub-based YAML theme registry index. Needs design work during Phase 9 planning. Low risk to v1 — defer.
- **Terminal width collapse breakpoints:** PITFALLS.md recommends collapsing to two-pane below 100 cols and single-pane below 60 cols. This behavior needs UX validation with real users. Implement the mechanism; tune the breakpoints post-launch.

## Sources

### Primary (HIGH confidence)
- PyPI JSON API (textual, rich, ruamel.yaml, platformdirs, send2trash, watchdog, asyncssh, uv, pytest, pytest-asyncio, pytest-textual-snapshot) — verified versions, 2026-03-09
- Textual official docs (reactivity, widgets, theming, testing, workers, screens, keymaps) — textual.textualize.io
- fsspec official docs and source (usage guide, SFTP implementation) — filesystem-spec.readthedocs.io
- Ranger GitHub source — ranger/ranger repository
- Yazi official features page and repository — yazi-rs.github.io, github.com/sxyazi/yazi
- nnn GitHub repository — github.com/jarun/nnn
- lf GitHub repository — github.com/gokcehan/lf
- Midnight Commander official site — midnight-commander.org
- Nerd Fonts discussion #829 (detection impossibility) — github.com/ryanoasis/nerd-fonts/discussions/829
- Python bug tracker #15100, #30400 (shutil race conditions)
- Textual GitHub Issue #4637 (DataTable binding priority conflict)

### Secondary (MEDIUM confidence)
- Textual widget system architecture — deepwiki.com/Textualize/textual
- Yazi architecture analysis — deepwiki.com/sxyazi/yazi
- Textual keymaps blog post — darren.codes/posts/textual-keymaps/
- Python packaging 2026 state — learn.repoforge.io
- Homebrew Python for Formula Authors — docs.brew.sh
- Textual algorithms for high-performance TUIs — textual.textualize.io/blog (Dec 2024)
- ruamel.yaml vs. PyYAML analysis — medium.com (corroborated by PyPI changelogs)
- itsfoss, tecmint, x-cmd, dev.to editorial TUI file manager surveys (cross-verified against official repos)

### Tertiary (LOW confidence)
- termscp repository — evaluated for SFTP scope complexity reference only

---
*Research completed: 2026-03-09*
*Ready for roadmap: yes*
