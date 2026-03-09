"""TDD tests for src/probefs/rendering/metadata.py.

Tests are written BEFORE the implementation (RED phase).
All cases come directly from the plan's <behavior> section.
"""
import os
import re

import pytest


# ---------------------------------------------------------------------------
# Import under test
# ---------------------------------------------------------------------------
from probefs.rendering.metadata import (
    ARCHIVE_EXTS,
    IMAGE_EXTS,
    format_mtime,
    get_category,
    human_size,
    uid_to_name,
)


# ---------------------------------------------------------------------------
# get_category tests
# ---------------------------------------------------------------------------

class TestGetCategory:
    """9 input cases specified in the plan."""

    def test_broken_symlink_nonexistent_destination(self):
        """islink=True, destination does not exist on local fs -> 'broken_symlink'."""
        entry = {"islink": True, "destination": "/nonexistent/path/that/never/exists/__probe_test__"}
        assert get_category(entry, fs=None) == "broken_symlink"

    def test_valid_symlink_to_root(self):
        """islink=True, destination='/' (always exists) -> 'symlink'."""
        entry = {"islink": True, "destination": "/"}
        assert get_category(entry, fs=None) == "symlink"

    def test_directory_mode(self):
        """islink=False, mode=0o040755 -> 'directory'."""
        entry = {"islink": False, "mode": 0o040755}
        assert get_category(entry) == "directory"

    def test_executable_mode(self):
        """islink=False, mode=0o100755 -> 'executable'."""
        entry = {"islink": False, "mode": 0o100755}
        assert get_category(entry) == "executable"

    def test_archive_extension(self):
        """islink=False, regular mode, .tar.gz extension -> 'archive'."""
        entry = {"islink": False, "mode": 0o100644, "name": "archive.tar.gz"}
        assert get_category(entry) == "archive"

    def test_image_extension(self):
        """islink=False, regular mode, .jpg extension -> 'image'."""
        entry = {"islink": False, "mode": 0o100644, "name": "photo.jpg"}
        assert get_category(entry) == "image"

    def test_plain_file(self):
        """islink=False, regular mode, .md extension -> 'file'."""
        entry = {"islink": False, "mode": 0o100644, "name": "README.md"}
        assert get_category(entry) == "file"

    def test_zero_mode_defaults_to_file(self):
        """islink=False, mode=0 -> 'file' (zero mode is not executable)."""
        entry = {"islink": False, "mode": 0, "name": "unknown"}
        assert get_category(entry) == "file"

    def test_symlink_with_empty_destination(self):
        """islink=True, destination='' -> 'symlink' (empty treated as valid per pitfall 1)."""
        entry = {"islink": True, "destination": ""}
        assert get_category(entry, fs=None) == "symlink"

    # Additional coverage
    def test_archive_zip(self):
        entry = {"islink": False, "mode": 0o100644, "name": "backup.zip"}
        assert get_category(entry) == "archive"

    def test_image_png(self):
        entry = {"islink": False, "mode": 0o100644, "name": "logo.png"}
        assert get_category(entry) == "image"

    def test_extension_case_insensitive(self):
        """Extension check must be case-insensitive."""
        entry = {"islink": False, "mode": 0o100644, "name": "PHOTO.JPG"}
        assert get_category(entry) == "image"

    def test_islink_takes_priority_over_directory_mode(self):
        """A symlink that points to a directory must be 'symlink', not 'directory'."""
        entry = {"islink": True, "mode": 0o040755, "destination": "/"}
        assert get_category(entry) == "symlink"


# ---------------------------------------------------------------------------
# ARCHIVE_EXTS and IMAGE_EXTS constants
# ---------------------------------------------------------------------------

class TestExtensionSets:
    def test_archive_exts_is_frozenset(self):
        assert isinstance(ARCHIVE_EXTS, frozenset)

    def test_image_exts_is_frozenset(self):
        assert isinstance(IMAGE_EXTS, frozenset)

    def test_tar_in_archive_exts(self):
        assert ".tar" in ARCHIVE_EXTS

    def test_gz_in_archive_exts(self):
        assert ".gz" in ARCHIVE_EXTS

    def test_zip_in_archive_exts(self):
        assert ".zip" in ARCHIVE_EXTS

    def test_jpg_in_image_exts(self):
        assert ".jpg" in IMAGE_EXTS

    def test_png_in_image_exts(self):
        assert ".png" in IMAGE_EXTS

    def test_svg_in_image_exts(self):
        assert ".svg" in IMAGE_EXTS


# ---------------------------------------------------------------------------
# human_size tests
# ---------------------------------------------------------------------------

class TestHumanSize:
    def test_none_returns_dash(self):
        assert human_size(None) == "    -"

    def test_zero(self):
        assert human_size(0) == "0.0B"

    def test_512_bytes(self):
        assert human_size(512) == "512.0B"

    def test_1024_is_1k(self):
        assert human_size(1024) == "1.0K"

    def test_1536_is_1_5k(self):
        assert human_size(1536) == "1.5K"

    def test_1_megabyte(self):
        assert human_size(1048576) == "1.0M"

    def test_1_gigabyte(self):
        assert human_size(1073741824) == "1.0G"


# ---------------------------------------------------------------------------
# format_mtime tests
# ---------------------------------------------------------------------------

class TestFormatMtime:
    def test_none_returns_twelve_spaces(self):
        result = format_mtime(None)
        assert result == "            "
        assert len(result) == 12

    def test_valid_timestamp_format_shape(self):
        """format_mtime(1741564800.0) must match 'Mmm DD HH:MM' format.

        We test the shape, not the exact value, because local TZ affects output.
        """
        result = format_mtime(1741564800.0)
        # Pattern: 3-letter month, space, 2-digit day, space, HH:MM
        # e.g. "Mar 09 14:23" or "Mar 10 00:00"
        assert re.match(r"^[A-Z][a-z]{2} \d{2} \d{2}:\d{2}$", result), (
            f"format_mtime output '{result}' does not match 'Mmm DD HH:MM'"
        )
        assert len(result) == 12

    def test_zero_timestamp(self):
        """Epoch zero should produce a valid formatted string."""
        result = format_mtime(0.0)
        assert re.match(r"^[A-Z][a-z]{2} \d{2} \d{2}:\d{2}$", result)


# ---------------------------------------------------------------------------
# uid_to_name tests
# ---------------------------------------------------------------------------

class TestUidToName:
    def test_current_user_uid(self):
        """os.getuid() should return the current username (real call, no mock)."""
        uid = os.getuid()
        result = uid_to_name(uid)
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not be a numeric string for a real user
        assert not result.isdigit(), f"Expected username, got numeric string '{result}'"

    def test_unknown_uid_fallback(self):
        """An unknown UID (999999999) should fall back to str(uid)."""
        result = uid_to_name(999999999)
        assert result == "999999999"

    def test_negative_uid_fallback(self):
        """Negative UIDs may raise OverflowError; must fall back to str(uid)."""
        result = uid_to_name(-1)
        assert result == "-1"
