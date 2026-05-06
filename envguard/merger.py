"""Merge multiple .env files with conflict detection and override support."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class MergeConflict:
    key: str
    values: List[Tuple[str, str]]  # list of (source_label, value)

    def __str__(self) -> str:
        sources = ", ".join(f"{src}={val!r}" for src, val in self.values)
        return f"Conflict on '{self.key}': {sources}"


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def __str__(self) -> str:
        lines = [f"Merged {len(self.merged)} keys from {len(self.sources)} source(s)."]
        if self.conflicts:
            lines.append(f"{len(self.conflicts)} conflict(s) detected:")
            for c in self.conflicts:
                lines.append(f"  {c}")
        return "\n".join(lines)


def _parse_env_text(text: str, label: str) -> Dict[str, str]:
    """Parse raw .env text into a key/value dict, skipping comments and blanks."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value.strip()
    return result


def merge_envs(
    sources: List[Tuple[str, str]],
    override: bool = False,
) -> MergeResult:
    """
    Merge multiple env sources.

    Args:
        sources: list of (label, raw_env_text) pairs, in priority order (last wins if override=True).
        override: if True, later sources silently override earlier ones;
                  if False, duplicate keys are recorded as conflicts.

    Returns:
        MergeResult with merged dict, conflicts, and source labels.
    """
    result = MergeResult(sources=[label for label, _ in sources])
    seen: Dict[str, List[Tuple[str, str]]] = {}  # key -> [(label, value), ...]

    for label, text in sources:
        parsed = _parse_env_text(text, label)
        for key, value in parsed.items():
            seen.setdefault(key, []).append((label, value))

    for key, entries in seen.items():
        if len(entries) == 1 or override:
            result.merged[key] = entries[-1][1]
        else:
            unique_values = list(dict.fromkeys(v for _, v in entries))
            if len(unique_values) > 1:
                result.conflicts.append(MergeConflict(key=key, values=entries))
                result.merged[key] = entries[-1][1]  # still populate with last value
            else:
                result.merged[key] = entries[-1][1]

    return result
