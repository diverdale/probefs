"""Tests for FileManagerCore navigation state machine.

All tests are pure synchronous — no filesystem I/O occurs inside
descend() or ascend(). ProbeFS is injected but never called during
navigation state transitions.
"""
from __future__ import annotations

import pytest

from probefs.core.file_manager import FileManagerCore
from probefs.fs.probe_fs import ProbeFS


@pytest.fixture
def fs() -> ProbeFS:
    """Provide a ProbeFS instance. No actual filesystem calls happen in tests."""
    return ProbeFS()


@pytest.fixture
def core(fs: ProbeFS) -> FileManagerCore:
    """FileManagerCore starting at /home/user."""
    return FileManagerCore(fs, "/home/user")


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_initial_cwd(core: FileManagerCore) -> None:
    assert core.cwd == "/home/user"


def test_initial_cursor_index(core: FileManagerCore) -> None:
    assert core.cursor_index == 0


def test_fs_stored_on_self(core: FileManagerCore, fs: ProbeFS) -> None:
    """ProbeFS instance must be accessible via core.fs for worker use."""
    assert core.fs is fs


# ---------------------------------------------------------------------------
# parent_path property
# ---------------------------------------------------------------------------


def test_parent_path_from_nested_dir(core: FileManagerCore) -> None:
    assert core.parent_path == "/home"


def test_parent_path_from_root(fs: ProbeFS) -> None:
    root_core = FileManagerCore(fs, "/")
    assert root_core.parent_path == "/"


def test_parent_path_does_not_mutate_cwd(core: FileManagerCore) -> None:
    _ = core.parent_path
    assert core.cwd == "/home/user"


def test_parent_path_two_levels_deep(fs: ProbeFS) -> None:
    c = FileManagerCore(fs, "/home/user/projects")
    assert c.parent_path == "/home/user"


# ---------------------------------------------------------------------------
# descend()
# ---------------------------------------------------------------------------


def test_descend_updates_cwd(core: FileManagerCore) -> None:
    result = core.descend("projects")
    assert result == "/home/user/projects"
    assert core.cwd == "/home/user/projects"


def test_descend_resets_cursor_index(core: FileManagerCore) -> None:
    core.cursor_index = 5
    core.descend("projects")
    assert core.cursor_index == 0


def test_descend_returns_new_cwd(core: FileManagerCore) -> None:
    returned = core.descend("projects")
    assert returned == core.cwd


def test_descend_chained(core: FileManagerCore) -> None:
    core.descend("projects")
    core.descend("probefs")
    assert core.cwd == "/home/user/projects/probefs"
    assert core.cursor_index == 0


def test_descend_from_root(fs: ProbeFS) -> None:
    root_core = FileManagerCore(fs, "/")
    root_core.descend("home")
    assert root_core.cwd == "/home"


# ---------------------------------------------------------------------------
# ascend()
# ---------------------------------------------------------------------------


def test_ascend_updates_cwd(core: FileManagerCore) -> None:
    result = core.ascend()
    assert result == "/home"
    assert core.cwd == "/home"


def test_ascend_resets_cursor_index(core: FileManagerCore) -> None:
    core.cursor_index = 7
    core.ascend()
    assert core.cursor_index == 0


def test_ascend_returns_new_cwd(core: FileManagerCore) -> None:
    returned = core.ascend()
    assert returned == core.cwd


def test_ascend_multiple_levels(core: FileManagerCore) -> None:
    core.ascend()  # /home/user -> /home
    core.ascend()  # /home -> /
    assert core.cwd == "/"


def test_ascend_at_root_stays_at_root(fs: ProbeFS) -> None:
    root_core = FileManagerCore(fs, "/")
    root_core.ascend()
    assert root_core.cwd == "/"
    assert root_core.cursor_index == 0


def test_ascend_at_root_does_not_panic(fs: ProbeFS) -> None:
    """ascend() at '/' must not raise any exception."""
    root_core = FileManagerCore(fs, "/")
    result = root_core.ascend()
    assert result == "/"


# ---------------------------------------------------------------------------
# Round-trip: descend then ascend
# ---------------------------------------------------------------------------


def test_descend_then_ascend_returns_to_start(core: FileManagerCore) -> None:
    original_cwd = core.cwd
    core.descend("projects")
    core.ascend()
    assert core.cwd == original_cwd


def test_cursor_always_zero_after_navigation(core: FileManagerCore) -> None:
    core.cursor_index = 99
    core.descend("a")
    assert core.cursor_index == 0
    core.cursor_index = 99
    core.ascend()
    assert core.cursor_index == 0
