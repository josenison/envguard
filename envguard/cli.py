"""Command-line interface for envguard: validate and lint .env files."""

import argparse
import sys
from typing import Optional, List

from envguard.linter import lint_env_file
from envguard.schema import load_schema
from envguard.validator import validate_env


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="envguard",
        description="Validate and lint .env files against a schema.",
    )
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "--schema",
        default="envguard.schema.yml",
        help="Path to the schema YAML file (default: envguard.schema.yml)",
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run linter checks in addition to schema validation",
    )
    parser.add_argument(
        "--lint-only",
        action="store_true",
        help="Run only linter checks, skip schema validation",
    )
    parser.add_argument(
        "--no-warnings",
        action="store_true",
        help="Suppress warning-level messages",
    )
    return parser.parse_args(argv)


def load_dotenv_file(path: str) -> dict:
    """Parse a .env file into a dict of key-value pairs."""
    env: dict = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    exit_code = 0

    if args.lint or args.lint_only:
        print(f"Linting {args.env_file} ...")
        lint_result = lint_env_file(args.env_file)
        for issue in lint_result.issues:
            if args.no_warnings and issue.severity == "warning":
                continue
            print(f"  {issue}")
        if lint_result.has_errors:
            exit_code = 1
        elif not lint_result.issues:
            print("  Lint passed with no issues.")

    if not args.lint_only:
        print(f"Validating {args.env_file} against {args.schema} ...")
        try:
            schema = load_schema(args.schema)
            env = load_dotenv_file(args.env_file)
            result = validate_env(env, schema)
            if not result.is_valid:
                for err in result.errors:
                    print(f"  [ERROR] {err}")
                exit_code = 1
            if result.warnings and not args.no_warnings:
                for warn in result.warnings:
                    print(f"  [WARNING] {warn}")
            if result.is_valid:
                print("  Validation passed.")
        except FileNotFoundError as exc:
            print(f"  [ERROR] {exc}")
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
