"""Type-check .env values against schema-declared types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envguard.schema import Schema


@dataclass
class TypeIssue:
    key: str
    expected: str
    actual_value: str
    message: str

    def __str__(self) -> str:
        return (
            f"[{self.key}] expected type '{self.expected}', "
            f"got value '{self.actual_value}': {self.message}"
        )


@dataclass
class TypeCheckResult:
    issues: List[TypeIssue] = field(default_factory=list)

    def has_issues(self) -> bool:
        return bool(self.issues)

    def __str__(self) -> str:
        if not self.issues:
            return "Type check passed — no issues found."
        lines = ["Type check issues:"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


def _check_value(key: str, value: str, expected_type: str) -> TypeIssue | None:
    """Return a TypeIssue if value does not match expected_type, else None."""
    t = expected_type.lower()
    if t == "int":
        try:
            int(value)
        except ValueError:
            return TypeIssue(key, expected_type, value, "cannot be parsed as integer")
    elif t == "float":
        try:
            float(value)
        except ValueError:
            return TypeIssue(key, expected_type, value, "cannot be parsed as float")
    elif t == "bool":
        if value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
            return TypeIssue(key, expected_type, value, "not a recognised boolean literal")
    elif t == "url":
        if not (value.startswith("http://") or value.startswith("https://")):
            return TypeIssue(key, expected_type, value, "does not start with http:// or https://")
    # 'str' and unknown types always pass
    return None


def typecheck_env(env: Dict[str, str], schema: Schema) -> TypeCheckResult:
    """Validate env value types against schema field rules."""
    result = TypeCheckResult()
    for rule in schema.fields:
        if rule.type in (None, "str", ""):
            continue
        value = env.get(rule.name)
        if value is None:
            continue  # missing keys are handled by the validator
        issue = _check_value(rule.name, value, rule.type)
        if issue:
            result.issues.append(issue)
    return result
