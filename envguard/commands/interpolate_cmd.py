"""CLI sub-command: interpolate — resolve variable references in a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

from envguard.interpolator import interpolate_env


def add_interpolate_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "interpolate",
        help="Resolve $VAR / ${VAR} references inside a .env file and print the result.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "--no-os-env",
        action="store_true",
        default=False,
        help="Do not fall back to os.environ for unresolved references.",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 if any reference cannot be resolved.",
    )


def _parse_env_file(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        env[key.strip()] = value.strip()
    return env


def run_interpolate(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"[error] env file not found: {env_path}", file=sys.stderr)
        return 1

    raw_env = _parse_env_file(env_path)
    result = interpolate_env(raw_env, use_os_env=not args.no_os_env)

    for k, v in result.resolved.items():
        print(f"{k}={v}")

    if result.has_warnings:
        print("", file=sys.stderr)
        for w in result.warnings:
            print(f"[warning] {w}", file=sys.stderr)

    if args.strict and result.has_warnings:
        return 1
    return 0
