# Phase 6: Preview Pane and Status Bar - Research

**Researched:** 2026-03-09
**Domain:** Textual 8.0.2 widget rendering, Rich Syntax, async file I/O, status bar layout
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PREV-01 | User can see a syntax-highlighted text preview of the focused file in the right pane | Rich Syntax + Static.update() — direct renderable injection, no extra deps |
| PREV-02 | Preview pane shows directory listing when a directory is focused | Reuse `DirectoryList.set_entries()` via ContentSwitcher inside PreviewPane |
| DISP-04 | A status bar displays the current path, item count, and free space | Custom `StatusBar` Widget with reactive attributes + ProbeFS.disk_usage() method |
</phase_requirements>

---

## Summary

Phase 6 replaces the stub `PreviewPane` widget with a fully functional two-mode widget: syntax-highlighted file preview and directory listing. The infrastructure (message routing, worker pattern, three-pane layout) is already in place from Phases 1–5. This phase is primarily body changes to existing stubs plus additive layout changes.

Rich 14.3.3 is already installed as a Textual dependency. `Syntax.from_path()` auto-detects file type via Pygments, falls back to `default` lexer for unknown extensions, and returns a `ConsoleRenderable` that `Static.update()` accepts directly as `VisualType`. No additional syntax dependencies are needed — `textual[syntax]` (tree-sitter) is explicitly NOT required for this approach.

The status bar (`DISP-04`) requires: (1) a new `ProbeFS.disk_usage(path)` FAL boundary method wrapping `shutil.disk_usage`, (2) a new `ProbeFS.read_text(path, max_bytes)` method for file preview, (3) a layout refactor in `main.py` and `probefs.tcss` to wrap the three-pane `Horizontal` in a `Vertical` with a `StatusBar` widget below, and (4) Textual's built-in `Footer` widget yielded from `MainScreen.compose()` for the key-hint bar (it auto-docks to bottom).

**Primary recommendation:** Use `Rich Syntax + Static.update()` for file preview (no new deps), `DirectoryList` reused inside `PreviewPane` for directory mode, `Footer` for key hints (already self-docking), and a custom `StatusBar(Widget)` with reactive strings for path/count/space updated via worker messages.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.0.2 | TUI framework — widgets, reactivity, workers | Locked project decision |
| rich | 14.3.3 | `Syntax` renderable for highlighted preview | Already installed (Textual dep); no new dep needed |
| shutil (stdlib) | stdlib | `disk_usage()` for free space | Standard library; accessed only through ProbeFS FAL |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| mimetypes (stdlib) | stdlib | Extension-based binary type hint before reading | First-pass filter before null-byte check |
| pygments | transitive via rich | Lexer auto-detection for `Syntax.from_path()` | Already present; no direct import needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `Rich Syntax + Static` | `TextArea.code_editor(read_only=True)` | TextArea requires `textual[syntax]` extra for tree-sitter highlighting; adds ~50MB of binary deps. Rich Syntax uses Pygments (already present) and is simpler for read-only display. |
| Custom `StatusBar(Widget)` | Extend Textual `Footer` | Footer only renders key bindings — it cannot display path/count/space. Custom widget required. |
| `Footer` for key hints | Custom horizontal bar | Footer auto-docks bottom, reads BINDINGS with `show=True`, requires zero maintenance. Use it. |
| Worker + `post_message` for preview | `call_from_thread(Static.update)` | Both work; `post_message` is explicitly thread-safe per Textual docs. Prefer message-based for consistency with existing codebase pattern. |

**Installation:**
```bash
# No new runtime dependencies — all required packages are already installed
# Rich and Pygments are transitive Textual dependencies
```

---

## Architecture Patterns

### Recommended Project Structure Changes
```
src/probefs/
├── fs/
│   └── probe_fs.py          # ADD: read_text(path, max_bytes), disk_usage(path)
├── widgets/
│   ├── preview_pane.py      # REPLACE stub body — two-mode: file preview + dir listing
│   ├── status_bar.py        # NEW: StatusBar widget with reactive path/count/space
│   └── directory_list.py    # UNCHANGED — reused inside PreviewPane for dir mode
├── screens/
│   └── main.py              # ADD: StatusBar + Footer to compose(); wire cursor→status updates
└── probefs.tcss             # MODIFY: Screen layout + StatusBar/Footer TCSS
```

### Pattern 1: Two-Mode PreviewPane with ContentSwitcher

**What:** `PreviewPane` composes two children: a `Static` (file mode) and a `DirectoryList` (directory mode). A `ContentSwitcher` toggles between them based on entry type.

**When to use:** Whenever a single widget needs to display fundamentally different content types without rebuild.

**Example:**
```python
# Source: verified against Textual docs + DirectoryList existing code
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, ContentSwitcher
from probefs.widgets.directory_list import DirectoryList

class PreviewPane(Widget):

    class FilePreviewReady(Message):
        def __init__(self, content, path: str) -> None:
            self.content = content   # Rich Syntax renderable OR str for errors
            self.path = path
            super().__init__()

    class DirPreviewReady(Message):
        def __init__(self, entries: list[dict], path: str) -> None:
            self.entries = entries
            self.path = path
            super().__init__()

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial="preview-file"):
            yield Static("", id="preview-file")
            yield DirectoryList(id="preview-dir")

    def show_entry(self, entry: dict) -> None:
        """Called from MainScreen on cursor change. Dispatches to correct worker."""
        ...
```

### Pattern 2: Async File Read Worker (non-blocking)

**What:** `@work(thread=True, exclusive=True)` worker reads the file in a thread, posts a message with the `Rich Syntax` renderable back to main thread. `exclusive=True` cancels pending workers when cursor moves quickly.

**When to use:** All file I/O in this project. Never block the main thread.

**Example:**
```python
# Source: Textual workers docs + existing _load_panes pattern in main.py
@work(thread=True, exclusive=True, exit_on_error=False)
def _load_file_preview(self, path: str) -> None:
    """Worker: read file, build Rich Syntax, post FilePreviewReady."""
    from rich.syntax import Syntax
    try:
        text = self.core.fs.read_text(path, max_bytes=512 * 1024)
    except (OSError, UnicodeDecodeError) as exc:
        self.post_message(PreviewPane.FilePreviewReady(str(exc), path))
        return
    syntax = Syntax(text, lexer=_detect_lexer(path), theme="ansi_dark",
                    line_numbers=True, word_wrap=False)
    self.post_message(PreviewPane.FilePreviewReady(syntax, path))

def on_preview_pane_file_preview_ready(self, event: PreviewPane.FilePreviewReady) -> None:
    static = self.query_one("#preview-file", Static)
    static.update(event.content)   # Rich Syntax is VisualType — accepted directly
```

### Pattern 3: Reactive StatusBar

**What:** `StatusBar(Widget)` with three reactive string attributes. `watch_` methods call `Label.update()`. MainScreen updates the reactive attrs after every cursor change and directory load.

**When to use:** Any single-line status display that must reflect changing state.

**Example:**
```python
# Source: Textual reactivity docs — watch_ pattern
from textual.reactive import reactive
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Label
from textual.containers import Horizontal

class StatusBar(Widget):
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        layout: horizontal;
    }
    """
    path = reactive("")
    item_count = reactive(0)
    free_space = reactive("")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("", id="sb-path")
            yield Label("", id="sb-count")
            yield Label("", id="sb-space")

    def watch_path(self, value: str) -> None:
        self.query_one("#sb-path", Label).update(value)

    def watch_item_count(self, value: int) -> None:
        self.query_one("#sb-count", Label).update(f"{value} items")

    def watch_free_space(self, value: str) -> None:
        self.query_one("#sb-space", Label).update(value)
```

### Pattern 4: Layout Refactor — Vertical Wrapper

**What:** Current `MainScreen.compose()` yields panes directly into a `Horizontal`. Adding `Footer` and `StatusBar` below requires wrapping in a `Vertical`.

**Why needed:** `Screen` has `layout: vertical` by default, but `probefs.tcss` overrides this with `Screen { layout: horizontal }`. That override must be removed and replaced with an explicit `Horizontal` container for the three panes, with `StatusBar` and `Footer` as siblings below.

**TCSS change:**
```css
/* REMOVE: Screen { layout: horizontal; } */

/* ADD: */
#panes {
    layout: horizontal;
    height: 1fr;
}
StatusBar {
    height: 1;
    dock: bottom;
}
```

**compose() change:**
```python
def compose(self) -> ComposeResult:
    with Horizontal(id="panes"):
        yield DirectoryList(id="pane-parent")
        yield DirectoryList(id="pane-current")
        yield PreviewPane(id="pane-preview")
    yield StatusBar(id="status-bar")
    yield Footer()
```

Note: `Footer` auto-docks to bottom via its own `DEFAULT_CSS` (`dock: bottom; height: 1`). `StatusBar` also docks bottom. Textual stacks bottom-docked widgets in compose order — yield `StatusBar` before `Footer` so StatusBar appears above the Footer key-hints.

### Anti-Patterns to Avoid

- **Blocking the main thread for file reads:** Never call `ProbeFS.read_text()` directly in `show_entry()` — always use a `@work(thread=True)` worker.
- **Calling `Static.update()` from a worker thread:** `post_message()` is thread-safe; UI updates are not. Post a message with the `Syntax` renderable and handle it on the main thread.
- **Using `TextArea` for read-only preview:** Requires `textual[syntax]` extra (tree-sitter binaries, large install). Rich Syntax uses the already-installed Pygments.
- **Calling `shutil.disk_usage()` from widget code:** FAL boundary — only `ProbeFS` methods. Add `ProbeFS.disk_usage(path)` and call that.
- **Reading entire large files:** Cap at 512KB (see Pitfall 2). `ProbeFS.read_text(path, max_bytes=524288)`.
- **Assuming `Footer` works with Screen bindings:** Confirmed it does — Footer reads the focused widget's available bindings at the screen level. App-level bindings with `show=True` will appear.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Key hint bar | Custom horizontal binding display widget | `textual.widgets.Footer` | Auto-docks, auto-reads BINDINGS, auto-filters `show=False`, zero maintenance |
| Syntax highlighting | Custom ANSI escape code renderer | `rich.syntax.Syntax` | Pygments already installed; handles 500+ languages; Textual accepts it as VisualType |
| Binary detection | Custom magic byte parser | Null-byte check in first 8KB | Simple, dependency-free, correct for 99% of cases; no `python-magic` needed |
| Lexer detection | Custom extension→language map | `Syntax.from_path()` auto-detection | Pygments covers all standard extensions; falls back to `default` lexer gracefully |

**Key insight:** Rich is already present as a Textual dependency. Using `Syntax.from_path()` + `Static.update()` is a zero-dep solution that leverages the entire Pygments ecosystem.

---

## Common Pitfalls

### Pitfall 1: Race Condition on Fast Cursor Movement

**What goes wrong:** User moves cursor quickly through 10 files. 10 `_load_file_preview` workers start. Workers complete out of order — an older file's preview overwrites the current one.

**Why it happens:** Each worker runs independently; slower disk reads for larger files mean earlier workers finish last.

**How to avoid:** Use `@work(exclusive=True)` — Textual cancels any pending worker of the same method before starting a new one. Check `get_current_worker().is_cancelled` before posting the final message.

**Warning signs:** Preview flickers between multiple different files when scrolling quickly.

### Pitfall 2: Large File Hangs Preview

**What goes wrong:** Focusing a 50MB log file causes the worker to read the entire file into memory, builds a massive `Syntax` renderable, and either OOMs or makes the preview pane unresponsive.

**Why it happens:** `Syntax.from_path()` reads the entire file without a size limit.

**How to avoid:** Use `ProbeFS.read_text(path, max_bytes=524288)` (512KB cap) in the worker. If `file_size > max_bytes`, show a truncated preview with a note: `"[dim]--- truncated at 512KB ---[/dim]"`. 512KB covers ~15,000 lines of typical source code.

**Warning signs:** Preview pane hangs/freezes when focusing large files.

### Pitfall 3: Binary File Decode Error

**What goes wrong:** Focusing a PNG or compiled binary causes `UnicodeDecodeError` when the worker attempts `read_text()`, crashing the worker silently (since `exit_on_error=False`).

**Why it happens:** Binary files contain non-UTF-8 byte sequences.

**How to avoid:** Two-layer protection: (1) check file extension via `mimetypes.guess_type()` for known binary types before reading; (2) wrap `read_text()` in `try/except UnicodeDecodeError` and show `"[dim]Binary file — preview unavailable[/dim]"`. Add `ProbeFS.read_text()` with `errors='replace'` fallback or explicit binary check.

**Warning signs:** Empty or error preview for image/binary files.

### Pitfall 4: StatusBar Calls ProbeFS Off-Thread

**What goes wrong:** `StatusBar` or `MainScreen` calls `ProbeFS.disk_usage()` directly on the main thread inside `on_directory_list_entry_highlighted`, blocking the UI during slow filesystem stat calls (network filesystems).

**Why it happens:** `disk_usage()` is a syscall that can block on network mounts.

**How to avoid:** Call `ProbeFS.disk_usage()` from within the `_load_panes` worker (already a thread) and include the result in the `DirectoryLoaded` message, or use a dedicated short worker for status updates.

### Pitfall 5: ContentSwitcher Breaks DirectoryList's DataTable State

**What goes wrong:** When `ContentSwitcher` hides the `#preview-dir` DirectoryList and then re-shows it, the DataTable's internal state (cursor position, columns) may be stale or columns may have been cleared.

**Why it happens:** Textual's `ContentSwitcher` uses CSS `display: none` / `display: block` to toggle children — it does NOT mount/unmount. The DataTable remains mounted but invisible. When re-shown, calling `set_entries()` with `dt.clear(columns=False)` is safe (same pattern as existing `DirectoryList`).

**Warning signs:** Directory preview shows wrong entries or empty table after switching back from file preview.

### Pitfall 6: Footer Not Showing Screen-Level Bindings

**What goes wrong:** Footer appears but shows no key hints for the file browser navigation keys.

**Why it happens:** All BINDINGS in `ProbeFSApp` have `show=False`. The Footer reads from the focused widget's effective bindings filtered by `show=True`.

**How to avoid:** For the key-hint bar to show useful bindings, either (a) set `show=True` on the key bindings you want displayed, or (b) add a small set of representative bindings with `show=True` to `ProbeFSApp.BINDINGS` for the Footer to render. All current bindings in `app.py` use `show=False` — this must be changed for at least the primary navigation keys.

**Warning signs:** Footer widget appears as an empty bar with no key labels.

---

## Code Examples

Verified patterns from official sources and in-venv inspection:

### Static.update() with Rich Syntax renderable
```python
# Source: Verified — rich.syntax.Syntax is_renderable()==True;
#         Static.update() accepts VisualType = RenderableType | SupportsVisual | Visual;
#         RenderableType includes ConsoleRenderable which Syntax implements.
from rich.syntax import Syntax
from textual.widgets import Static

syntax = Syntax.from_path(
    path,
    encoding="utf-8",
    theme="ansi_dark",     # uses terminal color scheme — best for TUI
    line_numbers=True,
    word_wrap=False,
    indent_guides=False,
)
static_widget.update(syntax)  # thread-safe via post_message pattern
```

### Rich Syntax constructor (verified via inspect)
```python
# Source: inspect.signature(Syntax.__init__) on Rich 14.3.3
Syntax(
    code,               # str
    lexer,              # str — language name or Pygments lexer ID
    theme="monokai",    # default; use "ansi_dark" for terminal-aware colors
    dedent=False,
    line_numbers=False,
    start_line=1,
    line_range=None,    # tuple (start, end) for partial display
    highlight_lines=None,
    code_width=None,
    tab_size=4,
    word_wrap=False,
    background_color=None,
    indent_guides=False,
    padding=0,
)
```

### Syntax.from_path() constructor (verified via inspect)
```python
# Source: inspect.signature(Syntax.from_path) on Rich 14.3.3
Syntax.from_path(
    path,               # str or Path
    encoding="utf-8",
    lexer=None,         # None = auto-detect from extension via Pygments
    theme="monokai",
    line_numbers=False,
    ...
)
# Fallback: unknown extensions get lexer="default" (plain text, no colors)
# Verified: .tcss → lexer="default", .py → lexer="python"
```

### Binary detection (no deps)
```python
# Source: standard Python pattern, verified in-venv
def _is_binary(path: str, chunk_size: int = 8192) -> bool:
    """Detect binary files by null byte presence in first chunk."""
    try:
        with open(path, "rb") as f:
            return b"\x00" in f.read(chunk_size)
    except OSError:
        return True
```

### shutil.disk_usage (verified in-venv)
```python
# Source: stdlib shutil, verified: shutil.disk_usage('/') returns usage(total, used, free)
import shutil
usage = shutil.disk_usage(path)
# usage.total, usage.used, usage.free — all in bytes
free_gb = usage.free / (1024 ** 3)
free_str = f"{free_gb:.1f} GB free"
```

### Footer auto-docking (verified in-venv DEFAULT_CSS)
```python
# Source: Footer.DEFAULT_CSS verified in Textual 8.0.2
# Footer docks itself: dock: bottom; height: 1;
# No explicit TCSS needed. Just yield Footer() in compose().
from textual.widgets import Footer
def compose(self) -> ComposeResult:
    yield Footer()  # self-docking, height: 1
```

### Worker with exclusive + cancellation check
```python
# Source: Textual workers docs pattern
from textual import work
from textual.worker import get_current_worker

@work(thread=True, exclusive=True, exit_on_error=False)
def _load_file_preview(self, path: str) -> None:
    worker = get_current_worker()
    # ... do I/O ...
    if not worker.is_cancelled:
        self.post_message(SomeMessage(result))
```

### Layout with Horizontal panes + StatusBar + Footer
```python
# Source: Textual layout docs + in-venv DEFAULT_CSS inspection
# Screen has layout: vertical by default.
# Current TCSS override "Screen { layout: horizontal }" must be replaced.

# main.py compose():
def compose(self) -> ComposeResult:
    with Horizontal(id="panes"):
        yield DirectoryList(id="pane-parent")
        yield DirectoryList(id="pane-current")
        yield PreviewPane(id="pane-preview")
    yield StatusBar(id="status-bar")
    yield Footer()

# probefs.tcss — replace "Screen { layout: horizontal }" with:
# #panes {
#     layout: horizontal;
#     height: 1fr;
# }
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom syntax widget | `Rich Syntax` + `Static.update()` | Rich existed from start | No new deps; Pygments auto-detects languages |
| Manual thread updates via `call_from_thread` | `post_message()` (thread-safe) | Always supported | Cleaner; matches existing codebase pattern |
| `TextArea` for read-only code display | `Static` + `Rich Syntax` | Textual 0.x era | TextArea adds tree-sitter dep; overkill for read-only |

**Deprecated/outdated:**
- `TextArea.code_editor(read_only=True)`: Valid but requires `textual[syntax]` — overkill for a read-only preview pane. Not recommended here.

---

## Open Questions

1. **Footer vs. custom key-hint bar for DISP-04 adjacency**
   - What we know: User requested a "footer key-hint bar" which `Footer` handles perfectly. `Footer` reads `BINDINGS` with `show=True`.
   - What's unclear: Current `app.py` has ALL bindings with `show=False`. The planner must decide which bindings to expose with `show=True` for the Footer to be non-empty.
   - Recommendation: Set `show=True` on the primary navigation bindings (j/k/l/h/enter/q) in `ProbeFSApp.BINDINGS`. Use `key_display` to show shorter labels (e.g., `key_display="j/k"` for combined up/down).

2. **Rich Syntax theme vs. Textual theme coordination**
   - What we know: `theme="ansi_dark"` on `Syntax` uses terminal ANSI colors, which respects whatever the terminal/user has set. `theme="monokai"` (default) uses fixed 24-bit colors.
   - What's unclear: Whether `ansi_dark` will look good against the probefs theme backgrounds.
   - Recommendation: Use `theme="ansi_dark"` as the default, expose it as a config option in `~/.probefs/probefs.yaml` (e.g., `preview_theme: ansi_dark`).

3. **File size threshold for "too large to preview"**
   - What we know: 512KB covers ~15,000 lines. Files larger than ~1MB are unusual source files.
   - What's unclear: Is 512KB right for the user's use case?
   - Recommendation: Hard-cap at 512KB (524,288 bytes). Show truncation notice. Make it a constant in `ProbeFS` or `PreviewPane`.

4. **Where to call disk_usage — in the pane cursor worker or separately**
   - What we know: `disk_usage` is a fast syscall on local filesystems but can block on network mounts. The FAL boundary requires it to go through ProbeFS.
   - What's unclear: Whether to include it in `_load_panes` worker or fire a separate dedicated worker.
   - Recommendation: Include `disk_usage()` in the `_load_panes` worker since it already runs in a thread. Pass the result in the `DirectoryLoaded` message for the "current" pane. No separate worker needed.

---

## Sources

### Primary (HIGH confidence)
- Textual 8.0.2 installed package — `inspect.signature`, `DEFAULT_CSS` inspection on `Footer`, `Static`, `Vertical`, `Horizontal`, `Screen`
- Rich 14.3.3 installed package — `inspect.signature(Syntax.__init__)`, `inspect.signature(Syntax.from_path)`, `is_renderable(Syntax())` verified True
- `shutil.disk_usage('/')` — verified in-venv, returns `usage(total, used, free)` namedtuple
- Existing codebase — `preview_pane.py`, `main.py`, `directory_list.py`, `probe_fs.py`, `probefs.tcss` read directly

### Secondary (MEDIUM confidence)
- https://textual.textualize.io/widgets/footer/ — Footer auto-docks, reads `show=True` bindings
- https://textual.textualize.io/widgets/static/ — `Static.update()` accepts `VisualType` (Rich renderables)
- https://textual.textualize.io/guide/workers/ — `@work(thread=True, exclusive=True)`, `post_message` thread-safe, `call_from_thread` for direct calls
- https://textual.textualize.io/guide/reactivity/ — `reactive` + `watch_` pattern for StatusBar
- https://rich.readthedocs.io/en/stable/syntax.html — `Syntax.from_path()`, `theme="ansi_dark"`, `line_numbers`
- https://textual.textualize.io/how-to/design-a-layout/ — Vertical wrapper, `height: 1fr` for main + `height: 1; dock: bottom` for status bar

### Tertiary (LOW confidence)
- Binary null-byte detection pattern — multiple web sources agree, standard Python practice, no single canonical doc

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages inspected in-venv; APIs verified by signature inspection
- Architecture patterns: HIGH — based on existing codebase patterns + official Textual docs
- Pitfalls: HIGH for P1/P2/P3 (common async/IO), MEDIUM for P5 (ContentSwitcher behavior inferred from docs)
- Layout refactor: HIGH — Screen DEFAULT_CSS verified; Footer DEFAULT_CSS verified

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (Textual 8.x is stable; Rich 14.x is stable)
