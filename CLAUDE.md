# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

probefs is a keyboard-driven, three-pane (miller-columns) TUI file browser built on [Textual](https://textual.textualize.io/). Entry point is `probefs.app:main` (console script `probefs`).

## Commands

```sh
uv sync                                   # install deps + dev group into .venv
uv run probefs                            # run the app
uv run probefs --sftp user@host           # launch straight into the SFTP screen
uv run pytest                             # run all tests
uv run pytest tests/test_file_manager_core.py            # one file
uv run pytest tests/test_file_manager_core.py::test_initial_cwd  # one test
uv run pytest -k "sort"                   # by name pattern
```

There is no linter configured. Python 3.10+ is required (`.python-version` pins 3.12 for local dev).

## Architecture

The layering is deliberate and the boundaries are load-bearing — respect them.

**`fs/probe_fs.py` — the Filesystem Abstraction Layer (FAL).** `ProbeFS` wraps an `fsspec` filesystem and is the *only* place permitted to touch the filesystem. Widgets, screens, rendering, and `FileManagerCore` must never call `os`, `pathlib` I/O, `shutil`, `open()`, `subprocess`, `zipfile`/`tarfile`, or `send2trash` directly — route everything through a `ProbeFS` method (`ls`, `info`, `copy`, `move`, `rename`, `trash`, `read_text`, `read_pdf_text`, `read_archive_listing`, `open_with_default`, `copy_to_clipboard`, `disk_usage`, etc.). This boundary is what makes the SFTP backend a drop-in `fsspec` swap. When adding a new filesystem operation, add a method here first.

**`core/file_manager.py` — pure navigation state machine.** `FileManagerCore` holds `cwd`, `cursor_index`, sort/hidden flags, and back/forward history stacks. `descend`/`ascend`/`jump_to`/`go_back`/`go_forward` are *pure path arithmetic with zero I/O* — they mutate state and return the new path. The screen reacts by spawning a worker that calls `fs.ls()`. Keep it I/O-free; its tests assert this.

**`screens/main.py` — the orchestrator.** `MainScreen` composes two `DirectoryList` panes (parent + current) and a `PreviewPane`, plus `StatusBar` and `FilterBar`. Key patterns:
- **All filesystem I/O happens in `@work(thread=True)` workers**, never on the main thread, so the UI stays responsive. `_load_panes` is the central reload.
- Workers post `Message` subclasses (`DirectoryLoaded`/`DirectoryLoadFailed`) back to the main thread; handlers (`on_directory_loaded`, etc.) do the UI mutation.
- File-op actions follow a fixed shape: `action_*` collects input via a modal (`InputDialog`/`ConfirmDialog`, dismissed with a callback), then fires a named `@work(thread=True)` worker (`_do_copy`, `_do_move`, …). Inside a worker, **all calls back into the app/UI must go through `self.app.call_from_thread(...)`** (e.g. `call_from_thread(self._load_panes)`) or `self.app.notify(...)`.
- `check_action` disables all screen bindings while the `FilterBar` is visible so keys pass through to it.

**`app.py` — `ProbeFSApp` + bindings + theme/keymap setup.** All keybindings live in `BINDINGS` with stable `id="probefs.*"` values and `priority=True`; actions are namespaced `screen.*` so they dispatch to `MainScreen` methods. User keybinding overrides from config are applied via `set_keymap()` and **replace** (not extend) the default key for a given binding ID.

**Theme system.** `theme/loader.py::ThemeLoader` is the *only* place that constructs a Textual `Theme(...)` — it validates every color field with `Color.parse()`, collects *all* errors, and raises `ThemeValidationError` before constructing. `theme/builtin.py` loads the bundled `themes/*.yaml`. Registration order in `app._setup_themes` is critical: register all built-ins, then user themes from `~/.probefs/themes/`, then `theme_file`, and only set `self.theme` last.

**Rendering.** `rendering/columns.py::build_row` is the single place an `fsspec` entry dict becomes DataTable cells. **Cell coloring uses Rich `Text` style strings, never TCSS** — TCSS cannot target individual DataTable cell text. `rendering/metadata.py` holds the formatting helpers (`human_size`, `format_mtime`, `uid_to_name`, `get_category`).

**Icons.** `icons/factory.py::load_icon_set(config)` returns an `IconSet` (`ascii` default / `nerd` opt-in / yaml). Nerd Fonts must be explicitly enabled in config — never auto-detected (impossible over SSH).

## Conventions

- **Config never crashes the app.** `config.py` loaders return empty/default on malformed YAML or `OSError`; `init_config_dir` swallows errors. Invalid config is silently ignored by design — preserve this. User config lives in `~/.probefs/` (`probefs.yaml`, `themes/`, `sftp_hosts.yaml`). SFTP profiles **never store passwords**.
- Paths are manipulated with `PurePosixPath` throughout (string-based, POSIX semantics) for forward-compatibility with remote filesystems — entry `name` from `fsspec` is a full path, so basename is `name.split("/")[-1]`.
- Every module uses `from __future__ import annotations`.
- Tests are plain `pytest`; `FileManagerCore` tests inject a `ProbeFS` but never trigger real I/O. `pytest-textual-snapshot` is available for snapshot tests but none exist yet.
