"""Normalize .env file values: unquote, unescape, and standardize booleans."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

_BOOL_TRUE = {"true", "yes", "1", "on"}
_BOOL_FALSE = {"false", "no", "0", "off"}


@dataclass
class NormalizeResult:
    lines: List[str] = field(default_factory=list)
    changes: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, old, new)

    def __str__(self) -> str:
        return "\n".join(self.lines)

    def was_changed(self) -> bool:
        return len(self.changes) > 0


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2:
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            inner = value[1:-1]
            # unescape common escape sequences for double-quoted strings
            if value.startswith('"'):
                inner = inner.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
            return inner
    return value


def _normalize_bool(value: str) -> str:
    """Normalize boolean-like strings to canonical 'true'/'false'."""
    lower = value.lower()
    if lower in _BOOL_TRUE:
        return "true"
    if lower in _BOOL_FALSE:
        return "false"
    return value


def normalize_env(
    text: str,
    normalize_booleans: bool = True,
    unquote_values: bool = True,
) -> NormalizeResult:
    """Normalize env file text and return a NormalizeResult."""
    result = NormalizeResult()

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            result.lines.append(raw_line)
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        original_value = value

        if unquote_values:
            value = _strip_quotes(value)

        if normalize_booleans:
            value = _normalize_bool(value)

        if value != original_value:
            result.changes.append((key, original_value, value))

        result.lines.append(f"{key}={value}")

    return result
