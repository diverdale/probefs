---
phase: 02-directory-rendering-and-icon-system
plan: 01
subsystem: ui
tags: [pytest, tdd, stat, pwd, datetime, fsspec, metadata, file-categorization]

# Dependency graph
requires:
  - phase: 01-core-scaffold-and-async-architecture
    provides: ProbeFS FAL (probe_fs.py) with fsspec entry dict shape (islink, mode, name, mtime, uid, destination)
provides:
  - get_category(entry, fs=None) pure function — drives icon selection and color in DataTable rows
  - human_size(n) — formats fsspec size field for the size column
  - format_mtime(mtime) — formats fsspec mtime field for the date column
  - uid_to_name(uid) — resolves fsspec uid field for the owner column
  - ARCHIVE_EXTS and IMAGE_EXTS frozensets — extension classification constants
  - src/probefs/rendering package — module namespace for all rendering utilities
affects:
  - 02-02 (icon system): imports get_category to drive IconSet.get_icon()/get_color()
  - 02-03 (DataTable widget): imports all four functions for build_row()
  - 02-04 (columns builder): uses human_size, format_mtime, uid_to_name directly

# Tech tracking
tech-stack:
  added: []
  patterns:
    - FAL boundary: get_category accepts optional ProbeFS (fs param) for broken-symlink check; falls back to os.path.exists for local-only callers
    - Priority order for file categorization: broken_symlink > symlink > directory > executable > archive > image > file
    - islink gate pattern: ALL symlink logic gated on islink=True FIRST before checking destination (prevents Pitfall 1)
    - OverflowError + KeyError dual catch in uid_to_name for cross-platform safety (negative UIDs)

key-files:
  created:
    - src/probefs/rendering/__init__.py
    - src/probefs/rendering/metadata.py
    - tests/test_rendering_metadata.py
  modified: []

key-decisions:
  - "get_category fs=None FAL boundary: widgets pass ProbeFS instance; pure callers and tests use os.path.exists fallback — future-proof for SFTP without breaking local use"
  - "Empty destination string on islink=True treated as valid symlink (not broken) — aligns with research Pitfall 1: never misidentify non-symlinks"
  - "human_size None returns '    -' (5 chars with leading spaces) not '  -' or 'N/A' — consistent column alignment in DataTable"
  - "format_mtime None returns 12 spaces — matches column width so missing mtime doesn't collapse the date column"

patterns-established:
  - "FAL boundary pattern: pure utility functions accept optional fs param; None triggers local fallback. Widgets always pass fs."
  - "Extension check pattern: os.path.splitext(basename)[1].lower() where basename = name.split('/')[-1] — handles full paths from fsspec"
  - "frozenset for extension sets — immutable, O(1) lookup, exported as module constants for reuse in future plans"

requirements-completed:
  - DISP-01
  - DISP-02
  - DISP-03

# Metrics
duration: 4min
completed: 2026-03-09
---

# Phase 02 Plan 01: File Type Categorization and Metadata Formatting Summary

**Pure rendering pipeline foundation: get_category() with 7-category priority classifier, human_size/format_mtime/uid_to_name formatters, and 34 TDD tests covering all 9 plan-specified input cases**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-09T14:16:12Z
- **Completed:** 2026-03-09T14:20:35Z
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 3

## Accomplishments

- Established `src/probefs/rendering/` package with full metadata module
- Implemented `get_category()` with FAL-safe broken-symlink detection via optional `fs` param
- All 34 pytest tests pass (54 total across full test suite — zero regressions)

## Task Commits

Each task was committed atomically:

1. **TDD RED: failing tests** - `5547aa3` (test)
2. **TDD GREEN: implementation** - `d030b27` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD tasks have two commits (test -> feat). No refactor commit needed — implementation was clean on first pass._

## Files Created/Modified

- `src/probefs/rendering/__init__.py` - Package marker for rendering module
- `src/probefs/rendering/metadata.py` - Four pure functions + ARCHIVE_EXTS/IMAGE_EXTS constants
- `tests/test_rendering_metadata.py` - 34 pytest tests covering all plan-specified cases

## Decisions Made

- `get_category(entry, fs=None)` accepts optional ProbeFS for FAL-safe broken-symlink check: when `fs` is provided, calls `fs._fs.exists(destination)`; when `None`, falls back to `os.path.exists`. This keeps the function usable standalone (tests, CLI) without sacrificing the FAL boundary for SFTP.
- Empty `destination` string on `islink=True` is treated as a valid symlink (returns `"symlink"`, not `"broken_symlink"`). Per research Pitfall 1: the function must never misidentify non-symlinks; when uncertain, default to valid.
- `human_size(None)` returns `"    -"` (4 spaces + dash = 5 chars) to maintain column alignment when size metadata is absent.
- `format_mtime(None)` returns exactly 12 spaces — matches the `%b %d %H:%M` output width so the date column doesn't collapse.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `get_category()` is ready for 02-02 (IconSet strategy) to consume as the primary dispatch function
- All four metadata formatters ready for 02-03 (DataTable widget) and 02-04 (build_row)
- `ARCHIVE_EXTS` and `IMAGE_EXTS` exported as module constants — 02-02 can import them if YAML icon themes need extension hints
- No blockers for subsequent plans

---
*Phase: 02-directory-rendering-and-icon-system*
*Completed: 2026-03-09*
