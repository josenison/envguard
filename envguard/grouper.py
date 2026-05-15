"""Group .env keys by prefix into named sections."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class GroupResult:
    groups: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)
    ungrouped: List[Tuple[str, str]] = field(default_factory=list)

    def __str__(self) -> str:
        lines: List[str] = []
        for group_name, pairs in sorted(self.groups.items()):
            lines.append(f"[{group_name}]")
            for k, v in pairs:
                lines.append(f"  {k}={v}")
        if self.ungrouped:
            lines.append("[ungrouped]")
            for k, v in self.ungrouped:
                lines.append(f"  {k}={v}")
        return "\n".join(lines)

    def all_pairs(self) -> List[Tuple[str, str]]:
        """Return every key/value pair across all groups and ungrouped."""
        result: List[Tuple[str, str]] = []
        for pairs in self.groups.values():
            result.extend(pairs)
        result.extend(self.ungrouped)
        return result


def _parse_pairs(text: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        pairs.append((key.strip(), value.strip()))
    return pairs


def group_env(
    text: str,
    prefixes: Optional[List[str]] = None,
    separator: str = "_",
) -> GroupResult:
    """Group env pairs by key prefix.

    Args:
        text: Raw .env file contents.
        prefixes: Explicit list of prefixes to group by.  When *None* every
            distinct prefix (the part before the first *separator*) is used.
        separator: Character that delimits the prefix from the rest of the key.
    """
    pairs = _parse_pairs(text)
    result = GroupResult()

    if prefixes is None:
        seen: List[str] = []
        for k, _ in pairs:
            if separator in k:
                p = k.split(separator, 1)[0]
                if p not in seen:
                    seen.append(p)
        prefixes = seen

    prefix_set = set(prefixes)

    for k, v in pairs:
        matched = False
        if separator in k:
            p = k.split(separator, 1)[0]
            if p in prefix_set:
                result.groups.setdefault(p, []).append((k, v))
                matched = True
        if not matched:
            result.ungrouped.append((k, v))

    return result
