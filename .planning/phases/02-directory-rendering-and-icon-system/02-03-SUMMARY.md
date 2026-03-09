---
phase: 02-directory-rendering-and-icon-system
plan: 03
subsystem: ui
tags: [textual, datatable, rich-text, directory-list, rendering]

# Dependency graph
requires:
  - phase: 02-01
    provides: get_category(), human_size(), format_mtime(), uid_to_name() from rendering/metadata.py
  - phase: 02-02
    provides: IconSet ABC, ASCIIIconSet, load_icon_set() factory, ProbeFS.exists() FAL method

provides:
  - build_row(entry, icon_set, fs=None) -> tuple[Text, Text, Text, Text, Text] in rendering/columns.py
  - DirectoryList rewritten with DataTable(cursor_type="row"), five-column Rich Text layout
  - set_entries(entries, show_hidden=False) with inline dotfile filtering
  - DataTable TCSS rule in probefs.tcss

affects:
  - 02-04 (visual verification checkpoint — this is what it will check)
  - Phase 3+ (any plan that adds features to DirectoryList)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - build_row() centralizes all entry-to-cell conversion; widgets never format metadata directly
    - Rich Text styles on DataTable cells (not TCSS) for per-cell coloring
    - dt.clear(columns=False) pattern prevents accidental column removal on refresh
    - action_cursor_down/up (not action_scroll_down/up) for cursor movement in DataTable

key-files:
  created:
    - src/probefs/rendering/columns.py
  modified:
    - src/probefs/widgets/directory_list.py
    - src/probefs/probefs.tcss

key-decisions:
  - "build_row() accepts optional fs param for FAL-safe broken symlink detection, defaulting to None for tests"
  - "dt.clear(columns=False) must be explicit — bare dt.clear() removes column definitions (Pitfall 2)"
  - "show_hidden filtering in set_entries() (not in worker) enables instant toggle without re-reading disk"
  - "action_cursor_down/up moves cursor_row; action_scroll_down/up only scrolls viewport — always use cursor variants"

patterns-established:
  - "Rich Text row builder pattern: all cell formatting centralized in build_row(), not in widget"
  - "DataTable column widths: name=None (flexible, fills space), fixed widths for metadata columns"
  - "Empty table guard: cursor_row is 0 even when table is empty, always check idx < len(self._entries)"

requirements-completed: [DISP-01, DISP-02, DISP-03, NAV-03]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 2 Plan 3: DataTable DirectoryList with Rich Text Row Builder Summary

**ListView replaced by DataTable(cursor_type="row") with five-column Rich Text cells built by centralized build_row() function**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T14:20:39Z
- **Completed:** 2026-03-09T14:22:01Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created `rendering/columns.py` with `build_row()` producing 5-tuple of Rich Text cells (name/icon, permissions, size, date, owner)
- Rewrote DirectoryList from ListView to DataTable(cursor_type="row") with all five columns
- Added `show_hidden=False` to `set_entries()` for instant dotfile toggle without re-reading disk
- Preserved public API: EntryHighlighted message, move_cursor_up/down, get_highlighted_entry

## Task Commits

Each task was committed atomically:

1. **Task 1: Create build_row() in rendering/columns.py** - `fe8e34b` (feat)
2. **Task 2: Rewrite DirectoryList to use DataTable** - `9052ca1` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/probefs/rendering/columns.py` - build_row() converting fsspec entry dict to 5-tuple of Rich Text cells
- `src/probefs/widgets/directory_list.py` - DirectoryList rewritten with DataTable; set_entries gains show_hidden param
- `src/probefs/probefs.tcss` - Added DirectoryList DataTable rule (height: 100%; background: $panel)

## Decisions Made
- `dt.clear(columns=False)` is explicit in set_entries — the bare `dt.clear()` removes column definitions (Pitfall 2 from research), which would require re-adding them on every update
- `show_hidden` filtering placed in set_entries() on main thread, not in the background worker — enables instant toggle without re-reading disk
- `action_cursor_down()/action_cursor_up()` used in move_cursor_down/up (not scroll variants) because scroll methods only move viewport, not cursor_row
- Empty table guard `0 <= idx < len(self._entries)` applied in both get_highlighted_entry() and on_data_table_row_highlighted() because DataTable.cursor_row is 0 even when empty

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- DirectoryList is now DataTable-based and renders five columns of Rich Text
- Visual verification checkpoint in 02-04 will confirm rendering appears correct in the TUI
- MainScreen requires no structural changes — public API is identical to the ListView version

## Self-Check: PASSED

- src/probefs/rendering/columns.py: FOUND
- src/probefs/widgets/directory_list.py: FOUND
- src/probefs/probefs.tcss: FOUND
- .planning/phases/02-directory-rendering-and-icon-system/02-03-SUMMARY.md: FOUND
- Commit fe8e34b (Task 1): FOUND
- Commit 9052ca1 (Task 2): FOUND

---
*Phase: 02-directory-rendering-and-icon-system*
*Completed: 2026-03-09*
