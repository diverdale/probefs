from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError


def config_path() -> Path:
    """Return the user's probefs.yaml config file path.

    ~/.probefs/probefs.yaml on all platforms.
    """
    return Path.home() / ".probefs" / "probefs.yaml"


def themes_dir() -> Path:
    """Return the user themes directory: ~/.probefs/themes/"""
    return Path.home() / ".probefs" / "themes"


_DEFAULT_CONFIG = """\
# probefs configuration
# https://github.com/diverdale/probefs/blob/master/docs/USER_GUIDE.md

# Theme — built-in options: probefs-dark, probefs-light, probefs-tokyo-night
# Drop custom themes in ~/.probefs/themes/ and reference them by name here.
theme: probefs-dark

# theme_file: ~/path/to/custom-theme.yaml  # overrides theme: above

# Icons — ascii (default, works everywhere) or nerd (requires Nerd Fonts)
icons: ascii

# Keybinding overrides — action ID: "key" or "key1,key2"
# Full action ID list: https://github.com/diverdale/probefs/blob/master/docs/USER_GUIDE.md
# keybindings:
#   probefs.cursor_down: "j"
#   probefs.quit: "q,ctrl+c"
"""


def init_config_dir() -> None:
    """Create ~/.probefs/ skeleton on first launch if it does not exist.

    Creates:
      ~/.probefs/               — config directory
      ~/.probefs/themes/        — user theme drop-in directory
      ~/.probefs/probefs.yaml   — commented default config (only if absent)

    Safe to call on every launch — all operations are no-ops if targets exist.
    Never raises; failures are silently ignored so a permissions issue never
    prevents probefs from starting.
    """
    try:
        config_path().parent.mkdir(parents=True, exist_ok=True)
        themes_dir().mkdir(parents=True, exist_ok=True)
        cfg = config_path()
        if not cfg.exists():
            cfg.write_text(_DEFAULT_CONFIG, encoding="utf-8")
    except OSError:
        pass


def load_config() -> dict:
    """Load probefs.yaml and return as a plain dict.

    Returns empty dict if the file does not exist (first-launch default).
    Returns empty dict if YAML is malformed (silent fallback — never crash
    on startup due to a config typo). Phase 4 extends this function to read
    the 'keybindings' key without modifying this return behavior.

    Phase 3 callers read:
      config.get('theme')       -> str | None  (theme name to activate)
      config.get('theme_file')  -> str | None  (path to custom theme YAML)
    """
    path = config_path()
    if not path.exists():
        return {}
    yaml = YAML()  # new instance per call — YAML() is not thread-safe
    try:
        data = yaml.load(path)
        return data if isinstance(data, dict) else {}
    except YAMLError:
        # Malformed config: return defaults, do not crash
        # Phase 4 may add logging here
        return {}
