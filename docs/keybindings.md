# probefs Keybinding Reference

All bindable actions have a stable string ID in the form `probefs.<action>`.
These IDs do not change between releases — you can safely use them in config files.

## Action IDs

| Action ID | Default Key | Description |
|-----------|-------------|-------------|
| `probefs.cursor_down` | `j` | Move cursor down |
| `probefs.cursor_down_arrow` | `down` | Move cursor down (arrow key) |
| `probefs.cursor_up` | `k` | Move cursor up |
| `probefs.cursor_up_arrow` | `up` | Move cursor up (arrow key) |
| `probefs.enter_dir` | `l` | Enter directory |
| `probefs.enter_dir_enter` | `enter` | Enter directory (Enter key) |
| `probefs.leave_dir` | `h` | Leave to parent directory |
| `probefs.leave_dir_backspace` | `backspace` | Leave to parent directory (Backspace) |
| `probefs.toggle_hidden` | `.` | Toggle hidden file visibility |
| `probefs.quit` | `q` | Quit probefs |
| `probefs.quit_ctrl_c` | `ctrl+c` | Quit probefs |

## Overriding Keybindings

Add a `keybindings:` section to `~/.probefs/probefs.yaml`:

```yaml
keybindings:
  probefs.cursor_down: "n"       # remap j -> n (j no longer works)
  probefs.cursor_up: "p"         # remap k -> p
  probefs.quit: "q,ctrl+q"       # keep q, also bind ctrl+q
```

Overrides take effect on the next launch.

### Replace semantics

An override **replaces** all original keys for that binding ID.
To keep the default key and add a new one, list both:

```yaml
keybindings:
  probefs.cursor_down: "n,j"    # n is new; j is kept explicitly
```

To swap to a new key only:

```yaml
keybindings:
  probefs.cursor_down: "n"      # j is gone; only n works
```

### Multiple keys

Comma-separated values bind multiple keys to the same action (not key sequences):

```yaml
keybindings:
  probefs.quit: "q,ctrl+c,ctrl+q"   # any of these three quits
```

Note: probefs does not support chord/sequence bindings (e.g. `gg`).

### Key conflicts

If two bindings end up on the same physical key after remapping, the last registration wins.
probefs does not warn about conflicts — review your config carefully.
