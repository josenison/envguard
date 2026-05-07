"""Rename keys in a .env file with optional dry-run support."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class RenameResult:
    """Result of a rename operation."""

    original_lines: List[str]
    renamed_lines: List[str]
    applied: List[Tuple[str, str]] = field(default_factory=list)   # (old, new)
    skipped: List[str] = field(default_factory=list)               # old names not found

    def __str__(self) -> str:  # pragma: no cover
        parts: List[str] = []
        for old, new in self.applied:
            parts.append(f"  renamed: {old} -> {new}")
        for key in self.skipped:
            parts.append(f"  skipped (not found): {key}")
        return "\n".join(parts) if parts else "  no changes"

    @property
    def was_changed(self) -> bool:
        return bool(self.applied)


def _parse_key(line: str) -> str | None:
    """Return the key of a KEY=VALUE line, or None for comments/blanks."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if "=" not in stripped:
        return None
    return stripped.split("=", 1)[0].strip()


def rename_keys(text: str, mapping: Dict[str, str]) -> RenameResult:
    """Rename keys in *text* according to *mapping* (old -> new).

    Lines that are comments, blank, or lack an ``=`` are passed through
    unchanged.  Keys in *mapping* that are not present in *text* are
    reported in ``RenameResult.skipped``.
    """
    original_lines = text.splitlines(keepends=True)
    renamed_lines: List[str] = []
    found: set[str] = set()

    for line in original_lines:
        key = _parse_key(line)
        if key is not None and key in mapping:
            new_key = mapping[key]
            # Preserve everything after the old key name
            rest = line[line.index(key) + len(key):]
            leading = line[: line.index(key)]
            renamed_lines.append(f"{leading}{new_key}{rest}")
            found.add(key)
        else:
            renamed_lines.append(line)

    applied = [(old, new) for old, new in mapping.items() if old in found]
    skipped = [old for old in mapping if old not in found]

    return RenameResult(
        original_lines=original_lines,
        renamed_lines=renamed_lines,
        applied=applied,
        skipped=skipped,
    )
