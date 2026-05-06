"""CLI sub-command: sort — sort and optionally group an .env file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

from envguard.sorter import sort_env


def add_sort_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "sort",
        help="Sort .env file keys alphabetically, optionally grouped.",
    )
    parser.add_argument("env_file", help="Path to the .env file to sort.")
    parser.add_argument(
        "--groups",
        metavar="JSON",
        default=None,
        help=(
            'JSON object mapping group names to key prefixes, e.g. '
            '{\"db\": [\"DB_\"], \"app\": [\"APP_\"]}'
        ),
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the original file with the sorted output.",
    )


def run_sort(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: env file not found: {env_path}", file=sys.stderr)
        return 1

    groups: Dict[str, List[str]] = {}
    if args.groups:
        try:
            groups = json.loads(args.groups)
        except json.JSONDecodeError as exc:
            print(f"error: invalid --groups JSON: {exc}", file=sys.stderr)
            return 1

    text = env_path.read_text(encoding="utf-8")
    result = sort_env(text, groups=groups)
    output = str(result)

    if args.in_place:
        env_path.write_text(output, encoding="utf-8")
        print(f"Sorted {env_path} in place.")
    else:
        print(output, end="")

    return 0
