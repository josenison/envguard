"""Deduplicator: remove duplicate keys from a .env file, keeping the last occurrence."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class DeduplicateResult:
    lines: List[str]
    removed: List[Tuple[int, str]]  # (1-based line number, key)

    def __str__(self) -> str:
        return "\n".join(self.lines)

    def was_changed(self) -> bool:
        return len(self.removed) > 0


def _parse_key(line: str) -> Optional[str]:
    """Return the key for a key=value line, or None for comments/blanks."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if "=" not in stripped:
        return None
    return stripped.split("=", 1)[0].strip()


def deduplicate_env(text: str, keep: str = "last") -> DeduplicateResult:
    """Remove duplicate keys from *text*, keeping either 'first' or 'last' occurrence.

    Args:
        text: Raw contents of a .env file.
        keep: ``'last'`` (default) keeps the final definition; ``'first'`` keeps
              the earliest definition.

    Returns:
        A :class:`DeduplicateResult` with the cleaned lines and metadata about
        which duplicates were removed.
    """
    raw_lines = text.splitlines()

    # Build a mapping: key -> list of (index, line)
    key_positions: dict[str, List[int]] = {}
    for idx, line in enumerate(raw_lines):
        key = _parse_key(line)
        if key is not None:
            key_positions.setdefault(key, []).append(idx)

    # Decide which indices to *remove*
    indices_to_remove: set[int] = set()
    removed: List[Tuple[int, str]] = []
    for key, positions in key_positions.items():
        if len(positions) < 2:
            continue
        # keep == 'last': remove all but the last; keep == 'first': remove all but the first
        drop = positions[:-1] if keep == "last" else positions[1:]
        for idx in drop:
            indices_to_remove.add(idx)
            removed.append((idx + 1, key))

    removed.sort(key=lambda t: t[0])
    kept_lines = [
        line for idx, line in enumerate(raw_lines) if idx not in indices_to_remove
    ]
    return DeduplicateResult(lines=kept_lines, removed=removed)
