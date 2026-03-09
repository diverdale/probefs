"""ProbeFSApp — Textual application entry point for probefs."""
from __future__ import annotations

from textual.app import App, InvalidThemeError
from textual.binding import Binding

from probefs.config import init_config_dir, load_config, themes_dir
from probefs.screens.main import MainScreen
from probefs.theme.builtin import load_all_builtin_themes
from probefs.theme.loader import ThemeLoader, ThemeValidationError

DEFAULT_THEME = "probefs-dark"


class ProbeFSApp(App):
    """Three-pane keyboard-driven file browser."""

    CSS_PATH = "probefs.tcss"

    ENABLE_COMMAND_PALETTE = False  # disable built-in palette — probefs uses its own keybindings

    SCREENS = {"main": MainScreen}

    BINDINGS = [
        # Navigation — show=True: these appear in Footer key hints
        Binding("j", "screen.cursor_down", "Down",
                priority=True, show=True, id="probefs.cursor_down"),
        Binding("down", "screen.cursor_down", "Down",
                priority=True, show=False, id="probefs.cursor_down_arrow"),  # duplicate of j
        Binding("k", "screen.cursor_up", "Up",
                priority=True, show=True, id="probefs.cursor_up"),
        Binding("up", "screen.cursor_up", "Up",
                priority=True, show=False, id="probefs.cursor_up_arrow"),  # duplicate of k
        Binding("l", "screen.enter_dir", "Open",
                priority=True, show=True, id="probefs.enter_dir"),
        Binding("enter", "screen.enter_dir", "Open",
                priority=True, show=False, id="probefs.enter_dir_enter"),  # duplicate of l
        Binding("h", "screen.leave_dir", "Back",
                priority=True, show=True, id="probefs.leave_dir"),
        Binding("backspace", "screen.leave_dir", "Back",
                priority=True, show=False, id="probefs.leave_dir_backspace"),  # duplicate of h
        Binding(".", "screen.toggle_hidden", "Hidden",
                priority=True, show=True, id="probefs.toggle_hidden"),
        Binding("s", "screen.sort", "Sort",
                priority=True, show=True, id="probefs.sort"),
        Binding("/", "screen.filter", "Filter",
                priority=True, show=True, id="probefs.filter"),
        Binding("ctrl+q", "quit", "Quit",
                priority=True, show=True, id="probefs.quit"),
        Binding("ctrl+c", "quit", "Quit",
                priority=True, show=False, id="probefs.quit_ctrl_c"),
        # File operations
        Binding("y", "screen.copy", "Copy",
                priority=True, show=True, id="probefs.copy"),
        Binding("p", "screen.move", "Move",
                priority=True, show=True, id="probefs.move"),
        Binding("d", "screen.delete", "Trash",
                priority=True, show=True, id="probefs.delete"),
        Binding("r", "screen.rename", "Rename",
                priority=True, show=True, id="probefs.rename"),
        Binding("n", "screen.new_file", "New file",
                priority=True, show=True, id="probefs.new_file"),
        Binding("ctrl+n", "screen.new_dir", "New dir",
                priority=True, show=True, id="probefs.new_dir"),
    ]

    def __init__(self) -> None:
        super().__init__()
        init_config_dir()
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

        # Step 2: Load and register all themes from ~/.probefs/themes/
        td = themes_dir()
        if td.is_dir():
            for theme_path in sorted(td.glob("*.yaml")):
                try:
                    custom = ThemeLoader.load(theme_path)
                    self.register_theme(custom)
                except ThemeValidationError as e:
                    print(f"Warning: Theme file {str(theme_path)!r} is invalid: {e}")

        # Step 3: Optionally load and register a custom theme from config
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

        # Step 4: Activate requested theme with fallback
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
