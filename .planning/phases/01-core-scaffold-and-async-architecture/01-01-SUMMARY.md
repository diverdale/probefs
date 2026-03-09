---
phase: 01-core-scaffold-and-async-architecture
plan: 01
subsystem: infra
tags: [uv, fsspec, textual, python, hatchling, probefs]

# Dependency graph
requires: []
provides:
  - uv package scaffold with hatchling build backend and probefs.app:main entry point
  - ProbeFS FAL class wrapping fsspec LocalFileSystem with ls(), info(), isdir()
  - FAL boundary: no widget or logic module may call os/pathlib/shutil directly
affects:
  - 01-02 (async architecture - depends on ProbeFS for FileManagerCore)
  - all future phases (FAL boundary is a project-wide invariant)

# Tech tracking
tech-stack:
  added: [uv, fsspec==2026.2.0, textual==8.0.2, pytest, pytest-asyncio, pytest-textual-snapshot, hatchling]
  patterns:
    - "All filesystem I/O routes through ProbeFS; never os/pathlib/shutil in src/probefs/fs/"
    - "fsspec.filesystem(protocol, **kwargs) enables drop-in SFTP replacement: ProbeFS('sftp', host=...)"
    - "Single self._fs instance per ProbeFS (not re-created per call)"

key-files:
  created:
    - pyproject.toml
    - .python-version
    - src/probefs/__init__.py
    - src/probefs/fs/__init__.py
    - src/probefs/fs/probe_fs.py
    - uv.lock
    - README.md
  modified: []

key-decisions:
  - "hatchling build backend chosen over uv_build (generated default) — more mature, standard in Python ecosystem"
  - "requires-python set to >=3.10 for match statement support and asyncssh compatibility in future phases"
  - ".python-version pinned to 3.12 as latest stable 3.10+ release"
  - "README.md required by hatchling build system — created as minimal stub"
  - "ProbeFS protocol + **kwargs pattern established so SFTP is drop-in: ProbeFS('sftp', host=..., username=...)"

patterns-established:
  - "FAL boundary: ProbeFS is the only filesystem gateway; os/pathlib/shutil forbidden in src/probefs/"
  - "fsspec protocol abstraction: LocalFileSystem now, SFTP later without widget changes"

requirements-completed: []

# Metrics
duration: 3min
completed: 2026-03-09
---

# Phase 1 Plan 01: Core Scaffold and ProbeFS FAL Summary

**uv package scaffold with hatchling + fsspec-backed ProbeFS FAL establishing the filesystem abstraction boundary for all future phases**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-09T13:27:45Z
- **Completed:** 2026-03-09T13:30:30Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- uv project initialized with hatchling build backend, `probefs.app:main` entry point, Python >=3.10
- textual and fsspec installed as runtime deps; pytest, pytest-asyncio, pytest-textual-snapshot as dev deps
- ProbeFS FAL implemented: single `self._fs` instance wrapping fsspec, exposing `ls()`, `info()`, `isdir()`
- FAL boundary enforced: no os/pathlib/shutil imports in `src/probefs/fs/`

## Task Commits

Each task was committed atomically:

1. **Task 1: Initialize uv package scaffold** - `eea2b75` (chore)
2. **Task 2: Implement ProbeFS FAL** - `03001d4` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `pyproject.toml` - Package definition with hatchling backend, entry point, runtime and dev deps
- `.python-version` - Pins Python 3.12
- `uv.lock` - Lockfile for reproducible installs
- `src/probefs/__init__.py` - Empty package marker
- `src/probefs/fs/__init__.py` - Empty fs subpackage marker
- `src/probefs/fs/probe_fs.py` - ProbeFS class wrapping fsspec with ls(), info(), isdir()
- `README.md` - Minimal stub required by hatchling build system

## Decisions Made

- Used hatchling build backend (not the uv_build default from `uv init`) — hatchling is the standard in the Python ecosystem and better documented
- `requires-python = ">=3.10"` to match asyncssh requirements for future SFTP phase and enable match statements
- README.md created as a minimal stub; hatchling requires the file referenced in pyproject.toml to exist

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created README.md required by hatchling build**
- **Found during:** Task 1 (uv sync after scaffold setup)
- **Issue:** pyproject.toml references `readme = "README.md"` but the file did not exist; hatchling raised `OSError: Readme file does not exist: README.md` and uv sync failed
- **Fix:** Created README.md with minimal stub content
- **Files modified:** README.md
- **Verification:** uv sync completed successfully after creation
- **Committed in:** eea2b75 (Task 1 commit)

**2. [Rule 3 - Blocking] Moved uv init output from nested dir to project root**
- **Found during:** Task 1 (uv init --package probefs)
- **Issue:** `uv init --package probefs` created a nested `probefs/` subdirectory instead of initializing in-place; the project root already existed as a git repo
- **Fix:** Copied pyproject.toml and src/ from the nested directory to the project root, then removed the nested directory
- **Files modified:** pyproject.toml, src/probefs/__init__.py
- **Verification:** `uv sync` succeeded from project root
- **Committed in:** eea2b75 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes were necessary to complete the scaffold. No scope creep.

## Issues Encountered

- `uv init --package probefs` nested the output in a subdirectory when run in an existing directory — files moved to root manually.
- hatchling build system requires README.md to exist if referenced in pyproject.toml — created stub.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- ProbeFS FAL is ready for use in Plan 02 (async architecture / FileManagerCore)
- Entry point `probefs.app:main` wired but `src/probefs/app.py` does not yet exist — Plan 02 or later must create it before `uv run probefs` can execute without ImportError
- FAL boundary enforcement is now project-wide invariant; all future widgets/logic must use ProbeFS

---
*Phase: 01-core-scaffold-and-async-architecture*
*Completed: 2026-03-09*

## Self-Check: PASSED

All created files verified on disk. Both task commits confirmed in git log.
