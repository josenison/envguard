"""CLI sub-command: typecheck — validate .env value types against schema."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

from envguard.schema import load_schema
from envguard.typecheck import typecheck_env


def add_typecheck_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "typecheck",
        help="Check that .env values match the types declared in the schema.",
    )
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument("schema_file", help="Path to the schema YAML/JSON file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def _parse_env_file(path: str) -> Dict[str, str]:
    env: Dict[str, str] = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return env
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        env[key.strip()] = value.strip()
    return env


def run_typecheck(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    schema_path = Path(args.schema_file)

    if not env_path.exists():
        print(f"Error: env file not found: {env_path}", file=sys.stderr)
        return 2
    if not schema_path.exists():
        print(f"Error: schema file not found: {schema_path}", file=sys.stderr)
        return 2

    env = _parse_env_file(str(env_path))
    schema = load_schema(str(schema_path))
    result = typecheck_env(env, schema)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        payload = [
            {"key": i.key, "expected": i.expected, "value": i.actual_value, "message": i.message}
            for i in result.issues
        ]
        print(json.dumps({"passed": not result.has_issues(), "issues": payload}, indent=2))
    else:
        print(str(result))

    return 1 if result.has_issues() else 0
