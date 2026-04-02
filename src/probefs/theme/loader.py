"""ThemeLoader — validate-then-construct gateway for Textual Theme objects.

ThemeLoader is the ONLY place in the codebase that constructs Theme(...).
It calls Color.parse() for every color field, collects ALL errors (not
fail-fast), and raises ThemeValidationError before constructing Theme.

This enforces THEME-02 and THEME-04: no invalid color strings ever reach
Textual's Theme dataclass.
"""
from __future__ import annotations

import io
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from textual.color import Color, ColorParseError
from textual.theme import Theme

COLOR_FIELDS = (
    "primary",
    "secondary",
    "warning",
    "error",
    "success",
    "accent",
    "foreground",
    "background",
    "surface",
    "panel",
    "boost",
)

REQUIRED_FIELDS = ("name", "primary")

FILE_COLOR_CATEGORIES: frozenset[str] = frozenset({
    "directory", "file", "executable", "symlink",
    "broken_symlink", "archive", "image",
})


class ThemeValidationError(Exception):
    """Raised when a theme YAML file fails validation.

    Attributes:
        errors: List of all validation error strings found.
        path: File path or source label where the error originated.
    """

    def __init__(self, errors: list[str], path: str = "") -> None:
        self.errors = errors
        self.path = path
        bullet_list = "\n  - ".join(errors)
        msg = f"Theme file {path!r} is invalid:\n  - {bullet_list}"
        super().__init__(msg)


class ThemeLoader:
    """Validate-then-construct gateway for Textual Theme objects.

    Never construct Theme(...) directly in application code.
    All theme construction must go through ThemeLoader.load() or
    ThemeLoader.load_from_string().
    """

    @classmethod
    def load(cls, path: str | Path) -> tuple[Theme, dict]:
        """Load and validate a user theme YAML file.

        Creates a new YAML() instance per call (not module-level — not
        thread-safe per ruamel.yaml design).

        Args:
            path: Path to the theme YAML file (str or Path).

        Returns:
            A tuple of (Theme, file_colors) where file_colors is a dict
            mapping category names to Rich color style strings (empty if not
            specified in the YAML).

        Raises:
            ThemeValidationError: If the file has any schema or color errors.
            FileNotFoundError: If the path does not exist.
        """
        path = Path(path)
        yaml = YAML()
        try:
            data = yaml.load(path)
        except YAMLError as e:
            raise ThemeValidationError([f"YAML parse error: {e}"], str(path)) from e

        errors = cls._validate(data)
        if errors:
            raise ThemeValidationError(errors, str(path))

        return cls._build_theme(data), cls._extract_file_colors(data)

    @classmethod
    def load_from_string(cls, content: str, source_label: str = "<string>") -> tuple[Theme, dict]:
        """Load and validate a theme from a YAML string.

        Used for built-in themes loaded via importlib.resources.

        Args:
            content: YAML string content.
            source_label: Label for error messages (e.g. filename).

        Returns:
            A tuple of (Theme, file_colors) where file_colors is a dict
            mapping category names to Rich color style strings (empty if not
            specified in the YAML).

        Raises:
            ThemeValidationError: If the content has any schema or color errors.
        """
        yaml = YAML()
        try:
            data = yaml.load(io.StringIO(content))
        except YAMLError as e:
            raise ThemeValidationError([f"YAML parse error: {e}"], source_label) from e

        errors = cls._validate(data)
        if errors:
            raise ThemeValidationError(errors, source_label)

        return cls._build_theme(data), cls._extract_file_colors(data)

    @classmethod
    def _validate(cls, data: object) -> list[str]:
        """Validate theme data dict. Returns list of error strings.

        Returns an empty list if valid. Never raises — callers check the
        returned list and raise ThemeValidationError if non-empty.

        Validates:
        - data must be a dict (YAML mapping)
        - Required fields: name, primary
        - All COLOR_FIELDS present in data must be valid Color.parse() strings
        - 'dark' field, if present, must be a Python bool
        """
        errors: list[str] = []

        if not isinstance(data, dict):
            return ["Theme file must be a YAML mapping (key: value pairs)"]

        for field in REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field!r}")

        for field in COLOR_FIELDS:
            value = data.get(field)
            if value is not None:
                try:
                    Color.parse(str(value))
                except ColorParseError as e:
                    errors.append(f"Invalid color for {field!r}: {value!r} — {e}")

        if "dark" in data and not isinstance(data["dark"], bool):
            errors.append(
                f"Field 'dark' must be a boolean (true/false), "
                f"got {type(data['dark']).__name__}: {data['dark']!r}"
            )

        file_colors = data.get("file_colors")
        if file_colors is not None:
            if not isinstance(file_colors, dict):
                errors.append("'file_colors' must be a YAML mapping (key: value pairs)")
            else:
                for cat in file_colors:
                    if cat not in FILE_COLOR_CATEGORIES:
                        errors.append(
                            f"Unknown file_colors category: {cat!r}. "
                            f"Valid categories: {sorted(FILE_COLOR_CATEGORIES)}"
                        )

        return errors

    @classmethod
    def _extract_file_colors(cls, data: dict) -> dict:
        """Extract file_colors mapping from validated theme data.

        Returns a dict mapping category name to Rich color style string.
        Only includes categories present in FILE_COLOR_CATEGORIES.
        Returns an empty dict if file_colors is absent or empty.
        """
        raw = data.get("file_colors")
        if not isinstance(raw, dict):
            return {}
        return {k: str(v) for k, v in raw.items() if k in FILE_COLOR_CATEGORIES}

    @classmethod
    def _build_theme(cls, data: dict) -> Theme:
        """Construct a Theme from a validated data dict.

        Only called internally after _validate() returns an empty list.
        Metadata fields (author, description, version) are silently ignored —
        they are not part of Textual's Theme dataclass.

        Args:
            data: Validated theme dict from YAML parsing.

        Returns:
            A Theme object.
        """
        kwargs: dict = {"name": data["name"], "primary": data["primary"]}

        for field in COLOR_FIELDS:
            if field != "primary" and field in data:
                kwargs[field] = data[field]

        if "dark" in data:
            kwargs["dark"] = data["dark"]
        if "luminosity_spread" in data:
            kwargs["luminosity_spread"] = float(data["luminosity_spread"])
        if "text_alpha" in data:
            kwargs["text_alpha"] = float(data["text_alpha"])

        return Theme(**kwargs)
