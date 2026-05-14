"""Patch (update or add) key-value pairs in an existing .env file content."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class PatchResult:
    lines: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        return "\n".join(self.lines)

    def was_changed(self) -> bool:
        return bool(self.added or self.updated)


def _parse_key(line: str) -> str | None:
    """Return the key for a key=value line, or None for comments/blanks."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if "=" not in stripped:
        return None
    return stripped.split("=", 1)[0].strip()


def patch_env(source: str, patches: Dict[str, str]) -> PatchResult:
    """Apply *patches* to *source* env text.

    Existing keys whose names appear in *patches* are updated in-place.
    Keys not already present are appended at the end of the file.
    Comments and blank lines are preserved.
    """
    result = PatchResult()
    remaining = dict(patches)  # keys we still need to handle

    for line in source.splitlines():
        key = _parse_key(line)
        if key is not None and key in remaining:
            new_line = f"{key}={remaining.pop(key)}"
            result.lines.append(new_line)
            result.updated.append(key)
        else:
            result.lines.append(line)

    # Append keys that were not found in the original content
    for key, value in remaining.items():
        result.lines.append(f"{key}={value}")
        result.added.append(key)

    return result
