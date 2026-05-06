"""CLI subcommand: merge multiple .env files."""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List

from envguard.merger import merge_envs


def add_merge_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "merge",
        help="Merge multiple .env files into one, detecting conflicts.",
    )
    parser.add_argument(
        "env_files",
        nargs="+",
        metavar="ENV_FILE",
        help="Two or more .env files to merge (in priority order, last wins).",
    )
    parser.add_argument(
        "--override",
        action="store_true",
        default=False,
        help="Later files silently override earlier ones (no conflict errors).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write merged result to FILE instead of stdout.",
    )
    parser.add_argument(
        "--format",
        choices=["env", "json"],
        default="env",
        dest="fmt",
        help="Output format: env (default) or json.",
    )
    parser.set_defaults(func=run_merge)


def run_merge(args: argparse.Namespace) -> int:
    sources = []
    for path in args.env_files:
        if not os.path.exists(path):
            print(f"[error] File not found: {path}", file=sys.stderr)
            return 1
        with open(path, "r", encoding="utf-8") as fh:
            sources.append((path, fh.read()))

    result = merge_envs(sources, override=args.override)

    if result.has_conflicts():
        print("[warn] Merge conflicts detected:", file=sys.stderr)
        for conflict in result.conflicts:
            print(f"  {conflict}", file=sys.stderr)

    if args.fmt == "json":
        output = json.dumps(result.merged, indent=2)
    else:
        lines = [f"{k}={v}" for k, v in sorted(result.merged.items())]
        output = "\n".join(lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output + "\n")
        print(f"Merged output written to {args.output}")
    else:
        print(output)

    return 1 if (result.has_conflicts() and not args.override) else 0
