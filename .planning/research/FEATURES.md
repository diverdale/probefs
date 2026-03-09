# Feature Research

**Domain:** TUI file manager (Python/Textual, ranger-style, server admin focus)
**Researched:** 2026-03-09
**Confidence:** HIGH (features cross-verified across 5+ official repos and multiple ecosystem surveys)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete. Established by surveying ranger, yazi, lf, nnn, midnight commander, and superfile.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Three-pane Miller columns layout | Ranger defined this as the canonical TUI layout; users switching from ranger expect it | MEDIUM | Parent / current / preview — probefs already scoped to this |
| Keyboard-driven navigation (hjkl + arrows) | Every competitor does this; vim-users expect hjkl, non-vim users expect arrows | LOW | Both bindings must work simultaneously |
| File list with permissions, size, date | Users need metadata at a glance without opening a separate tool | LOW | `ls -lh`-equivalent column display |
| File type colors | LS_COLORS / extension-based coloring is assumed; monochrome feels broken | LOW | Must integrate with the YAML/JSON theme system |
| Directory-aware preview pane | Right pane shows file content or dir listing; critical for 3-pane UX | MEDIUM | Text preview is minimum; image preview is advanced |
| Copy / move / delete / rename | Core CRUD — any missing operation breaks the tool for daily use | MEDIUM | Needs progress indication for large operations |
| Multi-select (visual mode) | Users select ranges to batch-operate; absent = painful one-at-a-time work | MEDIUM | Visual mode selection + space-toggle per item |
| Create file / create directory | Must be inline (not shell fallback) to feel like a file manager | LOW | Single keybind prompt |
| Incremental search / filter | Type to filter current directory in real time; nnn/yazi/lf all do this | LOW | Not full fuzzy-find — just instant prefix/substring filter |
| Sort controls | Sort by name, size, modified date, type; toggle asc/desc | LOW | Must persist per directory or globally |
| Bookmarks / jump list | Sysadmins have deep paths they return to constantly; repeated navigation is painful | LOW | Store named shortcuts; single-key recall |
| Shell integration (cd on quit) | After quitting, your shell should be in the directory you left probefs at | LOW | Shell wrapper function (standard pattern across all managers) |
| Symlink awareness | Show symlink targets; indicate broken symlinks visually | LOW | Critical for server environments with complex symlink trees |
| Hidden file toggle | Show/hide dotfiles with a keypress | LOW | `H` is the conventional key |
| Status bar with current path + selection count | Always visible context; users get disoriented without it | LOW | Bottom bar: path, item count, selected count, free space |
| Configurable keybindings | Users have muscle memory from other tools; must be able to remap | MEDIUM | probefs already scoped as user-local override YAML |
| ASCII fallback for environments without Nerd Fonts | SSH to servers rarely has Nerd Fonts installed; broken boxes destroy UX | LOW | Auto-detect font capability and fall back gracefully |

---

### Differentiators (Competitive Advantage)

Features that set probefs apart from ranger (aging Python), lf (config-heavy, no built-ins), and nnn (extreme minimalism).

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| YAML/JSON color theme system with GitHub registry | Ranger theming is opaque config files; yazi theming requires Lua knowledge. A discoverable registry lowers the "make it pretty" barrier dramatically for sysadmins | MEDIUM | Registry fetch + local cache; version locking matters |
| Nerd Fonts icon themes with auto-detect fallback | Only yazi does this well built-in; most tools require manual config. Auto-detect removes a known friction point for new users | MEDIUM | Detect by writing a glyph and checking terminal response; store result |
| Per-user keybinding overrides without patching source | lf and ranger both require editing config files with shell knowledge; probefs's YAML override is more approachable | LOW | Already scoped; the differentiator is the UX of the override format |
| First-class pipx / PyPI distribution | Most Rust/Go TUI managers require a build toolchain or distro package. `pipx install probefs` is instantly accessible to Python ecosystem users | LOW | Standard Python packaging; the value is the distribution channel |
| Trash support (safe delete) | Permanent delete by default is dangerous on servers. Most managers (lf, nnn) don't implement trash — they just `rm`. Trash-by-default is a meaningful safety feature for sysadmins | MEDIUM | Use freedesktop.org Trash spec; require explicit override to permanent-delete |
| Task manager with background operation progress | Yazi has this; ranger does not. Large file copy/move should show progress and be cancellable without blocking navigation | HIGH | Requires async operation handling; Textual's worker API is suited for this |
| Git status in file listing | Broot and yazi both do this; ranger does not. Developers and sysadmins in repos want diff/modified/untracked indicators inline | MEDIUM | Shell out to `git status --porcelain` per directory; cache aggressively |
| Bulk rename via editor (vimrename pattern) | Open selected filenames in $EDITOR, save to rename — ranger and yazi do this; it is beloved by power users and practically unknown outside TUI managers | MEDIUM | Write names to tempfile, open editor, apply diff on save |
| SFTP support (future milestone, but architect for it now) | Sysadmins frequently need to manage remote filesystems without mounting; building a filesystem abstraction layer early avoids a rewrite | HIGH | Defer to future milestone; but VFS layer must be abstracted from local filesystem calls from day one |

---

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Built-in text editor | Users want to edit config files without leaving the file manager | Editors are complex; maintaining even a basic editor diverts focus from navigation. mc does this and it is mc's most-complained-about component. `$EDITOR` integration is enough. | Open file in `$EDITOR` (already standard practice); do not embed an editor |
| Built-in terminal emulator / shell pane | Users want a split terminal alongside the file tree | Terminal emulation inside a TUI adds enormous complexity and fragile escape sequence handling. Textual does not expose a proper VTE widget. | Shell integration (cd-on-quit) + `!` to drop to shell; that covers 95% of the use case |
| FTP/SMB/WebDAV in v1 | Sysadmins want remote protocol support | Scope-kills v1. Each protocol is a significant implementation. Starting with SFTP (planned future milestone) is already ambitious. | Scope SFTP as a future milestone; do not touch FTP, SMB, WebDAV |
| Dual-pane mode | Power users from mc/Total Commander background request this | Conflicts with probefs's core identity as a ranger-style three-pane tool. Implementing dual-pane means maintaining two layout modes. Context switching across two panes is also cognitively heavier for the sysadmin use case. | Three-pane is the product; multi-tab (multiple panes stacked as tabs) is sufficient for the dual-pane workflow |
| Mouse-as-primary-interaction | GUI converts want clickable UI | TUI file managers are keyboard-first tools. Investing engineering time optimizing mouse is misaligned with the sysadmin audience, who work over SSH. | Mouse support for scroll and click-to-select is fine as a convenience; never required |
| Image preview | Users of yazi/ranger love inline image rendering | Image protocols (kitty, iTerm2, sixel, ueberzug++) are highly terminal-dependent and often break in SSH/tmux contexts. Chasing image preview in v1 is a reliability trap. | Text preview is sufficient for v1; stub an image preview interface that can be enabled optionally in v1.x |
| Plugin/scripting engine | Power users want extensibility | Building a Lua/Python scripting engine is a product in itself. Yazi spent significant effort on this. For v1, shell command integration (`!command` passthrough) covers most plugin use cases. | Shell passthrough for custom commands; revisit scripting engine in v2 if demand is there |

---

## Feature Dependencies

```
[File listing with colors]
    └──requires──> [Theme system (YAML/JSON)]

[Icon display]
    └──requires──> [Nerd Fonts auto-detect]
                       └──requires──> [ASCII fallback system]

[Multi-select]
    └──requires──> [Visual mode selection]
                       └──enables──> [Bulk rename via editor]
                       └──enables──> [Batch copy/move/delete]

[Batch copy/move/delete]
    └──enhances──> [Task manager with progress]

[Trash support]
    └──requires──> [Delete operation]
    └──conflicts──> [Permanent delete as default]

[Bulk rename via editor]
    └──requires──> [Multi-select]
    └──requires──> [$EDITOR integration]

[Bookmarks]
    └──enhances──> [Shell integration (cd on quit)]

[SFTP support (future)]
    └──requires──> [VFS abstraction layer]
                       └──must exist at v1 architecture level even if not exposed

[Theme registry (GitHub-based)]
    └──requires──> [Local theme application (YAML/JSON)]
    └──requires──> [Network fetch + caching]

[Git status in listing]
    └──requires──> [Per-directory metadata fetching]
    └──requires──> [Background worker / caching (avoid blocking navigation)]
```

### Dependency Notes

- **VFS abstraction requires early design attention:** If local filesystem calls are not abstracted from day one, adding SFTP later requires rewriting every file operation. This is the highest-priority architectural concern.
- **Theme system must precede icon themes:** Icon themes are a theming subsystem; the base YAML/JSON theme engine should be built first.
- **Task manager enables safe large operations:** Without background progress, users have no way to cancel or monitor a large recursive copy. This makes the tool feel fragile for server workloads.
- **Multi-select is a prerequisite for bulk rename and batch ops:** Both features depend on the same selection model; build selection first, bulk operations second.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what sysadmins need to validate probefs as a daily driver.

- [ ] Three-pane Miller columns layout — core product identity
- [ ] hjkl + arrow keyboard navigation with preview pane
- [ ] File metadata display (permissions, size, modified date, owner)
- [ ] File type colors via theme system (YAML/JSON)
- [ ] Copy / move / delete / rename (single file)
- [ ] Multi-select with visual mode
- [ ] Create file / create directory
- [ ] Incremental search/filter in current directory
- [ ] Sort by name/size/date/type
- [ ] Hidden file toggle
- [ ] Bookmarks (named shortcuts, single-key recall)
- [ ] Shell integration (cd on quit wrapper)
- [ ] Symlink display with target
- [ ] Status bar (path, count, free space)
- [ ] Nerd Fonts icon themes with ASCII fallback auto-detect
- [ ] User-local keybinding overrides (YAML)
- [ ] Trash support (safe delete, freedesktop spec)
- [ ] Text file preview in right pane
- [ ] PyPI / pipx distribution

### Add After Validation (v1.x)

Features to add once core is working and user feedback is gathered.

- [ ] Bulk rename via editor — trigger when adoption shows power users are primary audience
- [ ] Task manager with background copy/move progress — trigger when users report pain with large file operations
- [ ] Git status indicators — trigger when developer/sysadmin ratio becomes clear
- [ ] GitHub theme registry — trigger when enough themes exist to justify the registry

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] SFTP support — high complexity; needs VFS abstraction layer from v1 architecture
- [ ] Scripting / plugin engine — only if shell passthrough proves insufficient
- [ ] Image preview (optional) — highly terminal-dependent; off by default even if implemented

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Three-pane layout + navigation | HIGH | MEDIUM | P1 |
| File operations (CRUD) | HIGH | MEDIUM | P1 |
| File type colors + theme system | HIGH | LOW | P1 |
| Multi-select | HIGH | MEDIUM | P1 |
| Trash / safe delete | HIGH | MEDIUM | P1 |
| Nerd Fonts + ASCII fallback | HIGH | LOW | P1 |
| Keybinding overrides | HIGH | LOW | P1 |
| Shell cd-on-quit integration | HIGH | LOW | P1 |
| Bookmarks | MEDIUM | LOW | P1 |
| Text file preview | MEDIUM | LOW | P1 |
| Sort controls | MEDIUM | LOW | P1 |
| Hidden file toggle | MEDIUM | LOW | P1 |
| Status bar | MEDIUM | LOW | P1 |
| Incremental search/filter | MEDIUM | LOW | P1 |
| Bulk rename via editor | HIGH | MEDIUM | P2 |
| Background task manager | HIGH | HIGH | P2 |
| Git status indicators | MEDIUM | MEDIUM | P2 |
| GitHub theme registry | MEDIUM | MEDIUM | P2 |
| SFTP support | HIGH | HIGH | P3 |
| Plugin/scripting engine | LOW | HIGH | P3 |
| Image preview | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | ranger | yazi | lf | nnn | probefs plan |
|---------|--------|------|----|-----|--------------|
| Three-pane layout | Yes | Yes | Yes | No | Yes (core identity) |
| Built-in keybinding config | rc.conf | keymap.toml | lfrc | env vars | YAML user-local overrides |
| Icon themes | Plugin | Built-in | Config | Plugin | Built-in, auto-detect |
| Color themes | Config file | flavor TOML | Config | Color env vars | YAML/JSON + GitHub registry |
| Image preview | External | Built-in (Lua) | External | Plugin | Deferred to v1.x (optional) |
| Text preview | Yes | Yes | Yes | External | Yes (v1) |
| Multi-select | Yes | Yes | Yes | Yes | Yes (v1) |
| Bulk rename via editor | Yes | Yes | Via shell | Via plugin | Yes (v1.x) |
| Background task manager | No | Yes | No | No | Yes (v1.x) |
| Trash support | No (rm) | Yes | No (rm) | Plugin | Yes (v1, safety default) |
| Git status | No | Plugin | No | No | Yes (v1.x) |
| SFTP/remote | No | No | No | SSHFS via plugin | Future milestone |
| Plugin/scripting | Python | Lua | Shell | Shell scripts | Shell passthrough (defer engine) |
| Distribution | pip | cargo/brew | brew | brew/pkg | pipx/PyPI/Homebrew |
| Language | Python | Rust | Go | C | Python + Textual |

---

## Sources

- [Yazi official features page](https://yazi-rs.github.io/features/) — HIGH confidence (official)
- [Yazi GitHub repository](https://github.com/sxyazi/yazi) — HIGH confidence (official)
- [ranger GitHub repository](https://github.com/ranger/ranger) — HIGH confidence (official)
- [nnn GitHub repository](https://github.com/jarun/nnn) — HIGH confidence (official)
- [lf GitHub repository](https://github.com/gokcehan/lf) — HIGH confidence (official)
- [Midnight Commander official site](https://midnight-commander.org/) — HIGH confidence (official)
- [14 Best Command-Line File Managers for Linux in 2026 — itsfoss](https://itsfoss.gitlab.io/post/14-best-command-line-file-managers-for-linux-in-2026/) — MEDIUM confidence (editorial)
- [Comprehensive Guide to File Managers: superfile, Yazi — x-cmd](https://www.x-cmd.com/install/25-ls/) — MEDIUM confidence (editorial, cross-verified against official docs)
- [Terminal file managers — DEV Community](https://dev.to/ccoveille/terminal-file-managers-1b5l) — MEDIUM confidence (community, cross-verified)
- [nnn, ranger, lf, joshuto, yazi comparison discussion — GitHub joshuto](https://github.com/kamiyaa/joshuto/discussions/454) — MEDIUM confidence (user community, unverified individual claims)
- [14 Must-Have Linux Terminal File Managers in 2026 — tecmint](https://www.tecmint.com/linux-terminal-file-managers/) — MEDIUM confidence (editorial)
- [termscp SFTP TUI — GitHub](https://github.com/veeso/termscp) — HIGH confidence (reference for SFTP scope complexity)

---
*Feature research for: TUI file manager (probefs)*
*Researched: 2026-03-09*
