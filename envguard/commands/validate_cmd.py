"""CLI subcommand: validate a .env file against a schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.schema import load_schema
from envguard.validator import validate_env
from envguard.linter import lint_env
from envguard.reporter import Report, OutputFormat


def add_validate_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'validate' subcommand."""
    parser = subparsers.add_parser(
        "validate",
        help="Validate a .env file against a schema and optionally lint it.",
    )
    parser.add_argument("env_file", help="Path to the .env file to validate.")
    parser.add_argument("schema_file", help="Path to the schema YAML file.")
    parser.add_argument(
        "--no-lint",
        action="store_true",
        default=False,
        help="Skip linting checks.",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        help="Output format (default: text).",
    )
    parser.set_defaults(func=run_validate)


def run_validate(args: argparse.Namespace) -> int:
    """Execute the validate subcommand. Returns exit code."""
    env_path = Path(args.env_file)
    schema_path = Path(args.schema_file)

    if not env_path.exists():
        print(f"Error: env file not found: {env_path}", file=sys.stderr)
        return 1

    if not schema_path.exists():
        print(f"Error: schema file not found: {schema_path}", file=sys.stderr)
        return 1

    env_text = env_path.read_text(encoding="utf-8")
    schema = load_schema(schema_path)

    # Parse key=value pairs into a dict for validation
    env_vars: dict[str, str] = {}
    for line in env_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            env_vars[key.strip()] = value.strip()

    validation_result = validate_env(env_vars, schema)
    lint_result = lint_env(env_text) if not args.no_lint else None

    fmt = OutputFormat(args.format)
    report = Report(validation=validation_result, lint=lint_result)
    print(report.render(fmt))

    return 0 if report.passed() else 1
