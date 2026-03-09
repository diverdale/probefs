# Phase 5: File Operations and Safety - Research

**Researched:** 2026-03-09
**Domain:** Textual 8.x modal dialogs, fsspec FAL extension, send2trash, shutil, inline rename patterns
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FOPS-01 | User can copy a file or directory to a new location with a confirmation dialog | ModalScreen[bool] for confirm; Input ModalScreen for destination path; ProbeFS.copy() wrapping shutil.copytree/copy2; @work(thread=True) for execution |
| FOPS-02 | User can move a file or directory with a confirmation dialog | Same confirm modal; ProbeFS.mv() already wraps shutil.move (handles dirs); @work(thread=True) |
| FOPS-03 | User can delete a file or directory by sending it to trash (not permanent delete) with a confirmation dialog | ModalScreen[bool] for confirm; send2trash.send2trash() sends to OS trash; raises OSError on failure |
| FOPS-04 | User can rename a file or directory inline | ModalScreen with pre-populated Input (no DataTable inline edit — not supported natively); ProbeFS.mv() for rename-in-place |
| FOPS-05 | User can create a new empty file in the current directory | ModalScreen with Input for name; ProbeFS.touch() wraps fs.touch() |
| FOPS-06 | User can create a new directory in the current directory | ModalScreen with Input for name; ProbeFS.mkdir() wraps fs.mkdir() |
</phase_requirements>

---

## Summary

File operations in probefs require three layers working together: (1) Textual `ModalScreen` dialogs for confirmation and input collection, (2) `ProbeFS` FAL extensions wrapping fsspec and shutil operations, and (3) `@work(thread=True)` workers to keep the event loop unblocked during I/O.

Textual 8.x `ModalScreen[T]` is the correct tool for all dialogs. It dims the background screen, blocks app-level keybindings, and can return typed values to callers via `dismiss(value)`. The caller uses either `push_screen(screen, callback)` for fire-and-forget or `await push_screen_wait(screen)` from within a worker for sequential logic. `push_screen_wait` is async and MUST be called from a `@work` worker — not from a synchronous action method.

The `LocalFileSystem.cp_file` implementation uses `shutil.copyfile` for files and only `makedirs` for directories — it does NOT recursively copy directory contents. For directory copy, ProbeFS must call `shutil.copytree` directly (the FAL wraps shutil; widgets never call shutil). Move is handled correctly via `fs.mv()` → `shutil.move()`. Rename in-place is also `fs.mv()` with same parent directory. `send2trash` version 2.1.0 is NOT in pyproject.toml yet and must be added; it raises `OSError` on macOS failure.

DataTable does NOT support native inline editing. The canonical approach for rename is a `ModalScreen` with an `Input` pre-populated with the current filename. The user edits and submits, which dismisses the modal with the new name.

**Primary recommendation:** All six FOPS requirements use `ModalScreen` dialogs + `@work(thread=True)` workers + ProbeFS FAL methods. No inline DataTable editing. Add `send2trash` to pyproject.toml before implementing FOPS-03.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Textual | 8.0.2 (installed) | `ModalScreen`, `Input`, `Button`, `push_screen_wait` | Built-in; ModalScreen is the canonical TUI dialog pattern |
| fsspec (LocalFileSystem) | installed | `mv()`, `mkdir()`, `makedirs()`, `touch()` via ProbeFS FAL | Already in use; mv/mkdir/touch are correct for local FS |
| shutil (stdlib) | Python 3.10+ | `copytree()` for directory copy; `copy2()` for file copy | LocalFileSystem.cp_file does NOT recurse into directories — must use shutil.copytree directly in ProbeFS |
| send2trash | 2.1.0 | OS-native trash (macOS Trash, Windows Recycle Bin, Linux FreeDesktop trash) | Mandatory per prior decisions; NOT yet in pyproject.toml |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib.PurePosixPath | stdlib | Path arithmetic for rename (same dir) and destination resolution | Used in FileManagerCore already; use for parent-dir calculation |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ModalScreen` + `Input` for rename | DataTable inline cell editing | DataTable has NO native inline editing in Textual 8.x; modal is the only supported approach |
| `shutil.copytree` in ProbeFS for dir copy | `fs.copy(recursive=True)` | fsspec's base-class `copy(recursive=True)` calls `cp_file` per path; `LocalFileSystem.cp_file` for a dir only does `makedirs`, not file copy — copytree handles the full tree with metadata |
| `send2trash.send2trash()` | `fs.rm(recursive=True)` | `rm()` is permanent deletion; send2trash is user-recoverable; prior decisions mandate send2trash |
| `push_screen(callback)` | `await push_screen_wait()` | `push_screen_wait` requires a `@work` worker; callback style works in any action method — use callback for simplicity, push_screen_wait for sequential logic |

**Installation:** Add `send2trash` to pyproject.toml dependencies before FOPS-03 implementation:
```bash
uv add send2trash
```

---

## Architecture Patterns

### Recommended Project Structure

```
src/probefs/
├── fs/
│   └── probe_fs.py        # Add: copy(), mv_or_rename(), mkdir(), touch(), trash()
├── core/
│   └── file_manager.py    # No changes — pure nav state machine
├── screens/
│   └── main.py            # Add: action_copy, action_move, action_delete, action_rename,
│                          #      action_new_file, action_new_dir; op workers
└── widgets/
    └── dialogs.py         # NEW: ConfirmDialog, InputDialog reusable modal screens
```

No new top-level modules required. Dialogs are reusable `ModalScreen` subclasses in a new `widgets/dialogs.py`.

### Pattern 1: Confirmation Dialog (ModalScreen[bool])

**What:** A modal that asks "Are you sure?" and returns `True` (confirmed) or `False`/`None` (cancelled).

**When to use:** Before delete (FOPS-03), copy (FOPS-01), move (FOPS-02).

**Example:**
```python
# Source: Textual 8.0.2 screen.py; confirmed by official docs
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Button, Label
from textual.containers import Vertical

class ConfirmDialog(ModalScreen[bool]):
    """Reusable confirmation modal. dismiss(True) = confirmed, dismiss(False) = cancelled."""

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Label(self._message)
            yield Button("Yes", variant="error", id="yes")
            yield Button("Cancel", variant="primary", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Do NOT await dismiss() from a message handler on the same screen.
        # Call without await — see Pitfall 1.
        self.dismiss(event.button.id == "yes")
```

### Pattern 2: Input Dialog (ModalScreen[str | None])

**What:** A modal that collects a text string from the user. Returns the string or `None` if cancelled.

**When to use:** Rename (FOPS-04), new file name (FOPS-05), new dir name (FOPS-06), copy destination path (FOPS-01).

**Example:**
```python
# Source: Textual 8.0.2 widgets/_input.py, screen.py
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label
from textual.containers import Vertical

class InputDialog(ModalScreen[str | None]):
    """Reusable text input modal. Returns entered string or None if cancelled."""

    def __init__(self, prompt: str, initial_value: str = "") -> None:
        super().__init__()
        self._prompt = prompt
        self._initial = initial_value

    def compose(self) -> ComposeResult:
        with Vertical(id="input-dialog"):
            yield Label(self._prompt)
            yield Input(value=self._initial, id="name-input")
            yield Button("OK", variant="primary", id="ok")
            yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        # Input is focused automatically (AUTO_FOCUS="*"); select all text for rename convenience
        inp = self.query_one("#name-input", Input)
        inp.action_select_all()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter key submits."""
        value = event.value.strip()
        self.dismiss(value if value else None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            value = self.query_one("#name-input", Input).value.strip()
            self.dismiss(value if value else None)
        else:
            self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
```

### Pattern 3: File Operation Worker with Modal Confirmation

**What:** Action method pushes a modal for confirmation/input, then a worker executes the operation. The result triggers a pane refresh.

**When to use:** All FOPS-01 through FOPS-06.

**Two valid approaches:**

**Approach A — callback style (sync action method):**
```python
# Source: Textual 8.0.2 app.py push_screen; probe_fs pattern
def action_delete(self) -> None:
    entry = self.query_one("#pane-current", DirectoryList).get_highlighted_entry()
    if entry is None:
        return
    path = entry["name"]
    name = path.split("/")[-1] if "/" in path else path
    msg = f"Send '{name}' to trash?"

    def _on_confirmed(confirmed: bool | None) -> None:
        if confirmed:
            self._do_trash(path)

    self.app.push_screen(ConfirmDialog(msg), _on_confirmed)

@work(thread=True, exit_on_error=False)
def _do_trash(self, path: str) -> None:
    try:
        from send2trash import send2trash
        send2trash(path)
    except OSError as exc:
        self.app.notify(f"Could not trash: {exc}", severity="error")
        return
    # notify() is thread-safe; _load_panes() must be called via call_from_thread
    self.app.notify(f"Moved to trash")
    self.call_from_thread(self._load_panes)
```

**Approach B — push_screen_wait style (must be in @work):**
```python
# Source: Textual 8.0.2 app.py push_screen_wait (line 2908)
# Note: push_screen_wait raises NoActiveWorker if called outside a worker.
@work(exit_on_error=False)
async def action_delete(self) -> None:
    entry = self.query_one("#pane-current", DirectoryList).get_highlighted_entry()
    if entry is None:
        return
    path = entry["name"]
    name = path.split("/")[-1] if "/" in path else path
    confirmed = await self.app.push_screen_wait(
        ConfirmDialog(f"Send '{name}' to trash?")
    )
    if confirmed:
        await asyncio.get_event_loop().run_in_executor(None, self._trash_sync, path)
        self._load_panes()
```

**Recommendation: use Approach A** (callback style). Approach B requires `@work` on the action itself, which means the action returns a Worker rather than None — this changes action dispatch semantics. Approach A keeps action methods synchronous and delegates I/O to a separate named worker.

### Pattern 4: ProbeFS FAL Extensions

**What:** New methods on `ProbeFS` that maintain the FAL boundary (widgets and screens never call os/shutil directly).

**When to use:** All file operations.

```python
# Source: fsspec/implementations/local.py (installed); stdlib shutil docs
import shutil
from send2trash import send2trash as _send2trash

class ProbeFS:
    # ... existing methods ...

    def copy(self, src: str, dst: str) -> None:
        """Copy file or directory tree to dst.

        For files: uses shutil.copy2 (preserves metadata).
        For directories: uses shutil.copytree (recursive, preserves metadata).
        Raises FileExistsError if dst already exists as a directory.
        Raises FileNotFoundError if src does not exist.
        Raises OSError for permission errors.
        """
        if self._fs.isdir(src):
            shutil.copytree(src, dst)  # raises FileExistsError if dst exists
        else:
            shutil.copy2(src, dst)

    def move(self, src: str, dst: str) -> None:
        """Move file or directory to dst.

        Wraps shutil.move — handles cross-device moves and directories.
        If dst is an existing directory, src is moved inside it.
        Raises OSError / shutil.Error on failure.
        """
        shutil.move(src, dst)

    def rename(self, src: str, new_name: str) -> None:
        """Rename a file or directory in-place (same parent directory).

        new_name is the basename only (not a full path).
        Raises FileExistsError if new_name already exists in parent.
        Raises OSError for permission errors.
        """
        from pathlib import PurePosixPath
        parent = str(PurePosixPath(src).parent)
        dst = str(PurePosixPath(parent) / new_name)
        if self._fs.exists(dst):
            raise FileExistsError(f"{dst!r} already exists")
        self._fs.mv(src, dst)

    def trash(self, path: str) -> None:
        """Send file or directory to OS trash. Never permanent delete.

        Raises OSError on macOS/Windows if trash operation fails.
        On Linux/BSD: raises send2trash.TrashPermissionError (subclass of
        PermissionError) if file is on different device from home dir.
        """
        _send2trash(path)

    def new_file(self, path: str) -> None:
        """Create an empty file at path.

        Uses fs.touch(truncate=True). Raises FileExistsError if already exists.
        Raises OSError for permission errors.
        """
        if self._fs.exists(path):
            raise FileExistsError(f"{path!r} already exists")
        self._fs.touch(path)

    def new_dir(self, path: str) -> None:
        """Create a directory at path.

        Raises FileExistsError if path already exists.
        Raises OSError for permission errors.
        """
        self._fs.mkdir(path, create_parents=False)
        # mkdir raises FileExistsError natively (LocalFileSystem line 45)
```

### Pattern 5: Post-Operation Refresh

**What:** After any file operation completes in a worker, the directory listing must be refreshed.

**When to use:** After every successful FOPS operation.

```python
# Source: probefs screens/main.py existing pattern
# _load_panes() is already defined on MainScreen as @work(thread=True, exclusive=True)
# From a thread worker, call via call_from_thread:

@work(thread=True, exit_on_error=False)
def _do_copy(self, src: str, dst: str) -> None:
    try:
        self.core.fs.copy(src, dst)
    except FileExistsError:
        self.app.notify(f"Destination already exists", severity="warning")
        return
    except OSError as exc:
        self.app.notify(f"Copy failed: {exc}", severity="error")
        return
    self.app.notify("Copied")
    self.call_from_thread(self._load_panes)   # thread-safe
```

**Key rule:** `notify()` is thread-safe (call directly from worker thread). `_load_panes()` is NOT thread-safe (must use `call_from_thread`).

### Pattern 6: New Keybinding Action IDs

**What:** File operation actions follow the same `Binding` + action ID pattern from Phase 4.

**When to use:** Adding all six file operation bindings to `ProbeFSApp.BINDINGS`.

**Proposed keybindings (based on ranger/nnn conventions, avoiding conflicts):**

| Key | Action | Action ID | Conflicts |
|-----|--------|-----------|-----------|
| `y` | Copy | `probefs.copy` | None (not used) |
| `p` | Move/paste | `probefs.move` | None (not used) |
| `d` | Delete to trash | `probefs.delete` | None (not used) |
| `r` | Rename | `probefs.rename` | None (not used) |
| `n` | New file | `probefs.new_file` | None (not used) |
| `ctrl+n` | New directory | `probefs.new_dir` | None (not used) |

**Conflict analysis:** `d` is clear — no existing binding uses `d`. `n` is clear. If the user has remapped any of these via Phase 4 config, the keymap system handles it. All should use `priority=True` to prevent focus stealing by DataTable.

**Alternative for new_dir:** `shift+n` or `ctrl+d`. The question context suggests `d=new dir` but `d` collides with the proposed delete binding — use `ctrl+n` for new directory to avoid conflict.

```python
# Source: app.py existing pattern (Phase 4)
Binding("y", "screen.copy", "Copy", priority=True, show=False, id="probefs.copy"),
Binding("p", "screen.move", "Move", priority=True, show=False, id="probefs.move"),
Binding("d", "screen.delete", "Delete to trash", priority=True, show=False, id="probefs.delete"),
Binding("r", "screen.rename", "Rename", priority=True, show=False, id="probefs.rename"),
Binding("n", "screen.new_file", "New file", priority=True, show=False, id="probefs.new_file"),
Binding("ctrl+n", "screen.new_dir", "New dir", priority=True, show=False, id="probefs.new_dir"),
```

### Anti-Patterns to Avoid

- **Awaiting `dismiss()` from a message handler on the same ModalScreen:** Textual raises `ScreenError` if you `await screen.dismiss()` from within the screen's own message handler. Call `self.dismiss(value)` without `await`.
- **Calling `_load_panes()` directly from a thread worker:** `_load_panes()` is a `@work(exclusive=True)` method — calling it from a thread context without `call_from_thread` violates thread safety. Use `self.call_from_thread(self._load_panes)`.
- **Using `fs.rm(recursive=True)` for delete:** This is permanent deletion. Breaks FOPS-03 requirement. Must use `send2trash` regardless of entry type.
- **Using `fs.copy(recursive=True)` for directory copy:** LocalFileSystem's `cp_file` for directories only creates an empty dir. Use `shutil.copytree` in the ProbeFS FAL.
- **Calling `push_screen_wait` outside a `@work` worker:** Raises `NoActiveWorker` exception (Textual app.py line 2890). Use the callback pattern for synchronous action methods.
- **Putting `send2trash` import inside the FAL method vs. at module top:** Import at top of `probe_fs.py` as a conditional import with a clear error if the package is missing — ensures fast failure at startup, not mid-operation.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OS trash (macOS/Windows/Linux) | Custom per-OS trash logic using os.system or subprocess | `send2trash.send2trash()` | Handles macOS Trash, Windows Recycle Bin, Linux FreeDesktop spec — tested across OS versions |
| Confirmation dialog | Custom key-intercept or overlay widget | `ModalScreen[bool]` | ModalScreen handles focus locking, key blocking, background dimming, dismiss lifecycle |
| Directory copy with metadata | Custom recursive `shutil.copyfile` loop | `shutil.copytree()` | Handles symlinks, permissions, timestamps, ignore patterns, `dirs_exist_ok` flag |
| Thread-to-UI communication | Direct method calls from worker thread | `post_message()` (thread-safe) and `call_from_thread()` | Textual is NOT thread-safe; direct calls cause race conditions and crashes |
| Inline rename in DataTable | DataTable cell editing widget | `ModalScreen` with `Input` | DataTable has no native inline editing in Textual 8.x (confirmed by Discussion #2449) |

**Key insight:** Every "simple" problem in this domain (trash, dialogs, directory copy) has hidden complexity. send2trash alone has platform-specific code paths for macOS Cocoa, Windows IFileOperation, and Linux FreeDesktop. Don't hand-roll any of it.

---

## Common Pitfalls

### Pitfall 1: Awaiting `dismiss()` from a Screen's Own Message Handler

**What goes wrong:** `await self.dismiss(True)` inside `on_button_pressed` raises `ScreenError: Can't await screen.dismiss() from the screen's message handler`.

**Why it happens:** Textual's `dismiss()` internally calls `pop_screen()` which is async. When called from within the screen's message handler, awaiting the return creates a scheduling conflict.

**How to avoid:** Call `self.dismiss(value)` WITHOUT `await` in message handlers. The source explicitly documents this (screen.py line 1898-1900).

**Warning signs:** `ScreenError: Can't await screen.dismiss()...` at runtime.

### Pitfall 2: `push_screen_wait` Outside a Worker

**What goes wrong:** Calling `await self.push_screen_wait(ConfirmDialog(...))` from an action method that is NOT decorated with `@work` raises `NoActiveWorker: push_screen must be run from a worker when wait_for_dismiss is True`.

**Why it happens:** `push_screen_wait` calls `get_current_worker()` and raises if there's no active worker context (app.py line 2887-2891).

**How to avoid:** Use the callback style `push_screen(screen, callback)` for regular action methods. Only use `push_screen_wait` inside `@work` decorated methods.

**Warning signs:** `NoActiveWorker` exception on any file operation trigger.

### Pitfall 3: LocalFileSystem.copy Does NOT Recursively Copy Directory Contents

**What goes wrong:** Calling `self._fs.copy(src_dir, dst_dir, recursive=True)` on a directory creates an empty directory at `dst_dir` but does NOT copy the files inside.

**Why it happens:** `LocalFileSystem.cp_file(dir_path, dst)` only calls `self.mkdirs(dst, exist_ok=True)`. While the base class's `copy()` with `recursive=True` does walk the tree and call `cp_file` on each file, `cp_file` uses `shutil.copyfile` (not `copy2`), losing metadata. For a directory tree, `shutil.copytree` is the correct tool — it preserves permissions, timestamps, and handles symlinks.

**How to avoid:** In `ProbeFS.copy()`, check `isdir(src)` and call `shutil.copytree(src, dst)` for directories, `shutil.copy2(src, dst)` for files.

**Warning signs:** After "copy" of a directory, destination exists but is empty.

### Pitfall 4: send2trash Is Not in pyproject.toml

**What goes wrong:** `ImportError: No module named 'send2trash'` when FOPS-03 is triggered.

**Why it happens:** Prior decisions state "send2trash is in pyproject.toml already" but the actual pyproject.toml only lists `textual`, `fsspec`, `ruamel-yaml`. send2trash is NOT present.

**How to avoid:** Run `uv add send2trash` before implementing FOPS-03. Verify with `uv.lock` that it appears.

**Warning signs:** `ImportError` at runtime on first delete attempt; `uv sync` warnings about missing package.

### Pitfall 5: `shutil.move` Behavior When Destination is an Existing Directory

**What goes wrong:** If `dst` is an existing directory, `shutil.move(src, dst)` moves `src` INSIDE `dst` (not replacing it), resulting in `dst/src_basename`. This silently changes the destination path.

**Why it happens:** `shutil.move` mimics `mv` behavior: if destination is a directory, put source inside it.

**How to avoid:** In `ProbeFS.move()`, check `self._fs.exists(dst)` before calling `shutil.move`. If the destination exists, raise a specific `FileExistsError` that the dialog layer can surface to the user.

**Warning signs:** File "moves" but ends up nested unexpectedly inside the destination directory.

### Pitfall 6: Calling `_load_panes()` From a Thread Worker Without `call_from_thread`

**What goes wrong:** Calling `self._load_panes()` directly from inside a `@work(thread=True)` body creates a new worker from a thread context, which may crash or cause a race condition.

**Why it happens:** `_load_panes()` is a `@work(exclusive=True)` method. Calling it from a thread bypasses Textual's event loop threading model.

**How to avoid:** Always use `self.call_from_thread(self._load_panes)` from thread workers.

**Warning signs:** `RuntimeError` about event loop; occasional crashes after operations complete.

### Pitfall 7: DataTable Rows Re-Index After Refresh

**What goes wrong:** After `_load_panes()` refreshes the directory listing, the cursor jumps to row 0 (first entry).

**Why it happens:** `set_entries()` calls `dt.clear()` then repopulates from scratch. There is no cursor preservation.

**How to avoid:** For non-destructive operations (copy, new file, new dir), preserve cursor position or move to the newly created entry. For destructive operations (delete, move), return to row 0 or the nearest valid entry. This requires the worker to communicate the desired post-op cursor position back to `_load_panes`.

**Warning signs:** After rename, cursor jumps away from the renamed file.

---

## Code Examples

Verified patterns from official/installed sources:

### ModalScreen dismiss (without await — mandatory)

```python
# Source: Textual 8.0.2 screen.py lines 1892-1925
# CORRECT — no await:
def on_button_pressed(self, event: Button.Pressed) -> None:
    self.dismiss(event.button.id == "yes")  # no await

# WRONG — raises ScreenError:
async def on_button_pressed(self, event: Button.Pressed) -> None:
    await self.dismiss(True)  # ScreenError!
```

### push_screen with callback (sync action method)

```python
# Source: Textual 8.0.2 app.py line 2822; official guide
def action_delete(self) -> None:
    entry = self.query_one("#pane-current", DirectoryList).get_highlighted_entry()
    if entry is None:
        return
    path = entry["name"]
    name = path.split("/")[-1] if "/" in path else path

    def _confirmed(result: bool | None) -> None:
        if result:
            self._do_trash(path)

    self.app.push_screen(ConfirmDialog(f"Send '{name}' to trash?"), _confirmed)
```

### @work(thread=True) file operation with thread-safe refresh

```python
# Source: Textual 8.0.2 _work_decorator.py; app.py notify() line 4539 (thread-safe)
# call_from_thread is the correct pattern for calling main-thread methods
from textual import work

@work(thread=True, exit_on_error=False)
def _do_trash(self, path: str) -> None:
    from send2trash import send2trash
    try:
        send2trash(path)
    except OSError as exc:
        self.app.notify(f"Could not trash '{path}': {exc}", severity="error")
        return
    self.app.notify("Moved to Trash")           # thread-safe
    self.call_from_thread(self._load_panes)     # required for non-thread-safe calls
```

### Input widget auto-focus and pre-selection in ModalScreen

```python
# Source: Textual 8.0.2 screen.py AUTO_FOCUS="*" (app.py line 396)
# Input is auto-focused by Textual when ModalScreen is pushed.
# No explicit focus() call needed. Select-all for rename UX:
def on_mount(self) -> None:
    self.query_one(Input).action_select_all()
```

### send2trash usage and exception handling

```python
# Source: send2trash 2.1.0 (PyPI); https://github.com/arsenetar/send2trash
from send2trash import send2trash

try:
    send2trash("/path/to/file_or_dir")  # returns None on success
except OSError as exc:
    # macOS: OSError when Trash operation fails
    # Windows: OSError for general failures
    print(f"Trash failed: {exc}")
except Exception:
    # Linux/BSD: send2trash.TrashPermissionError (subclass of PermissionError)
    # inherits from PermissionError which inherits from OSError
    # so catching OSError is sufficient for all platforms
    raise
```

### ProbeFS.copy with shutil.copytree for directories

```python
# Source: stdlib shutil docs; fsspec/implementations/local.py (installed)
# LocalFileSystem.cp_file for a dir only does makedirs — does NOT copy contents.
import shutil

def copy(self, src: str, dst: str) -> None:
    if self._fs.isdir(src):
        shutil.copytree(src, dst)            # raises FileExistsError if dst exists
    else:
        shutil.copy2(src, dst)               # preserves metadata; overwrites dst if exists
```

### fsspec LocalFileSystem mv (shutil.move)

```python
# Source: fsspec/implementations/local.py line 162-173 (installed)
# LocalFileSystem.mv() uses shutil.move — handles cross-device, directories
# Rename in-place: same parent dir, different name
self._fs.mv(src_path, dst_path)   # or self._fs.rename(src, dst) — same impl
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Roll custom trash with `os.remove` + shell | `send2trash.send2trash()` | Available since ~2013; 2.1.0 Jan 2026 | Single call, OS-native trash, no per-platform branching |
| `push_screen` + poll for result | `push_screen_wait()` in `@work` | Textual ~0.50 | Clean sequential async code in workers; no callbacks needed for worker context |
| Callback-style push_screen | Callback style still valid | Always | For sync action methods, callbacks remain the simpler approach |
| DataTable inline cell editing | ModalScreen + Input (workaround) | Still the state in Textual 8.x (Discussion #2449 open) | Rename UX is modal, not inline — a minor UX difference from some file managers |

**Deprecated/outdated:**
- `os.remove()` / `shutil.rmtree()` for user-initiated delete: these permanently delete; use `send2trash` instead.
- `fs.rm(recursive=True)` via FAL for user-initiated delete: same concern — permanent.

---

## Open Questions

1. **Keybinding `d` for delete vs. future conflict with v2 "cut/yank" pattern**
   - What we know: Current keybindings have `d` free. Ranger uses `dd` for cut, but we're not implementing that in v1.
   - What's unclear: Will v2 batch operations (FOPS-V2-01) want `d` for delete, `y` for yank, `p` for paste (ranger-style)? If so, v1 choices should anticipate v2.
   - Recommendation: Use `d` for delete in v1. Document in ROADMAP that v2 may want `dd` (chord, custom logic) for cut. `d` single-key for delete is consistent with many other TUI file managers.

2. **Copy destination input: full path vs. relative vs. filename-only**
   - What we know: copy requires a destination path. The user must type it. fsspec's `copy` and shutil both accept absolute paths.
   - What's unclear: Should the dialog pre-populate with the current directory, accept relative paths, or only accept basenames for copy-in-place?
   - Recommendation: Pre-populate with `cwd/` (current directory prefix). User appends or edits the filename. Validate that the destination is an absolute path before executing. This is the ranger pattern.

3. **Progress indication for large directory copies**
   - What we know: v2 requirements include a background task manager (UX-V2-03). v1 does not require it.
   - What's unclear: For very large directories, the copy will block the worker thread with no visual feedback.
   - Recommendation: For v1, accept the limitation — no progress bar. The `@work(thread=True)` keeps the UI responsive (user can still navigate). Add a "Copy in progress..." notification at start, "Copy complete" at end. v2 adds cancellation + progress.

4. **send2trash error on read-only files on macOS**
   - What we know: `send2trash` raises `OSError` for generic failures on macOS.
   - What's unclear: Whether send2trash handles the case where a file is locked/read-only on macOS (Finder can trash read-only files by prompting for auth; command-line may get Permission denied).
   - Recommendation: Wrap `send2trash` call in `try/except OSError` and surface a `notify(..., severity="error")` with the exception message. Do not retry or prompt for authentication in v1.

---

## Sources

### Primary (HIGH confidence)

- Textual 8.0.2 installed source `/Users/dalwrigh/dev/probefs/.venv/lib/python3.12/site-packages/textual/screen.py` — `ModalScreen` class, `dismiss()` implementation (lines 1892-1925), `action_dismiss()`, `AUTO_FOCUS`, `push_screen_wait` NoActiveWorker guard (line 2890)
- Textual 8.0.2 installed source `/Users/dalwrigh/dev/probefs/.venv/lib/python3.12/site-packages/textual/app.py` — `push_screen()` signature, `push_screen_wait()` (lines 2908-2926), `notify()` thread-safety docs (line 4552), `AUTO_FOCUS = "*"` (line 396)
- Textual 8.0.2 installed source `/Users/dalwrigh/dev/probefs/.venv/lib/python3.12/site-packages/textual/widgets/_input.py` — `Input.BINDINGS` (lines 75-133), `Submitted` message (lines 300-319), `Changed` message (lines 277-297), no Escape binding defined
- Textual 8.0.2 installed source `/Users/dalwrigh/dev/probefs/.venv/lib/python3.12/site-packages/textual/_work_decorator.py` — `@work` decorator signature, `thread=True`, `exclusive=True` parameters
- fsspec installed source `/Users/dalwrigh/dev/probefs/.venv/lib/python3.12/site-packages/fsspec/spec.py` — `copy()`, `mv()`, `touch()`, `rm()`, `mkdir()`, `mkdirs()` implementations
- fsspec installed source `/Users/dalwrigh/dev/probefs/.venv/lib/python3.12/site-packages/fsspec/implementations/local.py` — `LocalFileSystem.cp_file` uses `shutil.copyfile` for files, `makedirs` for dirs (lines 132-143); `mv` uses `shutil.move` (lines 162-173); `rm` uses `shutil.rmtree` (lines 191-204)
- Python stdlib `shutil` docs — `copytree(dirs_exist_ok)`, `copy2`, `move` behavior verified against https://docs.python.org/3/library/shutil.html

### Secondary (MEDIUM confidence)

- https://textual.textualize.io/guide/screens/ — ModalScreen pattern confirmed by installed source; `push_screen_wait` requires worker context
- https://textual.textualize.io/api/app/ — `push_screen` with callback confirmed; `push_screen_wait` return type
- https://github.com/arsenetar/send2trash — send2trash 2.1.0 (Jan 2026); `OSError` for macOS failures; `TrashPermissionError(PermissionError)` for Linux FreeDesktop edge cases
- https://textual.textualize.io/guide/workers/ — `call_from_thread`, thread-safety rules, `post_message` thread-safety confirmed

### Tertiary (LOW confidence)

- https://github.com/Textualize/textual/discussions/2449 — DataTable inline editing not supported (open discussion from 2023, no resolution found in 8.x). Verified by absence of inline-edit methods in installed DataTable source.
- https://github.com/ranger/ranger/wiki/Official-user-guide — keybinding conventions (yy=copy, pp=paste, dd=cut, cw=rename) for UX alignment. Not authoritative for probefs — used as ecosystem reference only.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against installed source and official docs
- Architecture patterns: HIGH — all patterns derived from reading actual installed Textual 8.0.2 source
- ProbeFS FAL extension: HIGH — fsspec LocalFileSystem source read directly; shutil API from stdlib docs
- send2trash availability: HIGH (library exists, API confirmed) / NOTE: not yet in pyproject.toml (must add)
- Pitfalls: HIGH — derived from reading actual source code, not speculation
- Keybinding recommendations: MEDIUM — ranger conventions used as reference; actual choices are discretionary

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (Textual 8.x, fsspec stable; send2trash 2.1.0 released Jan 2026)
