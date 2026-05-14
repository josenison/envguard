"""CLI sub-command: inject .env variables into the current environment and exec a command."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from envguard.injector import inject_env


def add_inject_subparser(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "inject",
        help="Inject .env variables into the environment and optionally run a command.",
    )
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing environment variables",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print what would be injected without modifying the environment",
    )
    parser.add_argument(
        "cmd",
        nargs=argparse.REMAINDER,
        help="Optional command to run with the injected environment",
    )


def run_inject(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"Error: env file not found: {env_path}", file=sys.stderr)
        return 1

    text = env_path.read_text(encoding="utf-8")

    if args.dry_run:
        # Inject into a copy so we don't pollute the real environment
        env_copy: dict[str, str] = dict(os.environ)
        result = inject_env(text, overwrite=args.overwrite, target=env_copy)
        print(str(result))
        return 0

    result = inject_env(text, overwrite=args.overwrite)
    print(str(result))

    cmd = args.cmd
    if cmd:
        # Strip leading '--' separator if present
        if cmd[0] == "--":
            cmd = cmd[1:]
        if cmd:
            proc = subprocess.run(cmd, env=os.environ)
            return proc.returncode

    return 0
