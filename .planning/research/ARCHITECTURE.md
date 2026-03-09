# Architecture Research

**Domain:** TUI file manager (Python + Textual, ranger-style three-pane layout)
**Researched:** 2026-03-09
**Confidence:** HIGH (Textual internals verified via official docs; ranger/yazi architecture verified via source/DeepWiki; fsspec SFTP verified via official docs)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Presentation Layer                          │
│                       (Textual App + Screens)                        │
│  ┌─────────────┐  ┌────────────────┐  ┌────────────┐  ┌──────────┐  │
│  │ ParentPane  │  │  CurrentPane   │  │PreviewPane │  │ StatusBar│  │
│  │  (Widget)   │  │   (Widget)     │  │  (Widget)  │  │ (Widget) │  │
│  └──────┬──────┘  └───────┬────────┘  └─────┬──────┘  └────┬─────┘  │
│         │                 │                 │               │        │
├─────────┴─────────────────┴─────────────────┴───────────────┴────────┤
│                          Controller Layer                             │
│            (Textual App class — event routing, key handling)          │
│  ┌──────────────────┐  ┌─────────────────┐  ┌──────────────────────┐ │
│  │  KeybindManager  │  │  ThemeRegistry  │  │    IconResolver      │ │
│  └──────────────────┘  └─────────────────┘  └──────────────────────┘ │
├───────────────────────────────────────────────────────────────────────┤
│                          Domain Layer                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                       FileManager Core                            │ │
│  │  navigation state · selection · clipboard · sort/filter          │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  FileOps     │  │  Previewer   │  │  TaskQueue   │                 │
│  │ (copy/move/  │  │ (text/image/ │  │ (async bg    │                 │
│  │  del/rename) │  │  archive)    │  │  operations) │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
├───────────────────────────────────────────────────────────────────────┤
│                     Filesystem Abstraction Layer (FAL)                 │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                   AbstractFilesystem (fsspec)                   │   │
│  │            ls · stat · open · copy · mv · rm · mkdir           │   │
│  └──────────────────────────────┬─────────────────────────────────┘   │
│       ┌────────────────────────┬┴──────────────────────┐              │
│  ┌────┴────┐            ┌──────┴──────┐       ┌────────┴──────┐       │
│  │LocalFS  │            │  SFTPfs     │       │  Future: S3   │       │
│  │(default)│            │(fsspec sftp)│       │  GCS, etc.    │       │
│  └─────────┘            └─────────────┘       └───────────────┘       │
└───────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `ProbeFSApp` | Top-level Textual App; mounts screens, holds global state, dispatches key events | Subclass of `textual.App` |
| `MainScreen` | Primary three-pane layout; composes the three pane widgets and status bar | Subclass of `textual.Screen` |
| `ParentPane` | Renders parent directory listing; highlights currently-focused item | `DirectoryList` widget |
| `CurrentPane` | Renders current directory; selection state, keyboard focus | `DirectoryList` widget with active state |
| `PreviewPane` | Renders preview of focused entry (text, syntax-highlighted, image, archive listing) | `Preview` widget |
| `StatusBar` | Renders path, permissions, size, mode information | `Static` widget |
| `FileManagerCore` | Holds navigation state (current path, selection set, clipboard, sort order, filter) | Plain Python dataclass / `reactive` attrs |
| `FileOps` | Executes file operations (copy, move, delete, rename, create) through FAL | Async service class |
| `Previewer` | Generates preview content for a given path/FS entry; dispatches to sub-renderers | Strategy pattern with sub-renderers per type |
| `TaskQueue` | Background async tasks with progress reporting (large copies, bulk ops) | `asyncio.Queue` + Textual `Worker` |
| `KeybindManager` | Loads user keymap config (YAML/JSON), feeds `App.set_keymap()` | Config loader + keymap dict |
| `ThemeRegistry` | Loads built-in + user YAML/JSON themes; registers `textual.Theme` objects; switches at runtime | Registry pattern |
| `IconResolver` | Maps file extension/mime type to Nerd Font glyph or ASCII fallback | Lookup table + capability detection |
| `AbstractFilesystem (FAL)` | Unified interface for all FS operations; wraps `fsspec.AbstractFileSystem` | Thin wrapper or direct use of `fsspec` |
| `LocalFS` | Local filesystem provider; default transport | `fsspec.filesystem('file')` |
| `SFTPfs` | SFTP transport; future phase | `fsspec.filesystem('sftp', host=..., ssh_kwargs=...)` |

## Recommended Project Structure

```
probefs/
├── __main__.py               # Entry point: probefs.main()
├── app.py                    # ProbeFSApp(textual.App) — top-level
├── screens/
│   ├── main.py               # MainScreen(textual.Screen)
│   └── modal.py              # Confirmation, rename, mkdir modals
├── widgets/
│   ├── directory_list.py     # DirectoryList widget (shared for parent+current panes)
│   ├── preview_pane.py       # PreviewPane widget
│   └── status_bar.py         # StatusBar widget
├── core/
│   ├── manager.py            # FileManagerCore — navigation/selection state
│   ├── fileops.py            # FileOps — async copy/move/delete/rename
│   ├── previewer.py          # Previewer — content dispatching
│   └── task_queue.py         # TaskQueue — background operations
├── fs/
│   ├── base.py               # AbstractFS wrapper type; protocol definition
│   ├── local.py              # LocalFS — wraps fsspec 'file'
│   └── sftp.py               # SFTPfs — wraps fsspec 'sftp' (future phase)
├── config/
│   ├── loader.py             # Loads YAML/JSON config from XDG dirs
│   ├── keybinds.py           # KeybindManager — loads and applies user keymap
│   └── schema.py             # Pydantic models for config validation
├── theming/
│   ├── registry.py           # ThemeRegistry — load + register Textual themes
│   ├── loader.py             # Parses YAML/JSON theme files
│   └── builtin/              # Bundled default themes (.yaml)
├── icons/
│   ├── resolver.py           # IconResolver — extension→glyph lookup
│   ├── nerd_font.py          # Nerd Font icon tables
│   └── ascii_fallback.py     # ASCII fallback tables
└── utils/
    ├── mime.py               # MIME type detection
    └── terminal.py           # Terminal capability detection (256 color, unicode)
```

### Structure Rationale

- **`fs/`:** Isolates all filesystem I/O behind a protocol boundary. Adding SFTP or S3 means adding a file here, never touching widgets.
- **`core/`:** Domain logic separated from presentation. `FileManagerCore` is testable without a running Textual app.
- **`widgets/`:** Textual widgets are presentation-only. They emit messages upward and receive reactive data downward.
- **`theming/`:** Isolated from core; themes are pure data (YAML → Textual Theme object). The registry is the single point of runtime theme switching.
- **`config/`:** All user-facing configuration (keybinds, theme selection, preferences) flows through one module. Pydantic validation catches bad configs at load time.
- **`icons/`:** Separated because Nerd Font availability is a runtime capability question, not a build-time one.

## Architectural Patterns

### Pattern 1: Filesystem Abstraction Layer (FAL) via fsspec

**What:** All filesystem operations go through `fsspec.AbstractFileSystem`. The rest of the app never calls `os.path`, `pathlib.Path`, or `os.listdir` directly.

**When to use:** From day one. The interface is identical for local and SFTP, so there is no migration cost later.

**Trade-offs:** Small indirection overhead (negligible). `fsspec` is actively maintained and already includes `SFTPFileSystem` backed by paramiko.

**Example:**
```python
# fs/base.py
import fsspec

class ProbeFS:
    """Thin wrapper around fsspec.AbstractFileSystem."""

    def __init__(self, protocol: str = "file", **kwargs):
        self._fs = fsspec.filesystem(protocol, **kwargs)

    def ls(self, path: str, detail: bool = True) -> list:
        return self._fs.ls(path, detail=detail)

    def stat(self, path: str) -> dict:
        return self._fs.stat(path)

    def copy(self, src: str, dst: str) -> None:
        self._fs.copy(src, dst)

    def rm(self, path: str, recursive: bool = False) -> None:
        self._fs.rm(path, recursive=recursive)

    def open(self, path: str, mode: str = "rb"):
        return self._fs.open(path, mode)


# SFTP (future phase — zero change to callers)
sftp_fs = ProbeFS("sftp", host="example.com", ssh_kwargs={"username": "user"})
local_fs = ProbeFS("file")
```

### Pattern 2: Messages-Up / Attributes-Down (Textual Idiom)

**What:** Parent widgets pass data to children via reactive attributes. Children communicate back to parents by posting custom `Message` subclasses that bubble up the DOM tree.

**When to use:** Always in Textual. Avoids tight coupling between widget siblings.

**Trade-offs:** Slightly more verbose than direct calls; pays off as widget count grows.

**Example:**
```python
# widgets/directory_list.py
class DirectoryList(Widget):
    entries: reactive[list[dict]] = reactive([])  # parent sets this

    class EntrySelected(Message):
        """Posted when user selects a file entry."""
        def __init__(self, entry: dict) -> None:
            self.entry = entry
            super().__init__()

    def on_key(self, event: Key) -> None:
        if event.key == "enter":
            self.post_message(self.EntrySelected(self.focused_entry))


# screens/main.py
class MainScreen(Screen):
    def on_directory_list_entry_selected(
        self, event: DirectoryList.EntrySelected
    ) -> None:
        self.preview_pane.path = event.entry["name"]  # push down to preview
        self.core.navigate_to(event.entry["name"])    # update domain state
```

### Pattern 3: Theme as Data, Runtime Switching via Textual Theme Registry

**What:** Themes are YAML files that map Textual's 11 base color variables. The `ThemeRegistry` loads them and calls `App.register_theme()` + `App.theme = name` for instant switching.

**When to use:** From the first themed build. Keeps TCSS stylesheets free of hardcoded colors.

**Trade-offs:** Requires users to learn Textual's 11-color token model. Worth it because all derived shades, text contrast, and component colors come for free.

**Example:**
```yaml
# theming/builtin/dracula.yaml
name: dracula
primary: "#6272a4"
secondary: "#bd93f9"
accent: "#ff79c6"
background: "#282a36"
surface: "#44475a"
foreground: "#f8f8f2"
success: "#50fa7b"
warning: "#ffb86c"
error: "#ff5555"
```

```python
# theming/registry.py
from textual.theme import Theme
import yaml

class ThemeRegistry:
    def load_and_register(self, app: App, path: Path) -> None:
        data = yaml.safe_load(path.read_text())
        theme = Theme(**data)
        app.register_theme(theme)

    def activate(self, app: App, name: str) -> None:
        app.theme = name
```

### Pattern 4: Keybinding Override via Textual set_keymap()

**What:** All bindable actions get stable string IDs. On startup, `KeybindManager` reads user YAML/JSON and calls `App.set_keymap(dict)`. Textual handles the rest.

**When to use:** Essential for user-local keybinding overrides. Built into Textual — do not reinvent.

**Trade-offs:** User must know binding IDs. Mitigate by documenting them in `--help` and the README.

**Example:**
```python
# In ProbeFSApp
BINDINGS = [
    Binding("j", "cursor_down", "Down", id="nav.down"),
    Binding("k", "cursor_up", "Up", id="nav.up"),
    Binding("h", "go_parent", "Parent dir", id="nav.parent"),
    Binding("l", "open_entry", "Open", id="nav.open"),
    Binding("dd", "delete_selected", "Delete", id="ops.delete"),
]

def on_mount(self) -> None:
    user_keymap = KeybindManager().load()  # reads ~/.config/probefs/keybinds.yaml
    if user_keymap:
        self.set_keymap(user_keymap)
```

## Data Flow

### Navigation Flow

```
User presses 'l' (open/enter)
    ↓
Textual Key Event dispatched
    ↓
ProbeFSApp.action_open_entry()
    ↓
FileManagerCore.navigate_to(path)
    ↓
FAL.ls(new_path) → list[dict]  (via fsspec)
    ↓
FileManagerCore.current_entries reactive updated
    ↓
CurrentPane re-renders (watch_current_entries)
    ↓
ParentPane updated with old current path
    ↓
PreviewPane.on_directory_list_entry_selected() triggered
    ↓
Previewer.generate(new_focused_entry) → Rich renderable
    ↓
PreviewPane re-renders
```

### File Operation Flow

```
User initiates delete (key: 'd')
    ↓
ConfirmationModal pushed (ModalScreen)
    ↓
User confirms
    ↓
Modal dismissed, result posted via Message
    ↓
FileOps.delete_async(path, fs=current_fs) dispatched to TaskQueue
    ↓
TaskQueue runs in Textual Worker (non-blocking)
    ↓
Progress posted via app.notify() or ProgressBar widget
    ↓
On completion: FileManagerCore refreshes current directory listing
```

### Theme Load Flow

```
App startup
    ↓
ThemeRegistry scans ~/.local/share/probefs/themes/ + bundled themes
    ↓
For each .yaml: parse → construct textual.Theme → app.register_theme()
    ↓
config.loader reads user preference: active_theme = "dracula"
    ↓
ThemeRegistry.activate(app, "dracula") → app.theme = "dracula"
    ↓
Textual regenerates all CSS variables, triggers full re-render
```

### Config Load Flow

```
App startup (before on_mount)
    ↓
config.loader resolves XDG_CONFIG_HOME/probefs/config.yaml
    ↓
Pydantic model validates; raises on invalid config with clear error
    ↓
KeybindManager reads keybinds.yaml → dict[binding_id, key_string]
    ↓
on_mount: App.set_keymap(user_keymap) applied
```

## SFTP Extension Point

The extension point is `ProbeFS.__init__(protocol, **kwargs)`. To mount an SFTP session:

```python
# Future: no changes to widgets, core, or ops
sftp = ProbeFS("sftp", host="server.example.com", ssh_kwargs={
    "username": "admin",
    "key_filename": "/home/user/.ssh/id_ed25519",
})
app.file_manager_core.mount_fs("sftp://server.example.com", sftp)
```

fsspec's `SFTPFileSystem` (backed by paramiko) is already available as `fsspec[sftp]`. The `ls`, `stat`, `open`, `copy`, `rm` interface is identical to the local filesystem implementation.

**What stays the same when SFTP is added:**
- All widgets (they never call FS directly)
- `FileManagerCore` navigation logic
- `FileOps` (already async-aware)
- `Previewer` (uses `fs.open()` which works for SFTP)
- All config/theme/icon subsystems

**What changes:**
- Add `fs/sftp.py` (thin instantiation wrapper)
- Add connection UI (modal for host/user/key)
- Add a "remote tab" concept to `FileManagerCore` if multi-session is desired
- `TaskQueue` may need priority adjustment for high-latency operations

## Anti-Patterns

### Anti-Pattern 1: Calling os.path or pathlib directly in widgets

**What people do:** Use `Path(path).iterdir()` inside `DirectoryList.on_mount()` for convenience.

**Why it's wrong:** SFTP is impossible to add without rewriting every widget that does this. Discovered in ranger's own history — it took significant refactoring to add remote filesystem support precisely because FS calls were scattered throughout.

**Do this instead:** All FS calls go through `FileManagerCore`, which holds the `ProbeFS` instance. Widgets receive pre-fetched entry lists as reactive data.

### Anti-Pattern 2: Synchronous FS Operations on the Main Thread

**What people do:** Call `fs.ls()` directly in an event handler, assuming it's fast for local.

**Why it's wrong:** Slow NFS mounts, large directories, and SFTP latency all block the UI thread. Textual runs its rendering loop on asyncio — a sync blocking call freezes the entire interface.

**Do this instead:** Use Textual's `Worker` API or `asyncio.to_thread()` for all FS operations, even local ones. Establishes the right pattern from the start.

```python
# Correct
async def refresh_current_dir(self) -> None:
    entries = await asyncio.to_thread(self.fs.ls, self.current_path)
    self.current_entries = entries
```

### Anti-Pattern 3: Hardcoding Colors in TCSS

**What people do:** Write `color: #bd93f9;` in `.tcss` files.

**Why it's wrong:** Makes theme switching impossible without rewriting stylesheets. Also breaks in terminals with limited color support.

**Do this instead:** Always use Textual CSS design tokens (`$primary`, `$surface`, `$accent`, etc.). These resolve to the active theme's values at runtime.

### Anti-Pattern 4: Monolithic App class

**What people do:** Put navigation logic, file operations, preview logic, and theming all in `ProbeFSApp` methods.

**Why it's wrong:** The Textual `App` class becomes untestable. Component boundaries collapse. Adding SFTP requires changes throughout.

**Do this instead:** `ProbeFSApp` is a thin coordinator. It mounts screens, owns global key bindings, and delegates everything else. `FileManagerCore` owns state. `FileOps` owns operations. `ThemeRegistry` owns themes.

### Anti-Pattern 5: Storing Full File Contents in Reactive State

**What people do:** Reactive attribute holds `file_contents: str = reactive("")` and sets it to the full text of a previewed file.

**Why it's wrong:** Large files (logs, source files) cause unnecessary re-renders and memory churn. The preview pane re-renders on every keystroke because the reactive attribute changed.

**Do this instead:** `PreviewPane` reads file content lazily when its `path` reactive changes, with a size guard (e.g., skip preview over 1 MB). Cache the rendered segment, not the raw bytes.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| fsspec (local) | `ProbeFS("file")` — zero config | Ships with fsspec base package |
| fsspec SFTP | `ProbeFS("sftp", host=..., ssh_kwargs=...)` | Requires `fsspec[sftp]` extra (paramiko) |
| Nerd Font icons | Static lookup table at import time | Falls back to ASCII if terminal capability check fails |
| GitHub theme registry | HTTP fetch to index URL; download `.yaml` to user theme dir | Future phase; use `httpx` for async fetch |
| PyPI distribution | `pyproject.toml` with `[project.scripts]` entry point | `pipx install probefs` invokes `probefs.__main__` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Widget → Widget | Never directly; always via parent screen | Preserves widget reusability |
| Widget → Core | Widget posts `Message`; Screen handler calls `core.method()` | Core is not a Textual object |
| Core → FAL | Direct method call (sync, wrapped in `asyncio.to_thread` by callers) | FAL has no Textual dependency |
| FAL → fsspec | Direct: `self._fs.ls(path)` etc. | fsspec is a pure-Python library |
| Config → App | `on_mount` reads config, calls `set_keymap` + `ThemeRegistry.activate` | Config is loaded once; user must restart for changes |
| ThemeRegistry → App | `App.register_theme()` + `App.theme = name` (Textual official API) | Runtime safe; triggers full re-render |

## Scaling Considerations

TUI file managers are single-user, single-process applications. "Scaling" means handling large directories and remote latency, not concurrent users.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Small dirs (<1k entries) | Sync ls → to_thread wrapping, all fine |
| Large dirs (10k+ entries) | Implement virtual scrolling in `DirectoryList`; load entries lazily in chunks |
| SFTP with high latency | `TaskQueue` must support cancellable in-flight requests; show loading indicator while ls is pending |
| Bulk file operations | `TaskQueue` with progress reporting; never block UI; allow cancel mid-operation |

### Scaling Priorities

1. **First bottleneck:** Large directory listings freeze the pane — fix by async ls + progressive render.
2. **Second bottleneck:** Preview of large files blocks — fix with size guard and streamed reads.

## Sources

- Textual widget system architecture: https://deepwiki.com/Textualize/textual/2.2-widget-system (MEDIUM confidence — DeepWiki analysis, consistent with official docs)
- Textual reactivity guide: https://textual.textualize.io/guide/reactivity/ (HIGH confidence — official docs)
- Textual widget guide: https://textual.textualize.io/guide/widgets/ (HIGH confidence — official docs)
- Textual theme/design system: https://textual.textualize.io/guide/design/ (HIGH confidence — official docs)
- Textual keymaps blog post: https://darren.codes/posts/textual-keymaps/ (MEDIUM confidence — community blog, consistent with official API)
- Textual screens/modal: https://textual.textualize.io/guide/screens/ (HIGH confidence — official docs)
- Ranger source structure: https://github.com/ranger/ranger/tree/master/ranger (HIGH confidence — official source)
- Yazi architecture: https://deepwiki.com/sxyazi/yazi/2.1-file-manager-(yazi) (MEDIUM confidence — DeepWiki analysis of open source)
- fsspec usage guide: https://filesystem-spec.readthedocs.io/en/latest/usage.html (HIGH confidence — official docs)
- fsspec SFTP implementation: https://filesystem-spec.readthedocs.io/en/latest/_modules/fsspec/implementations/sftp.html (HIGH confidence — official source)
- fs.sshfs (pyfilesystem2 SFTP): https://github.com/althonos/fs.sshfs (MEDIUM confidence — evaluated but not recommended; fsspec preferred)

---
*Architecture research for: TUI file manager (probefs)*
*Researched: 2026-03-09*
