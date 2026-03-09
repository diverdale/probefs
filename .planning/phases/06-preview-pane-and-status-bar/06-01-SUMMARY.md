---
phase: 06-preview-pane-and-status-bar
plan: "01"
subsystem: filesystem
tags: [probefs, fal, preview, disk-usage, mimetypes]

# Dependency graph
requires:
  - phase: 05-file-operations-and-safety
    provides: ProbeFS with copy, move, rename, trash, new_file, new_dir FAL methods
provides:
  - read_text() on ProbeFS with two-layer binary detection and 512 KB size cap
  - disk_usage() on ProbeFS returning free bytes via shutil
  - MAX_PREVIEW_BYTES = 524288 module-level constant
affects:
  - 06-02-preview-pane (PreviewPane widget calls fs.read_text())
  - 06-03-status-bar (StatusBar calls fs.disk_usage() from _load_panes worker)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Two-layer binary detection (MIME type first, null-byte fallback) for FAL read methods

key-files:
  created: []
  modified:
    - src/probefs/fs/probe_fs.py

key-decisions:
  - "MAX_PREVIEW_BYTES defined at module level (not inside class) so it can be used as a default argument in the method signature"
  - "read_text() uses stdlib open() internally (not fsspec), consistent with copy/move using shutil — FAL boundary applies to callers, not ProbeFS internals"
  - "disk_usage() reuses existing shutil import — no new import needed"

patterns-established:
  - "Binary detection pattern: MIME type (fast, no I/O) then null-byte check in first 8 KB (catches extensionless binaries)"
  - "FAL boundary: widgets/screens must never call open() or shutil.disk_usage directly — use fs.read_text() and fs.disk_usage()"

requirements-completed:
  - PREV-01
  - DISP-04

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 6 Plan 01: ProbeFS FAL Methods for Preview and Disk Usage Summary

**Two new FAL methods on ProbeFS: read_text() with MIME+null-byte binary detection and 512 KB cap, disk_usage() wrapping shutil for free space queries**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T17:06:49Z
- **Completed:** 2026-03-09T17:08:13Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Added `MAX_PREVIEW_BYTES = 524_288` (512 KB) at module level for use as method default argument
- Added `read_text()` with two-layer binary detection: MIME type for known extensions (fast, no I/O), null-byte check in first 8 KB for extensionless files
- Added `disk_usage()` returning free space as int (bytes), using already-imported shutil — no new imports needed

## Task Commits

Each task was committed atomically:

1. **Task 1: Add read_text() to ProbeFS** - `b629ff9` (feat)
2. **Task 2: Add disk_usage() to ProbeFS** - `778a05d` (feat)

## Files Created/Modified

- `src/probefs/fs/probe_fs.py` - Added MAX_PREVIEW_BYTES constant, read_text(), and disk_usage() methods

## Decisions Made

- `MAX_PREVIEW_BYTES` placed at module level (not inside class) — required for use as a default argument in `read_text()`'s method signature
- `read_text()` uses stdlib `open()` internally, not `fsspec.open()` — fsspec LocalFileSystem does not support partial reads the same way; this is consistent with `copy()` and `move()` using shutil internally; FAL boundary restricts callers (widgets), not ProbeFS itself
- `disk_usage()` uses the already-imported `shutil` — no new import needed, free field returned as int

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `fs.read_text(path)` ready for PreviewPane widget (06-02) — call from worker thread, handle ValueError for binary files
- `fs.disk_usage(path)` ready for StatusBar (06-03) — call from `_load_panes` worker thread
- Both methods documented with FAL boundary enforcement notes

---
*Phase: 06-preview-pane-and-status-bar*
*Completed: 2026-03-09*
