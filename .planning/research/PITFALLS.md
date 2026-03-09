# Pitfalls Research

**Domain:** Python TUI file manager (probefs — Textual, three-pane, SSH/server context)
**Researched:** 2026-03-09
**Confidence:** MEDIUM-HIGH (Textual-specific claims verified via official docs and GitHub issues; SFTP/packaging claims MEDIUM from official docs; Nerd Font detection HIGH from official nerd-fonts discussion)

---

## Critical Pitfalls

### Pitfall 1: Blocking the UI Event Loop with Synchronous File I/O

**What goes wrong:**
Any synchronous filesystem call — `os.scandir()`, `stat()`, `shutil.copy()` — made directly in a message handler or `on_mount` freezes the entire Textual event loop. Because coroutines can only yield at `await` points, a blocking call with no await causes the UI to hang visibly, making the app feel broken. This is especially acute when navigating to network mounts, slow NFS volumes, or large directories where stat calls are expensive.

**Why it happens:**
Developers prototype with direct function calls in event handlers (`on_key`, `on_mount`, `compose`) and it works fine on fast local SSDs. The issue only surfaces on slow storage or when the operation touches many files, at which point it's already woven deep into the architecture.

**How to avoid:**
Use Textual's `@work(thread=True)` decorator to push all filesystem calls into a thread worker. Never call `os.scandir()`, `pathlib.iterdir()`, `stat()`, `shutil.*`, or any blocking file I/O directly on the main async thread. Use `app.call_from_thread()` to post UI updates back to the main thread from worker functions. Treat the main event loop as I/O-free.

**Warning signs:**
- UI "freezes" for a fraction of a second when entering a directory
- Arrow key input queues up while a directory loads
- Any function in a message handler that does not contain an `await`
- `@work` decorator not visible anywhere near directory listing code

**Phase to address:**
Core scaffold phase (Phase 1). Establish the worker pattern before any real filesystem code is written. Retrofitting async discipline into synchronous code is a costly rewrite.

---

### Pitfall 2: Nerd Font Detection is Impossible — Attempting It Anyway

**What goes wrong:**
Developers attempt to automatically detect whether a Nerd Font is installed by rendering a glyph and checking the result, querying environment variables, or probing the terminal. None of these approaches work reliably. Terminals don't expose rendered output back to applications, and there is no standard ANSI escape sequence to query font capabilities. The result is a detection algorithm that produces false positives (shows broken box-character glyphs to users who don't have Nerd Fonts) or false negatives (shows ASCII fallback to users who do have Nerd Fonts).

**Why it happens:**
The SSH/server context makes this worse: the font is rendered by the local terminal emulator on the client machine, but the app runs on the remote server. Environment variables set client-side don't propagate over SSH by default. A user on WezTerm (which bundles Nerd Font fallback automatically) looks identical at the protocol level to a user on a minimal terminal with no icon fonts.

**How to avoid:**
Do not attempt automatic detection. Follow the consensus approach from the nerd-fonts maintainers: expose an explicit opt-in. Use a config file flag (`icons: nerd` vs `icons: ascii`), an environment variable (`PROBEFS_ICONS=nerd`), and a CLI flag (`--icons nerd`). Default to ASCII. Let users who have configured Nerd Fonts set the flag once in their config. This is how successful tools (lf, yazi, starship) handle it.

**Warning signs:**
- Any code path that tries to render a test glyph and checks if it's a replacement character
- Environment variable checks for `TERM`, `TERM_PROGRAM`, or font names as proxies for Nerd Font support
- SSH_TTY or SSH_CONNECTION checks as a proxy for "might not have fonts"

**Phase to address:**
Icon system phase. Design the icon resolver as a strategy pattern from the start: `IconSet` protocol with `NerdIconSet` and `ASCIIIconSet` implementations. The selection logic is trivial; the design boundary is what matters.

---

### Pitfall 3: Theming System Impedance Mismatch — YAML/JSON vs. Textual's Python Theme Objects

**What goes wrong:**
Textual's theming system works with Python `Theme` objects defined in code. There is no built-in mechanism to load themes from YAML or JSON files. Developers who design a YAML-first theming system discover mid-development that Textual's CSS variable generation system (which produces `-lighten-1` through `-darken-3` shades from 11 base colors) is opaque — overriding base colors without understanding shade generation produces color combinations that break contrast and legibility. The `$foreground` legibility guarantee (must be readable against `$background`, `$surface`, and `$panel`) is an implicit contract that custom themes can silently violate.

**Why it happens:**
The theming system looks simple from the outside (11 named colors). The full complexity — automatic shade generation, CSS variable scope, the `variables` dict for fine-grained overrides — is documented in parts across multiple pages. YAML theme schemas designed without mapping to this system end up requiring a translation layer that handles edge cases like missing required colors, invalid contrast pairs, and CSS variable names that differ from the YAML key names.

**How to avoid:**
Design the YAML theme schema to map 1:1 onto Textual's 11 base colors plus the `variables` dict. Write a `ThemeLoader` class that validates input and constructs a `Theme` object — this is the only boundary between user config and Textual internals. Validate contrast ratios at load time with a warning, not silently. Ship one built-in theme that serves as the canonical schema example. Use `layout: false` on reactive variables that drive only color to avoid triggering unnecessary layout passes on theme change.

**Warning signs:**
- YAML schema with arbitrary color keys that don't map to Textual's 11 base color names
- No validation layer between config file parsing and `Theme` construction
- Color pairs in themes that have never been tested for accessibility contrast

**Phase to address:**
Theming phase. Before writing any YAML parsing code, implement a `ThemeLoader` that accepts a dict and produces a valid `Theme` object. Test the loader independently of the file parsing.

---

### Pitfall 4: Keybinding Priority Inversion — Widget Defaults Override App Bindings

**What goes wrong:**
Textual resolves key bindings by walking the DOM from the focused widget up to the app. If a built-in widget (e.g., `ListView`, `DataTable`, `Input`) defines a default binding for a key that the app also handles, the widget's binding wins unless explicitly configured otherwise. This means adding a new widget to the layout can silently "steal" a keybinding that was working everywhere else. With user-overridable keybindings, this becomes harder: a user's custom binding on `j`/`k` for navigation can be eaten by a focused input widget's character handling.

**Why it happens:**
The priority system exists (`priority=True` on `Binding`) but is not applied by default. Textual 0.67.0 introduced this bug explicitly for `DataTable` (fixed in 0.67.1), showing that even the framework maintainers hit this edge case during development. File managers with many panels have many competing keybinding scopes.

**How to avoid:**
Use `priority=True` on all app-level bindings that must work regardless of focus. For user-configurable bindings, implement a `KeymapManager` that applies overrides at the App level with `priority=True` so they cannot be shadowed by widgets. Test every default keybinding with focus in each pane (left panel, center panel, right panel, command input). Document which bindings are focus-dependent vs. global.

**Warning signs:**
- A keybinding works in one pane but not another
- Adding a new widget breaks a previously working shortcut
- User reports that custom bindings "only sometimes work"
- No automated keybinding tests across focus states

**Phase to address:**
Keybinding system phase (before user-configurable overrides are added). The binding priority architecture must be established before the first user-facing keybinding is documented.

---

### Pitfall 5: Destructive File Operations Without Atomicity or Trash Semantics

**What goes wrong:**
`shutil.copy()`, `shutil.move()`, and `os.remove()` are not atomic. `shutil.copy()` silently overwrites the destination if it already exists. `os.remove()` on a directory fails with `IsADirectoryError`; `shutil.rmtree()` on a directory succeeds with no confirmation and no recovery path. A file manager that exposes these operations directly to keyboard shortcuts (e.g., `d` for delete) can result in irreversible data loss from a single accidental keypress.

**Why it happens:**
Python's stdlib presents these operations as simple function calls, obscuring their destructive semantics. The race condition window (check-then-act) exists in all the shutil operations — if a file is created at the destination between the existence check and the copy, it will be overwritten silently (documented in Python bug tracker issues 15100 and 30400).

**How to avoid:**
Never invoke `shutil.rmtree()` or `os.remove()` without: (1) a confirmation dialog for single files, (2) a multi-step confirmation (type filename or count) for recursive directory deletion. Use `send2trash` library to move to OS trash instead of permanent deletion as the default operation. For move/copy operations, check for destination conflicts before the operation, not inside it. Implement an operation log that records completed destructive operations so at minimum the user can reconstruct what happened even if undo is not implemented.

**Warning signs:**
- Delete bound to a single key with no confirmation widget
- Any `shutil.rmtree()` call without an explicit user-confirmation gate
- No `send2trash` dependency in the project
- File operation tests that don't test the "destination already exists" case

**Phase to address:**
File operations phase. The confirmation dialog and trash integration must be implemented before delete/move operations are exposed to any keybinding.

---

### Pitfall 6: Ranger-Style Sync I/O Causing Sluggish Feel at Scale

**What goes wrong:**
Ranger (Python, synchronous) is the reference implementation for three-pane file managers, but its synchronous I/O model is widely cited as its primary weakness. Projects that model their architecture on Ranger inherit the problem: listing a directory blocks the preview pane from rendering, stat-on-hover for file metadata freezes navigation, and watching a directory for changes ties up the main thread. On servers with slow storage or many inodes (e.g., `/usr/lib` with 5,000+ files), this creates a noticeable lag on every pane navigation.

**Why it happens:**
The three-pane layout requires coordinating three concurrent data sources (parent dir, current dir, preview). If any of these is synchronous, the entire display stutters. Yazi (Rust, async) is fast specifically because all three panes load concurrently via async I/O — this is the architecture probefs must replicate in Python/Textual.

**How to avoid:**
Each pane's directory listing must be an independent `@work(thread=True)` task. Cancel and restart the worker when the user navigates before it completes (don't let stale data arrive after navigation). Use `os.scandir()` (not `os.listdir()`) and yield entries lazily — never load all entries into memory before displaying the first one. For the preview pane, implement a debounce (100-200ms) so rapid arrow-key navigation doesn't spawn a new preview worker per keypress.

**Warning signs:**
- Directory listing populates as a single batch (all-or-nothing display)
- Any blocking call in a `watch_` method that tracks cursor position
- Preview pane that loads synchronously in the same handler as navigation
- No debounce on preview worker spawning

**Phase to address:**
Core layout/navigation phase. The async worker architecture for pane loading is the foundational decision that everything else depends on.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Synchronous directory listing in MVP | Simpler code, faster to ship | Entire navigation system must be rewritten for SSH/slow storage support | Never — use `@work(thread=True)` from day one |
| Hardcoded keybindings without a `KeymapManager` | No abstraction layer needed early | User-configurable keybindings require full refactor of binding registration | MVP only if user config is post-MVP |
| No YAML theme validation (accept raw dicts) | Faster to ship theming | Silent contrast failures, crashes on malformed themes | Never — write the validator before the first theme |
| `shutil.rmtree()` without confirmation | Simpler delete implementation | Irreversible data loss for users | Never |
| Icon rendering inline without a strategy pattern | Fewer files | Nerd Font / ASCII switch requires touching every rendering site | Never — introduce `IconSet` protocol at first icon render |
| Storing all directory entries in a `list` | Simplest data structure | Memory usage grows with directory size; 100K-file dirs cause sluggishness | Acceptable if entries are loaded lazily via `os.scandir()` |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| SFTP (future) | Using paramiko's synchronous `SFTPClient` directly in event handlers | Use `asyncssh` or run paramiko in a thread worker; never block main thread on network I/O |
| SFTP (future) | Treating remote paths as `pathlib.Path` objects | Implement a `FilesystemBackend` protocol with separate local and SFTP implementations; use string paths or a custom path type for remote |
| Homebrew packaging | Letting pip resolve dependencies at install time | Declare every transitive dependency explicitly as a `resource` block; use `brew update-python-resources` to generate stanzas |
| Homebrew packaging | Not installing into `libexec` virtualenv | Must use `virtualenv_install_with_resources` helper and `Language::Python::Virtualenv`; Python 3.12+ enforces PEP 668 |
| PyPI/pipx | Not defining `console_scripts` entry points | Add `[project.scripts]` in `pyproject.toml`; pipx installs only work with proper entry points |
| Textual theming | Bypassing `Theme` class and injecting raw CSS variables | Always construct `Theme` objects; raw variable injection bypasses shade generation and breaks dark/light mode switching |
| OS trash | Using `os.remove()` as the default delete | Depend on `send2trash` for cross-platform trash support; `os.remove()` should be a secondary "permanent delete" with stronger confirmation |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `os.listdir()` on large directories (loads all to memory) | High memory, slow initial paint for dirs with 10K+ files | Use `os.scandir()` with lazy iteration; yield entries in batches | Dirs with >5,000 files |
| Full reactive refresh on cursor move | Arrow key navigation causes visible lag (>50ms per keypress) | Use `var` (not `reactive`) for cursor position; update only the two rows that change (previous and new selection) | Any directory with >200 entries rendered |
| Spawning a new preview worker per keypress | Preview pane flickers on fast navigation; high CPU from worker churn | Debounce preview requests by 150ms; cancel in-flight workers before spawning replacement | When navigation speed exceeds ~5 keys/sec |
| `watch_` method calling `refresh(layout=True)` | Layout recalculation on every data change; frame drops | Use `refresh(layout=False)` for content-only updates; reserve `layout=True` for structural changes | Any `watch_` method that fires more than 2x/sec |
| `recompose()` inside reactive watchers | Full widget tree teardown/rebuild on state change | Reserve `recompose()` for structural changes; use `refresh()` for visual updates | Any watcher tied to navigation events |
| CJK or emoji in filenames without width accounting | Misaligned columns, truncation at wrong position | Use `rich.cells.cell_len()` for display width calculation; never use `len(str)` for terminal layout math | Any directory containing CJK filenames |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Following symlinks during recursive delete without cycle detection | Infinite loop or deletion of files outside intended tree | Use `os.scandir()` with `entry.is_symlink()` check; never follow symlinks during `rmtree`-style operations; use `os.lstat()` not `os.stat()` |
| Executing file content as shell commands from the preview pane | Arbitrary code execution if a malicious file tricks the user | Preview should be read-only display only; never `eval`, `exec`, or `subprocess` based on file content |
| SFTP credentials stored in config files without restriction | Credential leak if config is world-readable | Warn if config file permissions allow group/world read; recommend `chmod 600`; never store passwords in config (use SSH key auth) |
| `os.makedirs()` with default permissions on shared servers | Directories created group/world-readable in multi-user environments | Use explicit `mode=0o700` for any directories created by probefs (config dir, cache dir) |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| ASCII fallback renders as garbled Unicode boxes | Looks broken on SSH sessions without Nerd Fonts; erodes trust | Default to ASCII; make `icons: nerd` an explicit opt-in in config |
| Delete key bound to permanent deletion (no trash) | Irreversible loss from accidental keypress; server admins have no `undo` | Default delete sends to OS trash; expose "permanent delete" as a secondary binding with confirmation dialog |
| Three-pane layout not adapting to narrow terminals (<80 cols) | Panes overlap or truncate unusably on narrow SSH windows | Detect terminal width on startup and on resize; collapse to two-pane below 100 cols, single-pane below 60 cols |
| Theme change requires app restart | Users can't preview theme changes; friction in customization workflow | Apply theme changes via `app.theme = new_theme` reactively; Textual supports live theme switching without restart |
| Blocking progress feedback during large file copies | User cannot tell if the operation is running or hung | Show progress bar with bytes/total and estimated time; update via worker messages at least every 200ms |
| Keybinding help buried in docs | SSH admins don't read docs; can't discover keybindings in-app | Implement `?` help overlay showing all active bindings for current focus context |

---

## "Looks Done But Isn't" Checklist

- [ ] **Directory listing:** Fast on local SSD — verify it doesn't block on a network mount or directory with 50,000+ files; worker cancellation works on rapid navigation
- [ ] **Nerd Font icons:** Looks correct in developer's terminal — verify on a fresh SSH session with no Nerd Fonts installed; confirm ASCII fallback is the default
- [ ] **Delete operation:** Works in testing — verify it uses `send2trash`, not `os.remove()`; confirm confirmation dialog cannot be dismissed accidentally
- [ ] **File copy/move:** Completes in testing — verify it handles destination-already-exists case; check cross-filesystem moves (temp dir copy+delete, not atomic rename)
- [ ] **Keybindings:** Work in focused pane — verify they work with focus in each of the three panes; verify user overrides apply globally with `priority=True`
- [ ] **YAML theme load:** Loads sample theme — verify validation catches missing required colors; verify contrast failure produces warning not crash
- [ ] **Homebrew formula:** Installs on dev machine — verify on clean macOS with no pip packages; all resources pinned to exact versions
- [ ] **Symlink handling:** Renders symlinks correctly — verify broken symlinks don't crash the listing; verify recursive operations don't follow symlinks into cycles
- [ ] **Terminal resize:** Looks fine at 120 cols — verify behavior at 80 cols and 60 cols; three-pane layout must gracefully degrade

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Synchronous I/O woven into navigation handlers | HIGH | Introduce `FilesystemBackend` interface; replace direct calls one handler at a time; requires regression testing each pane independently |
| Hardcoded keybindings without priority architecture | MEDIUM | Introduce `KeymapManager` as a layer; migrate existing bindings to use it; user config system can be added on top |
| YAML theme schema mismatch with Textual Theme API | MEDIUM | Write schema migration validator; map old keys to new; warn users on first load with incompatible themes |
| No `send2trash` integration (direct `os.remove`) | LOW | Replace delete handler with `send2trash` call; add dependency to `pyproject.toml`; single-site change if delete is centralized |
| Nerd Font auto-detection attempted and failed | LOW | Remove detection code; add config flag and env var; update docs; users were already confused |
| Blocking preview pane freezing navigation | HIGH | Decouple preview into independent worker; add debounce; requires architectural separation of pane state |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Blocking UI event loop with sync I/O | Phase 1 — Core scaffold | No message handler contains a blocking call; `@work(thread=True)` used for all filesystem operations |
| Nerd Font detection attempted | Phase 2 — Icon system | `IconSet` protocol exists; selection via config/env var only; no detection heuristic in codebase |
| YAML theme/Textual API mismatch | Phase 3 — Theming | `ThemeLoader` unit tests cover all 11 base colors; invalid themes produce validation errors |
| Keybinding priority inversion | Phase 4 — Keybinding system | Keybinding integration tests with focus in each pane; user overrides apply globally |
| Destructive operations without safety | Phase 5 — File operations | `send2trash` integration test; delete requires confirmation dialog; `shutil.rmtree()` not called anywhere without gate |
| Ranger-style sync architecture | Phase 1 — Core scaffold | Three-pane loading is concurrent; navigating quickly does not produce stale data in panes |
| CJK/emoji filename width errors | Phase 2 — Directory rendering | Test fixture with CJK filenames; column alignment verified |
| Homebrew packaging errors | Phase 7 — Distribution | Clean macOS install test with `brew install`; no system pip dependencies |
| SFTP blocking transport | Phase 8 — SFTP transport | All SFTP calls in thread workers; local and SFTP panes share `FilesystemBackend` interface |
| Symlink cycles in recursive operations | Phase 5 — File operations | Test fixture with circular symlinks; recursive operations do not follow symlinks |

---

## Sources

- Textual official blog — "7 Things I've Learned Building a Modern TUI Framework": https://www.textualize.io/blog/7-things-ive-learned-building-a-modern-tui-framework/
- Textual official blog — "Algorithms for High Performance Terminal Apps" (December 2024): https://textual.textualize.io/blog/2024/12/12/algorithms-for-high-performance-terminal-apps/
- Textual GitHub Issue #4637 — DataTable binding priority conflict: https://github.com/Textualize/textual/issues/4637
- Textual Workers documentation: https://textual.textualize.io/guide/workers/
- Textual Themes/Design documentation: https://textual.textualize.io/guide/design/
- Textual Reactivity documentation: https://textual.textualize.io/guide/reactivity/
- Nerd Fonts discussion #829 — How to detect if Nerd Font is installed: https://github.com/ryanoasis/nerd-fonts/discussions/829
- Python bug tracker #15100 — Race conditions in shutil.copy: https://bugs.python.org/issue15100
- Python bug tracker #30400 — Race condition in shutil.copyfile(): https://bugs.python.org/issue30400
- Homebrew — Python for Formula Authors: https://docs.brew.sh/Python-for-Formula-Authors
- Yazi architecture analysis — async I/O vs Ranger sync: https://www.x-cmd.com/install/25-ls/
- Textual Discussion #4509 — Modular widget styling and themes: https://github.com/Textualize/textual/discussions/4509
- Python packaging entry points spec: https://packaging.python.org/en/latest/specifications/entry-points/

---
*Pitfalls research for: Python TUI file manager (probefs)*
*Researched: 2026-03-09*
