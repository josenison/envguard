"""Redactor module: mask sensitive values in .env files for safe logging/display."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Keys whose values should be fully or partially masked
DEFAULT_SENSITIVE_PATTERNS: List[str] = [
    "PASSWORD",
    "PASSWD",
    "SECRET",
    "TOKEN",
    "API_KEY",
    "PRIVATE_KEY",
    "AUTH",
    "CREDENTIAL",
    "DSN",
]

REDACT_PLACEHOLDER = "***REDACTED***"


@dataclass
class RedactResult:
    """Holds the redacted key/value pairs and metadata."""

    original_count: int
    redacted_keys: List[str] = field(default_factory=list)
    values: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = []
        for key, value in self.values.items():
            lines.append(f"{key}={value}")
        return "\n".join(lines)


def _is_sensitive(key: str, patterns: List[str]) -> bool:
    """Return True if the key matches any sensitive pattern (case-insensitive)."""
    upper = key.upper()
    return any(pattern in upper for pattern in patterns)


def _partial_mask(value: str) -> str:
    """Show only the first 2 and last 2 characters; mask the rest."""
    if len(value) <= 4:
        return REDACT_PLACEHOLDER
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def redact_env(
    env: Dict[str, str],
    sensitive_patterns: Optional[List[str]] = None,
    partial: bool = False,
) -> RedactResult:
    """Redact sensitive values from an env mapping.

    Args:
        env: Dictionary of environment variable key/value pairs.
        sensitive_patterns: List of substrings that mark a key as sensitive.
            Defaults to DEFAULT_SENSITIVE_PATTERNS.
        partial: If True, show a partial mask instead of full redaction.

    Returns:
        RedactResult with masked values for sensitive keys.
    """
    patterns = sensitive_patterns if sensitive_patterns is not None else DEFAULT_SENSITIVE_PATTERNS
    redacted_keys: List[str] = []
    result_values: Dict[str, str] = {}

    for key, value in env.items():
        if _is_sensitive(key, patterns):
            redacted_keys.append(key)
            result_values[key] = _partial_mask(value) if partial else REDACT_PLACEHOLDER
        else:
            result_values[key] = value

    return RedactResult(
        original_count=len(env),
        redacted_keys=redacted_keys,
        values=result_values,
    )
