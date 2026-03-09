from __future__ import annotations

from pathlib import Path

import platformdirs
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError


def config_path() -> Path:
    """Return the user's probefs.yaml config file path.

    macOS:  ~/Library/Application Support/probefs/probefs.yaml
    Linux:  ~/.config/probefs/probefs.yaml  (respects XDG_CONFIG_HOME)
    Windows: %APPDATA%/probefs/probefs.yaml
    """
    return Path(platformdirs.user_config_dir("probefs")) / "probefs.yaml"


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
