---
phase: 05-file-operations-and-safety
plan: 01
subsystem: filesystem
tags: [fsspec, send2trash, shutil, fal, probefs]

# Dependency graph
requires:
  - phase: 01-core-scaffold-and-async-architecture
    provides: ProbeFS FAL base class with ls, info, exists, isdir, home methods

provides:
  - send2trash 2.1.0 installed as declared project dependency
  - ProbeFS.copy(src, dst) — shutil.copytree for dirs, shutil.copy2 for files
  - ProbeFS.move(src, dst) — shutil.move with FileExistsError guard on existing-dir dst
  - ProbeFS.rename(src, new_name) — in-place rename via fs.mv, same parent dir only
  - ProbeFS.trash(path) — OS-native trash via send2trash, never permanent delete
  - ProbeFS.new_file(path) — fs.touch with FileExistsError guard
  - ProbeFS.new_dir(path) — fs.mkdir(create_parents=False) with native FileExistsError
affects: [05-02, 05-03, 05-04, screens/main.py, widgets/dialogs.py]

# Tech tracking
tech-stack:
  added: [send2trash==2.1.0]
  patterns:
    - FAL boundary enforced — all file ops go through ProbeFS; widgets/screens never call shutil or os.remove directly
    - shutil.copytree used for directory copy (not fsspec recursive copy which doesn't preserve content)
    - send2trash imported at module top as _send2trash — fast failure at startup not mid-operation
    - FileExistsError raised explicitly in move() when dst is existing dir (Pitfall 5 guard)

key-files:
  created: []
  modified:
    - src/probefs/fs/probe_fs.py
    - pyproject.toml
    - uv.lock

key-decisions:
  - "shutil.copytree used for directory copy in ProbeFS.copy() — fsspec LocalFileSystem.cp_file only calls makedirs for dirs, does not copy contents"
  - "ProbeFS.move() raises FileExistsError when dst is an existing directory — prevents silent mv-into-directory behavior (Pitfall 5)"
  - "send2trash imported at module top as _send2trash — fast failure on import, not mid-operation during first trash attempt"
  - "PurePosixPath used for parent/dst arithmetic in rename() — filesystem-agnostic, consistent with existing ProbeFS patterns"
  - "new_dir() relies on fsspec LocalFileSystem.mkdir native FileExistsError — no redundant existence check needed (verified local.py line 45)"

patterns-established:
  - "Pattern: FAL boundary — ProbeFS is the only place shutil and send2trash are called; widgets and screens import nothing from shutil or send2trash"
  - "Pattern: FileExistsError guard in move() — always check isdir(dst) before shutil.move to prevent silent path changes"
  - "Pattern: new_file() existence guard — fs.exists(path) check before fs.touch() because touch() does not raise on existing files"

requirements-completed: [FOPS-01, FOPS-02, FOPS-03, FOPS-04, FOPS-05, FOPS-06]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 5 Plan 01: File Operations FAL Foundation Summary

**ProbeFS FAL extended with 6 file operation methods (copy, move, rename, trash, new_file, new_dir) backed by shutil/send2trash; send2trash 2.1.0 added as declared dependency**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T16:00:50Z
- **Completed:** 2026-03-09T16:02:03Z
- **Tasks:** 2
- **Files modified:** 3 (probe_fs.py, pyproject.toml, uv.lock)

## Accomplishments
- send2trash 2.1.0 added to pyproject.toml dependencies and installed via `uv add send2trash`
- ProbeFS extended with all 6 FAL methods required by FOPS-01 through FOPS-06
- FAL boundary preserved — shutil and send2trash called only inside probe_fs.py
- Smoke test verifies new_file, new_dir, copy, rename, move, and FileExistsError guard all function correctly

## Task Commits

Each task was committed atomically:

1. **Task 1: Add send2trash dependency** - `1848e4f` (chore)
2. **Task 2: Extend ProbeFS with file operation methods** - `235254f` (feat)

## Files Created/Modified
- `src/probefs/fs/probe_fs.py` - Added shutil/PurePosixPath/send2trash imports + copy, move, rename, trash, new_file, new_dir methods (85 lines added)
- `pyproject.toml` - send2trash>=2.1.0 added to [project] dependencies
- `uv.lock` - Updated with send2trash 2.1.0 resolution

## Decisions Made
- `shutil.copytree` used for directory copy rather than `fsspec.copy(recursive=True)` — fsspec LocalFileSystem.cp_file only calls makedirs for directories, does not copy file contents (confirmed Pitfall 3 from research)
- `ProbeFS.move()` raises `FileExistsError` when dst is an existing directory — prevents silent mv-into-directory behavior documented as Pitfall 5
- `send2trash` imported at module top as `_send2trash` — ensures fast failure at startup if package is missing, not mid-operation on first delete attempt
- `PurePosixPath` used for path arithmetic in `rename()` — consistent with existing ProbeFS and FileManagerCore patterns, filesystem-agnostic

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- ProbeFS FAL foundation complete — all 6 methods ready for UI wiring in 05-02 (dialogs) and 05-03/05-04 (action wiring in MainScreen)
- send2trash 2.1.0 installed and importable in venv
- No blockers

---
*Phase: 05-file-operations-and-safety*
*Completed: 2026-03-09*
