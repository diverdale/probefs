---
phase: 03-theme-system
plan: "03"
subsystem: ui
tags: [textual, themes, yaml, config, probefs-dark, probefs-light, probefs-tokyo-night]

# Dependency graph
requires:
  - phase: 03-01
    provides: ThemeLoader and ThemeValidationError for custom theme_file loading
  - phase: 03-02
    provides: load_all_builtin_themes(), load_config(), built-in theme YAML package

provides:
  - ProbeFSApp._setup_themes() wiring load_config() result into theme registration and activation
  - DEFAULT_THEME constant ("probefs-dark") as module-level fallback
  - InvalidThemeError fallback: unknown theme name logs warning and falls back to probefs-dark
  - ThemeValidationError/FileNotFoundError fallback: invalid or missing theme_file logs warning, uses built-ins
  - Config path at ~/.probefs/probefs.yaml (user-writable, discoverable)

affects: [04-config-infrastructure]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Theme registration order: register all built-ins first, then custom, then set self.theme — registration must precede activation"
    - "load_config() called once in __init__, passed as dict to _setup_themes() — never re-read at runtime"
    - "Graceful fallback chain: invalid theme_file -> warning + continue; unknown theme name -> warning + DEFAULT_THEME"
    - "Config at ~/.probefs/probefs.yaml — user-writable, no helper command needed to locate"

key-files:
  created: []
  modified:
    - src/probefs/app.py
    - src/probefs/config.py

key-decisions:
  - "Registration before activation: all themes registered before self.theme is assigned — Textual requires this ordering"
  - "load_config() called in __init__ (not on_mount) — themes must be active before the TUI event loop starts"
  - "Config path changed to ~/.probefs/probefs.yaml — macOS ~/Library/Application Support is not user-writable by default; ~/.probefs/ is always writable and discoverable without a helper command"
  - "InvalidThemeError caught with warning + fallback — app never crashes on bad theme: key in config"
  - "ThemeValidationError and FileNotFoundError caught separately — different user messages for invalid YAML vs missing file"

patterns-established:
  - "App startup theme pattern: load_config() -> _setup_themes(config) -> themes active before first render"
  - "Fallback safety: two-level protection (custom theme errors + unknown theme name errors) ensures app always launches"

requirements-completed:
  - THEME-01
  - THEME-02
  - THEME-03
  - THEME-04

# Metrics
duration: 13min
completed: 2026-03-09
---

# Phase 3 Plan 03: App Theme Wiring Summary

**ProbeFSApp._setup_themes() connects load_config() and load_all_builtin_themes() at startup — all 3 built-in themes register before activation, unknown themes fall back to probefs-dark, verified visually across all three built-in themes**

## Performance

- **Duration:** 13 min
- **Started:** 2026-03-09T15:03:56Z
- **Completed:** 2026-03-09T15:16:39Z
- **Tasks:** 2 (1 auto + 1 human-verify)
- **Files modified:** 2

## Accomplishments

- `ProbeFSApp.__init__` calls `load_config()` and `_setup_themes(config)` on every launch
- `_setup_themes()` registers all 3 built-in themes via `load_all_builtin_themes()` before `self.theme` is set — enforces research Pitfall 2
- Graceful fallback for invalid/missing `theme_file` (ThemeValidationError, FileNotFoundError) and unknown theme name (InvalidThemeError)
- Config path corrected to `~/.probefs/probefs.yaml` (user-discoverable and always writable)
- Human verification confirmed: probefs-dark, probefs-light, and probefs-tokyo-night all render visually distinct; unknown theme fallback works; custom theme loading works

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire theme setup into ProbeFSApp.__init__** - `b207e9e` (feat)
2. **Config path fix: ~/.probefs/probefs.yaml** - `e6504d8` (fix) — deviation discovered during human verification

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `src/probefs/app.py` - Added `__init__`, `_setup_themes()`, new imports, `DEFAULT_THEME` constant
- `src/probefs/config.py` - Config path corrected to `~/.probefs/probefs.yaml`

## Decisions Made

- `load_config()` called in `__init__` (not `on_mount`) — themes must be active before the TUI event loop starts; `on_mount` would be too late
- Registration order enforced: all built-in themes registered before `self.theme` is set — Textual requires registered themes before activation
- Config path changed from platformdirs to `~/.probefs/probefs.yaml` — macOS `~/Library/Application Support` is not reliably user-writable; `~/.probefs/` is always writable and immediately discoverable

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Config path changed to ~/.probefs/probefs.yaml**
- **Found during:** Task 2 (human verification)
- **Issue:** `platformdirs` returned `~/Library/Application Support/probefs/probefs.yaml` on macOS, which is not user-writable by default; user could not create the config file without elevated permissions or a helper command
- **Fix:** Changed `config_path()` in `src/probefs/config.py` to use `Path.home() / ".probefs" / "probefs.yaml"` — always writable, no helper needed, consistent across platforms
- **Files modified:** `src/probefs/config.py`
- **Verification:** Human confirmed config file created at `~/.probefs/probefs.yaml` and read correctly during theme switching verification
- **Committed in:** `e6504d8` (fix commit, separate from Task 1)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in config path)
**Impact on plan:** Fix was required for human verification to proceed — macOS users could not write the config file. No scope creep; config.py was already within Phase 3 scope.

## Issues Encountered

None beyond the config path deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 3 complete: ThemeLoader, 3 built-in themes, config.py, and ProbeFSApp theme wiring all shipped and verified
- Config at `~/.probefs/probefs.yaml` is the established config location for Phase 4 to extend with additional keys
- `load_config()` returns plain dict — Phase 4 reads additional keys without changing the return signature
- All 99 tests pass with no regressions

## Self-Check: PASSED

- FOUND: src/probefs/app.py (contains _setup_themes, __init__, DEFAULT_THEME)
- FOUND: src/probefs/config.py (updated config path)
- FOUND commit: b207e9e (feat(03-03): wire theme system into ProbeFSApp.__init__)
- FOUND commit: e6504d8 (fix(config): use ~/.probefs/probefs.yaml instead of platformdirs path)
- FOUND: .planning/phases/03-theme-system/03-03-SUMMARY.md (this file)

---
*Phase: 03-theme-system*
*Completed: 2026-03-09*
