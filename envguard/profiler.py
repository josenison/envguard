"""Profile .env files to summarise key statistics and patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


_SENSITIVE_KEYWORDS = ("password", "secret", "token", "key", "api", "auth", "private")


@dataclass
class ProfileResult:
    total_keys: int = 0
    empty_values: List[str] = field(default_factory=list)
    sensitive_keys: List[str] = field(default_factory=list)
    duplicate_keys: List[str] = field(default_factory=list)
    longest_key: str = ""
    longest_value_key: str = ""
    type_guesses: Dict[str, str] = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            f"Total keys      : {self.total_keys}",
            f"Empty values    : {len(self.empty_values)}",
            f"Sensitive keys  : {len(self.sensitive_keys)}",
            f"Duplicate keys  : {len(self.duplicate_keys)}",
            f"Longest key     : {self.longest_key or '—'}",
            f"Longest value   : {self.longest_value_key or '—'}",
        ]
        return "\n".join(lines)


def _guess_type(value: str) -> str:
    if value == "":
        return "empty"
    if value.lower() in ("true", "false"):
        return "boolean"
    try:
        int(value)
        return "integer"
    except ValueError:
        pass
    try:
        float(value)
        return "float"
    except ValueError:
        pass
    return "string"


def _is_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(kw in lower for kw in _SENSITIVE_KEYWORDS)


def profile_env(pairs: Dict[str, str]) -> ProfileResult:
    """Analyse a dictionary of env key/value pairs and return a ProfileResult."""
    seen: Dict[str, int] = {}
    result = ProfileResult()

    longest_key = ""
    longest_val_key = ""

    for key, value in pairs.items():
        seen[key] = seen.get(key, 0) + 1
        result.total_keys += 1

        if value == "":
            result.empty_values.append(key)

        if _is_sensitive(key):
            result.sensitive_keys.append(key)

        result.type_guesses[key] = _guess_type(value)

        if len(key) > len(longest_key):
            longest_key = key
        if len(value) > len(pairs.get(longest_val_key, "")):
            longest_val_key = key

    result.duplicate_keys = [k for k, count in seen.items() if count > 1]
    result.longest_key = longest_key
    result.longest_value_key = longest_val_key
    return result
