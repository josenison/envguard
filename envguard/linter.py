"""Linter for .env files: checks style, naming conventions, and common issues."""

from dataclasses import dataclass, field
from typing import List, Tuple
import re


@dataclass
class LintIssue:
    line_number: int
    message: str
    severity: str  # 'error' | 'warning' | 'info'

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] Line {self.line_number}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def add(self, issue: LintIssue) -> None:
        self.issues.append(issue)

    def __str__(self) -> str:
        if not self.issues:
            return "No lint issues found."
        return "\n".join(str(i) for i in self.issues)


KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]*$')


def lint_env_lines(lines: List[str]) -> LintResult:
    """Lint a list of raw .env file lines and return a LintResult."""
    result = LintResult()

    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        # Skip blank lines and comments
        if not line.strip() or line.strip().startswith("#"):
            continue

        if "=" not in line:
            result.add(LintIssue(lineno, f"Line is not a valid KEY=VALUE pair: {line!r}", "error"))
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        if not KEY_PATTERN.match(key):
            result.add(LintIssue(lineno, f"Key {key!r} should be UPPER_SNAKE_CASE", "warning"))

        if value.startswith(("'", '"')) and not (
            (value.startswith("'") and value.endswith("'")) or
            (value.startswith('"') and value.endswith('"'))
        ):
            result.add(LintIssue(lineno, f"Key {key!r} has mismatched quotes in value", "error"))

        if value == "":
            result.add(LintIssue(lineno, f"Key {key!r} has an empty value", "info"))

        if " " in key:
            result.add(LintIssue(lineno, f"Key {key!r} contains spaces", "error"))

    return result


def lint_env_file(path: str) -> LintResult:
    """Read a .env file from disk and lint it."""
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    return lint_env_lines(lines)
