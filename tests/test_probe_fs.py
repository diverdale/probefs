"""Tests for ProbeFS FAL methods."""
from __future__ import annotations

from probefs.fs.probe_fs import ProbeFS


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
