---
phase: 06-preview-pane-and-status-bar
plan: "03"
subsystem: ui
tags: [textual, rich, syntax-highlighting, content-switcher, workers, threading]

# Dependency graph
requires:
  - phase: 06-01
    provides: ProbeFS.read_text() with 512KB cap and binary detection
  - phase: 01-03
    provides: PreviewPane.CursorChanged message routing from MainScreen

provides:
  - Two-mode PreviewPane with ContentSwitcher (file preview + directory listing)
  - Async file preview worker using Rich Syntax with ansi_dark theme
  - Async directory preview worker reusing DirectoryList
  - Race-condition-safe exclusive workers that cancel in-flight loads

affects:
  - 06-04
  - 07

# Tech tracking
tech-stack:
  added: [rich.syntax.Syntax, rich.console.Group, textual.widgets.ContentSwitcher]
  patterns:
    - exclusive=True workers for race-condition-safe async preview loading
    - call_from_thread() for all UI mutations from thread workers
    - is_cancelled checked before every call_from_thread call
    - app.get_screen("main") to access core.fs from workers without coupling widget to initialization order

key-files:
  created: []
  modified:
    - src/probefs/widgets/preview_pane.py

key-decisions:
  - "ContentSwitcher(initial='preview-file') chosen as initial state so empty dirs don't show blank DirectoryList on launch"
  - "app.get_screen('main').core.fs access pattern avoids storing ProbeFS reference on PreviewPane (decouples widget from initialization order)"
  - "Syntax(text, lexer=...) used instead of Syntax.from_path() — from_path() reads file without size cap, bypassing ProbeFS FAL boundary"
  - "rich.console.Group used to compose Syntax + truncation Text notice — Static.update() can only show one renderable at a time"
  - "lexer falls back to 'text' if extension is empty or Pygments raises on unknown lexer"

patterns-established:
  - "ContentSwitcher toggle pattern: switch mode before populating widget (no flash of wrong content)"
  - "Thread worker pattern: get_current_worker() at top of worker, check is_cancelled before every UI call"

requirements-completed:
  - PREV-01
  - PREV-02

# Metrics
duration: 1min
completed: 2026-03-09
---

# Phase 6 Plan 03: PreviewPane Full Implementation Summary

**Two-mode PreviewPane with ContentSwitcher, syntax-highlighted file preview via Rich Syntax, and directory listing via DirectoryList — both backed by exclusive async workers that cancel in-flight loads on rapid cursor movement.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-09T17:12:46Z
- **Completed:** 2026-03-09T17:13:46Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Replaced Phase 1 stub PreviewPane with full two-mode implementation
- File preview: Rich Syntax with ansi_dark theme, line numbers, exclusive worker cancels stale loads
- Directory preview: DirectoryList.set_entries() populated via exclusive worker
- Binary file detection: ValueError from read_text() caught and shown as dim text message
- Large file truncation: files >512KB show truncation notice via rich.console.Group
- CursorChanged message interface preserved exactly — MainScreen.py requires no changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace PreviewPane stub with two-mode implementation** - `c4c5e51` (feat)

**Plan metadata:** (docs: complete plan — see below)

## Files Created/Modified
- `src/probefs/widgets/preview_pane.py` - Full two-mode PreviewPane replacing Phase 1 stub

## Decisions Made
- ContentSwitcher(initial="preview-file") ensures file mode is shown on launch, not a blank DirectoryList
- app.get_screen("main").core.fs access pattern used in workers instead of storing ProbeFS reference on PreviewPane — keeps widget decoupled from screen initialization order
- Syntax(text, lexer=...) over Syntax.from_path() — from_path() bypasses the ProbeFS FAL boundary and 512KB size cap
- rich.console.Group used to compose Syntax renderable with truncation notice text (Static.update() accepts only one renderable)
- Exception guard around Syntax construction falls back to lexer="text" for unknown extensions

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- PREV-01 and PREV-02 complete — syntax-highlighted file preview and directory listing in preview pane both working
- PreviewPane is ready for 06-04 (CSS/layout integration) and final phase wiring
- CursorChanged interface unchanged — MainScreen.py integration requires no modifications

## Self-Check: PASSED

- FOUND: src/probefs/widgets/preview_pane.py
- FOUND: commit c4c5e51

---
*Phase: 06-preview-pane-and-status-bar*
*Completed: 2026-03-09*
