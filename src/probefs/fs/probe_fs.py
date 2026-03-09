"""ProbeFS — Filesystem Abstraction Layer wrapping fsspec.

ALL filesystem I/O in probefs goes through this class.
Widgets and FileManagerCore must never call os, pathlib, or shutil directly.
This boundary is what makes the SFTP backend a drop-in replacement later.
"""
from __future__ import annotations

import os
import shutil
from pathlib import PurePosixPath

import fsspec
from send2trash import send2trash as _send2trash

MAX_PREVIEW_BYTES: int = 524_288  # 512 KB — module-level constant, not inside the class


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

    def copy(self, src: str, dst: str) -> None:
        """Copy file or directory tree to dst.

        For files: shutil.copy2 (preserves metadata).
        For directories: shutil.copytree (recursive, preserves metadata).

        Raises FileExistsError if dst already exists as a directory (copytree
        will raise natively). Raises OSError for permission errors.

        FAL boundary: callers must never call shutil directly.
        """
        if self._fs.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    def move(self, src: str, dst: str) -> None:
        """Move file or directory to dst.

        Wraps shutil.move — handles cross-device moves and directories.
        If dst is an existing directory, src is moved inside it keeping its name
        (standard mv semantics, same as copy behavior).

        Raises OSError / shutil.Error on other failures.
        """
        shutil.move(src, dst)

    def rename(self, src: str, new_name: str) -> None:
        """Rename a file or directory in-place (same parent directory).

        new_name is the basename only — not a full path. The parent directory
        is computed from src. Cross-directory rename is ProbeFS.move(), not this.

        Raises FileExistsError if new_name already exists in the parent directory.
        Raises OSError for permission errors.
        """
        parent = str(PurePosixPath(src).parent)
        dst = str(PurePosixPath(parent) / new_name)
        if self._fs.exists(dst):
            raise FileExistsError(f"{new_name!r} already exists in {parent!r}")
        self._fs.mv(src, dst)

    def trash(self, path: str) -> None:
        """Send file or directory to OS Trash. Never permanent deletion.

        Uses send2trash — handles macOS Trash, Windows Recycle Bin, Linux
        FreeDesktop trash spec. Never calls os.remove or shutil.rmtree.

        Raises OSError on macOS/Windows if the trash operation fails.
        Raises send2trash.TrashPermissionError (subclass of PermissionError,
        subclass of OSError) on Linux if cross-device trash is not supported.
        Catching OSError covers all platforms.
        """
        _send2trash(path)

    def new_file(self, path: str) -> None:
        """Create a new empty file at path.

        Raises FileExistsError if path already exists (file or directory).
        Raises OSError for permission errors.
        """
        if self._fs.exists(path):
            raise FileExistsError(f"{path!r} already exists")
        self._fs.touch(path, truncate=True)

    def new_dir(self, path: str) -> None:
        """Create a new directory at path.

        Does NOT create intermediate parent directories (parents=False semantics).
        Raises FileExistsError if path already exists.
        Raises OSError for permission errors or if parent does not exist.
        """
        self._fs.mkdir(path, create_parents=False)

    def read_text(self, path: str, max_bytes: int = MAX_PREVIEW_BYTES) -> str:
        """Read text content of a file for preview purposes, with a size cap.

        Two-layer binary detection:
        1. mimetypes.guess_type() for known binary extensions (images, audio, video, PDFs)
        2. Null-byte check in first 8 KB for files with no recognized extension

        Raises ValueError for binary files (caller shows "Binary file" message).
        Raises UnicodeDecodeError if file contains non-UTF-8 bytes (caller handles).
        Raises OSError for permission errors or missing files.

        FAL boundary — widgets must call this, never open() directly.
        The max_bytes cap prevents OOM on large log files.
        """
        import mimetypes

        # First-pass: extension-based binary type check (fast, no I/O)
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type and not mime_type.startswith("text/"):
            # Recognized binary type: image/*, audio/*, video/*, application/pdf, etc.
            raise ValueError(f"Binary file ({mime_type}) — preview unavailable")

        # Second-pass: null-byte check in first 8 KB (catches binaries with no extension)
        chunk_size = 8192
        with open(path, "rb") as f:
            head = f.read(chunk_size)
        if b"\x00" in head:
            raise ValueError("Binary file — preview unavailable")

        # Read up to max_bytes — truncate silently; caller appends truncation notice
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_bytes)
