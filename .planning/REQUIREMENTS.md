# Requirements: probefs

**Defined:** 2026-03-09
**Core Value:** A fast, beautiful, keyboard-driven file browser that feels at home in any terminal — local or remote — with a theming ecosystem that makes it yours.

## v1 Requirements

### Navigation

- [ ] **NAV-01**: User can navigate a three-pane Miller columns layout (parent dir | current dir | preview pane) using hjkl and arrow keys
- [ ] **NAV-02**: User can enter a directory by pressing l/Enter and move up with h/Backspace
- [ ] **NAV-03**: User can toggle hidden files (dotfiles) on and off with a single key

### File Operations

- [ ] **FOPS-01**: User can copy a file or directory to a new location with a confirmation dialog
- [ ] **FOPS-02**: User can move a file or directory with a confirmation dialog
- [ ] **FOPS-03**: User can delete a file or directory by sending it to trash (not permanent delete) with a confirmation dialog
- [ ] **FOPS-04**: User can rename a file or directory inline
- [ ] **FOPS-05**: User can create a new empty file in the current directory
- [ ] **FOPS-06**: User can create a new directory in the current directory

### Display

- [ ] **DISP-01**: User can see file metadata columns in the current pane: permissions, size, modified date, and owner
- [ ] **DISP-02**: Files are colored by type (directories, executables, symlinks, archives, images, etc.) using the active theme
- [ ] **DISP-03**: Symlinks display their target path; broken symlinks are visually distinct
- [ ] **DISP-04**: A status bar displays the current path, item count, and free space

### Theming

- [ ] **THEME-01**: User can switch the active color theme by editing a config file
- [ ] **THEME-02**: User can create a custom color theme by writing a YAML theme file
- [ ] **THEME-03**: Theme YAML files include metadata fields: name, author, description, version (for registry sharing)
- [ ] **THEME-04**: probefs ships with at least 3 built-in themes (e.g., Default Dark, Default Light, Dracula-inspired)
- [ ] **THEME-05**: User can assign icons to file types via an icon theme YAML file
- [ ] **THEME-06**: Icon themes support Nerd Font glyphs as the configured icon set
- [ ] **THEME-07**: Icon themes fall back to ASCII symbols by default; Nerd Font icons require explicit opt-in via config

### Preview

- [ ] **PREV-01**: User can see a syntax-highlighted text preview of the focused file in the right pane
- [ ] **PREV-02**: Preview pane shows directory listing when a directory is focused

### Keybindings

- [ ] **KEYS-01**: User can override any action's keybinding by editing a local YAML keybindings file
- [ ] **KEYS-02**: All bindable actions have stable string IDs referenced in the keybindings file

### Distribution

- [ ] **DIST-01**: User can install probefs via `pip install probefs` or `pipx install probefs`
- [ ] **DIST-02**: User can install probefs via Homebrew on macOS

## v2 Requirements

### Navigation

- **NAV-V2-01**: User can incrementally search/filter the current directory listing by typing
- **NAV-V2-02**: User can bookmark directories and recall them with a single key

### File Operations

- **FOPS-V2-01**: User can select multiple files with visual mode and perform batch copy/move/delete
- **FOPS-V2-02**: User can sort the directory listing by name, size, date, or type (ascending/descending)
- **FOPS-V2-03**: User can bulk-rename selected files via $EDITOR

### UX

- **UX-V2-01**: Shell integration wrapper allows the shell to cd to the last directory when probefs exits
- **UX-V2-02**: ? key shows a help overlay with all current keybindings
- **UX-V2-03**: Background task manager shows progress for large copy/move operations with cancellation
- **UX-V2-04**: Git status indicators appear in file listings for repositories

### Themes

- **THEME-V2-01**: User can install community themes via `probefs theme install <name>` from the GitHub registry

## v3 Requirements (Future Milestones)

- **SFTP-01**: User can connect to a remote server via SFTP and browse files in a pane
- **SFTP-02**: User can transfer files between local and remote panes

## Out of Scope

| Feature | Reason |
|---------|--------|
| Built-in text editor | Use $EDITOR integration; built-in editor is a known anti-feature (see: Midnight Commander) |
| Built-in terminal emulator | Textual cannot embed a VTE; shell integration covers the use case |
| Dual-pane mode | Conflicts with three-pane product identity |
| FTP / SMB / WebDAV | Non-SSH remote protocols deferred indefinitely |
| Plugin/scripting framework | Shell passthrough covers v1; keybinding overrides cover customization needs |
| Image preview | Terminal-dependent, fragile over SSH; stub interface only if needed |
| XML theme format | Explicitly rejected; YAML/JSON only |
| Nerd Font auto-detection | Technically impossible over SSH; explicit opt-in is the correct design |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| NAV-01 | Phase 1 | Pending |
| NAV-02 | Phase 1 | Pending |
| NAV-03 | Phase 2 | Pending |
| FOPS-01 | Phase 5 | Pending |
| FOPS-02 | Phase 5 | Pending |
| FOPS-03 | Phase 5 | Pending |
| FOPS-04 | Phase 5 | Pending |
| FOPS-05 | Phase 5 | Pending |
| FOPS-06 | Phase 5 | Pending |
| DISP-01 | Phase 2 | Pending |
| DISP-02 | Phase 2 | Pending |
| DISP-03 | Phase 2 | Pending |
| DISP-04 | Phase 6 | Pending |
| THEME-01 | Phase 3 | Pending |
| THEME-02 | Phase 3 | Pending |
| THEME-03 | Phase 3 | Pending |
| THEME-04 | Phase 3 | Pending |
| THEME-05 | Phase 2 | Pending |
| THEME-06 | Phase 2 | Pending |
| THEME-07 | Phase 2 | Pending |
| PREV-01 | Phase 6 | Pending |
| PREV-02 | Phase 6 | Pending |
| KEYS-01 | Phase 4 | Pending |
| KEYS-02 | Phase 4 | Pending |
| DIST-01 | Phase 7 | Pending |
| DIST-02 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-09*
*Last updated: 2026-03-09 after roadmap creation*
