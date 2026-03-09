---
phase: 06-preview-pane-and-status-bar
plan: "04"
subsystem: ui
tags: [textual, layout, status-bar, footer, key-bindings, tcss]

# Dependency graph
requires:
  - phase: 06-01
    provides: ProbeFS FAL methods (disk_usage, read_text, MAX_PREVIEW_BYTES)
  - phase: 06-02
    provides: StatusBar widget with reactive path/item_count/free_space attributes
  - phase: 06-03
    provides: PreviewPane widget with ContentSwitcher two-mode implementation
provides:
  - Three-pane layout wired via #panes Horizontal container in probefs.tcss
  - StatusBar docked at bottom, updated after every directory load
  - Footer with show=True key hints for primary navigation bindings
  - DirectoryLoaded message extended with free_space field
  - Complete Phase 6 feature set integrated and functional
affects:
  - Phase 07 (any future layout or UI changes build on this structure)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "StatusBar updated reactively from on_directory_loaded — no separate polling or events"
    - "TCSS layout container (#panes) separates concerns from Screen-level styling"
    - "Footer key hints driven by show=True on Binding — no custom footer code needed"

key-files:
  created: []
  modified:
    - src/probefs/screens/main.py
    - src/probefs/probefs.tcss
    - src/probefs/app.py

key-decisions:
  - "StatusBar yielded before Footer in compose() — Textual stacks bottom-docked widgets in compose order, StatusBar must precede Footer to appear above it"
  - "Screen { layout: horizontal } removed from TCSS — replaced by explicit #panes Horizontal container with height:1fr so panes fill remaining space above status bar and footer"
  - "Duplicate key bindings (arrow/enter/backspace/ctrl+c) kept show=False — prevents duplicate labels in Footer; primary vim-style keys j/k/l/h are the canonical shown bindings"
  - "free_space update conditional on message.free_space > 0 — avoids overwriting a valid value if disk_usage returns 0 on edge-case path"

patterns-established:
  - "TCSS docking order: #panes fills 1fr height above two bottom-docked widgets (StatusBar then Footer)"
  - "Worker populates message with side-effect data (free_space) to keep main-thread handler free of I/O"

requirements-completed:
  - PREV-01
  - PREV-02
  - DISP-04

# Metrics
duration: 8min
completed: 2026-03-09
---

# Phase 6 Plan 04: Layout Integration and StatusBar Wiring Summary

**Three-pane layout finalized with #panes Horizontal container, StatusBar docked above Footer, and navigation bindings surfaced as Footer key hints using show=True**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-09T00:00:00Z
- **Completed:** 2026-03-09T00:08:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Replaced `Screen { layout: horizontal }` TCSS override with explicit `#panes { layout: horizontal; height: 1fr }` container so panes fill exactly the space above the status bar and footer
- Wired StatusBar into MainScreen.compose() — yielded before Footer so Textual's bottom-dock stacking order is correct
- Extended DirectoryLoaded message with free_space field and updated _load_panes worker to call disk_usage() on every directory load
- Updated on_directory_loaded to set StatusBar.path, item_count, and free_space after each current-pane load
- Changed j, k, l, h, ., q bindings to show=True with compact descriptions so Footer displays useful navigation hints

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor TCSS layout and update MainScreen compose + wiring** - `84b24fa` (feat)
2. **Task 2: Update app.py bindings for Footer key hints** - `f9bf02b` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/probefs/screens/main.py` - Added Footer/StatusBar imports, updated compose(), extended DirectoryLoaded, updated _load_panes and on_directory_loaded
- `src/probefs/probefs.tcss` - Replaced Screen layout override with #panes container, added StatusBar dock styling
- `src/probefs/app.py` - Updated 6 navigation bindings to show=True with compact descriptions

## Decisions Made
- StatusBar must be yielded before Footer in compose() — Textual stacks bottom-docked widgets in compose order; wrong order places StatusBar below Footer's key-hint bar
- Screen-level `layout: horizontal` removed — the old TCSS worked but left no way to control height of the pane area relative to the bottom widgets; #panes with height:1fr solves this cleanly
- Footer key hints use only the primary vim-style keys (j/k/l/h/./q) — arrow/enter/backspace/ctrl+c duplicates stay show=False to avoid redundant labels in the Footer bar
- free_space update guarded by `> 0` check — protects against overwriting a valid displayed value on edge-case paths where disk_usage returns 0

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All Phase 6 components (ProbeFS FAL, StatusBar, PreviewPane, layout integration) are complete and wired
- App is runnable with `uv run probefs` — three-pane layout, live StatusBar, Footer key hints, full file operations
- Phase 7 can build on this layout without structural changes

---
*Phase: 06-preview-pane-and-status-bar*
*Completed: 2026-03-09*
