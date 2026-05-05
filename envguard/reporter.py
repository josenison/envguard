"""Reporter module for formatting and outputting validation and lint results."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import sys

from envguard.validator import ValidationResult
from envguard.linter import LintResult


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


@dataclass
class Report:
    validation: Optional[ValidationResult] = None
    lint: Optional[LintResult] = None

    @property
    def passed(self) -> bool:
        validation_ok = self.validation.is_valid if self.validation else True
        lint_ok = (not self.lint.has_errors()) if self.lint else True
        return validation_ok and lint_ok


def _format_text(report: Report) -> str:
    lines = []

    if report.lint:
        if report.lint.has_errors() or report.lint.has_warnings():
            lines.append("=== Lint Issues ===")
            for issue in report.lint.issues:
                lines.append(f"  [{issue.severity.upper()}] Line {issue.line}: {issue.message}")
        else:
            lines.append("=== Lint: OK ===")

    if report.validation:
        if not report.validation.is_valid or report.validation.warnings:
            lines.append("=== Validation Issues ===")
            for err in report.validation.errors:
                lines.append(f"  [ERROR] {err}")
            for warn in report.validation.warnings:
                lines.append(f"  [WARNING] {warn}")
        else:
            lines.append("=== Validation: OK ===")

    status = "PASSED" if report.passed else "FAILED"
    lines.append(f"\nResult: {status}")
    return "\n".join(lines)


def _format_json(report: Report) -> str:
    import json

    data = {"passed": report.passed}
    if report.lint:
        data["lint"] = [
            {"severity": i.severity, "line": i.line, "message": i.message}
            for i in report.lint.issues
        ]
    if report.validation:
        data["validation"] = {
            "errors": [str(e) for e in report.validation.errors],
            "warnings": list(report.validation.warnings),
        }
    return json.dumps(data, indent=2)


def render(report: Report, fmt: OutputFormat = OutputFormat.TEXT, file=None) -> str:
    """Render a report to a string and optionally write it to a file-like object."""
    if fmt == OutputFormat.JSON:
        output = _format_json(report)
    else:
        output = _format_text(report)

    if file is not None:
        print(output, file=file)

    return output
