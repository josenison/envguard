"""CLI sub-command: patch — update or add key-value pairs in a .env file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.patcher import patch_env


def add_patch_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "patch",
        help="Update or add key=value pairs in a .env file.",
    )
    parser.add_argument("env_file", help="Path to the .env file to patch.")
    parser.add_argument(
        "--set",
        metavar="JSON",
        required=True,
        help='JSON object of key/value pairs to apply, e.g. \'{"KEY": "val"}\'.'
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the patched content without writing to disk.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress summary output.",
    )


def run_patch(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"[error] env file not found: {env_path}", file=sys.stderr)
        return 1

    try:
        patches: dict = json.loads(args.set)
    except json.JSONDecodeError as exc:
        print(f"[error] invalid JSON for --set: {exc}", file=sys.stderr)
        return 1

    if not isinstance(patches, dict):
        print("[error] --set must be a JSON object", file=sys.stderr)
        return 1

    source = env_path.read_text(encoding="utf-8")
    result = run_patch_core(source, patches)

    patched_text = "\n".join(result.lines)
    if result.lines and not patched_text.endswith("\n"):
        patched_text += "\n"

    if args.dry_run:
        print(patched_text, end="")
    else:
        env_path.write_text(patched_text, encoding="utf-8")

    if not args.quiet:
        if result.updated:
            print(f"[patch] updated: {', '.join(result.updated)}")
        if result.added:
            print(f"[patch] added:   {', '.join(result.added)}")
        if not result.was_changed():
            print("[patch] no changes applied")

    return 0


# Thin wrapper so tests can call core logic without argparse objects
def run_patch_core(source: str, patches: dict):
    from envguard.patcher import patch_env as _patch
    return _patch(source, patches)
