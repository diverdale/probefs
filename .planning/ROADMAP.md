# Roadmap: probefs

## Overview

probefs is built in seven phases that follow a strict dependency order dictated by the async architecture. Phase 1 establishes the non-negotiable foundation: the Filesystem Abstraction Layer and async worker pattern that every subsequent phase builds on. Phases 2-6 layer in the visible product — rendering, theming, keybindings, file operations, and preview — in an order where each phase can be verified on its own before the next begins. Phase 7 proves the distribution story on a clean install before v1 ships.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Core Scaffold and Async Architecture** - Three-pane layout with FAL and async worker pattern for all I/O
- [ ] **Phase 2: Directory Rendering and Icon System** - File metadata columns, type coloring, icon themes, symlinks, hidden file toggle
- [ ] **Phase 3: Theme System** - YAML theme loading, built-in themes, runtime theme switching
- [ ] **Phase 4: Keybinding System and Config Infrastructure** - User YAML keybinding overrides and stable action IDs
- [ ] **Phase 5: File Operations and Safety** - Copy, move, delete, rename, create — all with confirmation dialogs
- [ ] **Phase 6: Preview Pane and Status Bar** - Syntax-highlighted preview and status bar
- [ ] **Phase 7: Distribution** - PyPI/pipx and Homebrew packaging verified on clean install

## Phase Details

### Phase 1: Core Scaffold and Async Architecture
**Goal**: Users can launch probefs and navigate a real filesystem in a three-pane layout using keyboard controls
**Depends on**: Nothing (first phase)
**Requirements**: NAV-01, NAV-02
**Success Criteria** (what must be TRUE):
  1. User can launch probefs and see three panes: parent directory, current directory, and an empty preview area
  2. User can move the cursor up and down through directory entries with k/j and arrow keys
  3. User can descend into a directory by pressing l or Enter, and the three panes update to reflect the new position
  4. User can move up to the parent directory by pressing h or Backspace
  5. All directory listing calls are non-blocking — the UI stays responsive while directories load
**Plans**: TBD

### Phase 2: Directory Rendering and Icon System
**Goal**: Users can read full file metadata and distinguish file types visually through icons and color-coded entries
**Depends on**: Phase 1
**Requirements**: NAV-03, DISP-01, DISP-02, DISP-03, THEME-05, THEME-06, THEME-07
**Success Criteria** (what must be TRUE):
  1. User can see permissions, size, modified date, and owner columns for every entry in the current pane
  2. Files are colored by type (directories, executables, symlinks, archives, images) according to the active theme
  3. Symlinks display their target path; broken symlinks appear visually distinct from valid symlinks
  4. User can toggle hidden dotfiles on and off with a single key press
  5. Nerd Font icons appear when `icons: nerd` is set in config; ASCII symbol fallback is active by default with no config required
**Plans**: TBD

### Phase 3: Theme System
**Goal**: Users can switch the active color theme and write custom themes that are shareable via the theme metadata format
**Depends on**: Phase 2
**Requirements**: THEME-01, THEME-02, THEME-03, THEME-04
**Success Criteria** (what must be TRUE):
  1. User can switch the active theme by editing the config file and restarting probefs
  2. User can write a YAML theme file with name, author, description, and version metadata fields and load it as the active theme
  3. At least 3 built-in themes ship with probefs (Default Dark, Default Light, and one curated extra) and each is usable without any config
  4. A theme file with an invalid schema is rejected with an informative error message rather than silently producing broken colors
**Plans**: TBD

### Phase 4: Keybinding System and Config Infrastructure
**Goal**: Users can override any action's keybinding by editing a local YAML file without modifying probefs source code
**Depends on**: Phase 3
**Requirements**: KEYS-01, KEYS-02
**Success Criteria** (what must be TRUE):
  1. User can create a local keybindings YAML file, assign a different key to any action, and the override takes effect on next launch
  2. Every bindable action in probefs has a stable string ID documented in the keybindings reference; the IDs do not change between releases
  3. User-defined keybinding overrides work correctly regardless of which of the three panes currently has focus
**Plans**: TBD

### Phase 5: File Operations and Safety
**Goal**: Users can perform all core file operations safely — with confirmation required before any destructive or irreversible action
**Depends on**: Phase 4
**Requirements**: FOPS-01, FOPS-02, FOPS-03, FOPS-04, FOPS-05, FOPS-06
**Success Criteria** (what must be TRUE):
  1. User can copy a file or directory to a target location; a confirmation dialog appears before the operation executes
  2. User can move a file or directory; a confirmation dialog appears before the operation executes
  3. User can delete a file or directory; it is sent to the OS trash (not permanently deleted) after confirming a dialog
  4. User can rename a file or directory inline without leaving the current pane
  5. User can create a new empty file or a new directory in the current directory with a single keybinding each
**Plans**: TBD

### Phase 6: Preview Pane and Status Bar
**Goal**: Users can see a syntax-highlighted preview of any text file in the right pane and read key filesystem context from the status bar
**Depends on**: Phase 5
**Requirements**: PREV-01, PREV-02, DISP-04
**Success Criteria** (what must be TRUE):
  1. Focusing a text file displays a syntax-highlighted preview in the right pane without blocking navigation
  2. Focusing a directory displays that directory's file listing in the right pane
  3. The status bar always shows the current path, total item count, and available free space for the current filesystem
**Plans**: TBD

### Phase 7: Distribution
**Goal**: Users can install probefs via pip/pipx or Homebrew and get a working application with no additional setup
**Depends on**: Phase 6
**Requirements**: DIST-01, DIST-02
**Success Criteria** (what must be TRUE):
  1. `pip install probefs` and `pipx install probefs` succeed on a clean Python 3.10+ environment and produce a working `probefs` command
  2. `brew install probefs` succeeds on macOS from the official Homebrew tap and produces a working `probefs` command
  3. A user who installs via any of the three methods can launch probefs and navigate their filesystem with no manual post-install steps
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Scaffold and Async Architecture | 0/TBD | Not started | - |
| 2. Directory Rendering and Icon System | 0/TBD | Not started | - |
| 3. Theme System | 0/TBD | Not started | - |
| 4. Keybinding System and Config Infrastructure | 0/TBD | Not started | - |
| 5. File Operations and Safety | 0/TBD | Not started | - |
| 6. Preview Pane and Status Bar | 0/TBD | Not started | - |
| 7. Distribution | 0/TBD | Not started | - |
