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
        """Return the home directory for this filesystem.

        For local filesystems: os.path.expanduser("~").
        For SFTP: uses the paramiko client's getcwd() (the directory the server
        puts you in on login, which is the remote home). Falls back through
        several approaches before giving up and returning "/".
        """
        protocol = getattr(self._fs, "protocol", "file")
        if isinstance(protocol, (list, tuple)):
            protocol = protocol[0]
        if protocol in ("file", "local", "abstract"):
            return os.path.expanduser("~")
        # SFTP: use paramiko's normalize(".") which sends a POSIX realpath
        # request and returns the absolute canonical CWD (the server's home
        # for this user).  getcwd() only works after chdir() so avoid it.
        # info(".") returns name="." (relative) — not useful for navigation.
        try:
            ftp = getattr(self._fs, "ftp", None)
            if ftp is not None:
                absolute = ftp.normalize(".")
                if absolute and absolute != ".":
                    return absolute
        except Exception:
            pass
        # Last resort.
        return "/"

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

    def read_pdf_text(self, path: str, max_pages: int = 20) -> str:
        """Extract text from a PDF file using pdftotext (poppler).

        Extracts up to max_pages pages. Poppler must be installed and pdftotext
        must be on PATH — raises RuntimeError if not found so the caller can
        show a friendly "install poppler" message instead of a generic error.

        Raises RuntimeError if pdftotext is not on PATH.
        Raises OSError if pdftotext fails or times out.

        FAL boundary — widgets must call this, never subprocess directly.
        Always call from a thread worker — pdftotext can be slow on large PDFs.
        """
        import subprocess

        if shutil.which("pdftotext") is None:
            raise RuntimeError(
                "pdftotext not found — install poppler to enable PDF preview\n"
                "  macOS:  brew install poppler\n"
                "  Ubuntu: sudo apt install poppler-utils\n"
                "  Fedora: sudo dnf install poppler-utils"
            )
        try:
            result = subprocess.run(
                ["pdftotext", "-l", str(max_pages), path, "-"],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            raise OSError("pdftotext timed out")
        if result.returncode != 0:
            raise OSError(result.stderr.strip() or "pdftotext failed")
        return result.stdout

    def open_with_default(self, path: str) -> None:
        """Open a file or directory with the OS default application.

        macOS: open(1). Linux: xdg-open. Windows: os.startfile.
        Non-blocking — the default app launches in the background.

        Raises OSError if the system command fails.
        FAL boundary — callers must not invoke subprocess/os.startfile directly.
        """
        import subprocess
        import sys

        if sys.platform == "darwin":
            subprocess.run(["open", path], check=True)
        elif sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", path], check=True)

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to the system clipboard.

        macOS: pbcopy. Linux: xclip (preferred) or xsel. Windows: clip.
        Raises OSError if no clipboard tool is available on the platform.

        FAL boundary — callers must not invoke subprocess directly.
        Always call from the main thread (fast, no disk I/O).
        """
        import subprocess
        import sys

        encoded = text.encode()
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=encoded, check=True)
        elif sys.platform == "win32":
            subprocess.run(["clip"], input=encoded, check=True)
        else:
            if shutil.which("xclip"):
                subprocess.run(
                    ["xclip", "-selection", "clipboard"], input=encoded, check=True
                )
            elif shutil.which("xsel"):
                subprocess.run(
                    ["xsel", "--clipboard", "--input"], input=encoded, check=True
                )
            else:
                raise OSError(
                    "No clipboard tool found — install xclip or xsel\n"
                    "  Ubuntu/Debian: sudo apt install xclip\n"
                    "  Fedora:        sudo dnf install xclip"
                )

    def open_read(self, path: str):
        """Return a binary file-like object for reading. Use as a context manager.

        FAL boundary — callers must not call self._fs.open() directly.
        Used for cross-filesystem streaming transfers (SFTP upload/download).
        """
        return self._fs.open(path, "rb")

    def open_write(self, path: str):
        """Return a binary file-like object for writing. Use as a context manager.

        FAL boundary — callers must not call self._fs.open() directly.
        Used for cross-filesystem streaming transfers (SFTP upload/download).
        """
        return self._fs.open(path, "wb")

    def read_archive_listing(self, path: str) -> str:
        """List contents of a ZIP or tar archive for preview.

        Uses Python stdlib only — no external dependencies.
        Supports: .zip, .tar, .tar.gz/.tgz, .tar.bz2/.tbz2, .tar.xz/.txz

        Returns a formatted text string with entry sizes and paths.
        Raises ValueError if the file is not a recognized archive format.
        Raises OSError for read errors or corrupt archives.

        FAL boundary — widgets must call this, never zipfile/tarfile directly.
        Always call from a thread worker — large tars can be slow to enumerate.
        """
        import zipfile
        import tarfile

        if zipfile.is_zipfile(path):
            try:
                with zipfile.ZipFile(path, "r") as zf:
                    infos = zf.infolist()
                    total = sum(i.file_size for i in infos)
                    lines = [
                        f"ZIP archive — {len(infos)} entries"
                        f"  ({_fmt_size(total)} uncompressed)\n"
                    ]
                    for info in sorted(infos, key=lambda i: i.filename):
                        if info.is_dir():
                            lines.append(f"       dir  {info.filename}")
                        else:
                            lines.append(f"  {_fmt_size(info.file_size):>7}  {info.filename}")
                    return "\n".join(lines)
            except zipfile.BadZipFile as exc:
                raise OSError(f"Bad ZIP: {exc}") from exc

        try:
            with tarfile.open(path, "r:*") as tf:
                members = tf.getmembers()
                total = sum(m.size for m in members if m.isfile())
                lines = [
                    f"TAR archive — {len(members)} entries"
                    f"  ({_fmt_size(total)} uncompressed)\n"
                ]
                for m in sorted(members, key=lambda m: m.name):
                    if m.isdir():
                        lines.append(f"       dir  {m.name}/")
                    else:
                        lines.append(f"  {_fmt_size(m.size):>7}  {m.name}")
                return "\n".join(lines)
        except tarfile.TarError as exc:
            raise ValueError(f"Not a recognized archive: {exc}") from exc

    def disk_usage(self, path: str) -> int:
        """Return free disk space in bytes for the filesystem containing path.

        Uses shutil.disk_usage internally (stdlib, no deps). Returns the .free
        field of the usage namedtuple as an integer (bytes).

        FAL boundary — callers (MainScreen worker) must use this, never shutil directly.
        This method may block briefly on network filesystems; always call from a thread.

        Raises OSError if path does not exist or stat fails.
        """
        usage = shutil.disk_usage(path)
        return usage.free


def _fmt_size(n: int) -> str:
    """Format a byte count as a compact human-readable string."""
    if n < 1024:
        return f"{n} B"
    elif n < 1024 ** 2:
        return f"{n / 1024:.1f} K"
    elif n < 1024 ** 3:
        return f"{n / 1024 ** 2:.1f} M"
    else:
        return f"{n / 1024 ** 3:.1f} G"
