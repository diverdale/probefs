# Phase 4: Keybinding System and Config Infrastructure - Research

**Researched:** 2026-03-09
**Domain:** Textual 8.x Keymap API, YAML config extension
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| KEYS-01 | User can override any action's keybinding by editing a local YAML keybindings file; overrides take effect on next launch | Textual's `set_keymap()` + `id` on `Binding` is the exact mechanism; YAML loaded via existing `load_config()` infra |
| KEYS-02 | All bindable actions have stable string IDs documented in the keybindings reference; IDs do not change between releases | `Binding.id` field is the stable string ID; document in YAML comments / README; IDs are source-controlled and never auto-generated |
</phase_requirements>

---

## Summary

Textual 8.x (the version installed) ships a first-class keymap override system introduced in 0.82.0. Every `Binding` can carry an `id` field; when the app calls `self.set_keymap(dict)`, Textual replaces the key for any binding whose `id` appears in the dict. The mechanism is built into `BindingsMap.apply_keymap` which is called on every `Screen._binding_chain` evaluation, so it works correctly regardless of which pane has focus.

The existing codebase already has all the plumbing needed: `load_config()` returns a dict, the YAML library (ruamel.yaml) is already in use, and `ProbeFSApp.__init__` is the right place to load the keybindings section and call `set_keymap()`. No changes to the screen-level action methods or Textual internals are required.

The only work is: (1) add stable `id=` strings to every `Binding` in `ProbeFSApp.BINDINGS`, (2) extend `load_config()` / `ProbeFSApp.__init__` to read `config['keybindings']` and pass it to `self.set_keymap()`, (3) add `q` as a quit binding, and (4) document the stable IDs.

**Primary recommendation:** Use Textual's native `Binding.id` + `App.set_keymap()` mechanism. Do not manipulate `BINDINGS` lists at runtime. Do not build a custom key-resolution layer.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Textual | 8.0.2 (installed) | `Binding.id`, `App.set_keymap()`, `App.update_keymap()` | First-class built-in mechanism for runtime key remapping |
| ruamel.yaml | >=0.19.1 (installed) | Parse `keybindings:` section from probefs.yaml | Already in use for config; no new dependency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python dataclasses | stdlib | `Binding` is a frozen dataclass; `with_key()` creates overridden copies | Used internally by Textual's apply_keymap |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `set_keymap()` | Mutate `BINDINGS` class variable at `__init__` time | Class mutation is global, affects all instances; `set_keymap` is instance-scoped and the official API |
| `set_keymap()` | Replace `ProbeFSApp.BINDINGS` with dynamically built list | Loses priority/description metadata; Textual's `apply_keymap` preserves all fields except `key` |
| ruamel.yaml (existing) | pyyaml or tomllib | ruamel.yaml already used; no new dependency needed |

**Installation:** No new dependencies required.

---

## Architecture Patterns

### Recommended Project Structure

```
src/probefs/
├── app.py              # Add id= to all Binding entries; load keybindings in __init__
├── config.py           # Extend load_config() docstring; no logic changes needed
└── keybindings.py      # (NEW) ACTION_IDS constant dict for documentation/reference
```

A `keybindings.py` module is not strictly required — the IDs can live in `app.py` as string literals — but a constants file makes the stable IDs easy to discover and prevents typos.

### Pattern 1: Add `id=` to BINDINGS, Call `set_keymap()` in `__init__`

**What:** Give each `Binding` a stable, human-readable `id`. In `ProbeFSApp.__init__`, after `super().__init__()`, read the `keybindings` key from config and call `self.set_keymap()`.

**When to use:** Always. This is the only pattern needed for Phase 4.

**Example:**
```python
# Source: Textual 8.0.2 binding.py (installed), app.py (installed)
# and https://darren.codes/posts/textual-keymaps/

from textual.binding import Binding

class ProbeFSApp(App):
    BINDINGS = [
        Binding("j", "screen.cursor_down", "Down", priority=True, show=False,
                id="probefs.cursor_down"),
        Binding("down", "screen.cursor_down", "Down", priority=True, show=False,
                id="probefs.cursor_down_arrow"),
        Binding("k", "screen.cursor_up", "Up", priority=True, show=False,
                id="probefs.cursor_up"),
        Binding("up", "screen.cursor_up", "Up", priority=True, show=False,
                id="probefs.cursor_up_arrow"),
        Binding("l", "screen.enter_dir", "Enter dir", priority=True, show=False,
                id="probefs.enter_dir"),
        Binding("enter", "screen.enter_dir", "Enter dir", priority=True, show=False,
                id="probefs.enter_dir_enter"),
        Binding("h", "screen.leave_dir", "Leave dir", priority=True, show=False,
                id="probefs.leave_dir"),
        Binding("backspace", "screen.leave_dir", "Leave dir", priority=True, show=False,
                id="probefs.leave_dir_backspace"),
        Binding(".", "screen.toggle_hidden", "Toggle hidden", priority=True, show=False,
                id="probefs.toggle_hidden"),
        Binding("q", "quit", "Quit", priority=True, show=False,
                id="probefs.quit"),
        Binding("ctrl+c", "quit", "Quit", priority=True, show=False,
                id="probefs.quit_ctrl_c"),
    ]

    def __init__(self) -> None:
        super().__init__()           # sets self._keymap = {}
        config = load_config()
        self._setup_themes(config)
        self._setup_keybindings(config)

    def _setup_keybindings(self, config: dict) -> None:
        """Load user keybinding overrides from config and apply to app keymap.

        safe to call from __init__: set_keymap() calls refresh_bindings()
        which checks _is_mounted and is a no-op if not yet mounted.
        The _keymap dict is applied by Screen._binding_chain on first keypress.
        """
        raw = config.get("keybindings")
        if not isinstance(raw, dict):
            return
        # Textual Keymap is Mapping[str, str] (binding_id -> key_string)
        # Values may be comma-separated for multiple keys: "i,up"
        keymap: dict[str, str] = {
            str(k): str(v) for k, v in raw.items() if k and v
        }
        if keymap:
            self.set_keymap(keymap)
```

### Pattern 2: YAML Keybindings Format

**What:** The `keybindings:` key in `~/.probefs/probefs.yaml` maps stable action IDs to key strings.

**When to use:** User-authored config file.

```yaml
# ~/.probefs/probefs.yaml

# Optional keybinding overrides.
# Keys: stable action IDs (never change between releases).
# Values: a key string, or comma-separated keys for multiple bindings.
#
# Available action IDs:
#   probefs.cursor_down       (default: j)
#   probefs.cursor_down_arrow (default: down)
#   probefs.cursor_up         (default: k)
#   probefs.cursor_up_arrow   (default: up)
#   probefs.enter_dir         (default: l)
#   probefs.enter_dir_enter   (default: enter)
#   probefs.leave_dir         (default: h)
#   probefs.leave_dir_backspace (default: backspace)
#   probefs.toggle_hidden     (default: .)
#   probefs.quit              (default: q)
#   probefs.quit_ctrl_c       (default: ctrl+c)

keybindings:
  probefs.cursor_down: "n"           # remap j -> n
  probefs.cursor_up: "p"             # remap k -> p
  probefs.quit: "q,ctrl+q"          # keep q, also bind ctrl+q
```

### Pattern 3: Overriding Replaces All Keys for That Binding

**What:** When you override a binding ID, ALL original keys for that ID are removed and replaced with the keymap value. If you want to keep the original key AND add a new one, list both in the value.

**When to use:** Any time the user configures a keybinding.

```yaml
# To remap AND keep the original:
keybindings:
  probefs.cursor_down: "n,j"    # n is new, j is kept explicitly

# To just swap:
keybindings:
  probefs.cursor_down: "n"      # j is gone; only n works
```

### Anti-Patterns to Avoid

- **Manipulating `ProbeFSApp.BINDINGS` at runtime:** `BINDINGS` is a class variable. Replacing it on the class affects all instances and breaks Textual's internal `_bindings` cache. Use `set_keymap()` instead.
- **Building a custom key dispatch layer:** Do not intercept `on_key` to manually dispatch actions. Textual's binding chain already handles priority, focus, and action routing. Custom dispatch will break priority semantics.
- **Setting `set_keymap()` after `push_screen()`:** The keymap is applied per-keystroke from `Screen._binding_chain`. Setting it at any point before or after screen push works — but the expected pattern is `__init__` for startup config.
- **Using the same `id` on two different bindings for different actions:** The keymap lookup is by ID; duplicate IDs for different actions will cause one to shadow the other.
- **Forgetting to add `id=` to bindings you want to be overridable:** Bindings without an `id` are silently skipped by `apply_keymap`. If a binding has no `id`, it cannot be remapped.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Runtime key remapping | Custom key-to-action dispatch in `on_key` | `App.set_keymap()` | Textual handles priority, focus scope, and `refresh_bindings` for you |
| Conflict detection | Custom clash checker | `App.handle_bindings_clash()` override | Built into `apply_keymap`; returns `KeymapApplyResult.clashed_bindings` |
| Per-binding key replacement | Rebuilding `BINDINGS` list | `Binding.with_key()` | Used internally; Textual preserves all other fields correctly |
| YAML key normalization | Custom key name mapper | `App._normalize_keymap()` (called by `set_keymap`) | Handles `"?"` -> `"question_mark"` and other character-to-key normalizations automatically |

**Key insight:** Textual 8.x ships the exact mechanism this phase needs. The feature was introduced in 0.82.0 and is present in the installed 8.0.2. Building anything custom here would duplicate work and likely miss edge cases (key normalization, priority preservation, clash detection).

---

## Common Pitfalls

### Pitfall 1: Overriding a Binding Drops the Original Key

**What goes wrong:** User adds `probefs.cursor_down: "n"` to config. Now `j` no longer works — only `n` does.
**Why it happens:** `apply_keymap` removes the old key entry from `key_to_bindings` and adds the new one. The original `j` binding is gone.
**How to avoid:** In docs, clearly state that override values REPLACE, not extend. Show the pattern `"n,j"` for additive remapping.
**Warning signs:** User reports that default keybinding stopped working after adding a custom one.

### Pitfall 2: Binding Without `id` Cannot Be Remapped

**What goes wrong:** A binding in `BINDINGS` has no `id`. User adds it to `keybindings:` in YAML. Nothing changes.
**Why it happens:** `apply_keymap` line 288: `if binding_id is None: continue` — bindings without ID are silently skipped.
**How to avoid:** Every `Binding` in `ProbeFSApp.BINDINGS` MUST have an `id=` field. Verify at startup or in tests.
**Warning signs:** User config has correct ID but key never changes.

### Pitfall 3: Spaces After Commas in Keymap Values

**What goes wrong:** User writes `"n, j"` (with a space) in YAML. The space becomes part of the key name `" j"` which Textual cannot match.
**Why it happens:** `apply_keymap` splits on `","` but does NOT strip spaces (unlike `Binding.make_bindings` which does `key.strip()`). This was a known bug in early 2025 (Textual issue #5694).
**How to avoid:** In `_setup_keybindings`, strip whitespace from each key token: `value.replace(" ", "")` or split-and-strip before passing to `set_keymap`.
**Warning signs:** Remapped binding has no effect despite correct ID.

### Pitfall 4: Calling `set_keymap` Before `super().__init__()`

**What goes wrong:** `self._keymap` does not exist yet. `set_keymap` will raise `AttributeError`.
**Why it happens:** `self._keymap = {}` is set in `App.__init__` at line 712, which is called by `super().__init__()`.
**How to avoid:** Always call `super().__init__()` first, then `_setup_keybindings()`. This is already the pattern in `ProbeFSApp.__init__`.
**Warning signs:** `AttributeError: 'ProbeFSApp' object has no attribute '_keymap'`

### Pitfall 5: YAML Returns Non-String Values

**What goes wrong:** A user writes `probefs.quit: q` without quotes in YAML. ruamel.yaml may parse the value as a Python scalar. The Textual keymap expects `Mapping[str, str]`.
**Why it happens:** YAML auto-types bare values (though single letters like `q` remain strings; numbers like `1` become int).
**How to avoid:** Coerce all values with `str(v)` when building the keymap dict. Already shown in Pattern 1 code example.
**Warning signs:** `TypeError` or silent no-op when user maps to a numeric key.

### Pitfall 6: `priority=True` and Focus

**What goes wrong:** Developer assumes that without `priority=True`, app-level bindings work globally. They don't — without priority, a focused widget that consumes the same key will shadow the app binding.
**Why it happens:** Textual's focus hierarchy: focused widget bindings take precedence over ancestor bindings unless `priority=True`. The `active_bindings` property in `screen.py` line 481 shows a priority binding replaces a non-priority one for the same key.
**How to avoid:** All current probefs bindings use `priority=True`. Keep this. New bindings added by users via keymap preserve the original `priority` flag via `with_key()`.
**Warning signs:** Keybinding works in empty app but fails when a widget is focused.

---

## Code Examples

Verified patterns from official sources:

### Complete `_setup_keybindings` Implementation

```python
# Source: textual/binding.py (installed 8.0.2), textual/app.py (installed 8.0.2)
# Pattern: set_keymap() is safe in __init__ because DOMNode.refresh_bindings()
# guards with `if self._is_mounted:` (dom.py line 1904)

def _setup_keybindings(self, config: dict) -> None:
    """Apply user keybinding overrides from config['keybindings']."""
    raw = config.get("keybindings")
    if not isinstance(raw, dict):
        return
    keymap: dict[str, str] = {}
    for k, v in raw.items():
        if k and v:
            # Strip spaces to handle "n, j" -> "n,j" (see Pitfall 3)
            keymap[str(k)] = str(v).replace(" ", "")
    if keymap:
        self.set_keymap(keymap)
```

### Binding ID Naming Convention

```python
# Source: probefs codebase pattern + darren.codes/posts/textual-keymaps/
# Convention: "probefs.<action_name>" for app-level bindings
# Dual-key actions get separate IDs per key variant

BINDINGS = [
    # Navigation — vim-style
    Binding("j", "screen.cursor_down", "Down",
            priority=True, show=False, id="probefs.cursor_down"),
    Binding("down", "screen.cursor_down", "Down",
            priority=True, show=False, id="probefs.cursor_down_arrow"),
    Binding("k", "screen.cursor_up", "Up",
            priority=True, show=False, id="probefs.cursor_up"),
    Binding("up", "screen.cursor_up", "Up",
            priority=True, show=False, id="probefs.cursor_up_arrow"),
    # Directory traversal — vim-style
    Binding("l", "screen.enter_dir", "Enter dir",
            priority=True, show=False, id="probefs.enter_dir"),
    Binding("enter", "screen.enter_dir", "Enter dir",
            priority=True, show=False, id="probefs.enter_dir_enter"),
    Binding("h", "screen.leave_dir", "Leave dir",
            priority=True, show=False, id="probefs.leave_dir"),
    Binding("backspace", "screen.leave_dir", "Leave dir",
            priority=True, show=False, id="probefs.leave_dir_backspace"),
    # Toggles
    Binding(".", "screen.toggle_hidden", "Toggle hidden",
            priority=True, show=False, id="probefs.toggle_hidden"),
    # Quit — add q as noted in Phase 2 testing
    Binding("q", "quit", "Quit",
            priority=True, show=False, id="probefs.quit"),
    Binding("ctrl+c", "quit", "Quit",
            priority=True, show=False, id="probefs.quit_ctrl_c"),
]
```

### How `apply_keymap` Processes the Override (Textual internals)

```python
# Source: textual/binding.py apply_keymap (installed 8.0.2)
# What happens when user sets keybindings: {probefs.cursor_down: "n"}:
#
# 1. Screen._binding_chain() calls bindings_map.apply_keymap(app._keymap)
# 2. For the "j" binding with id="probefs.cursor_down":
#    - keymap.get("probefs.cursor_down") -> "n"
#    - Delete "j" from key_to_bindings
#    - Create new binding via binding.with_key(key="n", key_display=None)
#    - binding.with_key() uses dataclasses.replace() — preserves priority, action, etc.
#    - Add new_bindings["n"] = [replaced_binding]
# 3. Result: "n" now triggers screen.cursor_down with priority=True
#
# The "down_arrow" binding (id="probefs.cursor_down_arrow") is NOT affected
# because its ID is different. Arrow key continues to work.
```

### Clash Detection Override

```python
# Source: textual/app.py handle_bindings_clash (installed 8.0.2)
# Override this in ProbeFSApp to warn users about key conflicts:

def handle_bindings_clash(
    self, clashed_bindings: set[Binding], node: DOMNode
) -> None:
    """Warn user when their keymap creates a key conflict."""
    for binding in clashed_bindings:
        # Use print() before app is fully running, or self.notify() after
        print(
            f"Warning: keybinding conflict — '{binding.key}' "
            f"was already bound to action '{binding.action}'"
        )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Override `on_key` for custom dispatch | `Binding.id` + `App.set_keymap()` | Textual 0.82.0 | First-class runtime remapping; no custom dispatch needed |
| Mutate `BINDINGS` class variable | `App.set_keymap()` instance method | Textual 0.82.0 | Instance-scoped, safe, works after mount |
| Separate key config file format | Any dict-like config section | N/A | `probefs.yaml` `keybindings:` key is idiomatic |

**Not available in Textual 8.x:**
- Sequential chord bindings (vim-style `gg` for go-to-top): Textual comma-separated keys mean "either key triggers same action" — simultaneous aliases, not sequences. Chord sequences require custom `on_key` logic. NOT needed for Phase 4 per requirements.
- Per-widget keymap overrides: `set_keymap()` is on `App` and applies globally to all bindings in the chain. Widget-level keymap overrides are not a built-in feature.

---

## Open Questions

1. **ID granularity: one ID per physical key vs one ID per action**
   - What we know: Two bindings for the same action (e.g., `j` and `down` for cursor_down) each need separate IDs if the user should be able to remap them independently.
   - What's unclear: Should `j` and `down` share one ID (meaning overriding either replaces both)? The current design in the code examples above gives separate IDs, which gives users maximum flexibility.
   - Recommendation: Use separate IDs per physical key variant. The naming convention `probefs.cursor_down` vs `probefs.cursor_down_arrow` makes the distinction clear.

2. **Where to document stable IDs (KEYS-02)**
   - What we know: IDs must be stable and documented. Phase 4 can put them in YAML comments in the config and/or in a `KEYBINDINGS.md` reference.
   - What's unclear: Whether to emit a default config file on first launch (nice-to-have, Phase 4 success criteria doesn't require it).
   - Recommendation: Embed the reference as comments in a documented YAML example in the README or a `docs/keybindings.md`. No default config file generation needed for Phase 4.

3. **Clash handling UX**
   - What we know: `handle_bindings_clash` is called by Textual when two bindings end up on the same key after keymap application.
   - What's unclear: Whether to emit a warning at startup (before the screen is fully rendered, `print()` to stderr may be swallowed by Textual's terminal takeover).
   - Recommendation: Log clashes to stderr before `App.run()` returns, using a validation pass in `_setup_keybindings` that checks for duplicate keys, rather than relying on `handle_bindings_clash` which fires per-keypress.

---

## Sources

### Primary (HIGH confidence)

- Textual 8.0.2 installed source: `/Users/dalwrigh/dev/probefs/.venv/lib/python3.12/site-packages/textual/binding.py` — `Binding` dataclass fields, `BindingsMap.apply_keymap`, `Keymap` type alias
- Textual 8.0.2 installed source: `/Users/dalwrigh/dev/probefs/.venv/lib/python3.12/site-packages/textual/app.py` — `set_keymap()`, `update_keymap()`, `_keymap` init at line 712
- Textual 8.0.2 installed source: `/Users/dalwrigh/dev/probefs/.venv/lib/python3.12/site-packages/textual/screen.py` — `_binding_chain` applies keymap per keystroke; `active_bindings` priority logic
- Textual 8.0.2 installed source: `/Users/dalwrigh/dev/probefs/.venv/lib/python3.12/site-packages/textual/dom.py` — `refresh_bindings()` guards with `_is_mounted` check (line 1904), making `set_keymap()` in `__init__` safe

### Secondary (MEDIUM confidence)

- https://darren.codes/posts/textual-keymaps/ — Confirmed by installed source: on_mount pattern, `set_keymap` dict format, override-replaces-all-keys gotcha
- https://textual.textualize.io/api/app/ — Confirmed `set_keymap`, `update_keymap`, `handle_bindings_clash` signatures

### Tertiary (LOW confidence)

- https://github.com/Textualize/textual/issues/5694 — Space-in-keymap-values bug mentioned; current installed source does not strip spaces in `apply_keymap` — VERIFY by testing before relying on this behavior

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against installed source code (8.0.2)
- Architecture: HIGH — all patterns derived from reading actual installed Textual source
- Pitfalls: HIGH (Pitfalls 1-4, 6) / MEDIUM (Pitfall 5 — yaml type coercion tested by inspection)
- Keymap API behavior: HIGH — read `apply_keymap`, `set_keymap`, `refresh_bindings` source directly

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (Textual 8.x is the installed version; API stable within minor versions)
