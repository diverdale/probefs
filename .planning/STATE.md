# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-09)

**Core value:** A fast, beautiful, keyboard-driven file browser that feels at home in any terminal — local or remote — with a theming ecosystem that makes it yours.
**Current focus:** Phase 1 - Core Scaffold and Async Architecture

## Current Position

Phase: 1 of 7 (Core Scaffold and Async Architecture)
Plan: 2 of TBD in current phase
Status: In progress
Last activity: 2026-03-09 — Completed 01-02 (FileManagerCore navigation state machine)

Progress: [██░░░░░░░░] 10%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 2.5 min
- Total execution time: 0.08 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-core-scaffold-and-async-architecture | 2 | 5 min | 2.5 min |

**Recent Trend:**
- Last 5 plans: 01-01 (3 min), 01-02 (2 min)
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

### Pending Todos

- Create src/probefs/app.py with main() stub so entry point resolves (Plan 02 or similar)

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-03-09
Stopped at: Completed 01-02-PLAN.md (FileManagerCore navigation state machine)
Resume file: None
