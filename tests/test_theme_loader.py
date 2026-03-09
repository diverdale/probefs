"""Tests for ThemeLoader — validate-then-construct gateway for Textual Theme objects.

TDD RED → GREEN → REFACTOR pattern.
"""
from __future__ import annotations

import pytest
from textual.theme import Theme

from probefs.theme import ThemeLoader, ThemeValidationError
from probefs.theme.loader import COLOR_FIELDS


# ---------------------------------------------------------------------------
# ThemeValidationError behavior
# ---------------------------------------------------------------------------


class TestThemeValidationError:
    def test_stores_errors_list(self):
        errors = ["error one", "error two"]
        exc = ThemeValidationError(errors)
        assert exc.errors == errors

    def test_stores_path(self):
        exc = ThemeValidationError(["e"], path="/some/file.yaml")
        assert exc.path == "/some/file.yaml"

    def test_default_path_is_empty_string(self):
        exc = ThemeValidationError(["e"])
        assert exc.path == ""

    def test_str_includes_path(self):
        exc = ThemeValidationError(["bad color"], path="/my/theme.yaml")
        assert "/my/theme.yaml" in str(exc)

    def test_str_includes_error_message(self):
        exc = ThemeValidationError(["Invalid color for 'primary': 'notacolor'"])
        assert "Invalid color for 'primary'" in str(exc)

    def test_str_includes_all_errors(self):
        errors = ["Missing required field: 'name'", "Missing required field: 'primary'"]
        exc = ThemeValidationError(errors)
        s = str(exc)
        assert "name" in s
        assert "primary" in s

    def test_is_exception(self):
        exc = ThemeValidationError(["e"])
        assert isinstance(exc, Exception)


# ---------------------------------------------------------------------------
# ThemeLoader._validate
# ---------------------------------------------------------------------------


class TestValidate:
    def test_empty_dict_missing_required_fields(self):
        errors = ThemeLoader._validate({})
        assert any("name" in e for e in errors)
        assert any("primary" in e for e in errors)

    def test_empty_dict_returns_two_errors(self):
        errors = ThemeLoader._validate({})
        assert len(errors) == 2

    def test_non_dict_string_returns_mapping_error(self):
        errors = ThemeLoader._validate("not a dict")
        assert len(errors) == 1
        assert "YAML mapping" in errors[0]

    def test_non_dict_none_returns_mapping_error(self):
        errors = ThemeLoader._validate(None)
        assert "YAML mapping" in errors[0]

    def test_non_dict_list_returns_mapping_error(self):
        errors = ThemeLoader._validate(["a", "b"])
        assert "YAML mapping" in errors[0]

    def test_valid_minimal_theme_no_errors(self):
        errors = ThemeLoader._validate({"name": "t", "primary": "#5B8DD9"})
        assert errors == []

    def test_invalid_primary_color_reported(self):
        errors = ThemeLoader._validate({"name": "t", "primary": "notacolor"})
        assert len(errors) == 1
        assert "primary" in errors[0]
        assert "notacolor" in errors[0]

    def test_invalid_optional_color_reported(self):
        errors = ThemeLoader._validate({"name": "t", "primary": "#fff", "error": "badcolor"})
        assert len(errors) == 1
        assert "error" in errors[0]
        assert "badcolor" in errors[0]

    def test_dark_string_yes_rejected(self):
        errors = ThemeLoader._validate({"name": "t", "primary": "#fff", "dark": "yes"})
        assert len(errors) == 1
        assert "dark" in errors[0]
        assert "boolean" in errors[0].lower()

    def test_dark_bool_true_accepted(self):
        errors = ThemeLoader._validate({"name": "t", "primary": "#fff", "dark": True})
        assert errors == []

    def test_dark_bool_false_accepted(self):
        errors = ThemeLoader._validate({"name": "t", "primary": "#fff", "dark": False})
        assert errors == []

    def test_multiple_bad_colors_both_reported(self):
        errors = ThemeLoader._validate({"name": "t", "primary": "bad1", "secondary": "bad2"})
        assert len(errors) == 2
        assert any("primary" in e for e in errors)
        assert any("secondary" in e for e in errors)

    def test_all_11_color_fields_valid(self):
        data = {
            "name": "full-theme",
            "primary": "#5B8DD9",
            "secondary": "#2D4A8A",
            "warning": "#FFB86C",
            "error": "#FF5555",
            "success": "#50FA7B",
            "accent": "#8BE9FD",
            "foreground": "#E0E0E0",
            "background": "#1C2023",
            "surface": "#252B2E",
            "panel": "#1E2528",
            "boost": "#8BE9FD",
        }
        errors = ThemeLoader._validate(data)
        assert errors == []

    def test_missing_name_only(self):
        errors = ThemeLoader._validate({"primary": "#5B8DD9"})
        assert len(errors) == 1
        assert "name" in errors[0]

    def test_missing_primary_only(self):
        errors = ThemeLoader._validate({"name": "t"})
        assert len(errors) == 1
        assert "primary" in errors[0]

    def test_color_fields_tuple_has_11_entries(self):
        assert len(COLOR_FIELDS) == 11

    def test_primary_in_color_fields(self):
        assert "primary" in COLOR_FIELDS


# ---------------------------------------------------------------------------
# ThemeLoader.load_from_string
# ---------------------------------------------------------------------------


class TestLoadFromString:
    def test_valid_minimal_yaml_returns_theme(self):
        yaml_str = "name: test-theme\nprimary: '#5B8DD9'\n"
        theme = ThemeLoader.load_from_string(yaml_str)
        assert isinstance(theme, Theme)
        assert theme.name == "test-theme"

    def test_valid_full_yaml_returns_theme(self):
        yaml_str = """\
name: probefs-dark
dark: true
primary: '#5B8DD9'
secondary: '#2D4A8A'
background: '#1C2023'
"""
        theme = ThemeLoader.load_from_string(yaml_str)
        assert isinstance(theme, Theme)
        assert theme.name == "probefs-dark"

    def test_default_source_label(self):
        yaml_str = "not valid yaml:\n  - oops\n  bad:"
        with pytest.raises(ThemeValidationError) as exc_info:
            ThemeLoader.load_from_string(yaml_str)
        # Either YAML parse error or validation error; source label appears in message
        # (for validation errors, path is in exc.path; for parse errors it's in message)
        exc = exc_info.value
        assert isinstance(exc, ThemeValidationError)

    def test_custom_source_label_in_error(self):
        yaml_str = "name: t\nprimary: notacolor\n"
        with pytest.raises(ThemeValidationError) as exc_info:
            ThemeLoader.load_from_string(yaml_str, source_label="myfile.yaml")
        assert exc_info.value.path == "myfile.yaml"

    def test_invalid_schema_raises_validation_error(self):
        yaml_str = "name: t\nprimary: not-a-color\n"
        with pytest.raises(ThemeValidationError) as exc_info:
            ThemeLoader.load_from_string(yaml_str)
        assert "primary" in str(exc_info.value)

    def test_non_mapping_yaml_raises_validation_error(self):
        yaml_str = "- item1\n- item2\n"
        with pytest.raises(ThemeValidationError):
            ThemeLoader.load_from_string(yaml_str)

    def test_empty_yaml_raises_validation_error(self):
        with pytest.raises(ThemeValidationError):
            ThemeLoader.load_from_string("")

    def test_missing_fields_error_lists_all_missing(self):
        yaml_str = "author: nobody\n"
        with pytest.raises(ThemeValidationError) as exc_info:
            ThemeLoader.load_from_string(yaml_str)
        errors = exc_info.value.errors
        assert any("name" in e for e in errors)
        assert any("primary" in e for e in errors)

    def test_multiple_errors_collected_not_fail_fast(self):
        yaml_str = "name: t\nprimary: bad1\nsecondary: bad2\n"
        with pytest.raises(ThemeValidationError) as exc_info:
            ThemeLoader.load_from_string(yaml_str)
        assert len(exc_info.value.errors) == 2


# ---------------------------------------------------------------------------
# ThemeLoader.load (file-based)
# ---------------------------------------------------------------------------


class TestLoad:
    def test_valid_file_returns_theme(self, tmp_path):
        f = tmp_path / "my-theme.yaml"
        f.write_text("name: my-theme\nprimary: '#5B8DD9'\n")
        theme = ThemeLoader.load(f)
        assert isinstance(theme, Theme)
        assert theme.name == "my-theme"

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ThemeLoader.load(tmp_path / "nonexistent.yaml")

    def test_invalid_schema_raises_validation_error_with_path(self, tmp_path):
        f = tmp_path / "bad.yaml"
        f.write_text("name: t\nprimary: notacolor\n")
        with pytest.raises(ThemeValidationError) as exc_info:
            ThemeLoader.load(f)
        assert str(f) in exc_info.value.path

    def test_load_accepts_string_path(self, tmp_path):
        f = tmp_path / "t.yaml"
        f.write_text("name: t\nprimary: '#aabbcc'\n")
        theme = ThemeLoader.load(str(f))
        assert isinstance(theme, Theme)

    def test_valid_file_with_all_color_fields(self, tmp_path):
        f = tmp_path / "full.yaml"
        f.write_text("""\
name: full-theme
primary: '#5B8DD9'
secondary: '#2D4A8A'
warning: '#FFB86C'
error: '#FF5555'
success: '#50FA7B'
accent: '#8BE9FD'
foreground: '#E0E0E0'
background: '#1C2023'
surface: '#252B2E'
panel: '#1E2528'
boost: '#8BE9FD'
dark: true
""")
        theme = ThemeLoader.load(f)
        assert isinstance(theme, Theme)
        assert theme.name == "full-theme"

    def test_non_mapping_yaml_raises_validation_error(self, tmp_path):
        f = tmp_path / "list.yaml"
        f.write_text("- item1\n- item2\n")
        with pytest.raises(ThemeValidationError):
            ThemeLoader.load(f)


# ---------------------------------------------------------------------------
# ThemeLoader._build_theme
# ---------------------------------------------------------------------------


class TestBuildTheme:
    def test_minimal_data_builds_theme(self):
        data = {"name": "t", "primary": "#5B8DD9"}
        theme = ThemeLoader._build_theme(data)
        assert isinstance(theme, Theme)
        assert theme.name == "t"
        assert theme.primary == "#5B8DD9"

    def test_optional_color_fields_included(self):
        data = {"name": "t", "primary": "#5B8DD9", "secondary": "#2D4A8A"}
        theme = ThemeLoader._build_theme(data)
        assert theme.secondary == "#2D4A8A"

    def test_dark_field_included(self):
        data = {"name": "t", "primary": "#5B8DD9", "dark": True}
        theme = ThemeLoader._build_theme(data)
        assert theme.dark is True

    def test_metadata_fields_not_in_theme(self):
        # author, description, version are metadata — silently ignored
        data = {"name": "t", "primary": "#5B8DD9", "author": "test", "version": "1.0"}
        theme = ThemeLoader._build_theme(data)
        assert isinstance(theme, Theme)
        assert not hasattr(theme, "author")


# ---------------------------------------------------------------------------
# Package imports
# ---------------------------------------------------------------------------


class TestPackageImports:
    def test_import_from_package(self):
        from probefs.theme import ThemeLoader, ThemeValidationError  # noqa: F401

    def test_import_color_fields_from_loader(self):
        from probefs.theme.loader import COLOR_FIELDS  # noqa: F401
        assert len(COLOR_FIELDS) == 11
