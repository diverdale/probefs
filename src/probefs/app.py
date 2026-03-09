"""ProbeFSApp — Textual application entry point for probefs."""
from __future__ import annotations

from textual.app import App, InvalidThemeError
from textual.binding import Binding

from probefs.config import load_config
from probefs.screens.main import MainScreen
from probefs.theme.builtin import load_all_builtin_themes
from probefs.theme.loader import ThemeLoader, ThemeValidationError

DEFAULT_THEME = "probefs-dark"


class ProbeFSApp(App):
    """Three-pane keyboard-driven file browser."""

    CSS_PATH = "probefs.tcss"

    SCREENS = {"main": MainScreen}

    BINDINGS = [
        Binding("j", "screen.cursor_down", "Down",
                priority=True, show=False, id="probefs.cursor_down"),
        Binding("down", "screen.cursor_down", "Down",
                priority=True, show=False, id="probefs.cursor_down_arrow"),
        Binding("k", "screen.cursor_up", "Up",
                priority=True, show=False, id="probefs.cursor_up"),
        Binding("up", "screen.cursor_up", "Up",
                priority=True, show=False, id="probefs.cursor_up_arrow"),
        Binding("l", "screen.enter_dir", "Enter dir",
                priority=True, show=False, id="probefs.enter_dir"),
        Binding("enter", "screen.enter_dir", "Enter dir",
                priority=True, show=False, id="probefs.enter_dir_enter"),
        Binding("h", "screen.leave_dir", "Leave dir",
                priority=True, show=False, id="probefs.leave_dir"),
        Binding("backspace", "screen.leave_dir", "Leave dir",
                priority=True, show=False, id="probefs.leave_dir_backspace"),
        Binding(".", "screen.toggle_hidden", "Toggle hidden",
                priority=True, show=False, id="probefs.toggle_hidden"),
        Binding("q", "quit", "Quit",
                priority=True, show=False, id="probefs.quit"),
        Binding("ctrl+c", "quit", "Quit",
                priority=True, show=False, id="probefs.quit_ctrl_c"),
    ]

    def __init__(self) -> None:
        super().__init__()
        config = load_config()
        self._setup_themes(config)
        self._setup_keybindings(config)

    def _setup_themes(self, config: dict) -> None:
        """Register built-in and optional custom themes, then activate.

        Registration order is critical (research Pitfall 2):
        1. Register all built-in themes FIRST
        2. Register optional custom theme from config
        3. Set self.theme LAST (after all registrations)
        """
        # Step 1: Register all built-in probefs themes
        for theme in load_all_builtin_themes():
            self.register_theme(theme)

        # Step 2: Optionally load and register a custom theme from config
        theme_file = config.get("theme_file")
        if theme_file:
            try:
                custom = ThemeLoader.load(theme_file)
                self.register_theme(custom)
            except ThemeValidationError as e:
                # Invalid theme YAML — print warning, continue with built-ins
                print(f"Warning: Theme file {theme_file!r} is invalid: {e}")
            except FileNotFoundError:
                print(f"Warning: Theme file not found: {theme_file!r}")

        # Step 3: Activate requested theme with fallback
        # config.get('theme') is None when key absent -> use DEFAULT_THEME
        requested = config.get("theme") or DEFAULT_THEME
        try:
            self.theme = requested
        except InvalidThemeError:
            print(
                f"Warning: Theme {requested!r} is not registered. "
                f"Falling back to {DEFAULT_THEME!r}."
            )
            self.theme = DEFAULT_THEME

    def _setup_keybindings(self, config: dict) -> None:
        """Apply user keybinding overrides from config['keybindings'].

        Safe to call from __init__: set_keymap() calls refresh_bindings()
        which guards with `if self._is_mounted:` — no-op if not yet mounted.
        The _keymap dict is applied by Screen._binding_chain on first keypress.

        Override values REPLACE (not extend) the original key for that binding ID.
        To keep the original key, include it in the value: "n,j" keeps j and adds n.
        Spaces in values are stripped to handle "n, j" -> "n,j" (Textual pitfall).
        """
        raw = config.get("keybindings")
        if not isinstance(raw, dict):
            return
        keymap: dict[str, str] = {}
        for k, v in raw.items():
            if k and v:
                # Strip spaces: "n, j" -> "n,j" — Textual's apply_keymap does not strip
                keymap[str(k)] = str(v).replace(" ", "")
        if keymap:
            self.set_keymap(keymap)

    def on_mount(self) -> None:
        """Push main screen on launch."""
        self.push_screen("main")


def main() -> None:
    """Entry point for `uv run probefs` and `probefs.app:main`."""
    ProbeFSApp().run()
