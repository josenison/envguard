"""Scanner: detect duplicate keys in a .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class ScanIssue:
    key: str
    lines: List[int]  # 1-based line numbers where the key appears
    severity: str = "error"

    def __str__(self) -> str:
        locs = ", ".join(str(ln) for ln in self.lines)
        return f"[{self.severity.upper()}] Duplicate key '{self.key}' found on lines: {locs}"


@dataclass
class ScanResult:
    issues: List[ScanIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def __str__(self) -> str:
        if not self.issues:
            return "No duplicate keys found."
        return "\n".join(str(i) for i in self.issues)


def _parse_key_locations(text: str) -> Dict[str, List[int]]:
    """Return a mapping of key -> list of 1-based line numbers."""
    locations: Dict[str, List[int]] = {}
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if not key:
            continue
        locations.setdefault(key, []).append(lineno)
    return locations


def scan_env(text: str) -> ScanResult:
    """Scan *text* (contents of a .env file) for duplicate key definitions."""
    result = ScanResult()
    locations = _parse_key_locations(text)
    for key, line_nums in sorted(locations.items()):
        if len(line_nums) > 1:
            result.issues.append(ScanIssue(key=key, lines=line_nums, severity="error"))
    return result
