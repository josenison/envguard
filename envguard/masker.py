"""Mask sensitive values in .env content for safe logging or display."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

_SENSITIVE_PATTERNS = ("password", "secret", "token", "key", "api", "auth", "private", "credential")
_MASK = "***"


@dataclass
class MaskResult:
    lines: List[str] = field(default_factory=list)
    masked_keys: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return "\n".join(self.lines)

    @property
    def was_masked(self) -> bool:
        return len(self.masked_keys) > 0


def _is_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(pat in lower for pat in _SENSITIVE_PATTERNS)


def _parse_pair(line: str) -> Tuple[str, str, str] | None:
    """Return (key, separator, value) or None if not a key=value line."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if "=" not in stripped:
        return None
    key, _, value = stripped.partition("=")
    return key.strip(), "=", value


def mask_env(text: str, reveal_keys: List[str] | None = None) -> MaskResult:
    """Mask sensitive key values in *text*.

    Args:
        text: Raw .env file content.
        reveal_keys: Optional list of keys that should NOT be masked even if
            they match a sensitive pattern.

    Returns:
        MaskResult with masked lines and a list of keys that were masked.
    """
    reveal = {k.upper() for k in (reveal_keys or [])}
    result = MaskResult()

    for line in text.splitlines():
        parsed = _parse_pair(line)
        if parsed is None:
            result.lines.append(line)
            continue

        key, sep, value = parsed
        upper_key = key.upper()

        if _is_sensitive(key) and upper_key not in reveal:
            result.lines.append(f"{key}{sep}{_MASK}")
            result.masked_keys.append(key)
        else:
            result.lines.append(line)

    return result
