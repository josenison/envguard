"""CLI subcommand: audit — check .env files for security issues."""
import argparse
import sys
from pathlib import Path

from envguard.auditor import audit_env


def add_audit_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "audit",
        help="Audit a .env file for sensitive key exposure and weak values.",
    )
    parser.add_argument("env_file", help="Path to the .env file to audit.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code if any warnings are found.",
    )


def _parse_env_file(path: Path) -> dict:
    env = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        env[key.strip()] = value.strip()
    return env


def run_audit(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"[ERROR] Env file not found: {env_path}", file=sys.stderr)
        return 1

    env = _parse_env_file(env_path)
    result = audit_env(env)

    if not result.issues:
        print("Audit passed: no security issues found.")
        return 0

    for issue in result.issues:
        print(str(issue))

    if result.has_errors():
        return 1
    if args.strict and result.has_warnings():
        return 1
    return 0
