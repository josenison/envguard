"""CLI sub-command: export a .env file to shell/docker/json format."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envguard.exporter import ExportFormat, export_env


def add_export_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "export",
        help="Export a .env file to shell, docker, or JSON format.",
    )
    parser.add_argument("env_file", help="Path to the .env file.")
    parser.add_argument(
        "--format",
        choices=[f.value for f in ExportFormat],
        default=ExportFormat.SHELL.value,
        dest="fmt",
        help="Output format (default: shell).",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Omit the 'export' keyword (shell format only).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write output to this file instead of stdout.",
    )


def _parse_env_file(text: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        env[key.strip()] = value.strip()
    return env


def run_export(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"[error] env file not found: {env_path}", file=sys.stderr)
        return 1

    env = _parse_env_file(env_path.read_text())
    fmt = ExportFormat(args.fmt)
    result = export_env(env, fmt=fmt, export_keyword=not args.no_export)

    if args.output:
        Path(args.output).write_text(result.content)
        print(f"Exported {len(result.keys_exported)} key(s) to {args.output}")
    else:
        print(result.content)

    return 0
