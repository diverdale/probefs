---
phase: 02-directory-rendering-and-icon-system
plan: "02"
subsystem: ui
tags: [icons, strategy-pattern, ascii, nerd-fonts, yaml, fsspec, ruamel-yaml]

# Dependency graph
requires:
  - phase: 01-core-scaffold-and-async-architecture
    provides: ProbeFS FAL wrapper with fsspec backend, ruamel.yaml decision established

provides:
  - IconSet ABC strategy interface with get_icon(category) and get_color(category)
  - ASCIIIconSet — default ASCII icon set, no config required
  - NerdIconSet — Nerd Font Unicode glyph set, explicit opt-in only
  - YAMLIconSet — user-supplied YAML theme file with ASCIIIconSet fallback
  - load_icon_set(config) factory function routing to correct implementation
  - ProbeFS.exists(path) FAL-safe method for broken symlink detection

affects:
  - 02-03 (DirectoryList rewrite will consume IconSet and ProbeFS.exists)
  - 02-04 (rendering/columns.py will use load_icon_set and get_category)
  - all future phases that render directory listings

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Strategy pattern for icon/color selection (IconSet ABC + three implementations + factory)
    - FAL boundary enforcement — ProbeFS.exists() wraps fsspec.exists(), widgets never call os.path.exists

key-files:
  created:
    - src/probefs/icons/__init__.py
    - src/probefs/icons/base.py
    - src/probefs/icons/ascii_set.py
    - src/probefs/icons/nerd_set.py
    - src/probefs/icons/yaml_set.py
    - src/probefs/icons/factory.py
  modified:
    - src/probefs/fs/probe_fs.py

key-decisions:
  - "ASCIIIconSet is the unconditional default — load_icon_set({}) returns ASCIIIconSet with no config required"
  - "NerdIconSet requires explicit 'icons: nerd' opt-in — auto-detection is impossible over SSH"
  - "YAMLIconSet uses ruamel.yaml (Phase 1 decision) and falls back to ASCIIIconSet for missing categories"
  - "ProbeFS.exists() added to FAL — widgets must never call os.path.exists directly"
  - "file icon in ASCIIIconSet is a single space character — truthy in Python, safe for bool checks"

patterns-established:
  - "Strategy pattern: IconSet ABC + concrete implementations + factory function"
  - "FAL boundary: all path existence checks go through ProbeFS.exists(), not os.path.exists"
  - "Nerd Font opt-in pattern: config.get('icons') == 'nerd' required, never auto-detected"

requirements-completed:
  - THEME-05
  - THEME-06
  - THEME-07

# Metrics
duration: 1min
completed: 2026-03-09
---

# Phase 2 Plan 02: IconSet Strategy Pattern and ProbeFS.exists() Summary

**IconSet strategy pattern with ASCIIIconSet (default), NerdIconSet (opt-in), YAMLIconSet (YAML theme file), factory function, and ProbeFS.exists() FAL method for broken symlink detection**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-09T14:16:16Z
- **Completed:** 2026-03-09T14:17:45Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Created complete `probefs.icons` package with strategy pattern: IconSet ABC, ASCIIIconSet, NerdIconSet, YAMLIconSet, and load_icon_set factory
- All seven file categories (directory, file, executable, symlink, broken_symlink, archive, image) have icons and colors in both ASCII and Nerd implementations
- Added `ProbeFS.exists()` to maintain FAL boundary — widgets can check path existence without calling os.path.exists directly
- YAMLIconSet loads user-supplied theme file and delegates missing categories to ASCIIIconSet fallback

## Task Commits

Each task was committed atomically:

1. **Task 1: Create icons package with IconSet ABC and three implementations** - `5bdc100` (feat)
2. **Task 2: Create icon factory and add ProbeFS.exists()** - `4875de0` (feat)

**Plan metadata:** `a3dcff6` (docs: complete icon-set strategy pattern plan)

## Files Created/Modified
- `src/probefs/icons/__init__.py` - Package marker
- `src/probefs/icons/base.py` - IconSet ABC with get_icon/get_color abstract methods
- `src/probefs/icons/ascii_set.py` - ASCIIIconSet with ASCII symbols, safe for all terminals
- `src/probefs/icons/nerd_set.py` - NerdIconSet with Nerd Font Unicode codepoints (U+E000+)
- `src/probefs/icons/yaml_set.py` - YAMLIconSet loading from ruamel.yaml, fallback to ASCIIIconSet
- `src/probefs/icons/factory.py` - load_icon_set(config) factory routing to correct implementation
- `src/probefs/fs/probe_fs.py` - Added exists() method delegating to self._fs.exists(path)

## Decisions Made
- ASCIIIconSet is the unconditional default — load_icon_set({}) returns ASCIIIconSet with no config required
- NerdIconSet requires explicit `icons: nerd` opt-in — auto-detection is impossible over SSH
- YAMLIconSet uses ruamel.yaml (established Phase 1 decision) and falls back to ASCIIIconSet for missing categories
- ProbeFS.exists() added to FAL now rather than later — low effort, correct from the start, prevents future SFTP breakage
- The "file" category ASCII icon is a single space character — truthy in Python (non-empty string), safe for bool checks in verification

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- IconSet strategy pattern fully implemented and verified
- ProbeFS.exists() available for use in rendering/categorization code
- Ready for 02-03 (DirectoryList rewrite using DataTable) which consumes IconSet and ProbeFS.exists()
- Ready for 02-04 (rendering/columns.py build_row() and get_category()) which uses load_icon_set and IconSet.get_icon/get_color

## Self-Check: PASSED

- FOUND: src/probefs/icons/__init__.py
- FOUND: src/probefs/icons/base.py
- FOUND: src/probefs/icons/ascii_set.py
- FOUND: src/probefs/icons/nerd_set.py
- FOUND: src/probefs/icons/yaml_set.py
- FOUND: src/probefs/icons/factory.py
- FOUND: src/probefs/fs/probe_fs.py (modified)
- FOUND: commit 5bdc100 (Task 1)
- FOUND: commit 4875de0 (Task 2)
- FOUND: commit a3dcff6 (metadata)

---
*Phase: 02-directory-rendering-and-icon-system*
*Completed: 2026-03-09*
