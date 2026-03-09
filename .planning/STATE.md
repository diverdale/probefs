# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-09)

**Core value:** A fast, beautiful, keyboard-driven file browser that feels at home in any terminal — local or remote — with a theming ecosystem that makes it yours.
**Current focus:** Phase 2 - Directory Rendering and Icon System

## Current Position

Phase: 2 of 7 (Directory Rendering and Icon System)
Plan: 2 of 4 in current phase
Status: In progress
Last activity: 2026-03-09 — Completed 02-02 (IconSet strategy pattern and ProbeFS.exists())

Progress: [████░░░░░░] 20%

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 6.7 min
- Total execution time: 0.33 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-core-scaffold-and-async-architecture | 3 | 20 min | 6.7 min |
| 02-directory-rendering-and-icon-system | 1 | 4 min | 4 min |

**Recent Trend:**
- Last 5 plans: 01-01 (3 min), 01-02 (2 min), 01-03 (15 min), 02-01 (4 min)
- Trend: -

*Updated after each plan completion*

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

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-03-09
Stopped at: Completed 02-02-PLAN.md (IconSet strategy pattern and ProbeFS.exists())
Resume file: None
