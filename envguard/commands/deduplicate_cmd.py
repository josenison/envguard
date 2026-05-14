"""CLI sub-command: deduplicate — remove duplicate keys from a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.deduplicator import deduplicate_env


def add_deduplicate_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "deduplicate",
        help="Remove duplicate keys from a .env file.",
    )
    parser.add_argument("env_file", help="Path to the .env file.")
    parser.add_argument(
        "--keep",
        choices=["first", "last"],
        default="last",
        help="Which occurrence to keep when a key appears multiple times (default: last).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the result without modifying the file.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational output.",
    )


def run_deduplicate(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"Error: env file not found: {env_path}", file=sys.stderr)
        return 1

    text = env_path.read_text(encoding="utf-8")
    result = deduplicate_env(text, keep=args.keep)

    if not result.was_changed():
        if not args.quiet:
            print("No duplicate keys found.")
        return 0

    if not args.quiet:
        for lineno, key in result.removed:
            print(f"  removed duplicate '{key}' at line {lineno}")

    output = "\n".join(result.lines)
    if not output.endswith("\n"):
        output += "\n"

    if args.dry_run:
        print(output)
    else:
        env_path.write_text(output, encoding="utf-8")
        if not args.quiet:
            print(f"Wrote deduplicated env to {env_path}")

    return 0
