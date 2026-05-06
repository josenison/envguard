"""Tests for envguard.linter module."""

import pytest
from envguard.linter import lint_env_lines, LintIssue, LintResult


def lines(*args):
    """Helper to build a list of newline-terminated strings."""
    return [f"{l}\n" for l in args]


def test_clean_env_no_issues():
    result = lint_env_lines(lines("DATABASE_URL=postgres://localhost/db", "SECRET_KEY=abc123"))
    assert not result.issues
    assert not result.has_errors
    assert not result.has_warnings


def test_blank_lines_and_comments_ignored():
    result = lint_env_lines(lines("", "# This is a comment", "APP_ENV=production"))
    assert not result.issues


def test_missing_equals_is_error():
    result = lint_env_lines(lines("BADLINE"))
    assert result.has_errors
    assert any("not a valid KEY=VALUE" in i.message for i in result.issues)


def test_lowercase_key_is_warning():
    result = lint_env_lines(lines("database_url=postgres://localhost"))
    assert result.has_warnings
    assert any("UPPER_SNAKE_CASE" in i.message for i in result.issues)


def test_mixed_case_key_is_warning():
    result = lint_env_lines(lines("DatabaseUrl=postgres://localhost"))
    assert result.has_warnings


def test_empty_value_is_info():
    result = lint_env_lines(lines("OPTIONAL_KEY="))
    info_issues = [i for i in result.issues if i.severity == "info"]
    assert len(info_issues) == 1
    assert "empty value" in info_issues[0].message


def test_mismatched_single_quotes_is_error():
    result = lint_env_lines(lines("SECRET='unclosed"))
    assert result.has_errors
    assert any("mismatched quotes" in i.message for i in result.issues)


def test_mismatched_double_quotes_is_error():
    result = lint_env_lines(lines('SECRET="unclosed'))
    assert result.has_errors


def test_matched_quotes_no_issue():
    result = lint_env_lines(lines('SECRET="my secret value"', "TOKEN='abc'"))
    assert not result.has_errors


def test_key_with_spaces_is_error():
    result = lint_env_lines(lines("MY KEY=value"))
    assert result.has_errors
    assert any("contains spaces" in i.message for i in result.issues)


def test_lint_result_str_no_issues():
    result = LintResult()
    assert str(result) == "No lint issues found."


def test_lint_result_str_with_issues():
    result = LintResult()
    result.add(LintIssue(1, "something wrong", "error"))
    assert "[ERROR]" in str(result)
    assert "Line 1" in str(result)


def test_line_numbers_are_accurate():
    result = lint_env_lines(lines("GOOD=value", "BADLINE", "ALSO_GOOD=1"))
    error = next(i for i in result.issues if i.severity == "error")
    assert error.line_number == 2


def test_multiple_issues_same_line():
    """A line can produce more than one issue (e.g. lowercase key AND empty value)."""
    result = lint_env_lines(lines("lowercase_key="))
    line_issues = [i for i in result.issues if i.line_number == 1]
    severities = {i.severity for i in line_issues}
    # Expect at least a warning for the key casing and an info for the empty value
    assert "warning" in severities
    assert "info" in severities
