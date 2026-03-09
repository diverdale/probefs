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
