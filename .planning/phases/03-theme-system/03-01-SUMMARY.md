---
phase: 03-theme-system
plan: "01"
subsystem: theme
tags: [textual, theme, yaml, validation, ruamel-yaml, color-parsing, tdd]

# Dependency graph
requires:
  - phase: 01-core-scaffold-and-async-architecture
    provides: project scaffold, pyproject.toml, ruamel-yaml dependency
provides:
  - ThemeLoader class: load(path), load_from_string(content), _validate(data), _build_theme(data)
  - ThemeValidationError exception with errors list and path attributes
  - COLOR_FIELDS tuple (11 fields) as public constant
  - src/probefs/theme/ sub-package exportable as probefs.theme
affects:
  - 03-02 (built-in themes use ThemeLoader.load_from_string)
  - 03-03 (app startup wires ThemeLoader.load for custom theme_file config)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Validate-then-construct: ThemeLoader._validate() collects all errors before Theme() construction"
    - "Per-call YAML() instance: never module-level (ruamel.yaml is not thread-safe)"
    - "Collect-all errors pattern: append to list, raise once — never fail-fast on first error"

key-files:
  created:
    - src/probefs/theme/__init__.py
    - src/probefs/theme/loader.py
    - tests/test_theme_loader.py
  modified: []

key-decisions:
  - "ThemeLoader is the ONLY place in the codebase that constructs Theme(...) — enforced by design"
  - "Color.parse() called for every COLOR_FIELD present in data (not just required ones)"
  - "ThemeValidationError collects ALL errors before raising (not fail-fast) — user fixes all problems at once"
  - "Metadata fields (author, description, version) silently accepted in YAML but not stored in Theme"
  - "YAML() instance created per-call in load() and load_from_string() — thread safety requirement"

patterns-established:
  - "Validate-then-construct: _validate() -> list[str] then _build_theme() only if empty"
  - "Error accumulation: errors: list[str] = []; errors.append(...); return errors"

requirements-completed:
  - THEME-02
  - THEME-04

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 3 Plan 01: ThemeLoader Summary

**ThemeValidationError + ThemeLoader with Color.parse validation using collect-all-errors pattern — enforces THEME-02 and THEME-04 by being the sole Theme construction gateway**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T14:57:48Z
- **Completed:** 2026-03-09T14:59:54Z
- **Tasks:** 3 (RED + GREEN + verify)
- **Files modified:** 3

## Accomplishments

- ThemeValidationError exception class with `errors: list[str]` attribute and `path` attribute; formatted bullet-list message
- ThemeLoader with four classmethods: `load(path)`, `load_from_string(content, source_label)`, `_validate(data)`, `_build_theme(data)`
- Collect-all-errors validation: calls `Color.parse()` for all 11 COLOR_FIELDS, checks required fields, validates `dark` bool type — raises once with complete error list
- 45 tests: RED commit (all failing), GREEN commit (all 45 passing), full regression suite (99/99 passing)

## Task Commits

Each task was committed atomically:

1. **RED: Failing tests for ThemeLoader** - `43baa20` (test)
2. **GREEN: ThemeLoader implementation** - `2313fa0` (feat)

_TDD plan: two commits (test → feat). No REFACTOR cycle needed — implementation was clean as written._

## Files Created/Modified

- `src/probefs/theme/__init__.py` - Package marker; exports ThemeLoader and ThemeValidationError from .loader
- `src/probefs/theme/loader.py` - ThemeValidationError, ThemeLoader, COLOR_FIELDS, REQUIRED_FIELDS
- `tests/test_theme_loader.py` - 45-test pytest suite covering validation, construction, file I/O, error accumulation

## Decisions Made

- ThemeLoader is the ONLY place in the codebase that constructs `Theme(...)` — this is enforced by design, not convention
- `Color.parse()` called for every COLOR_FIELD present in data (not just required ones) — optional fields get validated too
- `ThemeValidationError` collects ALL errors before raising — user sees all problems at once, not just the first
- Metadata fields (`author`, `description`, `version`) silently accepted in YAML but not stored in Theme — forward-compatible with future metadata display
- `YAML()` instance created per-call in `load()` and `load_from_string()` — ruamel.yaml is not thread-safe at module level

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `ThemeLoader` and `ThemeValidationError` are importable from `probefs.theme`
- `load_from_string()` is ready for 03-02 (built-in theme YAML loading via importlib.resources)
- `load()` is ready for 03-03 (custom theme file loading from user config)
- `COLOR_FIELDS` tuple exported for any future introspection needs

---
*Phase: 03-theme-system*
*Completed: 2026-03-09*
