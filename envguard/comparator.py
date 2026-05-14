"""Compare two .env files and report value-level differences."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ValueDiff:
    key: str
    value_a: Optional[str]
    value_b: Optional[str]

    def __str__(self) -> str:
        a = self.value_a if self.value_a is not None else "<missing>"
        b = self.value_b if self.value_b is not None else "<missing>"
        return f"{self.key}: {a!r} -> {b!r}"


@dataclass
class CompareResult:
    diffs: List[ValueDiff] = field(default_factory=list)

    def has_differences(self) -> bool:
        return bool(self.diffs)

    def added(self) -> List[ValueDiff]:
        return [d for d in self.diffs if d.value_a is None]

    def removed(self) -> List[ValueDiff]:
        return [d for d in self.diffs if d.value_b is None]

    def changed(self) -> List[ValueDiff]:
        return [d for d in self.diffs if d.value_a is not None and d.value_b is not None]

    def __str__(self) -> str:
        if not self.diffs:
            return "No differences found."
        lines = []
        for d in self.diffs:
            lines.append(str(d))
        return "\n".join(lines)


def _parse_env_pairs(text: str) -> Dict[str, str]:
    pairs: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        pairs[key.strip()] = value.strip()
    return pairs


def compare_envs(text_a: str, text_b: str, ignore_keys: Optional[List[str]] = None) -> CompareResult:
    """Compare two env file contents and return value-level diffs."""
    ignore = set(ignore_keys or [])
    pairs_a = _parse_env_pairs(text_a)
    pairs_b = _parse_env_pairs(text_b)
    all_keys = sorted(set(pairs_a) | set(pairs_b))
    result = CompareResult()
    for key in all_keys:
        if key in ignore:
            continue
        va = pairs_a.get(key)
        vb = pairs_b.get(key)
        if va != vb:
            result.diffs.append(ValueDiff(key=key, value_a=va, value_b=vb))
    return result
