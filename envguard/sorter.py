"""Sort and group .env file keys alphabetically or by custom group order."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SortResult:
    groups: Dict[str, List[str]]  # group_name -> ["KEY=value", ...]
    ungrouped: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines: List[str] = []
        for group, entries in self.groups.items():
            lines.append(f"# --- {group} ---")
            lines.extend(sorted(entries))
            lines.append("")
        if self.ungrouped:
            lines.append("# --- other ---")
            lines.extend(sorted(self.ungrouped))
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"


def _parse_pairs(text: str) -> List[tuple[str, str]]:
    """Return (key, raw_line) pairs from env text, skipping blanks/comments."""
    pairs: List[tuple[str, str]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        pairs.append((key, stripped))
    return pairs


def sort_env(
    text: str,
    groups: Optional[Dict[str, List[str]]] = None,
) -> SortResult:
    """Sort env entries, optionally bucketing keys into named groups.

    Args:
        text: Raw .env file content.
        groups: Mapping of group_name -> list of key prefixes/exact keys
                that belong to that group.  Order of the dict determines
                output order.

    Returns:
        SortResult with grouped and ungrouped entries.
    """
    groups = groups or {}
    result_groups: Dict[str, List[str]] = {name: [] for name in groups}
    ungrouped: List[str] = []

    for key, line in _parse_pairs(text):
        placed = False
        for group_name, patterns in groups.items():
            if any(key == p or key.startswith(p) for p in patterns):
                result_groups[group_name].append(line)
                placed = True
                break
        if not placed:
            ungrouped.append(line)

    return SortResult(groups=result_groups, ungrouped=ungrouped)
