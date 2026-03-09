# Phase 1: Core Scaffold and Async Architecture - Research

**Researched:** 2026-03-09
**Domain:** Python TUI (Textual 8.0.2), async worker pattern, fsspec local filesystem, uv project scaffold
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NAV-01 | User can navigate a three-pane Miller columns layout (parent dir \| current dir \| preview pane) using hjkl and arrow keys | Textual Horizontal layout with three ListView widgets; BINDINGS with priority=True for hjkl; @work(thread=True) for non-blocking ls() |
| NAV-02 | User can enter a directory by pressing l/Enter and move up with h/Backspace | action methods bound to l/Enter (descend) and h/Backspace (ascend); navigation state in FileManagerCore; workers fire after each navigation to reload pane content |
</phase_requirements>

---

## Summary

Phase 1 establishes the two foundational architectural invariants that every subsequent phase depends on: the three-pane layout composition and the `@work(thread=True)` pattern for all filesystem I/O. These are not independently movable — they must both be correct from the first commit or Phase 1 becomes a rewrite.

The three-pane layout maps directly onto Textual's widget composition model: a `Horizontal` container holds three child widgets (`DirectoryList` x2 for parent and current panes, `PreviewPane` for the right pane), each assigned fractional widths via TCSS. Navigation state lives in `FileManagerCore` on the `MainScreen` — widgets are pure display surfaces that receive data downward (via reactive attributes or direct method calls) and post `Message` events upward. This is the Messages-up / attributes-down pattern that Textual's architecture enforces.

The async constraint is architectural, not a performance optimization. Textual's main event loop is a single asyncio thread. Any blocking `os.scandir()`, `pathlib.iterdir()`, or fsspec `ls()` call on that thread freezes the entire UI until it returns. The `@work(thread=True)` decorator runs the decorated method in a ThreadPoolExecutor thread and provides `call_from_thread()` and `post_message()` as the only safe ways to update the UI from that thread. `post_message()` is thread-safe by design; `call_from_thread()` runs an arbitrary callable on the main thread. Both patterns are verified in Textual's official docs and blog.

**Primary recommendation:** Build `ProbeFSApp → MainScreen → (DirectoryList × 2 + PreviewPane)` as the widget tree. Every filesystem call must go through `@work(thread=True)` on `FileManagerCore`, which posts `DirectoryLoaded` messages back to `MainScreen` to update widget state. Wire navigation keys at the `MainScreen`/`ProbeFSApp` level with `priority=True` — never at the individual pane widget level, to prevent binding capture.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.0.2 | TUI framework — App, Screen, Widget, Worker, TCSS | Only viable async Python TUI in 2026; async-native, official Worker API, no alternatives |
| fsspec | 2025.12.x | Filesystem abstraction (FAL) — `ls`, `info`, `open` | Identical API for local and SFTP; required from Phase 1 to avoid future rewrite |
| Python | 3.10+ | Runtime | asyncssh requires 3.10+; match statement syntax usable in keybinding dispatch |
| uv | 0.10+ | Package and project manager | `uv init --package`, `uv sync`, `uv build`; replaces pip/poetry |

### Supporting (Phase 1 scope)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | latest | Test runner | All tests |
| pytest-asyncio | latest | Async test support | Required for `async def test_` functions |
| pytest-textual-snapshot | latest | Visual regression testing | Snapshot tests for layout assertions |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| fsspec | pathlib + os | pathlib has no SFTP backend; switching later requires touching every FS call site |
| @work(thread=True) | asyncio.to_thread | @work gives Worker.StateChanged events, cancellation, exclusive mode; asyncio.to_thread gives none of this |
| ListView per pane | DirectoryTree | DirectoryTree is a single hierarchical tree widget; Miller columns need three independent flat lists |

**Installation:**
```bash
uv init --package probefs
uv add textual fsspec
uv add --dev pytest pytest-asyncio pytest-textual-snapshot
```

### pyproject.toml entry point
```toml
[project.scripts]
probefs = "probefs.app:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Architecture Patterns

### Recommended Project Structure

```
probefs/
├── src/
│   └── probefs/
│       ├── __init__.py
│       ├── app.py              # ProbeFSApp(App) + main() entry point
│       ├── screens/
│       │   └── main.py         # MainScreen(Screen) — three-pane layout
│       ├── widgets/
│       │   ├── directory_list.py   # DirectoryList(Widget) — shared for parent + current pane
│       │   └── preview_pane.py     # PreviewPane(Widget) — right pane stub
│       ├── core/
│       │   └── file_manager.py     # FileManagerCore — navigation state, cursor, ProbeFS instance
│       └── fs/
│           └── probe_fs.py         # ProbeFS — fsspec wrapper (FAL entry point)
├── tests/
│   └── test_navigation.py
├── pyproject.toml
└── .python-version
```

### Pattern 1: App / Screen / Widget Composition

**What:** `ProbeFSApp` mounts `MainScreen`, which composes `DirectoryList` × 2 and `PreviewPane` inside a `Horizontal` container. App holds global bindings with `priority=True`. Screen holds navigation state via `FileManagerCore`.

**When to use:** Every time the widget tree is wired. This is the fixed structure for Phase 1.

**Example:**
```python
# Source: textual.textualize.io/guide/widgets/ and /guide/layout/
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Horizontal
from textual.binding import Binding

class MainScreen(Screen):
    CSS = """
    #pane-parent  { width: 1fr; height: 100%; }
    #pane-current { width: 1fr; height: 100%; }
    #pane-preview { width: 2fr; height: 100%; }
    """

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield DirectoryList(id="pane-parent")
            yield DirectoryList(id="pane-current")
            yield PreviewPane(id="pane-preview")

class ProbeFSApp(App):
    SCREENS = {"main": MainScreen}

    BINDINGS = [
        Binding("j,down",  "cursor_down", "Down",   priority=True),
        Binding("k,up",    "cursor_up",   "Up",     priority=True),
        Binding("l,enter", "enter_dir",   "Enter",  priority=True),
        Binding("h,backspace", "leave_dir", "Back", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True, show=False),
    ]

    def on_mount(self) -> None:
        self.push_screen("main")
```

### Pattern 2: @work(thread=True) for All FS I/O

**What:** All calls to fsspec (ls, stat, info) run in a thread worker decorated with `@work(thread=True)`. The worker posts a custom `Message` back to the screen via `self.post_message()` (which is thread-safe). The screen's message handler updates widget state on the main thread.

**When to use:** Every time any filesystem method is called. No exceptions. This is the invariant that prevents the Ranger sync-IO bug.

**Example:**
```python
# Source: textual.textualize.io/guide/workers/ + blog 2024-09-15
from textual.worker import get_current_worker
from textual.message import Message

class DirectoryLoaded(Message):
    def __init__(self, entries: list[dict]) -> None:
        self.entries = entries
        super().__init__()

class MainScreen(Screen):
    @work(thread=True, exclusive=True, exit_on_error=False)
    def _load_directory(self, path: str) -> None:
        worker = get_current_worker()
        entries = self.app.core.fs.ls(path, detail=True)
        if not worker.is_cancelled:
            self.post_message(DirectoryLoaded(entries))

    def on_directory_loaded(self, event: DirectoryLoaded) -> None:
        # Runs on main thread — safe to update widgets
        self.query_one("#pane-current", DirectoryList).set_entries(event.entries)
```

**Key detail:** `post_message()` is thread-safe — call it directly from a thread worker. `call_from_thread()` is the fallback for calling arbitrary UI methods, but `post_message()` is preferred because it participates in Textual's message routing.

### Pattern 3: Messages-Up / Attributes-Down

**What:** Widgets never reference sibling widgets directly. Child widgets post `Message` subclasses upward; parent screens handle those messages and push updated data back down via method calls or reactive attributes.

**When to use:** Whenever a widget needs to communicate with any other widget.

**Example:**
```python
# Source: textual.textualize.io/guide/widgets/
class DirectoryList(Widget, can_focus=True):
    class EntryHighlighted(Message):
        def __init__(self, entry: dict) -> None:
            self.entry = entry
            super().__init__()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        # Widget-internal: convert ListView event to our domain message
        self.post_message(self.EntryHighlighted(self._entries[event.index]))

class MainScreen(Screen):
    @on(DirectoryList.EntryHighlighted, "#pane-current")
    def on_current_highlighted(self, event: DirectoryList.EntryHighlighted) -> None:
        # Screen handles it — updates parent pane and preview
        self._load_directory(event.entry["name"])  # triggers the worker
```

### Pattern 4: Navigation State in FileManagerCore

**What:** All navigation state (current path, parent path, cursor index) lives in `FileManagerCore`, not in widgets. Widgets are stateless display surfaces. The screen is the only owner of a `FileManagerCore` instance. This is the testability boundary — core logic can be tested without a running Textual app.

**Example:**
```python
from pathlib import PurePosixPath

class FileManagerCore:
    def __init__(self, fs: "ProbeFS", start_path: str) -> None:
        self.fs = fs
        self.cwd: str = start_path
        self.cursor_index: int = 0

    @property
    def parent_path(self) -> str:
        return str(PurePosixPath(self.cwd).parent)

    def descend(self, entry_name: str) -> str:
        """Return new cwd after descending into entry_name."""
        self.cwd = str(PurePosixPath(self.cwd) / entry_name)
        self.cursor_index = 0
        return self.cwd

    def ascend(self) -> str:
        """Return new cwd after moving up one directory."""
        self.cwd = self.parent_path
        self.cursor_index = 0
        return self.cwd
```

### Pattern 5: ProbeFS as the Single FAL Gateway

**What:** `ProbeFS` wraps `fsspec.filesystem("file")` for Phase 1 local access. Widgets and `FileManagerCore` call only `ProbeFS` methods — never `os`, `pathlib.iterdir()`, `shutil`, or raw fsspec directly. This is what makes SFTP drop-in later.

**Example:**
```python
# Source: filesystem-spec.readthedocs.io/en/latest/usage.html
import fsspec

class ProbeFS:
    def __init__(self, protocol: str = "file", **kwargs):
        self._fs = fsspec.filesystem(protocol, **kwargs)

    def ls(self, path: str, *, detail: bool = True) -> list[dict]:
        return self._fs.ls(path, detail=detail)

    def info(self, path: str) -> dict:
        return self._fs.info(path)

    def isdir(self, path: str) -> bool:
        return self._fs.isdir(path)
```

### Pattern 6: Binding Resolution with priority=True

**What:** Textual resolves bindings by walking from the focused widget UP through the widget tree to the App. A widget with `j` in its `BINDINGS` will consume the `j` keypress before it reaches the App. `priority=True` inverts this — the binding is checked at the App level FIRST, before any widget sees it.

**When to use:** All navigation bindings (hjkl, arrows, Enter, Backspace) MUST be defined at the App level with `priority=True`. Never define hjkl in individual pane widgets.

```python
# Source: textual.textualize.io/api/binding/
from textual.binding import Binding

class ProbeFSApp(App):
    BINDINGS = [
        # priority=True: these fire before any widget binding
        Binding("j", "cursor_down", "Down", priority=True),
        Binding("k", "cursor_up",   "Up",   priority=True),
        Binding("l", "enter_dir",   "Enter dir", priority=True),
        Binding("h", "leave_dir",   "Leave dir", priority=True),
    ]
```

### Anti-Patterns to Avoid

- **Blocking I/O on the main thread:** `os.scandir()` or `fs.ls()` called directly in an action method, `on_key` handler, or `on_mount` without `@work(thread=True)` will freeze the UI. This is the single most dangerous anti-pattern for this phase.
- **Widget-to-widget direct references:** `self.app.query_one("#pane-parent").update(...)` called from inside `#pane-current` creates tight coupling that breaks as the widget tree changes. Use Messages.
- **Navigation bindings in widget BINDINGS:** Defining `j`/`k` inside `DirectoryList.BINDINGS` steals those keys from the App, making global navigation impossible when that widget is focused.
- **Calling `self.refresh()` from a thread worker:** `refresh()` is not thread-safe. Use `call_from_thread(self.refresh)` or, better, use reactive attributes which trigger refresh automatically.
- **Mutable reactive objects without `mutate_reactive()`:** If a reactive attribute holds a `list`, replacing items in-place won't trigger watchers. Use `self.mutate_reactive(DirectoryList.entries)` after modifying the list in place, or assign a new list.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async filesystem calls | Custom asyncio.Queue + thread pool | `@work(thread=True)` + Textual Worker | Worker gives cancellation, exclusive mode, StateChanged events, error handling out of the box |
| Scrollable file list with keyboard navigation | Custom scrollable widget with key handlers | `ListView` + `ListItem` | ListView handles scroll-into-view, up/down bindings, `Highlighted`/`Selected` messages, index tracking |
| Thread-safe UI updates from background threads | Manual `threading.Lock` + callback queue | `post_message()` (thread-safe) or `call_from_thread()` | Textual's message bus is already thread-safe; home-rolled solutions introduce races |
| fsspec instance per call | `fsspec.filesystem("file")` on every directory load | Single `ProbeFS` instance on `FileManagerCore` | fsspec LocalFileSystem is designed for reuse; re-instantiating per call wastes memory and bypasses caching |
| Project scaffold + entry points | `setup.py`, `setup.cfg`, manual venv | `uv init --package` + `uv sync` | uv handles `src/` layout, `pyproject.toml`, entry points, and dev deps in one step |

**Key insight:** The value of `@work(thread=True)` is not just threading — it is the entire Worker lifecycle (cancellation, exclusive mode, error handling, state events) that would take hundreds of lines to replicate correctly. Use it for every FS call.

---

## Common Pitfalls

### Pitfall 1: Blocking I/O on the Main Event Loop
**What goes wrong:** `os.listdir()`, `pathlib.iterdir()`, or `fs.ls()` called directly in an action method or widget handler. The UI freezes for the duration of the call — on a slow NFS mount this can be multiple seconds.
**Why it happens:** It feels natural to call `entries = self.core.fs.ls(path)` inline. The async machinery is invisible when it works.
**How to avoid:** Every filesystem call in a `@work(thread=True)` method. No exceptions. Code review rule: if `fs.` appears outside a `@work`-decorated method body, it is wrong.
**Warning signs:** UI feels "jerky" on directory changes; pressing keys while a directory loads causes missed inputs.

### Pitfall 2: Widget Binding Capture (Keybinding Priority Inversion)
**What goes wrong:** `DirectoryList` has `j`/`k` in its own `BINDINGS`. When `DirectoryList` is focused, it consumes `j` and `k` before the `App`-level navigation actions fire. Navigation breaks.
**Why it happens:** Textual's default resolution walks UP from the focused widget. Widget bindings win unless `priority=True` is set at the App level.
**How to avoid:** Define all hjkl and arrow navigation at `ProbeFSApp` level with `Binding(..., priority=True)`. `DirectoryList` handles only internal scroll state; external navigation is the App's responsibility.
**Warning signs:** `j`/`k` scrolls the list instead of changing the cursor and triggering pane reload. Verify by checking which handler fires in `textual console`.

### Pitfall 3: post_message() vs call_from_thread() Confusion
**What goes wrong:** Developer uses `call_from_thread(self.some_method)` where `post_message()` would be cleaner, OR calls a non-thread-safe UI method directly from the worker (no `call_from_thread`).
**Why it happens:** The thread-safety rules are not obvious. `reactive` attribute assignments ARE NOT thread-safe without `call_from_thread`.
**How to avoid:** From a `@work(thread=True)` body: use `self.post_message(SomeMessage(...))` for domain events (preferred), or `self.call_from_thread(widget_method, args)` for direct method calls. Never access reactive attributes directly from a thread worker.
**Warning signs:** `RuntimeError: Attempt to update reactive from thread` or silent state corruption.

### Pitfall 4: DirectoryList ListView Population Race
**What goes wrong:** User presses `j` fast enough to trigger a second `_load_directory` worker before the first completes. First worker returns stale entries AFTER the second worker has already populated the list — the list shows stale data.
**Why it happens:** Two workers posting `DirectoryLoaded` messages; the second one arrives first.
**How to avoid:** Use `@work(thread=True, exclusive=True)` for directory loading. `exclusive=True` cancels the in-flight worker before starting a new one, so only the most recent result wins.
**Warning signs:** Directory listing occasionally shows wrong directory contents after rapid navigation.

### Pitfall 5: fsspec info() Dict Key Assumptions
**What goes wrong:** Code assumes fsspec `ls(detail=True)` returns only `name`, `size`, `type`. Phase 2 needs `mtime`, `mode`, `uid`, `gid`, `islink`. Accessing missing keys raises `KeyError`.
**Why it happens:** fsspec documents only the three required keys. The LocalFileSystem implementation returns additional keys but the spec doesn't guarantee them.
**How to avoid:** Use `entry.get("mtime")` with defaults. In Phase 1, only `name` and `type` are required. Design `ProbeFS.ls()` to return a typed `DirEntry` dataclass that normalizes the dict, so key differences between backends are hidden at the FAL boundary.
**Warning signs:** `KeyError: 'mtime'` in Phase 2 when rendering metadata columns.

### Pitfall 6: Empty Preview Pane Architecture Decision
**What goes wrong:** Preview pane is skipped as "just a stub" in Phase 1, so it receives no data wiring. Phase 6 then requires surgical changes to the message routing established in Phase 1.
**Why it happens:** Phase 6 work isn't visible from Phase 1.
**How to avoid:** Wire `PreviewPane` to receive the same cursor-change messages as the parent pane reload, even if the handler body is `pass` in Phase 1. The message routing infrastructure must be correct from the start.
**Warning signs:** Phase 6 requires changing the message types and handler signatures established in Phase 1.

---

## Code Examples

Verified patterns from official sources:

### Minimal Textual App with Screen
```python
# Source: textual.textualize.io/guide/screens/
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Static

class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Hello from MainScreen")

class ProbeFSApp(App):
    SCREENS = {"main": MainScreen}

    def on_mount(self) -> None:
        self.push_screen("main")

def main() -> None:
    ProbeFSApp().run()
```

### Three-Pane Horizontal Layout in TCSS
```css
/* Source: textual.textualize.io/guide/layout/ */
#pane-parent {
    width: 1fr;
    height: 100%;
    border-right: solid $panel-lighten-1;
}
#pane-current {
    width: 1fr;
    height: 100%;
    border-right: solid $panel-lighten-1;
}
#pane-preview {
    width: 2fr;
    height: 100%;
}
```

### Thread Worker Loading a Directory
```python
# Source: textual.textualize.io/guide/workers/
from textual import work
from textual.worker import get_current_worker

class MainScreen(Screen):
    @work(thread=True, exclusive=True, exit_on_error=False)
    def load_current_dir(self) -> None:
        worker = get_current_worker()
        try:
            entries = self.app.core.fs.ls(self.app.core.cwd, detail=True)
        except Exception as exc:
            if not worker.is_cancelled:
                self.post_message(DirectoryLoadFailed(str(exc)))
            return
        if not worker.is_cancelled:
            self.post_message(DirectoryLoaded(entries))
```

### Receiving Worker Results via Messages
```python
# Source: textual.textualize.io/api/on/ and /guide/widgets/
from textual.on import on

class MainScreen(Screen):
    def on_directory_loaded(self, event: DirectoryLoaded) -> None:
        current_pane = self.query_one("#pane-current", DirectoryList)
        current_pane.set_entries(event.entries)

    def on_directory_load_failed(self, event: DirectoryLoadFailed) -> None:
        self.notify(event.error_message, severity="error")
```

### fsspec Local Filesystem
```python
# Source: filesystem-spec.readthedocs.io/en/latest/usage.html
import fsspec

fs = fsspec.filesystem("file")
entries = fs.ls("/home/user/projects", detail=True)
# Each entry: {"name": str, "size": int, "type": "file"|"directory",
#              "mtime": float, "mode": int, "uid": int, "gid": int,
#              "islink": bool, "destination": str (if islink)}
```

### ListView Basics for a Pane
```python
# Source: textual.textualize.io/widgets/list_view/
from textual.widgets import ListView, ListItem, Label

class DirectoryList(Widget, can_focus=True):
    def compose(self) -> ComposeResult:
        yield ListView()

    def set_entries(self, entries: list[dict]) -> None:
        lv = self.query_one(ListView)
        lv.clear()
        for e in entries:
            lv.append(ListItem(Label(e["name"])))
```

### Priority Binding Declaration
```python
# Source: textual.textualize.io/api/binding/
from textual.binding import Binding

class ProbeFSApp(App):
    BINDINGS = [
        Binding("j",         "cursor_down", "Down",      priority=True, show=False),
        Binding("down",      "cursor_down", "Down",      priority=True, show=False),
        Binding("k",         "cursor_up",   "Up",        priority=True, show=False),
        Binding("up",        "cursor_up",   "Up",        priority=True, show=False),
        Binding("l",         "enter_dir",   "Enter dir", priority=True, show=False),
        Binding("enter",     "enter_dir",   "Enter dir", priority=True, show=False),
        Binding("h",         "leave_dir",   "Leave dir", priority=True, show=False),
        Binding("backspace", "leave_dir",   "Leave dir", priority=True, show=False),
        Binding("ctrl+c",    "quit",        "Quit",      priority=True, show=False),
    ]
```

### Testing with Pilot
```python
# Source: textual.textualize.io/guide/testing/
import pytest
from textual.testing import Pilot

@pytest.mark.asyncio
async def test_navigation_descend():
    app = ProbeFSApp()
    async with app.run_test(size=(120, 40)) as pilot:
        # Wait for initial directory load worker to complete
        await pilot.pause(0.1)
        initial_path = app.screen.core.cwd
        await pilot.press("l")
        await pilot.pause(0.1)
        assert app.screen.core.cwd != initial_path
```

### uv Project Initialization
```bash
# Source: docs.astral.sh/uv/concepts/projects/init/
uv init --package probefs
cd probefs
uv add textual fsspec
uv add --dev pytest pytest-asyncio pytest-textual-snapshot
uv sync        # installs project + deps into .venv
uv run probefs  # runs entry point defined in pyproject.toml
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `asyncio.to_thread()` for background FS calls | `@work(thread=True)` with Textual Worker | Textual ~0.20 (2023) | Worker gives cancellation, exclusive mode, StateChanged events — much richer than bare asyncio |
| Hardcoded bindings in widget BINDINGS | App-level `Binding(..., priority=True)` + `set_keymap()` for user overrides | Textual 0.82 (2024) | Clean separation: defaults in code, user overrides in YAML dict via `set_keymap()` |
| `pip install` + `setup.py` | `uv init --package` + `uv sync` | uv 1.x (2024) | 10-100x faster; lockfile (`uv.lock`) by default; single tool for all lifecycle operations |
| Per-call fsspec instantiation | Single `fsspec.filesystem("file")` instance held by FAL | Always | fsspec LocalFileSystem is reusable; re-instantiating wastes memory and bypasses the (optional) directory cache |
| Direct `pathlib.Path.iterdir()` in widgets | All FS calls through `ProbeFS` FAL | Architecture decision | FAL is the rewrite-prevention boundary for SFTP in Phase 10 |

**Deprecated/outdated in this context:**
- `urwid`, `curses`: No layout system, no async, no testing API — do not use.
- `python-prompt-toolkit`: Interactive prompts, not full TUI apps — wrong domain.
- `poetry`: Slower than uv; still functional but not the 2026 standard.

---

## Open Questions

1. **ListView vs custom `render_line()` widget for very large directories**
   - What we know: `ListView` + `ListItem` is the standard Textual scrollable list. For directories with tens of thousands of entries (e.g., `/proc`, large git repos), creating one `ListItem` per entry may be slow.
   - What's unclear: What is the practical ListView item limit before performance degrades? Textual's blog (Dec 2024) mentions a line-rendering API (`render_line()`) for high-performance scrollable content.
   - Recommendation: Ship Phase 1 with `ListView` for simplicity. Add a benchmark in the test suite (`ls /proc` with ~50k entries). If it's slow, Phase 2 or Phase 6 can refactor to `render_line()` without changing the message routing architecture.

2. **Cursor index: held in FileManagerCore vs ListView.index reactive**
   - What we know: `ListView` has its own `index` reactive attribute tracking the highlighted item. `FileManagerCore` also needs to know the cursor position to report the "selected entry" to workers.
   - What's unclear: Which is the source of truth? If the user scrolls with the mouse, `ListView.index` changes but `FileManagerCore.cursor_index` doesn't.
   - Recommendation: `ListView.index` is the authoritative cursor position. `FileManagerCore` stores it as a snapshot only for serialization purposes (e.g., restoring position on back navigation). Wire `on_list_view_highlighted` on the screen to sync `core.cursor_index` after every ListView change.

3. **Entry point: `app.py:main()` or `__main__.py`**
   - What we know: Both work with `uv run probefs`. `[project.scripts]` requires a callable; `__main__.py` enables `python -m probefs`.
   - What's unclear: Which is cleaner for the project structure being built.
   - Recommendation: Use `app.py:main()` for the PyPI entry point (explicit) AND provide `__main__.py` that calls `main()` for `python -m probefs` during development. Both in 10 lines total.

---

## Sources

### Primary (HIGH confidence)
- `textual.textualize.io/guide/workers/` — `@work(thread=True)`, `exclusive=True`, `call_from_thread`, `post_message` thread safety, `get_current_worker()`
- `textual.textualize.io/api/worker/` — Worker class, WorkerState enum, `cancel()`, `is_cancelled`, `StateChanged` message
- `textual.textualize.io/api/binding/` — `Binding` class parameters including `priority=True` and `id` for keymaps
- `textual.textualize.io/guide/input/` — BINDINGS class variable, key handlers, `priority=True` binding resolution
- `textual.textualize.io/guide/layout/` — `Horizontal` container, fractional widths (`1fr`), TCSS layout
- `textual.textualize.io/guide/widgets/` — `compose()`, `on_mount()`, custom `Message` classes, `can_focus=True`
- `textual.textualize.io/guide/reactivity/` — `reactive()`, `var()`, `watch_*`, `mutate_reactive()`, `data_bind()`
- `textual.textualize.io/guide/screens/` — `Screen` subclass, `SCREENS` dict, `push_screen()`, `ModalScreen`
- `textual.textualize.io/guide/actions/` — `action_` methods, namespaced actions (`app.`, `screen.`)
- `textual.textualize.io/guide/testing/` — `run_test()`, `Pilot`, `pilot.press()`, `pilot.pause()`, snapshot testing
- `textual.textualize.io/widgets/list_view/` — `ListView`, `ListItem`, `clear()`, `append()`, `Highlighted`/`Selected` messages
- `textual.textualize.io/api/on/` — `@on` decorator, CSS selector filtering for message handlers
- `textual.textualize.io/blog/2024/09/15/anatomy-of-a-textual-user-interface/` — `call_from_thread()` practical pattern
- `filesystem-spec.readthedocs.io/en/latest/usage.html` — `fsspec.filesystem("file")`, `ls(detail=True)`, `info()`, `isdir()`
- `docs.astral.sh/uv/concepts/projects/init/` — `uv init --package`, `[project.scripts]`, build backends, `uv sync`
- PyPI JSON API for textual — version 8.0.2 confirmed as latest stable (2026-03-09)

### Secondary (MEDIUM confidence)
- WebSearch cross-reference: fsspec `info()` dict keys include `mtime`, `mode`, `uid`, `gid`, `islink`, `destination` (from GitHub issue #526 and source code references)
- WebSearch cross-reference: `set_keymap()` API (Textual 0.82+), binding IDs, keymap dict format — confirmed from official API docs URL in search results
- `docs.astral.sh/uv/guides/projects/` — `uv add`, `uv run`, entry point activation

### Tertiary (LOW confidence)
- WebSearch: `ListView` performance limit with large item counts — no official benchmark found; flagged as Open Question

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified via PyPI JSON API and official docs on 2026-03-09
- Architecture patterns: HIGH — all patterns verified against official Textual docs; code examples cite official source URLs
- Worker/async patterns: HIGH — verified via official workers guide, API docs, and 2024 blog post
- fsspec info() dict keys: MEDIUM — guaranteed keys (name, size, type) are from spec; extended keys (mtime, mode, uid, gid, islink) from GitHub issue/source search, not official spec page
- ListView performance at scale: LOW — no official benchmark; flagged as Open Question

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (30 days — Textual 8.x is stable; uv moves fast but API is stable)
