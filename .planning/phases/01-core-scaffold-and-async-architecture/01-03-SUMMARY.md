---
phase: 01-core-scaffold-and-async-architecture
plan: 03
subsystem: ui
tags: [textual, tui, three-pane, file-browser, async, workers, tcss, fsspec]

# Dependency graph
requires:
  - phase: 01-core-scaffold-and-async-architecture
    plan: 01
    provides: ProbeFS FAL wrapping fsspec (ls, home, info)
  - phase: 01-core-scaffold-and-async-architecture
    plan: 02
    provides: FileManagerCore navigation state machine (cwd, descend, ascend, parent_path)
provides:
  - ProbeFSApp(App) with priority=True hjkl/arrow/enter/backspace bindings
  - MainScreen three-pane layout with @work(thread=True) directory loading
  - DirectoryList widget (ListView-backed) for parent and current panes
  - PreviewPane stub wired to receive CursorChanged messages
  - Three-column fractional TCSS layout (1fr / 1fr / 2fr)
  - Working `uv run probefs` entry point
affects:
  - phase 6 (preview pane content rendering - handler body only, wiring already done)
  - any phase adding new screen types (ProbeFSApp SCREENS dict pattern established)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "@work(thread=True, exclusive=True, exit_on_error=False) for all FS I/O — never call fs.ls() on main thread"
    - "Messages-up / attributes-down: widgets post domain messages (EntryHighlighted), screen passes data down (set_entries)"
    - "priority=True on all navigation bindings — prevents Textual's focus-based key routing from swallowing hjkl"
    - "Namespaced actions (screen.cursor_down) — bindings on App dispatch to active screen's action methods"
    - "exclusive=True workers — new _load_panes() call cancels any in-flight worker automatically"

key-files:
  created:
    - src/probefs/app.py
    - src/probefs/screens/__init__.py
    - src/probefs/screens/main.py
    - src/probefs/widgets/__init__.py
    - src/probefs/widgets/directory_list.py
    - src/probefs/widgets/preview_pane.py
    - src/probefs/probefs.tcss
  modified: []

key-decisions:
  - "exclusive=True on _load_panes worker cancels in-flight loads automatically — no manual cancellation needed"
  - "Single worker loads both parent and current directories to minimize thread overhead"
  - "DirectoryLoaded/DirectoryLoadFailed messages defined in main.py (not a separate messages.py) for Phase 1 simplicity"
  - "PreviewPane receives CursorChanged via post_message() not bubbling — requires event.control None guard in screen handler"

patterns-established:
  - "Widget message classes defined on the widget that generates them (DirectoryList.EntryHighlighted, PreviewPane.CursorChanged)"
  - "Screen message handlers are the integration point — widgets know nothing about each other"
  - "FAL boundary enforced: zero os/pathlib/shutil calls in app.py, screens/, or widgets/"

requirements-completed:
  - NAV-01
  - NAV-02

# Metrics
duration: 15min
completed: 2026-03-09
---

# Phase 1 Plan 03: Three-Pane TUI Summary

**Textual three-pane file browser with @work(thread=True) non-blocking directory loading, priority=True hjkl navigation, and ListView-backed DirectoryList widgets wired via domain messages.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-09
- **Completed:** 2026-03-09
- **Tasks:** 3 (including 1 bug fix)
- **Files modified:** 7 created, 1 modified (bug fix)

## Accomplishments

- Three-pane TUI launches via `uv run probefs` with no crash
- Directory loading runs entirely in @work(thread=True) workers — UI stays responsive during I/O
- All navigation bindings use priority=True — hjkl keys never captured by focused widgets
- FAL boundary clean — zero os/pathlib/shutil calls in app, screens, or widgets layers

## Task Commits

Each task was committed atomically:

1. **Task 1: Build ProbeFSApp, MainScreen, and TCSS layout** - `68faa30` (feat)
2. **Task 2: Implement DirectoryList and PreviewPane widgets** - `19bfe1f` (feat)
3. **Bug fix: null guard on event.control in EntryHighlighted handler** - `224b0a2` (fix)

## Files Created/Modified

- `src/probefs/app.py` - ProbeFSApp with priority=True BINDINGS, SCREENS dict, main() entry point
- `src/probefs/screens/__init__.py` - Empty package init
- `src/probefs/screens/main.py` - MainScreen: three-pane layout, @work directory loader, message handlers, action methods
- `src/probefs/widgets/__init__.py` - Empty package init
- `src/probefs/widgets/directory_list.py` - DirectoryList(Widget): ListView-backed, set_entries(), move_cursor_up/down(), EntryHighlighted message
- `src/probefs/widgets/preview_pane.py` - PreviewPane(Widget): Static display stub, CursorChanged message handler
- `src/probefs/probefs.tcss` - Three-column fractional layout (1fr / 1fr / 2fr with right borders)

## Decisions Made

- Single `_load_panes()` worker loads both parent and current directories to minimize thread overhead vs. two separate workers
- `exclusive=True` on the worker means a new navigation keystroke automatically cancels any in-flight directory load
- `DirectoryLoaded` and `DirectoryLoadFailed` message classes kept in `main.py` for Phase 1 simplicity; can be extracted to `messages.py` in a later phase if the module count grows
- `PreviewPane.CursorChanged` is posted directly via `preview.post_message()` rather than bubbling — this is intentional (screen is the integration point), but it means `event.control` is `None` in the handler, requiring a null guard

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added None guard for event.control before .id access**

- **Found during:** Task 3 (verification / app launch)
- **Issue:** `on_directory_list_entry_highlighted` accessed `event.control.id` unconditionally. When `DirectoryList` posts `EntryHighlighted` via `post_message()` (not bubbling), Textual does not set `event.control`, causing `AttributeError: 'NoneType' object has no attribute 'id'` on every cursor move at startup.
- **Fix:** Added `if event.control is None or event.control.id != "pane-current": return` — short-circuits safely when control is unset
- **Files modified:** `src/probefs/screens/main.py` line 88
- **Verification:** `uv run probefs` starts without traceback; Textual renders three-pane layout in terminal
- **Committed in:** `224b0a2` (fix(01-03))

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Fix was necessary for the app to run at all. No scope creep — single line change.

## Issues Encountered

None beyond the bug above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Three-pane TUI is working and navigable
- PreviewPane stub is wired and ready for Phase 6 content rendering (only handler body needs changing)
- @work pattern, priority=True bindings, and FAL boundary are established — all future phases build on this foundation
- Next: Phase 1 plans 04+ (if any), or Phase 2

---
*Phase: 01-core-scaffold-and-async-architecture*
*Completed: 2026-03-09*
