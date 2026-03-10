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


def sftp_hosts_path() -> Path:
    """Return path to SFTP connection profiles: ~/.probefs/sftp_hosts.yaml"""
    return Path.home() / ".probefs" / "sftp_hosts.yaml"


def load_sftp_hosts() -> list[dict]:
    """Load saved SFTP connection profiles. Returns [] on any error."""
    path = sftp_hosts_path()
    if not path.exists():
        return []
    yaml = YAML()
    try:
        data = yaml.load(path)
        return data if isinstance(data, list) else []
    except YAMLError:
        return []


def save_sftp_host(host: str, port: int, username: str, key_path: str = "") -> None:
    """Save or update an SFTP connection profile. Never stores passwords.

    Uses "username@host" as the profile name. Updates existing entry if
    host+username match, otherwise appends. Silent on write errors.
    """
    hosts = load_sftp_hosts()
    name = f"{username}@{host}"
    for entry in hosts:
        if entry.get("host") == host and entry.get("username") == username:
            entry["port"] = port
            entry["key_path"] = key_path
            break
    else:
        hosts.append({"name": name, "host": host, "port": port,
                      "username": username, "key_path": key_path})
    try:
        yaml = YAML()
        with open(sftp_hosts_path(), "w", encoding="utf-8") as f:
            yaml.dump(hosts, f)
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
