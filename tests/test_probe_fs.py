"""Tests for ProbeFS FAL methods."""
from __future__ import annotations

from probefs.fs.probe_fs import ProbeFS, _clean_fstype, _match_mount


def test_disk_usage_returns_total_used_free() -> None:
    fs = ProbeFS()
    usage = fs.disk_usage("/")
    assert usage.total >= usage.free > 0
    # used/free need not sum to total (reserved blocks), but both are bounded.
    assert 0 <= usage.used <= usage.total
    assert usage.free <= usage.total


def test_disk_usage_fields_are_ints() -> None:
    fs = ProbeFS()
    usage = fs.disk_usage("/")
    assert isinstance(usage.total, int)
    assert isinstance(usage.used, int)
    assert isinstance(usage.free, int)


# ---------------------------------------------------------------------------
# fs_label helpers
# ---------------------------------------------------------------------------

_MOUNTS = [
    ("/", "ext4"),
    ("/home", "btrfs"),
    ("/home/dale/nas", "nfs4"),
    ("/mnt/usb", "vfat"),
    ("/mnt/remote", "fuse.sshfs"),
]


def test_match_mount_longest_prefix_wins() -> None:
    assert _match_mount(_MOUNTS, "/home/dale/nas/photos") == "nfs4"
    assert _match_mount(_MOUNTS, "/home/dale/docs") == "btrfs"
    assert _match_mount(_MOUNTS, "/etc") == "ext4"


def test_match_mount_exact_mountpoint() -> None:
    assert _match_mount(_MOUNTS, "/mnt/usb") == "vfat"


def test_match_mount_is_component_aware() -> None:
    # /home2 must NOT match the /home mount
    assert _match_mount([("/", "ext4"), ("/home", "btrfs")], "/home2/x") == "ext4"


def test_match_mount_no_match_returns_none() -> None:
    assert _match_mount([("/mnt/usb", "vfat")], "/etc") is None


def test_clean_fstype() -> None:
    assert _clean_fstype("ext4") == "EXT4"
    assert _clean_fstype("vfat") == "VFAT"
    assert _clean_fstype("fuse.sshfs") == "SSHFS"


def test_fs_label_real_root_is_nonempty_string() -> None:
    label = ProbeFS().fs_label("/")
    assert isinstance(label, str) and label
