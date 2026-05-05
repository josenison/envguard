"""Tests for envguard.reporter module."""

import json
import io
import pytest

from envguard.reporter import Report, OutputFormat, render
from envguard.validator import ValidationResult
from envguard.linter import LintResult, LintIssue


def make_clean_validation() -> ValidationResult:
    vr = ValidationResult()
    return vr


def make_clean_lint() -> LintResult:
    return LintResult()


def make_lint_with_issues() -> LintResult:
    lr = LintResult()
    lr.add(LintIssue(severity="error", line=3, message="Missing '=' sign"))
    lr.add(LintIssue(severity="warning", line=7, message="Lowercase key 'port'"))
    return lr


def make_validation_with_issues() -> ValidationResult:
    vr = ValidationResult()
    vr.add("error", "Missing required field: DATABASE_URL")
    vr.add("warning", "Optional field SECRET_KEY not set")
    return vr


def test_report_passed_when_no_issues():
    report = Report(validation=make_clean_validation(), lint=make_clean_lint())
    assert report.passed is True


def test_report_failed_when_lint_errors():
    report = Report(lint=make_lint_with_issues())
    assert report.passed is False


def test_report_failed_when_validation_errors():
    report = Report(validation=make_validation_with_issues())
    assert report.passed is False


def test_render_text_clean(capsys):
    report = Report(validation=make_clean_validation(), lint=make_clean_lint())
    output = render(report, fmt=OutputFormat.TEXT)
    assert "Lint: OK" in output
    assert "Validation: OK" in output
    assert "PASSED" in output


def test_render_text_with_issues():
    report = Report(validation=make_validation_with_issues(), lint=make_lint_with_issues())
    output = render(report, fmt=OutputFormat.TEXT)
    assert "[ERROR]" in output
    assert "[WARNING]" in output
    assert "FAILED" in output


def test_render_json_structure():
    report = Report(validation=make_validation_with_issues(), lint=make_lint_with_issues())
    output = render(report, fmt=OutputFormat.JSON)
    data = json.loads(output)
    assert data["passed"] is False
    assert len(data["lint"]) == 2
    assert len(data["validation"]["errors"]) == 1
    assert len(data["validation"]["warnings"]) == 1


def test_render_writes_to_file():
    report = Report(validation=make_clean_validation())
    buf = io.StringIO()
    render(report, fmt=OutputFormat.TEXT, file=buf)
    assert "Validation: OK" in buf.getvalue()


def test_report_no_sections():
    report = Report()
    assert report.passed is True
    output = render(report, fmt=OutputFormat.TEXT)
    assert "PASSED" in output
