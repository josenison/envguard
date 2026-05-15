"""CLI sub-command: group .env keys by prefix."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from envguard.grouper import group_env


def add_group_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "group",
        help="Group .env keys by prefix into named sections.",
    )
    parser.add_argument("env_file", help="Path to the .env file.")
    parser.add_argument(
        "--prefixes",
        metavar="JSON",
        default=None,
        help='JSON array of prefixes, e.g. \'["DB","AWS"]\'. '
             "Omit to auto-detect all prefixes.",
    )
    parser.add_argument(
        "--separator",
        default="_",
        help="Key prefix separator (default: _).",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output result as JSON.",
    )


def run_group(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: env file not found: {env_path}", file=sys.stderr)
        return 1

    prefixes: Optional[List[str]] = None
    if args.prefixes is not None:
        try:
            prefixes = json.loads(args.prefixes)
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON for --prefixes: {exc}", file=sys.stderr)
            return 1
        if not isinstance(prefixes, list) or not all(
            isinstance(p, str) for p in prefixes
        ):
            print("error: --prefixes must be a JSON array of strings.", file=sys.stderr)
            return 1

    text = env_path.read_text(encoding="utf-8")
    result = group_env(text, prefixes=prefixes, separator=args.separator)

    if args.output_json:
        data = {
            "groups": {g: [list(p) for p in pairs] for g, pairs in result.groups.items()},
            "ungrouped": [list(p) for p in result.ungrouped],
        }
        print(json.dumps(data, indent=2))
    else:
        print(str(result))

    return 0
