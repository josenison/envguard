"""Snapshot utility: capture and compare .env state over time."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class SnapshotDiff:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)

    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def __str__(self) -> str:
        lines: List[str] = []
        for k in self.added:
            lines.append(f"+ {k}")
        for k in self.removed:
            lines.append(f"- {k}")
        for k in self.changed:
            lines.append(f"~ {k}")
        return "\n".join(lines) if lines else "No differences."


@dataclass
class Snapshot:
    timestamp: str
    keys: Dict[str, str]  # key -> value

    def to_dict(self) -> dict:
        return {"timestamp": self.timestamp, "keys": self.keys}

    @staticmethod
    def from_dict(data: dict) -> "Snapshot":
        return Snapshot(timestamp=data["timestamp"], keys=data["keys"])


def create_snapshot(env: Dict[str, str]) -> Snapshot:
    """Create a new snapshot from a dict of env vars."""
    ts = datetime.now(timezone.utc).isoformat()
    return Snapshot(timestamp=ts, keys=dict(env))


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load_snapshot(path: str) -> Snapshot:
    """Load a snapshot from a JSON file.

    Raises:
        FileNotFoundError: If the snapshot file does not exist.
        ValueError: If the file content is not valid JSON or is missing
            required fields ('timestamp' or 'keys').
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Snapshot file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in snapshot file '{path}': {exc}") from exc
    if "timestamp" not in data or "keys" not in data:
        raise ValueError(
            f"Snapshot file '{path}' is missing required fields ('timestamp', 'keys')."
        )
    return Snapshot.from_dict(data)


def compare_snapshots(old: Snapshot, new: Snapshot) -> SnapshotDiff:
    """Return keys added, removed, or changed between two snapshots."""
    old_keys = set(old.keys)
    new_keys = set(new.keys)

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    changed = sorted(
        k for k in old_keys & new_keys if old.keys[k] != new.keys[k]
    )
    return SnapshotDiff(added=added, removed=removed, changed=changed)
