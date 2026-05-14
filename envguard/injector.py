"""Inject variables from a .env file into the current process environment."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InjectionResult:
    injected: Dict[str, str] = field(default_factory=dict)
    skipped: Dict[str, str] = field(default_factory=dict)
    overwritten: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        lines: List[str] = []
        if self.injected:
            lines.append(f"Injected ({len(self.injected)}): {', '.join(sorted(self.injected))}")
        if self.skipped:
            lines.append(f"Skipped ({len(self.skipped)}): {', '.join(sorted(self.skipped))}")
        if self.overwritten:
            lines.append(f"Overwritten ({len(self.overwritten)}): {', '.join(sorted(self.overwritten))}")
        return "\n".join(lines) if lines else "Nothing to inject."

    @property
    def total_injected(self) -> int:
        return len(self.injected) + len(self.overwritten)


def _parse_env_pairs(text: str) -> Dict[str, str]:
    pairs: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        if key:
            pairs[key] = value
    return pairs


def inject_env(
    text: str,
    *,
    overwrite: bool = False,
    target: Optional[Dict[str, str]] = None,
) -> InjectionResult:
    """Parse *text* as a .env file and inject variables into *target* (defaults to os.environ)."""
    if target is None:
        target = os.environ  # type: ignore[assignment]

    result = InjectionResult()
    pairs = _parse_env_pairs(text)

    for key, value in pairs.items():
        if key in target:
            if overwrite:
                result.overwritten[key] = value
                target[key] = value
            else:
                result.skipped[key] = value
        else:
            result.injected[key] = value
            target[key] = value

    return result
