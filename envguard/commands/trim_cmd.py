"""CLI sub-command: trim undeclared keys from a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.schema import load_schema
from envguard.trimmer import trim_env


def add_trim_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "trim",
        help="Remove keys not declared in the schema from a .env file.",
    )
    parser.add_argument("env_file", help="Path to the .env file to trim.")
    parser.add_argument("schema_file", help="Path to the schema YAML file.")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the .env file with the trimmed output.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print trimmed output without writing changes.",
    )


def run_trim(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    schema_path = Path(args.schema_file)

    if not env_path.exists():
        print(f"[error] env file not found: {env_path}", file=sys.stderr)
        return 1

    if not schema_path.exists():
        print(f"[error] schema file not found: {schema_path}", file=sys.stderr)
        return 1

    schema = load_schema(schema_path.read_text())
    result = trim_env(env_path.read_text(), schema)

    if result.removed_keys:
        print(f"Removed {len(result.removed_keys)} undeclared key(s): {', '.join(result.removed_keys)}")
    else:
        print("No undeclared keys found — nothing to trim.")

    if args.dry_run or not args.in_place:
        print("--- trimmed output ---")
        print(str(result))
    elif args.in_place and result.was_changed():
        env_path.write_text(str(result))
        print(f"Written trimmed output to {env_path}")

    return 0
