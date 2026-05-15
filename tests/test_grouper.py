"""Tests for envguard.grouper."""
import pytest
from envguard.grouper import GroupResult, _parse_pairs, group_env


ENV_TEXT = """
# database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb

# AWS credentials
AWS_ACCESS_KEY=AKIA123
AWS_SECRET_KEY=secret

APP_ENV=production
DEBUG=true
"""


def test_parse_pairs_basic():
    pairs = _parse_pairs("FOO=bar\nBAZ=qux")
    assert pairs == [("FOO", "bar"), ("BAZ", "qux")]


def test_parse_pairs_ignores_comments_and_blanks():
    pairs = _parse_pairs("# comment\n\nFOO=bar")
    assert pairs == [("FOO", "bar")]


def test_parse_pairs_ignores_lines_without_equals():
    pairs = _parse_pairs("NOEQUALS\nFOO=bar")
    assert pairs == [("FOO", "bar")]


def test_auto_detect_prefixes():
    result = group_env(ENV_TEXT)
    assert "DB" in result.groups
    assert "AWS" in result.groups
    assert "APP" in result.groups
    assert len(result.groups["DB"]) == 3
    assert len(result.groups["AWS"]) == 2


def test_explicit_prefixes_limits_groups():
    result = group_env(ENV_TEXT, prefixes=["DB"])
    assert list(result.groups.keys()) == ["DB"]
    # AWS_* and APP_* fall into ungrouped
    ungrouped_keys = [k for k, _ in result.ungrouped]
    assert "AWS_ACCESS_KEY" in ungrouped_keys
    assert "DEBUG" in ungrouped_keys


def test_ungrouped_contains_no_prefix_keys():
    result = group_env(ENV_TEXT)
    ungrouped_keys = [k for k, _ in result.ungrouped]
    assert "DEBUG" in ungrouped_keys


def test_custom_separator():
    text = "DB.HOST=localhost\nDB.PORT=5432\nOTHER=value"
    result = group_env(text, separator=".")
    assert "DB" in result.groups
    assert len(result.groups["DB"]) == 2
    assert result.ungrouped == [("OTHER", "value")]


def test_str_output_has_section_headers():
    result = group_env("DB_HOST=localhost\nDEBUG=true")
    output = str(result)
    assert "[DB]" in output
    assert "[ungrouped]" in output
    assert "DB_HOST=localhost" in output


def test_all_pairs_returns_everything():
    result = group_env(ENV_TEXT)
    all_keys = [k for k, _ in result.all_pairs()]
    assert "DB_HOST" in all_keys
    assert "AWS_ACCESS_KEY" in all_keys
    assert "DEBUG" in all_keys


def test_empty_env_returns_empty_result():
    result = group_env("")
    assert result.groups == {}
    assert result.ungrouped == []


def test_no_prefixed_keys_all_ungrouped():
    result = group_env("FOO=1\nBAR=2")
    assert result.groups == {}
    assert len(result.ungrouped) == 2
