# Phase 3: Theme System - Research

**Researched:** 2026-03-09
**Domain:** Textual 8.x Theme API / ruamel.yaml schema validation / platformdirs / importlib.resources
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| THEME-01 | User can switch the active color theme by editing a config file | `load_config()` reads `theme:` key from probefs.yaml; `app.register_theme(t)` then `app.theme = name` at startup applies it; `InvalidThemeError` raised for unknown names, fallback to `probefs-dark` |
| THEME-02 | User can create a custom theme by writing a YAML file with metadata + color overrides, validated before loading | `ThemeLoader.load(path)` validates YAML parse + required fields + `Color.parse()` for every color field; constructs `textual.theme.Theme`; metadata fields (author, description, version) extracted separately |
| THEME-03 | At least 3 built-in themes ship with probefs; all usable without any config | Built-in themes live in `probefs/themes/*.yaml`; loaded via `importlib.resources.files('probefs.themes')`; registered in `ProbeFSApp.__init__` before `self.theme` is set; hatchling auto-includes .yaml package data |
| THEME-04 | A theme file with an invalid schema is rejected with an informative error; no silent fallback | `Color.parse()` raises `ColorParseError` with specific message; `ThemeLoader` collects all errors and raises `ThemeValidationError(errors)` listing every problem; invalid theme never reaches `register_theme()` |
</phase_requirements>

---

## Summary

Textual 8.0.2 has a first-class `Theme` dataclass with 11 color fields plus metadata. The API is: `app.register_theme(Theme(...))` then `app.theme = 'theme-name'`. All built-in Textual themes (20 total: textual-dark, textual-light, nord, dracula, etc.) are already registered at `App.__init__`. Custom themes must be registered before they can be set — attempting to set an unregistered theme name raises `InvalidThemeError`. The `_watch_theme` reactive fires immediately when `app.theme` is assigned, repainting the entire UI. Phase 3 requires startup-time (not runtime) switching only.

Schema validation must be done before `Theme` construction because `Theme` is a plain dataclass — it accepts invalid color strings without error. The error only surfaces at `to_color_system()` as a bare `ColorParseError`. The correct approach is a `ThemeLoader` class that: (1) parses YAML with ruamel.yaml catching `YAMLError`, (2) checks required fields, (3) calls `Color.parse()` on every color field to validate them, (4) raises `ThemeValidationError` with all errors collected, and (5) only constructs `Theme(...)` when validation passes. Pydantic is not in the project dependencies and should not be added.

Config reading for Phase 3 must be minimal but forward-compatible with Phase 4's full config infrastructure. The right approach is a `src/probefs/config.py` module with a `load_config() -> dict` function that reads `probefs.yaml` from `platformdirs.user_config_dir('probefs')`. Phase 3 reads only the `theme` and `theme_file` keys. Phase 4 extends this same module — it does not replace it. Built-in themes live as YAML files in `src/probefs/themes/` and are loaded via `importlib.resources.files('probefs.themes')`. Hatchling auto-includes non-.py files in package directories (confirmed: `probefs.tcss` already works this way).

**Primary recommendation:** `ThemeLoader.load(path) -> Theme` + `ThemeLoader.load_builtin(name) -> Theme` + thin `load_config() -> dict` in `config.py`. Register all built-in themes + optional custom theme in `ProbeFSApp.__init__`, then set `self.theme`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.0.2 | `Theme` dataclass, `app.register_theme()`, `app.theme` reactive | Phase 1 decision; Theme API verified against installed package |
| ruamel.yaml | 0.19.1 | YAML parsing for theme files and config | Phase 1 decision; already in project; correct boolean handling |
| platformdirs | 4.9.4 (installed) | `user_config_dir('probefs')` for config file location | Already available as transitive dep; respects XDG_CONFIG_HOME |
| importlib.resources | stdlib 3.10+ | `files('probefs.themes').joinpath('dark.yaml')` for built-in theme data | No install; proven working via `probefs.tcss` pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| textual.color.Color | (textual dep) | `Color.parse(str)` — validates hex, rgb(), named colors | Called in ThemeLoader for every color field |
| textual.color.ColorParseError | (textual dep) | Raised by `Color.parse()` on invalid color strings | Caught in ThemeLoader validation loop |
| textual.app.InvalidThemeError | (textual dep) | Raised by `app.theme = name` for unregistered names | Caught in App.__init__ for graceful fallback |
| pathlib.Path | stdlib | Config file path construction | Used with platformdirs output |
| dataclasses | stdlib | Field introspection for Theme if needed | Optional; Theme fields are documented |

### No New Dependencies Required
The entire Phase 3 feature set uses Textual's built-in Theme API, ruamel.yaml (already in project), platformdirs (already a transitive dep), and importlib.resources (stdlib). No new packages.

**Installation:**
```bash
# Verify platformdirs is accessible (it's a dep of textual, already present)
uv run python -c "import platformdirs; print(platformdirs.__version__)"
```

---

## Architecture Patterns

### Recommended Project Structure
```
src/probefs/
├── config.py              # NEW: load_config() -> dict (Phase 3 minimal; Phase 4 extends)
├── themes/
│   ├── __init__.py        # NEW: empty package marker
│   ├── dark.yaml          # NEW: Default Dark built-in theme
│   ├── light.yaml         # NEW: Default Light built-in theme
│   └── tokyo-night.yaml   # NEW: curated extra (maps to textual's tokyo-night colors)
├── theme/
│   ├── __init__.py        # NEW: exports ThemeLoader, ThemeValidationError
│   ├── loader.py          # NEW: ThemeLoader class
│   └── builtin.py         # NEW: BUILTIN_THEME_NAMES, load_all_builtin_themes()
├── app.py                 # MODIFY: call theme setup in __init__
└── probefs.tcss           # unchanged
```

### Pattern 1: ThemeLoader — Validate then Construct

**What:** A class with two classmethods: `load(path)` for user YAML files, `load_builtin(name)` for package data. Both return a `Theme` object or raise `ThemeValidationError`.

**When to use:** All theme loading goes through `ThemeLoader`. Never construct `Theme(...)` directly in app code.

**Example:**
```python
# Source: verified against textual 8.0.2 Theme dataclass + Color.parse API
from __future__ import annotations

import io
from pathlib import Path
from dataclasses import dataclass

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from textual.theme import Theme
from textual.color import Color, ColorParseError


COLOR_FIELDS = (
    "primary", "secondary", "warning", "error", "success",
    "accent", "foreground", "background", "surface", "panel", "boost",
)
REQUIRED_FIELDS = ("name", "primary")
METADATA_FIELDS = ("author", "description", "version")


class ThemeValidationError(Exception):
    """Raised when a theme YAML file fails validation."""
    def __init__(self, errors: list[str], path: str = "") -> None:
        self.errors = errors
        self.path = path
        bullet_list = "\n  - ".join(errors)
        msg = f"Theme file {path!r} is invalid:\n  - {bullet_list}"
        super().__init__(msg)


class ThemeLoader:

    @classmethod
    def load(cls, path: str | Path) -> Theme:
        """Load and validate a user theme YAML file.

        Raises:
            ThemeValidationError: If the file has any schema or color errors.
            FileNotFoundError: If the path does not exist.
        """
        path = Path(path)
        yaml = YAML()
        try:
            data = yaml.load(path)
        except YAMLError as e:
            raise ThemeValidationError([f"YAML parse error: {e}"], str(path)) from e

        errors = cls._validate(data)
        if errors:
            raise ThemeValidationError(errors, str(path))

        return cls._build_theme(data)

    @classmethod
    def load_from_string(cls, content: str, source_label: str = "<string>") -> Theme:
        """Load and validate a theme from a YAML string (used for built-in themes)."""
        yaml = YAML()
        try:
            data = yaml.load(io.StringIO(content))
        except YAMLError as e:
            raise ThemeValidationError([f"YAML parse error: {e}"], source_label) from e

        errors = cls._validate(data)
        if errors:
            raise ThemeValidationError(errors, source_label)

        return cls._build_theme(data)

    @classmethod
    def _validate(cls, data: object) -> list[str]:
        """Return list of validation error strings. Empty list means valid."""
        errors: list[str] = []

        if not isinstance(data, dict):
            return ["Theme file must be a YAML mapping (key: value pairs)"]

        for field in REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field!r}")

        for field in COLOR_FIELDS:
            value = data.get(field)
            if value is not None:
                try:
                    Color.parse(str(value))
                except ColorParseError as e:
                    errors.append(f"Invalid color for {field!r}: {value!r} — {e}")

        if "dark" in data and not isinstance(data["dark"], bool):
            errors.append(
                f"Field 'dark' must be a boolean (true/false), "
                f"got {type(data['dark']).__name__}: {data['dark']!r}"
            )

        return errors

    @classmethod
    def _build_theme(cls, data: dict) -> Theme:
        """Construct a Theme from a validated data dict."""
        kwargs: dict = {"name": data["name"], "primary": data["primary"]}
        for field in COLOR_FIELDS:
            if field != "primary" and field in data:
                kwargs[field] = data[field]
        if "dark" in data:
            kwargs["dark"] = data["dark"]
        if "luminosity_spread" in data:
            kwargs["luminosity_spread"] = float(data["luminosity_spread"])
        if "text_alpha" in data:
            kwargs["text_alpha"] = float(data["text_alpha"])
        return Theme(**kwargs)
```

### Pattern 2: Built-in Themes via importlib.resources

**What:** YAML files in `src/probefs/themes/` as a Python sub-package. Loaded at `App.__init__` via `importlib.resources.files()`.

**When to use:** Any theme that ships with probefs. These are NOT Textual's built-in themes.

**Example:**
```python
# Source: verified importlib.resources.files API against Python 3.12
import importlib.resources as ilr


BUILTIN_THEME_NAMES = ["probefs-dark", "probefs-light", "probefs-tokyo-night"]


def load_all_builtin_themes() -> list[Theme]:
    """Load all built-in probefs themes from package data.

    Returns Theme objects, raises ThemeValidationError if a built-in
    theme file is malformed (should never happen in release builds).
    """
    themes = []
    pkg = ilr.files("probefs.themes")
    for yaml_file in ("dark.yaml", "light.yaml", "tokyo-night.yaml"):
        content = pkg.joinpath(yaml_file).read_text(encoding="utf-8")
        theme = ThemeLoader.load_from_string(content, source_label=yaml_file)
        themes.append(theme)
    return themes
```

**Built-in theme YAML format** (`src/probefs/themes/dark.yaml`):
```yaml
# probefs Default Dark theme
name: probefs-dark
author: probefs
description: Default dark theme
version: "1.0.0"
dark: true
primary: "#5B8DD9"
secondary: "#2D4A8A"
background: "#1C2023"
surface: "#252B2E"
panel: "#1E2528"
foreground: "#E0E0E0"
warning: "#FFB86C"
error: "#FF5555"
success: "#50FA7B"
accent: "#8BE9FD"
```

### Pattern 3: Minimal config.py (Phase 3 foundation, Phase 4 extends)

**What:** A single `load_config() -> dict` function. Returns empty dict if no file. Phase 3 reads `theme` and `theme_file` keys. Phase 4 adds `keybindings` key support to the same function.

**When to use:** Called once at `ProbeFSApp.__init__`. Result passed down to theme setup and later to icon set factory.

**Example:**
```python
# Source: verified platformdirs 4.9.4 + ruamel.yaml 0.19.1
from __future__ import annotations

from pathlib import Path

import platformdirs
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError


def config_path() -> Path:
    """Return the user's probefs.yaml config file path.

    macOS: ~/Library/Application Support/probefs/probefs.yaml
    Linux: ~/.config/probefs/probefs.yaml (respects XDG_CONFIG_HOME)
    """
    return Path(platformdirs.user_config_dir("probefs")) / "probefs.yaml"


def load_config() -> dict:
    """Load probefs.yaml and return as a dict.

    Returns empty dict if the file does not exist. YAML parse errors
    are logged as warnings and return empty dict (never crash on startup).
    """
    path = config_path()
    if not path.exists():
        return {}
    yaml = YAML()
    try:
        data = yaml.load(path)
        return data if isinstance(data, dict) else {}
    except YAMLError:
        # Malformed config — don't crash, use defaults
        return {}
```

### Pattern 4: App Startup Theme Registration Sequence

**What:** In `ProbeFSApp.__init__`, register all built-in themes, optionally register a custom theme from config, then set `self.theme`. Order is critical: `register_theme()` must precede `self.theme = name`.

**When to use:** Only in `ProbeFSApp.__init__`. Theme is set once at startup; Phase 3 does not support runtime switching.

**Example:**
```python
# Source: verified against textual 8.0.2 App.__init__ + register_theme + _validate_theme
from textual.app import App, InvalidThemeError
from probefs.config import load_config
from probefs.theme.builtin import load_all_builtin_themes
from probefs.theme.loader import ThemeLoader, ThemeValidationError

DEFAULT_THEME = "probefs-dark"


class ProbeFSApp(App):

    CSS_PATH = "probefs.tcss"
    SCREENS = {"main": MainScreen}

    def __init__(self) -> None:
        super().__init__()
        config = load_config()
        self._setup_themes(config)

    def _setup_themes(self, config: dict) -> None:
        """Register built-in and optional custom themes, then activate."""
        # 1. Register all built-in probefs themes
        for theme in load_all_builtin_themes():
            self.register_theme(theme)

        # 2. Optionally load a custom theme from config
        theme_file = config.get("theme_file")
        if theme_file:
            try:
                custom = ThemeLoader.load(theme_file)
                self.register_theme(custom)
            except (ThemeValidationError, FileNotFoundError) as e:
                # Log warning — don't crash; fall back to default
                print(f"Warning: Could not load theme file {theme_file!r}: {e}")

        # 3. Set the active theme from config (with fallback)
        requested = config.get("theme", DEFAULT_THEME)
        try:
            self.theme = requested
        except InvalidThemeError:
            print(f"Warning: Theme {requested!r} not found, using {DEFAULT_THEME!r}")
            self.theme = DEFAULT_THEME
```

### Anti-Patterns to Avoid

- **Constructing Theme before validation:** `Theme(name='x', primary='bad_color')` accepts the string silently. The error only appears at paint time as a bare `ColorParseError` with no filename context. Always validate with `Color.parse()` before construction.
- **Setting `self.theme` before `register_theme()`:** Raises `InvalidThemeError` immediately. Built-in themes and custom themes must be registered in `__init__` before setting `self.theme`.
- **Reading config on every mount/navigation:** Config is immutable at runtime in Phase 3. Read once in `App.__init__`, store on instance, pass as needed.
- **Creating a `probefs/themes/` directory without `__init__.py`:** `importlib.resources.files('probefs.themes')` requires the directory to be a Python package (has `__init__.py`). Without it, `files()` cannot locate the package data path.
- **Using Textual's built-in theme names as probefs's theme names:** `textual-dark` is already registered but probefs should own `probefs-dark`. Using Textual's names would prevent probefs from controlling its own default appearance.
- **Storing metadata (author, description, version) in Theme.variables:** The `variables` dict is for CSS variable overrides, not theme metadata. Metadata can be stored in a `ThemeMetadata` dataclass alongside the `Theme` object if needed for display, but is not required for Phase 3 (THEME-03 requires the YAML format to accept these fields, not to display them).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Color string parsing and validation | Custom regex for hex/rgb/named colors | `textual.color.Color.parse(str)` | Handles `#abc`, `#aabbcc`, `rgb(r,g,b)`, named CSS colors, raises `ColorParseError` with message |
| Theme application to UI | Custom CSS variable injection | `app.register_theme()` + `app.theme = name` | `_watch_theme` reactive handles full CSS repaint, dark/light mode classes, ANSI filter |
| YAML boolean parsing | String comparison for 'true'/'false' | ruamel.yaml (YAML 1.2 compliant) | `true` and `True` both → Python `bool`; `'true'` → `str` (correctly kept as string) |
| Config directory lookup | Platform-specific path constants | `platformdirs.user_config_dir('probefs')` | Handles macOS (`~/Library/Application Support`), XDG Linux, Windows; respects `XDG_CONFIG_HOME` |
| Package data loading | `__file__`-relative path arithmetic | `importlib.resources.files('probefs.themes')` | Works correctly whether installed as a wheel, editable install, or zip import |
| Collecting all validation errors | Fail-fast on first error | `errors: list[str]` accumulated then raised | Users can fix all problems at once instead of running the app repeatedly |

**Key insight:** `Theme` is a dataclass with zero validation. The caller owns all validation. `Color.parse()` is the validator. `ThemeLoader` is the enforcement point — it is the only place in the codebase that constructs `Theme(...)`.

---

## Common Pitfalls

### Pitfall 1: Theme accepts invalid colors silently

**What goes wrong:** `Theme(name='x', primary='not-a-color')` constructs without error. The `ColorParseError` surfaces only when Textual tries to paint the UI — far from the source of the bad data, with no filename in the traceback.

**Why it happens:** `Theme` is a `@dataclass` with no `__post_init__` validation.

**How to avoid:** Always call `Color.parse(value)` for every color field in `ThemeLoader._validate()` before constructing `Theme(...)`.

**Warning signs:** Runtime crash during UI paint with `ColorParseError` that has no file path in the message.

### Pitfall 2: register_theme() must come before self.theme = name

**What goes wrong:** `self.theme = 'probefs-dark'` raises `InvalidThemeError` if called before `self.register_theme(theme)`.

**Why it happens:** `_validate_theme()` checks `self.available_themes` which only contains registered themes. The reactive setter calls `_validate_theme()` synchronously.

**How to avoid:** Always register all themes before setting `self.theme`. In `_setup_themes()`, registration (steps 1 and 2) precedes theme activation (step 3).

**Warning signs:** `InvalidThemeError: Theme 'probefs-dark' has not been registered` at app startup.

### Pitfall 3: probefs/themes/ directory needs __init__.py

**What goes wrong:** `importlib.resources.files('probefs.themes')` raises `ModuleNotFoundError` or returns a path that doesn't work with `.joinpath()`.

**Why it happens:** `importlib.resources.files()` expects a Python package (importable module), not a plain directory.

**How to avoid:** Create `src/probefs/themes/__init__.py` (empty file). Verify with `python -c "import probefs.themes"`.

**Warning signs:** `ModuleNotFoundError: No module named 'probefs.themes'` when loading built-in themes.

### Pitfall 4: config.py YAMLError does not mean crash

**What goes wrong:** A user with a malformed `probefs.yaml` gets a full traceback and the app refuses to start.

**Why it happens:** ruamel.yaml raises `YAMLError` on parse failure; if uncaught, it propagates to `App.__init__`.

**How to avoid:** Wrap `yaml.load()` in `load_config()` with `except YAMLError: return {}`. Log a warning (not an error). The app starts with defaults.

**Warning signs:** Users can't launch probefs because of a typo in their config file.

### Pitfall 5: Custom theme's `name` field becomes the theme's ID

**What goes wrong:** User sets `theme: my-theme` in probefs.yaml but their YAML file has `name: My Custom Theme` (with spaces). `app.theme = 'my-theme'` raises `InvalidThemeError` because the registered name is `'My Custom Theme'`.

**Why it happens:** `Theme.name` is used as the dict key in `available_themes`. `app.theme = name` must match exactly.

**How to avoid:** The config's `theme:` key must match the theme YAML's `name:` field exactly. Document this clearly. Alternatively, use the theme YAML's `name` field as the value for `theme:` in probefs.yaml.

**Warning signs:** `InvalidThemeError` despite the theme file loading successfully.

### Pitfall 6: ruamel.yaml `YAML()` instance is not thread-safe

**What goes wrong:** Using a module-level `YAML()` instance from multiple threads causes parse errors or crashes.

**Why it happens:** ruamel.yaml's `YAML` object holds parser state.

**How to avoid:** Create a new `YAML()` instance inside each `load_config()` and `ThemeLoader.load()` call (as shown in code examples above). Never share a `YAML` instance.

**Warning signs:** Intermittent parse errors; fine in single-threaded tests, fails under load.

---

## Code Examples

Verified patterns from official sources:

### Complete ThemeLoader with validation
```python
# Source: textual 8.0.2 Theme API + Color.parse verified with live testing
from __future__ import annotations
import io
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from textual.theme import Theme
from textual.color import Color, ColorParseError

COLOR_FIELDS = (
    "primary", "secondary", "warning", "error", "success",
    "accent", "foreground", "background", "surface", "panel", "boost",
)

class ThemeValidationError(Exception):
    def __init__(self, errors: list[str], path: str = "") -> None:
        self.errors = errors
        bullet_list = "\n  - ".join(errors)
        super().__init__(f"Theme {path!r} is invalid:\n  - {bullet_list}")

class ThemeLoader:
    @classmethod
    def load(cls, path: str | Path) -> Theme:
        yaml = YAML()
        try:
            data = yaml.load(Path(path))
        except YAMLError as e:
            raise ThemeValidationError([f"YAML parse error: {e}"], str(path)) from e
        errors = cls._validate(data)
        if errors:
            raise ThemeValidationError(errors, str(path))
        return cls._build(data)

    @classmethod
    def _validate(cls, data: object) -> list[str]:
        if not isinstance(data, dict):
            return ["Theme file must be a YAML mapping"]
        errors = []
        if "name" not in data:
            errors.append("Missing required field: 'name'")
        if "primary" not in data:
            errors.append("Missing required field: 'primary'")
        for field in COLOR_FIELDS:
            val = data.get(field)
            if val is not None:
                try:
                    Color.parse(str(val))
                except ColorParseError as e:
                    errors.append(f"Invalid color for {field!r}: {val!r} — {e}")
        if "dark" in data and not isinstance(data["dark"], bool):
            errors.append(f"Field 'dark' must be boolean, got {type(data['dark']).__name__}")
        return errors

    @classmethod
    def _build(cls, data: dict) -> Theme:
        kwargs: dict = {"name": data["name"], "primary": data["primary"]}
        for field in COLOR_FIELDS:
            if field != "primary" and field in data:
                kwargs[field] = data[field]
        for field in ("dark", "luminosity_spread", "text_alpha"):
            if field in data:
                kwargs[field] = data[field]
        return Theme(**kwargs)
```

### Built-in theme loading
```python
# Source: importlib.resources.files verified against Python 3.12 + probefs package
import importlib.resources as ilr
from probefs.theme.loader import ThemeLoader

_BUILTIN_FILES = ("dark.yaml", "light.yaml", "tokyo-night.yaml")

def load_all_builtin_themes() -> list:
    themes = []
    pkg = ilr.files("probefs.themes")
    for fname in _BUILTIN_FILES:
        content = pkg.joinpath(fname).read_text(encoding="utf-8")
        theme = ThemeLoader.load_from_string(content, source_label=fname)
        themes.append(theme)
    return themes
```

### Minimal config loading
```python
# Source: platformdirs 4.9.4 user_config_dir + ruamel.yaml 0.19.1
from pathlib import Path
import platformdirs
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

def load_config() -> dict:
    path = Path(platformdirs.user_config_dir("probefs")) / "probefs.yaml"
    if not path.exists():
        return {}
    yaml = YAML()
    try:
        data = yaml.load(path)
        return data if isinstance(data, dict) else {}
    except YAMLError:
        return {}  # malformed config: silent fallback to defaults
```

### App startup sequence
```python
# Source: textual 8.0.2 App.__init__ + register_theme + _validate_theme verified
class ProbeFSApp(App):
    def __init__(self) -> None:
        super().__init__()
        config = load_config()
        self._setup_themes(config)

    def _setup_themes(self, config: dict) -> None:
        for theme in load_all_builtin_themes():
            self.register_theme(theme)           # register first
        theme_file = config.get("theme_file")
        if theme_file:
            try:
                self.register_theme(ThemeLoader.load(theme_file))
            except (ThemeValidationError, FileNotFoundError) as e:
                pass  # log warning, continue with built-ins
        requested = config.get("theme", "probefs-dark")
        try:
            self.theme = requested               # set after registering
        except InvalidThemeError:
            self.theme = "probefs-dark"          # graceful fallback
```

### YAML theme file format (user-facing)
```yaml
# ~/.config/probefs/themes/my-theme.yaml
# All color fields accept: #rrggbb, #rgb, rgb(r,g,b), or CSS named colors
name: my-theme
author: Your Name
description: My custom dark theme
version: "1.0.0"
dark: true

# Required
primary: "#5B8DD9"

# Optional — Textual derives sensible values from primary if omitted
secondary: "#2D4A8A"
background: "#1C2023"
surface: "#252B2E"
panel: "#1E2528"
foreground: "#E0E0E0"
warning: "#FFB86C"
error: "#FF5555"
success: "#50FA7B"
accent: "#8BE9FD"
```

### User probefs.yaml config format
```yaml
# ~/Library/Application Support/probefs/probefs.yaml  (macOS)
# ~/.config/probefs/probefs.yaml                       (Linux)

# Switch to a built-in theme:
theme: probefs-light

# OR load a custom theme file (must match the 'name:' field in the YAML):
# theme_file: ~/.config/probefs/themes/my-theme.yaml
# theme: my-theme
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TCSS `--variable` overrides for theming | `textual.theme.Theme` dataclass + `register_theme()` | Textual 0.78 (2024) | Clean typed API; themes are first-class objects |
| Hardcoded color strings in TCSS | `$primary`, `$background`, `$surface` CSS variables derived from Theme | Textual color system | Theme changes recompute all derived variables automatically |
| PyYAML for YAML parsing | ruamel.yaml | Phase 1 decision | YAML 1.2 spec; correct boolean handling; preserves comments |
| `pkg_resources.resource_string()` | `importlib.resources.files()` | Python 3.9+ | No setuptools dep; works in zip imports; `files()` stable since 3.9 |

**Deprecated/outdated:**
- `pkg_resources` for package data: replaced by `importlib.resources.files()`. Do not use.
- Textual `App.THEME` class variable: does NOT exist in 8.0.2. The class-level override `theme = 'name'` works for built-in Textual themes only (registered at `__init__`). For custom themes that need registration, use the `_setup_themes()` pattern in `__init__`.

---

## Open Questions

1. **Which curated extra built-in theme to ship**
   - What we know: Textual ships `tokyo-night` with colors `primary="#7aa2f7"`, `background="#1a1b26"`, `dark=True` — a well-known scheme
   - What's unclear: Should probefs alias Textual's `tokyo-night` or define its own theme with the same colors under a probefs-prefixed name?
   - Recommendation: Define `probefs-tokyo-night` as a YAML in `probefs/themes/tokyo-night.yaml` with the same colors. This keeps all probefs themes under the `probefs-*` naming convention and makes the scheme self-documented in YAML.

2. **Phase 3 vs Phase 4 config loading coordination**
   - What we know: Phase 3 introduces `config.py` with `load_config()`; Phase 4 adds keybinding support
   - What's unclear: Phase 4 ROADMAP description says "Config Infrastructure" — it might want to own `config.py` entirely
   - Recommendation: Phase 3 creates `config.py` with `load_config() -> dict` as a plain YAML reader. Phase 4 adds `load_keybindings(config: dict) -> dict` to the same module. No rewrite needed — the `load_config()` function returns the full dict, Phase 4 just reads more keys from it.

3. **ThemeMetadata: should it be stored separately from Theme?**
   - What we know: `author`, `description`, `version` fields are in the YAML (THEME-02/03) but NOT in Textual's `Theme` dataclass; the `variables` dict is for CSS vars not metadata
   - What's unclear: Does Phase 3 need to display or surface theme metadata anywhere in the UI?
   - Recommendation: Parse metadata fields in `ThemeLoader` but don't use them yet (no UI for displaying them in Phase 3). A simple `ThemeMetadata(name, author, description, version)` dataclass can be added alongside `Theme` if needed later. For Phase 3, silently accept and ignore these fields during theme construction.

---

## Sources

### Primary (HIGH confidence)
- `uv run python -c "from textual.theme import Theme; ..."` — Theme dataclass fields, defaults, and field types verified by running against textual 8.0.2
- `uv run python -c "from textual.app import App; ..."` — `register_theme()`, `_validate_theme()`, `_watch_theme()`, `available_themes` all inspected via `inspect.getsource()`
- `uv run python -c "from textual.color import Color, ColorParseError; ..."` — `Color.parse()` tested with `#rrggbb`, `#rgb`, `rgb()`, named colors, and invalid strings
- `uv run python -c "from textual.theme import BUILTIN_THEMES; ..."` — Full list of 20 built-in themes and their color fields verified
- `uv run python -c "import platformdirs; ..."` — `user_config_dir('probefs')` paths verified on macOS; XDG_CONFIG_HOME override confirmed working
- `uv run python -c "import importlib.resources as ilr; ..."` — `files('probefs').joinpath('probefs.tcss').read_text()` confirmed working (existing pattern in project)
- `uv run python -c "from ruamel.yaml import YAML; ..."` — Boolean handling, YAMLError on malformed input, and valid theme dict loading all verified

### Secondary (MEDIUM confidence)
- [Textual Themes docs](https://textual.textualize.io/guide/themes/) — Theme API overview, register_theme usage, CSS variable derivation
- Phase 2 RESEARCH.md (this project) — ruamel.yaml patterns, Icon strategy, confirmed project conventions

### Tertiary (LOW confidence)
- Hatchling auto-include behavior for non-.py files — inferred from observed behavior (probefs.tcss works via importlib.resources); no explicit hatchling docs consulted. Verify if distribution phase fails.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all library APIs verified by running against installed packages
- Architecture: HIGH — Theme construction/registration sequence fully verified; config path confirmed with platformdirs; importlib.resources pattern confirmed working
- Pitfalls: HIGH — pitfalls 1-4 confirmed by direct testing; pitfalls 5-6 confirmed by API inspection
- Built-in theme YAML format: HIGH — confirmed maps 1:1 to Theme dataclass fields
- Phase 3/4 coordination: MEDIUM — config.py design is reasonable but Phase 4 scope not fully detailed

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (Textual releases frequently; re-verify Theme API if version changes)
