"""Diff two .env files or a .env file against a schema to surface missing/extra keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from envguard.schema import Schema


@dataclass
class DiffResult:
    """Result of comparing two sets of environment keys."""

    missing_in_env: List[str] = field(default_factory=list)
    extra_in_env: List[str] = field(default_factory=list)
    common: List[str] = field(default_factory=list)

    def has_differences(self) -> bool:
        return bool(self.missing_in_env or self.extra_in_env)

    def __str__(self) -> str:  # pragma: no cover
        lines = []
        for key in sorted(self.missing_in_env):
            lines.append(f"- {key}  (missing from env)")
        for key in sorted(self.extra_in_env):
            lines.append(f"+ {key}  (extra in env, not in schema)")
        for key in sorted(self.common):
            lines.append(f"  {key}")
        return "\n".join(lines) if lines else "(no differences)"


def diff_env_against_schema(env_keys: Set[str], schema: Schema) -> DiffResult:
    """Compare a set of env keys against a schema's declared fields."""
    schema_keys: Set[str] = {f.name for f in schema.fields}
    missing = sorted(schema_keys - env_keys)
    extra = sorted(env_keys - schema_keys)
    common = sorted(env_keys & schema_keys)
    return DiffResult(missing_in_env=missing, extra_in_env=extra, common=common)


def diff_two_envs(env_a: Set[str], env_b: Set[str]) -> DiffResult:
    """Compare two .env key sets (e.g. staging vs production)."""
    missing = sorted(env_b - env_a)   # in b but not a  -> missing from a
    extra = sorted(env_a - env_b)     # in a but not b  -> extra in a
    common = sorted(env_a & env_b)
    return DiffResult(missing_in_env=missing, extra_in_env=extra, common=common)


def parse_env_keys(text: str) -> Set[str]:
    """Extract variable names from raw .env file text."""
    keys: Set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key = line.split("=", 1)[0].strip()
            if key:
                keys.add(key)
    return keys
