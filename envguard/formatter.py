"""Formatter: normalize and reformat .env file contents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class FormatResult:
    lines: List[str] = field(default_factory=list)
    changes: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return "\n".join(self.lines)

    @property
    def was_changed(self) -> bool:
        return len(self.changes) > 0


def _normalize_line(raw: str, line_no: int) -> Tuple[str, List[str]]:
    """Return a normalized line and a list of change descriptions."""
    changes: List[str] = []
    stripped = raw.rstrip("\n")

    # Preserve blank lines and comments unchanged
    if stripped.strip() == "" or stripped.lstrip().startswith("#"):
        return stripped, changes

    if "=" not in stripped:
        return stripped, changes

    key, _, value = stripped.partition("=")

    # Strip surrounding whitespace from key
    clean_key = key.strip()
    if clean_key != key:
        changes.append(f"line {line_no}: stripped whitespace from key '{key.strip()}'")

    # Strip surrounding whitespace from value (but not quoted values)
    clean_value = value.strip()
    if clean_value != value and not (clean_value.startswith('"') or clean_value.startswith("'")):
        changes.append(f"line {line_no}: stripped whitespace from value of '{clean_key}'")
    else:
        clean_value = value

    # Remove inline comments (value # comment) only for unquoted values
    if not (clean_value.startswith('"') or clean_value.startswith("'")):
        if " #" in clean_value:
            without_comment = clean_value.split(" #")[0].rstrip()
            if without_comment != clean_value:
                changes.append(f"line {line_no}: removed inline comment from '{clean_key}'")
                clean_value = without_comment

    normalized = f"{clean_key}={clean_value}"
    return normalized, changes


def format_env(text: str) -> FormatResult:
    """Parse raw .env text and return a normalized FormatResult."""
    result = FormatResult()
    for line_no, raw in enumerate(text.splitlines(), start=1):
        normalized, changes = _normalize_line(raw, line_no)
        result.lines.append(normalized)
        result.changes.extend(changes)
    return result
