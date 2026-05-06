"""Export validated env data to various formats (shell, docker, JSON)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class ExportFormat(str, Enum):
    SHELL = "shell"
    DOCKER = "docker"
    JSON = "json"


@dataclass
class ExportResult:
    format: ExportFormat
    content: str
    keys_exported: List[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        return self.content


def _quote_shell(value: str) -> str:
    """Wrap value in single quotes, escaping any existing single quotes."""
    escaped = value.replace("'", "'\\''")
    return f"'{escaped}'"


def export_env(
    env: Dict[str, str],
    fmt: ExportFormat = ExportFormat.SHELL,
    export_keyword: bool = True,
) -> ExportResult:
    """Serialise *env* dict to the requested format.

    Args:
        env: Mapping of variable names to values.
        fmt: Target format.
        export_keyword: For SHELL format, prefix each line with ``export``.

    Returns:
        An :class:`ExportResult` containing the rendered content.
    """
    keys = sorted(env.keys())

    if fmt == ExportFormat.JSON:
        content = json.dumps({k: env[k] for k in keys}, indent=2)

    elif fmt == ExportFormat.DOCKER:
        lines = [f"{k}={env[k]}" for k in keys]
        content = "\n".join(lines)

    else:  # SHELL
        prefix = "export " if export_keyword else ""
        lines = [f"{prefix}{k}={_quote_shell(env[k])}" for k in keys]
        content = "\n".join(lines)

    return ExportResult(format=fmt, content=content, keys_exported=keys)
