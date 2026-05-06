"""Variable interpolation support for .env files.

Supports ${VAR} and $VAR syntax, resolving references within the same env
dictionary or falling back to os.environ.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_BRACE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_BARE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationWarning:
    key: str
    ref: str
    message: str

    def __str__(self) -> str:
        return f"[{self.key}] unresolved reference '${self.ref}': {self.message}"


@dataclass
class InterpolationResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    warnings: List[InterpolationWarning] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


def _resolve_value(
    key: str,
    value: str,
    env: Dict[str, str],
    warnings: List[InterpolationWarning],
    use_os_env: bool,
) -> str:
    def replace_ref(match: re.Match) -> str:
        ref = match.group(1)
        if ref in env:
            return env[ref]
        if use_os_env and ref in os.environ:
            return os.environ[ref]
        warnings.append(
            InterpolationWarning(
                key=key,
                ref=ref,
                message="variable not found in env or os.environ",
            )
        )
        return match.group(0)  # leave original token

    result = _BRACE_RE.sub(replace_ref, value)
    result = _BARE_RE.sub(replace_ref, result)
    return result


def interpolate_env(
    env: Dict[str, str],
    use_os_env: bool = True,
) -> InterpolationResult:
    """Resolve variable references in *env* values.

    Parameters
    ----------
    env:
        Mapping of key -> raw value (may contain ``$VAR`` / ``${VAR}`` tokens).
    use_os_env:
        When *True* (default), fall back to ``os.environ`` for unknown refs.
    """
    warnings: List[InterpolationWarning] = []
    resolved: Dict[str, str] = {}
    for k, v in env.items():
        resolved[k] = _resolve_value(k, v, env, warnings, use_os_env)
    return InterpolationResult(resolved=resolved, warnings=warnings)
