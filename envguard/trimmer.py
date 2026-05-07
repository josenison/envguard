"""Trim unused or undeclared keys from a .env file based on a schema."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from envguard.schema import Schema


@dataclass
class TrimResult:
    original_lines: List[str]
    kept_lines: List[str]
    removed_keys: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return "\n".join(self.kept_lines)

    def was_changed(self) -> bool:
        return len(self.removed_keys) > 0


def _parse_key(line: str) -> str | None:
    """Return the key name if the line is a key=value pair, else None."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if "=" not in stripped:
        return None
    key, _, _ = stripped.partition("=")
    return key.strip()


def trim_env(text: str, schema: Schema) -> TrimResult:
    """Remove lines whose keys are not declared in *schema*.

    Blank lines and comments are always preserved.
    Returns a :class:`TrimResult` describing what was kept and removed.
    """
    allowed: Set[str] = {f.name for f in schema.fields}
    original_lines = text.splitlines()
    kept_lines: List[str] = []
    removed_keys: List[str] = []

    for line in original_lines:
        key = _parse_key(line)
        if key is None:
            # blank line or comment — always keep
            kept_lines.append(line)
        elif key in allowed:
            kept_lines.append(line)
        else:
            removed_keys.append(key)

    return TrimResult(
        original_lines=original_lines,
        kept_lines=kept_lines,
        removed_keys=removed_keys,
    )
