# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-09)

**Core value:** A fast, beautiful, keyboard-driven file browser that feels at home in any terminal — local or remote — with a theming ecosystem that makes it yours.
**Current focus:** Phase 1 - Core Scaffold and Async Architecture

## Current Position

Phase: 1 of 7 (Core Scaffold and Async Architecture)
Plan: 1 of TBD in current phase
Status: In progress
Last activity: 2026-03-09 — Completed 01-01 (uv scaffold + ProbeFS FAL)

Progress: [█░░░░░░░░░] 5%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 3 min
- Total execution time: 0.05 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-core-scaffold-and-async-architecture | 1 | 3 min | 3 min |

**Recent Trend:**
- Last 5 plans: 01-01 (3 min)
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

### Pending Todos

- Create src/probefs/app.py with main() stub so entry point resolves (Plan 02 or similar)

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-03-09
Stopped at: Completed 01-01-PLAN.md (uv scaffold + ProbeFS FAL)
Resume file: None
