"""Classify .env keys by category based on naming conventions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

# Patterns mapped to category labels (checked in order)
_CATEGORY_PATTERNS: List[tuple[str, str]] = [
    ("DATABASE", "database"),
    ("DB_", "database"),
    ("POSTGRES", "database"),
    ("MYSQL", "database"),
    ("REDIS", "cache"),
    ("CACHE", "cache"),
    ("MEMCACHE", "cache"),
    ("AWS", "cloud"),
    ("GCP", "cloud"),
    ("AZURE", "cloud"),
    ("S3_", "cloud"),
    ("SECRET", "security"),
    ("PASSWORD", "security"),
    ("TOKEN", "security"),
    ("API_KEY", "security"),
    ("PRIVATE", "security"),
    ("LOG", "logging"),
    ("DEBUG", "logging"),
    ("SENTRY", "logging"),
    ("PORT", "network"),
    ("HOST", "network"),
    ("URL", "network"),
    ("DOMAIN", "network"),
    ("SMTP", "email"),
    ("EMAIL", "email"),
    ("MAIL", "email"),
    ("FEATURE", "feature_flag"),
    ("FLAG", "feature_flag"),
    ("ENABLE_", "feature_flag"),
    ("DISABLE_", "feature_flag"),
]

_UNCATEGORIZED = "uncategorized"


@dataclass
class ClassifyResult:
    categories: Dict[str, List[str]] = field(default_factory=dict)

    def __str__(self) -> str:
        lines: List[str] = []
        for cat in sorted(self.categories):
            keys = ", ".join(sorted(self.categories[cat]))
            lines.append(f"[{cat}] {keys}")
        return "\n".join(lines) if lines else "(no keys)"

    def category_of(self, key: str) -> str:
        for cat, members in self.categories.items():
            if key in members:
                return cat
        return _UNCATEGORIZED


def _classify_key(key: str) -> str:
    upper = key.upper()
    for pattern, category in _CATEGORY_PATTERNS:
        if pattern in upper:
            return category
    return _UNCATEGORIZED


def classify_env(pairs: Dict[str, str]) -> ClassifyResult:
    """Classify a dict of env key→value pairs into named categories."""
    result = ClassifyResult()
    for key in pairs:
        cat = _classify_key(key)
        result.categories.setdefault(cat, []).append(key)
    return result
