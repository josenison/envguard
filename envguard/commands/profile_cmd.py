"""CLI subcommand: profile — display statistics about a .env file."""
from __future__ import annotations

import argparse
import sys
from typing import Dict

from envguard.profiler import profile_env


def add_profile_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "profile",
        help="Display statistics and insights about a .env file.",
    )
    parser.add_argument("env_file", help="Path to the .env file to profile.")
    parser.add_argument(
        "--show-types",
        action="store_true",
        default=False,
        help="Include per-key type guesses in output.",
    )


def _parse_env_file(path: str) -> Dict[str, str]:
    """Parse a .env file into a dictionary of key/value pairs.

    Lines that are blank, start with ``#``, or do not contain ``=`` are
    silently skipped.  Returns an empty dict if the file cannot be opened.
    """
    pairs: Dict[str, str] = {}
    try:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                pairs[key.strip()] = value.strip()
    except FileNotFoundError:
        return {}
    return pairs


def run_profile(args: argparse.Namespace) -> int:
    """Execute the profile subcommand.  Returns an exit code."""
    import os

    if not os.path.isfile(args.env_file):
        print(f"[error] env file not found: {args.env_file}", file=sys.stderr)
        return 1

    pairs = _parse_env_file(args.env_file)
    result = profile_env(pairs)

    print(result.summary())

    if result.empty_values:
        print("\nEmpty values:")
        for k in result.empty_values:
            print(f"  - {k}")

    if result.sensitive_keys:
        print("\nSensitive keys detected:")
        for k in result.sensitive_keys:
            print(f"  - {k}")

    if result.duplicate_keys:
        print("\nDuplicate keys:")
        for k in result.duplicate_keys:
            print(f"  - {k}")

    if args.show_types:
        print("\nType guesses:")
        for k, t in sorted(result.type_guesses.items()):
            print(f"  {k}: {t}")

    return 0
