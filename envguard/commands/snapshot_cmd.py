"""CLI sub-command: snapshot — capture or compare .env snapshots."""
from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from typing import Dict

from envguard.snapshotter import (
    compare_snapshots,
    create_snapshot,
    load_snapshot,
    save_snapshot,
)


def add_snapshot_subparser(subparsers) -> None:  # type: ignore[type-arg]
    parser: ArgumentParser = subparsers.add_parser(
        "snapshot", help="Capture or compare .env snapshots"
    )
    parser.add_argument("--env", required=True, help="Path to .env file")
    parser.add_argument("--save", metavar="FILE", help="Save snapshot to FILE")
    parser.add_argument(
        "--compare", metavar="FILE", help="Compare current env against saved snapshot"
    )


def _parse_env_file(path: str) -> Dict[str, str]:
    env: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return env


def run_snapshot(args: Namespace) -> int:
    import os

    if not os.path.isfile(args.env):
        print(f"[error] env file not found: {args.env}", file=sys.stderr)
        return 1

    env = _parse_env_file(args.env)
    snapshot = create_snapshot(env)

    if args.save:
        save_snapshot(snapshot, args.save)
        print(f"Snapshot saved to {args.save} ({len(env)} keys).")
        return 0

    if args.compare:
        if not os.path.isfile(args.compare):
            print(f"[error] snapshot file not found: {args.compare}", file=sys.stderr)
            return 1
        old = load_snapshot(args.compare)
        diff = compare_snapshots(old, snapshot)
        if diff.has_differences():
            print("Snapshot diff:")
            print(diff)
            return 1
        print("No differences from snapshot.")
        return 0

    print(f"Snapshot created in memory ({len(env)} keys). Use --save or --compare.")
    return 0
