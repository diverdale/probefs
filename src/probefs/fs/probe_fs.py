"""ProbeFS — Filesystem Abstraction Layer wrapping fsspec.

ALL filesystem I/O in probefs goes through this class.
Widgets and FileManagerCore must never call os, pathlib, or shutil directly.
This boundary is what makes the SFTP backend a drop-in replacement later.
"""
from __future__ import annotations

import os

import fsspec


class ProbeFS:
    """Single filesystem gateway. Wraps fsspec.AbstractFileSystem."""

    def __init__(self, protocol: str = "file", **kwargs: object) -> None:
        # Single instance — fsspec LocalFileSystem is reusable; re-instantiating
        # per call wastes memory and bypasses directory caching.
        self._fs = fsspec.filesystem(protocol, **kwargs)

    def ls(self, path: str, *, detail: bool = True) -> list[dict]:
        """List directory entries.

        Returns list of dicts with at minimum: name (str), type ('file'|'directory'),
        size (int). LocalFileSystem also returns mtime, mode, uid, gid, islink.
        Use .get() with defaults for any key beyond name/type — other backends
        may not provide them.
        """
        return self._fs.ls(path, detail=detail)

    def info(self, path: str) -> dict:
        """Return metadata dict for a single path."""
        return self._fs.info(path)

    def exists(self, path: str) -> bool:
        """Return True if path exists (follows symlinks).

        FAL boundary method for broken symlink detection.
        For local filesystem: equivalent to os.path.exists().
        For SFTP backend: delegates to the remote filesystem.
        Widgets and rendering code must use this method, not os.path.exists directly.
        """
        return self._fs.exists(path)

    def isdir(self, path: str) -> bool:
        """Return True if path is a directory."""
        return self._fs.isdir(path)

    def home(self) -> str:
        """Return the user's home directory path.

        FAL boundary helper — callers (screens, widgets) must not use os/pathlib directly.
        For SFTP backends, this would return the remote home path.
        """
        return os.path.expanduser("~")
