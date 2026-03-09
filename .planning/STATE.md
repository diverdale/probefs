# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-09)

**Core value:** A fast, beautiful, keyboard-driven file browser that feels at home in any terminal — local or remote — with a theming ecosystem that makes it yours.
**Current focus:** Phase 4 (Phase 3 complete)

## Current Position

Phase: 4 of 7 — COMPLETE
Plan: 2 of 2 in current phase
Status: Phase 4 complete — keybinding override system runtime-verified (replace semantics, additive mapping, zero-config defaults confirmed)
Last activity: 2026-03-09 — Completed 04-02 (human-verified keybinding overrides end-to-end)

Progress: [██████████] 78%

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: 7.4 min
- Total execution time: 0.86 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-core-scaffold-and-async-architecture | 3 | 20 min | 6.7 min |
| 02-directory-rendering-and-icon-system | 4 | 32 min | 8 min |

**Recent Trend:**
- Last 5 plans: 01-03 (15 min), 02-01 (4 min), 02-02 (4 min), 02-03 (2 min), 02-04 (13 min)
- Trend: stable

*Updated after each plan completion*
| Phase 02 P04 | 2 | 2 tasks | 3 files |
| Phase 03-theme-system P01 | 2 | 3 tasks | 3 files |
| Phase 03-theme-system P02 | 3 | 2 tasks | 6 files |
| Phase 03-theme-system P03 | 13 | 2 tasks | 2 files |
| Phase 04-keybinding-system-and-config-infrastructure P01 | 6 | 2 tasks | 2 files |
| Phase 04-keybinding-system-and-config-infrastructure P02 | 4 | 1 task | 0 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: All FS I/O must use `@work(thread=True)` from Phase 1 — retrofitting is as costly as a rewrite
- [Roadmap]: FAL (fsspec wrapper) is mandatory from Phase 1 — no widget may call os/pathlib/shutil directly
- [Roadmap]: Nerd Font icons require explicit `icons: nerd` opt-in — auto-detection is impossible over SSH
- [Roadmap]: Theme YAML schema maps 1:1 to Textual's 11 base colors — validated by ThemeLoader before construction
- [Roadmap]: Delete uses send2trash (OS trash), never shutil.rmtree — confirmation modal required before any destructive key is wired
- [01-01]: hatchling build backend chosen over uv_build (generated default) — more mature, standard in Python ecosystem
- [01-01]: requires-python set to >=3.10 for match statement support and asyncssh compatibility in future phases
- [01-01]: ProbeFS protocol + **kwargs pattern established so SFTP is drop-in: ProbeFS('sftp', host=..., username=...)
- [01-01]: Entry point probefs.app:main wired in pyproject.toml — app.py stub must be created before uv run probefs works
- [01-02]: PurePosixPath used for path arithmetic — filesystem-agnostic, never calls stat/lstat, keeping descend/ascend pure
- [01-02]: ascend() at root is silent no-op for cwd (parent == cwd == '/') but still resets cursor_index to 0
- [01-02]: ProbeFS stored on core.fs at construction — workers call core.fs.ls() after navigation events, not inside transitions
- [01-03]: exclusive=True on _load_panes worker cancels in-flight loads automatically — no manual cancellation needed
- [01-03]: PreviewPane.CursorChanged posted via post_message() (not bubbling) — event.control is None, requires null guard in screen handler
- [01-03]: Single _load_panes() worker loads both parent and current directories to minimize thread overhead
- [Phase 02]: get_category fs=None FAL boundary: widgets pass ProbeFS; callers/tests use os.path.exists fallback
- [Phase 02]: Empty destination on islink=True treated as valid symlink — aligns with Pitfall 1 (never misidentify non-symlinks)
- [02-02]: ASCIIIconSet is the unconditional default — load_icon_set({}) returns ASCIIIconSet with no config required
- [02-02]: NerdIconSet requires explicit 'icons: nerd' opt-in — auto-detection is impossible over SSH
- [02-02]: ProbeFS.exists() added to FAL — widgets must never call os.path.exists directly for symlink detection
- [Phase 02]: dt.clear(columns=False) must be explicit in set_entries — bare dt.clear() removes column definitions
- [Phase 02]: show_hidden filtering in set_entries() on main thread enables instant dotfile toggle without re-reading disk
- [Phase 02]: action_cursor_down/up (not action_scroll_down/up) required for cursor_row movement in DataTable
- [02-04]: show_hidden state stored on FileManagerCore (not DirectoryList) — widget is stateless re: filter; core owns all nav state
- [02-04]: action_toggle_hidden re-calls _load_panes() rather than filtering in-place — simpler; exclusive=True cancels stale loads
- [02-04]: Binding priority=True on '.' is required — without it Textual may consume '.' for focus traversal before screen action fires
- [03-01]: ThemeLoader is the ONLY place in the codebase that constructs Theme(...) — enforced by design, not convention
- [03-01]: ThemeValidationError collects ALL errors before raising (not fail-fast) — user fixes all problems at once
- [03-01]: YAML() instance created per-call in load() and load_from_string() — ruamel.yaml is not thread-safe at module level
- [03-01]: Metadata fields (author, description, version) silently accepted in YAML but not stored in Theme — forward-compatible with future display
- [Phase 03-theme-system]: probefs-tokyo-night defined as own YAML (not aliasing Textual's tokyo-night) — keeps all themes under probefs-* convention
- [Phase 03-theme-system]: config.py is Phase 3 minimal: load_config() returns plain dict, Phase 4 extends same module by reading more keys
- [Phase 03-theme-system]: YAML() instance created per load_config() call (never module-level) — ruamel.yaml parser state is not thread-safe
- [Phase 03-theme-system]: load_config() returns {} for missing file or malformed YAML — never raises exception, never crashes app startup
- [03-03]: load_config() called in __init__ (not on_mount) — themes must be active before TUI event loop starts
- [03-03]: Registration before activation enforced — all themes registered before self.theme assigned (Textual requirement)
- [03-03]: Config path changed to ~/.probefs/probefs.yaml — macOS ~/Library/Application Support not user-writable by default; ~/.probefs/ always writable and discoverable
- [Phase 04-keybinding-system-and-config-infrastructure]: Textual native Binding.id + set_keymap() used for remapping — no custom key dispatch layer
- [Phase 04-keybinding-system-and-config-infrastructure]: Separate IDs per physical key variant (probefs.cursor_down vs probefs.cursor_down_arrow) for independent remap control
- [Phase 04-keybinding-system-and-config-infrastructure]: Space-stripping guard str(v).replace(' ', '') in _setup_keybindings() prevents Textual Pitfall 3 (spaces in keymap values)
- [04-02]: Override replace semantics verified at runtime — users must list original key explicitly to keep it (e.g. "n,j" not just "n")
- [04-02]: Zero-config confirmed — app starts cleanly with no keybindings section and removing it fully restores all defaults

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-03-09
Stopped at: Completed 04-02-PLAN.md (keybinding override system human-verified — Phase 4 complete)
Resume file: None
