"""CLI sub-command: rename keys inside a .env file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.renamer import rename_keys


def add_rename_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "rename",
        help="Rename one or more keys in a .env file.",
    )
    parser.add_argument("env_file", help="Path to the .env file.")
    parser.add_argument(
        "--map",
        required=True,
        metavar="JSON",
        help='JSON object mapping old key names to new ones, e.g. \'{"OLD": "NEW"}\'',
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Overwrite the original file with the renamed content.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print what would change without writing anything.",
    )


def run_rename(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: env file not found: {env_path}", file=sys.stderr)
        return 1

    try:
        mapping: dict[str, str] = json.loads(args.map)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON for --map: {exc}", file=sys.stderr)
        return 1

    if not isinstance(mapping, dict):
        print("error: --map must be a JSON object", file=sys.stderr)
        return 1

    text = env_path.read_text(encoding="utf-8")
    result = rename_keys(text, mapping)

    if args.dry_run or not args.in_place:
        print("".join(result.renamed_lines), end="")

    if result.skipped:
        for key in result.skipped:
            print(f"warning: key not found, skipped: {key}", file=sys.stderr)

    if args.in_place and not args.dry_run:
        env_path.write_text("".join(result.renamed_lines), encoding="utf-8")
        print(f"wrote {env_path}")

    return 0
