"""CLI sub-command: compare two .env files at the value level."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.comparator import compare_envs


def add_compare_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "compare",
        help="Compare two .env files and show value-level differences.",
    )
    parser.add_argument("env_a", help="Path to the first .env file.")
    parser.add_argument("env_b", help="Path to the second .env file.")
    parser.add_argument(
        "--ignore",
        metavar="KEY",
        nargs="*",
        default=[],
        help="Keys to exclude from comparison.",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output differences as JSON.",
    )


def run_compare(args: argparse.Namespace) -> int:
    path_a = Path(args.env_a)
    path_b = Path(args.env_b)

    if not path_a.exists():
        print(f"Error: file not found: {path_a}", file=sys.stderr)
        return 1
    if not path_b.exists():
        print(f"Error: file not found: {path_b}", file=sys.stderr)
        return 1

    text_a = path_a.read_text(encoding="utf-8")
    text_b = path_b.read_text(encoding="utf-8")
    ignore = list(args.ignore or [])

    result = compare_envs(text_a, text_b, ignore_keys=ignore)

    if getattr(args, "output_json", False):
        payload = [
            {"key": d.key, "value_a": d.value_a, "value_b": d.value_b}
            for d in result.diffs
        ]
        print(json.dumps(payload, indent=2))
    else:
        print(str(result))

    return 1 if result.has_differences() else 0
