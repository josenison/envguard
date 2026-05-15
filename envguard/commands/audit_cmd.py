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
    """Parse a .env file into a dictionary of key-value pairs.

    Skips blank lines and lines beginning with '#' (comments).
    Lines without an '=' separator are also skipped.

    Args:
        path: Path to the .env file.

    Returns:
        A dict mapping environment variable names to their string values.

    Raises:
        OSError: If the file cannot be read.
    """
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


def _print_summary(result) -> None:
    """Print a summary line showing the count of errors and warnings.

    Args:
        result: An audit result object with an ``issues`` attribute and
                ``has_errors``/``has_warnings`` helper methods.
    """
    error_count = sum(1 for i in result.issues if i.severity == "error")
    warning_count = sum(1 for i in result.issues if i.severity == "warning")
    parts = []
    if error_count:
        parts.append(f"{error_count} error(s)")
    if warning_count:
        parts.append(f"{warning_count} warning(s)")
    print(f"Audit complete: {', '.join(parts)} found.")


def run_audit(args: argparse.Namespace) -> int:
    """Execute the audit subcommand.

    Parses the specified .env file, runs the auditor, and prints any issues
    found.  Returns an exit code suitable for passing to ``sys.exit``.

    Args:
        args: Parsed CLI arguments.  Expected attributes:
            - ``env_file`` (str): path to the .env file.
            - ``strict`` (bool): if True, treat warnings as errors.

    Returns:
        0 if no issues (or only warnings when not in strict mode),
        1 if errors are present or strict mode is enabled and warnings exist.
    """
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

    _print_summary(result)

    if result.has_errors():
        return 1
    if args.strict and result.has_warnings():
        return 1
    return 0
