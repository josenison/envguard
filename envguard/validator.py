"""Core validation logic for .env files against a Schema."""

import re
from dataclasses import dataclass, field
from typing import Optional

from envguard.schema import Schema, FieldRule

_TYPE_PATTERNS = {
    "integer": re.compile(r"^-?\d+$"),
    "boolean": re.compile(r"^(true|false|1|0|yes|no)$", re.IGNORECASE),
    "url": re.compile(r"^https?://.+", re.IGNORECASE),
    "email": re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$"),
}


@dataclass
class ValidationError:
    field: str
    message: str
    severity: str = "error"  # error | warning

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(e.severity == "error" for e in self.errors)

    def add(self, field: str, message: str, severity: str = "error") -> None:
        self.errors.append(ValidationError(field=field, message=message, severity=severity))


def validate(env_vars: dict[str, str], schema: Schema) -> ValidationResult:
    """Validate a dict of env variables against the given schema."""
    result = ValidationResult()

    for rule in schema.fields:
        value = env_vars.get(rule.name)

        if value is None or value == "":
            if rule.default is not None:
                continue  # default covers missing value
            if rule.required:
                result.add(rule.field if hasattr(rule, 'field') else rule.name,
                           "Required variable is missing or empty")
            else:
                result.add(rule.name, "Optional variable is not set", severity="warning")
            continue

        # Type check
        if rule.type in _TYPE_PATTERNS:
            if not _TYPE_PATTERNS[rule.type].match(value):
                result.add(rule.name, f"Value '{value}' does not match expected type '{rule.type}'")

        # Custom pattern check
        if rule.pattern:
            if not re.fullmatch(rule.pattern, value):
                result.add(rule.name, f"Value '{value}' does not match pattern '{rule.pattern}'")

    return result
