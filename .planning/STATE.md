# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-09)

**Core value:** A fast, beautiful, keyboard-driven file browser that feels at home in any terminal — local or remote — with a theming ecosystem that makes it yours.
**Current focus:** Phase 3 (Phase 2 complete)

## Current Position

Phase: 2 of 7 (Directory Rendering and Icon System) — COMPLETE
Plan: 4 of 4 in current phase
Status: Phase 2 complete
Last activity: 2026-03-09 — Completed 02-04 (show_hidden toggle wired end-to-end; Phase 2 human-verified)

Progress: [████████░░] 57%

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

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-03-09
Stopped at: Completed 02-04-PLAN.md (show_hidden toggle end-to-end wired; Phase 2 complete, human-verified)
Resume file: None
