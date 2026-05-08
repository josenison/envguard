"""Tests for envguard.formatter."""
import pytest
from envguard.formatter import format_env, FormatResult


def test_clean_env_no_changes():
    text = "KEY=value\nDEBUG=true"
    result = format_env(text)
    assert result.lines == ["KEY=value", "DEBUG=true"]
    assert result.changes == []
    assert not result.was_changed


def test_blank_lines_and_comments_preserved():
    text = "# comment\n\nKEY=value"
    result = format_env(text)
    assert result.lines[0] == "# comment"
    assert result.lines[1] == ""
    assert result.lines[2] == "KEY=value"
    assert not result.was_changed


def test_whitespace_stripped_from_key():
    text = "  KEY =value"
    result = format_env(text)
    assert result.lines[0] == "KEY=value"
    assert result.was_changed
    assert any("KEY" in c for c in result.changes)


def test_whitespace_stripped_from_unquoted_value():
    text = "KEY=  hello world  "
    result = format_env(text)
    assert result.lines[0] == "KEY=hello world"
    assert result.was_changed


def test_quoted_value_whitespace_preserved():
    text = 'KEY="  spaced  "'
    result = format_env(text)
    assert result.lines[0] == 'KEY="  spaced  "'


def test_inline_comment_removed_from_unquoted_value():
    text = "KEY=value # this is a comment"
    result = format_env(text)
    assert result.lines[0] == "KEY=value"
    assert result.was_changed
    assert any("inline comment" in c for c in result.changes)


def test_inline_comment_preserved_in_quoted_value():
    text = 'KEY="value # not a comment"'
    result = format_env(text)
    assert result.lines[0] == 'KEY="value # not a comment"'
    assert not result.was_changed


def test_format_result_str_joins_lines():
    text = "A=1\nB=2"
    result = format_env(text)
    assert str(result) == "A=1\nB=2"


def test_line_without_equals_passed_through():
    text = "BADLINE"
    result = format_env(text)
    assert result.lines[0] == "BADLINE"
    assert not result.was_changed


def test_multiple_changes_recorded():
    text = "  KEY =  value # comment "
    result = format_env(text)
    assert result.was_changed
    assert len(result.changes) >= 2


def test_empty_value_preserved():
    """An assignment with no value should remain valid and unchanged."""
    text = "KEY="
    result = format_env(text)
    assert result.lines[0] == "KEY="
    assert not result.was_changed


def test_empty_string_input():
    """Formatting an empty string should return an empty result without error."""
    result = format_env("")
    assert result.lines == [""]
    assert not result.was_changed
    assert str(result) == ""
