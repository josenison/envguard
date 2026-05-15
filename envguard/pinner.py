"""Pin current .env values to a lockfile for drift detection."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PinEntry:
    key: str
    value_hash: str
    value_preview: str  # first 4 chars + '…' for non-sensitive, full for plain


@dataclass
class PinResult:
    entries: List[PinEntry] = field(default_factory=list)
    drifted: List[str] = field(default_factory=list)
    new_keys: List[str] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)

    def has_drift(self) -> bool:
        return bool(self.drifted or self.new_keys or self.removed_keys)

    def __str__(self) -> str:
        lines: List[str] = []
        if self.drifted:
            lines.append("Drifted keys: " + ", ".join(self.drifted))
        if self.new_keys:
            lines.append("New keys: " + ", ".join(self.new_keys))
        if self.removed_keys:
            lines.append("Removed keys: " + ", ".join(self.removed_keys))
        if not lines:
            lines.append("No drift detected.")
        return "\n".join(lines)


_SENSITIVE_FRAGMENTS = ("password", "secret", "token", "key", "api", "auth", "pwd")


def _is_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(frag in lower for frag in _SENSITIVE_FRAGMENTS)


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _preview(key: str, value: str) -> str:
    if _is_sensitive(key):
        return "****"
    return (value[:4] + "\u2026") if len(value) > 4 else value


def _parse_env_pairs(text: str) -> Dict[str, str]:
    pairs: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        pairs[key.strip()] = value.strip()
    return pairs


def pin_env(env_text: str) -> List[PinEntry]:
    """Create pin entries from env file text."""
    pairs = _parse_env_pairs(env_text)
    return [
        PinEntry(key=k, value_hash=_hash_value(v), value_preview=_preview(k, v))
        for k, v in sorted(pairs.items())
    ]


def compare_pin(
    env_text: str, lockfile_data: Dict
) -> PinResult:
    """Compare current env against a previously saved lockfile dict."""
    current_pairs = _parse_env_pairs(env_text)
    locked: Dict[str, str] = {e["key"]: e["value_hash"] for e in lockfile_data.get("entries", [])}

    drifted = [
        k for k, v in current_pairs.items()
        if k in locked and locked[k] != _hash_value(v)
    ]
    new_keys = [k for k in current_pairs if k not in locked]
    removed_keys = [k for k in locked if k not in current_pairs]

    entries = pin_env(env_text)
    return PinResult(entries=entries, drifted=drifted, new_keys=new_keys, removed_keys=removed_keys)


def lockfile_to_dict(entries: List[PinEntry]) -> Dict:
    return {"entries": [{"key": e.key, "value_hash": e.value_hash, "value_preview": e.value_preview} for e in entries]}
