---
phase: 02-directory-rendering-and-icon-system
plan: 04
subsystem: ui
tags: [textual, datatable, file-manager, dotfiles, keybinding, toggle]

# Dependency graph
requires:
  - phase: 02-03
    provides: DirectoryList with DataTable and set_entries(show_hidden=False), build_row() Rich Text row builder

provides:
  - FileManagerCore.show_hidden: bool = False attribute — persists toggle state across pane reloads
  - MainScreen.action_toggle_hidden() — flips core.show_hidden, calls _load_panes() to refresh both panes
  - MainScreen.on_directory_loaded() passes show_hidden=self.core.show_hidden to set_entries()
  - ProbeFSApp Binding('.', 'screen.toggle_hidden', priority=True) — '.' key wired end-to-end
  - Human-verified complete Phase 2 rendering pipeline (5 columns, colors, symlinks, toggle)

affects:
  - Phase 3+ (any plan extending FileManagerCore state or MainScreen actions)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Toggle state stored on FileManagerCore (not on widget) — single source of truth, survives pane reloads
    - _load_panes() re-called on toggle — OS directory cache makes re-read near-instant; exclusive=True cancels in-flight loads
    - Binding priority=True on '.' prevents Textual from intercepting the keypress for focus traversal

key-files:
  created: []
  modified:
    - src/probefs/core/file_manager.py
    - src/probefs/screens/main.py
    - src/probefs/app.py

key-decisions:
  - "show_hidden state stored on FileManagerCore (not DirectoryList) — widget is stateless re: filter; core owns nav state"
  - "action_toggle_hidden re-calls _load_panes() rather than filtering in-place — simpler and correct; exclusive=True cancels stale load"
  - "Binding priority=True on '.' is required — without it Textual may consume '.' for focus traversal before reaching screen"

patterns-established:
  - "Navigation state pattern: all persistent nav state (cwd, cursor_index, show_hidden) lives on FileManagerCore"
  - "Screen action pattern: MainScreen actions call _load_panes() to refresh UI after any state change"

requirements-completed: [NAV-03, DISP-01, DISP-02, DISP-03, THEME-05, THEME-06, THEME-07]

# Metrics
duration: 13min
completed: 2026-03-09
---

# Phase 2 Plan 4: Show-Hidden Toggle and Phase 2 Visual Verification Summary

**'.' key wired end-to-end through FileManagerCore.show_hidden -> action_toggle_hidden -> set_entries(), with human-verified 5-column DataTable rendering, file-type coloring, and symlink display**

## Performance

- **Duration:** 13 min
- **Started:** 2026-03-09T14:24:10Z
- **Completed:** 2026-03-09T14:38:04Z
- **Tasks:** 2 (1 auto + 1 human-verify checkpoint)
- **Files modified:** 3

## Accomplishments
- Added `show_hidden: bool = False` to `FileManagerCore.__init__` as the single source of truth for dotfile filter state
- Wired `action_toggle_hidden()` in `MainScreen` — flips `core.show_hidden` and calls `_load_panes()` to refresh both panes
- Updated `on_directory_loaded()` to pass `show_hidden=self.core.show_hidden` to every `set_entries()` call
- Added `Binding(".", "screen.toggle_hidden", priority=True)` to `ProbeFSApp.BINDINGS`
- Human verifier confirmed all Phase 2 requirements working: 5 columns visible, colors correct, symlinks show `-> target`, hidden toggle instant, navigation intact

## Task Commits

Each task was committed atomically:

1. **Task 1: Add show_hidden to FileManagerCore and wire toggle through MainScreen and app.py** - `d9a8654` (feat)
2. **Task 2: Visual verification of complete Phase 2 rendering** - human-approved checkpoint (no code commit)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/probefs/core/file_manager.py` - Added `self.show_hidden: bool = False` attribute to `__init__`
- `src/probefs/screens/main.py` - Added `action_toggle_hidden()`; updated `on_directory_loaded()` to pass `show_hidden`
- `src/probefs/app.py` - Added `Binding(".", "screen.toggle_hidden", priority=True, show=False)` to BINDINGS

## Decisions Made
- `show_hidden` stored on `FileManagerCore` (not on `DirectoryList`) — the widget is stateless with respect to the filter; FileManagerCore is the single source of truth for all navigation state
- `action_toggle_hidden` re-calls `_load_panes()` rather than directly calling `set_entries()` on each pane — simpler and correct; `exclusive=True` on the worker cancels any in-flight stale load automatically
- `priority=True` on the `'.'` binding is required — without it Textual may consume the keypress for its own focus traversal before the screen action fires

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 2 is complete. All four plans executed and human-verified.
- Rendering pipeline (5-column DataTable, Rich Text coloring, symlink display, dotfile toggle) is fully wired and confirmed working.
- FileManagerCore carries `show_hidden` state; all future phases adding navigation state should follow this pattern.
- Ready for Phase 3 planning.

## Self-Check: PASSED

- src/probefs/core/file_manager.py: FOUND
- src/probefs/screens/main.py: FOUND
- src/probefs/app.py: FOUND
- .planning/phases/02-directory-rendering-and-icon-system/02-04-SUMMARY.md: FOUND
- Commit d9a8654 (Task 1): FOUND

---
*Phase: 02-directory-rendering-and-icon-system*
*Completed: 2026-03-09*
