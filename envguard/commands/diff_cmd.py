"""CLI sub-command: diff two .env files or a .env against a schema."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.differ import diff_env_against_schema, diff_two_envs, parse_env_keys
from envguard.schema import load_schema


def add_diff_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "diff",
        help="Diff two .env files, or a .env file against a schema.",
    )
    parser.add_argument("env_a", metavar="ENV_A", help="First .env file path.")
    parser.add_argument(
        "env_b_or_schema",
        metavar="ENV_B_OR_SCHEMA",
        help="Second .env file OR a schema YAML/JSON file.",
    )
    parser.add_argument(
        "--against-schema",
        action="store_true",
        default=False,
        help="Treat the second argument as a schema file instead of a .env file.",
    )
    parser.set_defaults(func=run_diff)


def run_diff(args: argparse.Namespace) -> int:
    """Execute the diff command; returns exit code."""
    path_a = Path(args.env_a)
    path_b = Path(args.env_b_or_schema)

    if not path_a.exists():
        print(f"error: file not found: {path_a}", file=sys.stderr)
        return 2
    if not path_b.exists():
        print(f"error: file not found: {path_b}", file=sys.stderr)
        return 2

    keys_a = parse_env_keys(path_a.read_text(encoding="utf-8"))

    if args.against_schema:
        schema = load_schema(str(path_b))
        result = diff_env_against_schema(keys_a, schema)
    else:
        keys_b = parse_env_keys(path_b.read_text(encoding="utf-8"))
        result = diff_two_envs(keys_a, keys_b)

    if result.has_differences():
        print(str(result))
        return 1

    print("No differences found.")
    return 0
