---
phase: 03-theme-system
plan: "02"
subsystem: ui
tags: [textual, themes, importlib-resources, ruamel-yaml, platformdirs, yaml]

requires:
  - phase: 03-01
    provides: ThemeLoader and ThemeValidationError for loading and validating YAML theme files

provides:
  - Three built-in theme YAML files (probefs-dark, probefs-light, probefs-tokyo-night) as package data
  - load_all_builtin_themes() loading all three via importlib.resources without file paths
  - BUILTIN_THEME_NAMES list of the three theme name strings
  - load_config() reading probefs.yaml from platform config directory via platformdirs
  - config_path() returning the platform-specific config file path

affects: [03-03-theme-system, 04-config-infrastructure]

tech-stack:
  added: [platformdirs (transitive dep, now used directly)]
  patterns:
    - importlib.resources.files() for package data access (requires __init__.py in themes/)
    - New YAML() instance per load_config() call (thread-safety)
    - Silent empty-dict fallback for missing or malformed config (never crash on startup)
    - probefs-* naming convention for all built-in themes

key-files:
  created:
    - src/probefs/themes/__init__.py
    - src/probefs/themes/dark.yaml
    - src/probefs/themes/light.yaml
    - src/probefs/themes/tokyo-night.yaml
    - src/probefs/theme/builtin.py
    - src/probefs/config.py
  modified: []

key-decisions:
  - "probefs-tokyo-night defined as own YAML (not aliasing Textual's tokyo-night) — keeps all themes under probefs-* convention"
  - "config.py is Phase 3 minimal: returns plain dict, Phase 4 extends same module by reading more keys"
  - "YAML() instance created per load_config() call (never module-level) — ruamel.yaml is not thread-safe"
  - "load_config() returns {} for malformed YAML — never raises, never crashes app startup on config typo"

patterns-established:
  - "Package data pattern: src/probefs/themes/__init__.py required for importlib.resources.files('probefs.themes')"
  - "All built-in themes accessible via load_all_builtin_themes() — no file paths, works in wheel/editable/zip"
  - "Config access pattern: load_config() once at App.__init__, pass dict downstream — never re-read at runtime"

requirements-completed: [THEME-03, THEME-04]

duration: 3min
completed: 2026-03-09
---

# Phase 3 Plan 02: Built-in Themes and Config Foundation Summary

**Three built-in YAML themes (dark/light/tokyo-night) loadable via importlib.resources plus minimal platformdirs-backed config.py that silently falls back to empty dict on any file error**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-09T14:57:48Z
- **Completed:** 2026-03-09T15:01:14Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Three built-in YAML themes ship as package data with full metadata (name, author, description, version) and all 10 color fields
- `load_all_builtin_themes()` loads all three Theme objects via `importlib.resources.files()` with no file path dependencies
- `config.py` provides `load_config() -> dict` and `config_path() -> Path` as minimal Phase 3 foundation; Phase 4 extends same module

## Task Commits

Each task was committed atomically:

1. **Task 1: Built-in theme YAML package and builtin.py loader** - `1261a30` (feat)
2. **Task 2: Minimal config.py for Phase 3** - `d560d7c` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `src/probefs/themes/__init__.py` - Empty package marker required for importlib.resources.files('probefs.themes')
- `src/probefs/themes/dark.yaml` - probefs-dark default dark theme
- `src/probefs/themes/light.yaml` - probefs-light default light theme
- `src/probefs/themes/tokyo-night.yaml` - probefs-tokyo-night based on Tokyo Night color palette
- `src/probefs/theme/builtin.py` - load_all_builtin_themes() and BUILTIN_THEME_NAMES exports
- `src/probefs/config.py` - load_config() and config_path() functions

## Decisions Made
- `probefs-tokyo-night` is defined as its own YAML file rather than aliasing Textual's built-in `tokyo-night` — keeps all probefs themes under the `probefs-*` convention and makes the scheme self-documented in YAML
- `config.py` is intentionally minimal (plain dict return) so Phase 4 can extend it by reading additional keys without modifying the return signature
- `YAML()` instance created per `load_config()` call, never module-level — ruamel.yaml parser holds state and is not thread-safe

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Executed 03-01 prerequisite before 03-02**
- **Found during:** Execution start
- **Issue:** `src/probefs/theme/` package didn't exist; `builtin.py` imports `ThemeLoader` from `probefs.theme.loader`; 03-02 cannot be verified without 03-01
- **Fix:** Verified 03-01 had been partially completed (tests and loader.py committed in prior run at `2313fa0`); confirmed all 45 tests GREEN; recorded missing commits; proceeded with 03-02
- **Files modified:** None (03-01 was already complete)
- **Verification:** `uv run pytest tests/test_theme_loader.py` passed 45/45 before starting 03-02 tasks
- **Committed in:** `2313fa0` (prior run feat commit)

---

**Total deviations:** 1 (prerequisite plan already complete, no new work needed)
**Impact on plan:** 03-02 tasks executed cleanly after confirming 03-01 was in GREEN state. No scope creep.

## Issues Encountered
None beyond the prerequisite detection above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 03-03 can wire themes into `ProbeFSApp`: register via `load_all_builtin_themes()`, read config via `load_config()`, activate with `app.theme = config.get('theme', 'probefs-dark')`
- All 99 existing tests pass — no regressions

## Self-Check: PASSED

- FOUND: src/probefs/themes/__init__.py
- FOUND: src/probefs/themes/dark.yaml
- FOUND: src/probefs/themes/light.yaml
- FOUND: src/probefs/themes/tokyo-night.yaml
- FOUND: src/probefs/theme/builtin.py
- FOUND: src/probefs/config.py
- FOUND: .planning/phases/03-theme-system/03-02-SUMMARY.md
- FOUND commit: 1261a30 (feat: built-in theme YAML package and builtin.py loader)
- FOUND commit: d560d7c (feat: minimal config.py for Phase 3 theme configuration)

---
*Phase: 03-theme-system*
*Completed: 2026-03-09*
