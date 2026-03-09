---
phase: 01-core-scaffold-and-async-architecture
plan: 02
subsystem: core
tags: [python, pathlib, PurePosixPath, pytest, tdd, navigation, state-machine]

# Dependency graph
requires:
  - phase: 01-core-scaffold-and-async-architecture
    plan: 01
    provides: ProbeFS FAL and uv scaffold this plan depends on for injection and packaging

provides:
  - FileManagerCore navigation state machine with cwd, cursor_index, descend(), ascend(), parent_path
  - Full pytest test suite (20 tests) with RED-GREEN-REFACTOR commits
  - tests/ package initialized for future test modules

affects:
  - 01-03 and later (MainScreen workers inject FileManagerCore and call core.fs.ls() after navigation events)
  - all future navigation phases (FileManagerCore is the authoritative navigation state; widgets never hold cwd directly)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Navigation state is pure: descend()/ascend() use PurePosixPath arithmetic only — no filesystem I/O"
    - "ProbeFS injected at FileManagerCore.__init__ stored on self.fs for worker access, not called during navigation"
    - "TDD RED-GREEN-REFACTOR: failing import error → all 20 passing — testability boundary verified before UI exists"

key-files:
  created:
    - src/probefs/core/__init__.py
    - src/probefs/core/file_manager.py
    - tests/__init__.py
    - tests/test_file_manager_core.py
  modified: []

key-decisions:
  - "PurePosixPath used for path arithmetic — it is filesystem-agnostic and never calls stat/lstat, keeping descend/ascend pure"
  - "ascend() at root is a silent no-op for cwd (parent == cwd == '/') but still resets cursor_index to 0"
  - "ProbeFS stored on self.fs at construction time — workers on MainScreen use core.fs.ls() after navigation, not inside transitions"

patterns-established:
  - "Testability boundary: FileManagerCore has zero async/UI dependencies — plain pytest with no asyncio fixtures needed"
  - "Navigation state ownership: cwd and cursor_index live only in FileManagerCore; widgets read from core, never hold their own"

requirements-completed: [NAV-02]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 1 Plan 02: FileManagerCore Navigation State Machine Summary

**PurePosixPath-backed navigation state machine with 20 pytest tests proving descend/ascend/parent_path are pure and root-safe**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-09T13:33:04Z
- **Completed:** 2026-03-09T13:34:30Z
- **Tasks:** 1 (TDD: RED + GREEN, REFACTOR not needed)
- **Files modified:** 4

## Accomplishments

- FileManagerCore class with cwd, cursor_index, parent_path, descend(), ascend() — all pure path operations
- 20 pytest tests covering initialization, parent_path immutability, descend chaining, ascend boundary at root, round-trips
- Confirmed: ascend() at "/" does not panic and cursor_index resets to 0 in every navigation case
- ProbeFS injected and stored on self.fs, ready for @work(thread=True) worker access in future MainScreen

## Task Commits

TDD commits (RED then GREEN, no REFACTOR needed):

1. **RED: Failing tests** - `dd4b918` (test)
2. **GREEN: FileManagerCore implementation** - `5a46d4c` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/probefs/core/__init__.py` - Empty package marker for probefs.core subpackage
- `src/probefs/core/file_manager.py` - FileManagerCore class with docstrings and pure state transitions
- `tests/__init__.py` - Empty package marker for test discovery
- `tests/test_file_manager_core.py` - 20 pytest tests covering all specified behaviors

## Decisions Made

- Used `PurePosixPath` from pathlib for path arithmetic — it is purely string-based and never calls `stat`, `lstat`, or any filesystem syscall, making it safe for the purity contract
- `ascend()` guards with `if parent != self.cwd` to handle root silently — `PurePosixPath("/").parent` returns `PurePosixPath("/")` so the condition naturally catches this without special-casing
- No `pytest-asyncio` fixtures needed in this test file — FileManagerCore has no Textual or async dependencies, keeping tests fast and simple

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- FileManagerCore is ready to be instantiated in MainScreen (Plan 03 or later)
- Workers on MainScreen call `self.app.screen.core.fs.ls(self.app.screen.core.cwd)` after descend/ascend events
- Pending todo from Plan 01 still open: `src/probefs/app.py` with `main()` stub required before `uv run probefs` works

---
*Phase: 01-core-scaffold-and-async-architecture*
*Completed: 2026-03-09*

## Self-Check: PASSED

All created files verified on disk. Both TDD commits confirmed in git log.
