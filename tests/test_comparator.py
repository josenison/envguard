"""Tests for envguard.comparator."""
import pytest
from envguard.comparator import compare_envs, CompareResult, ValueDiff, _parse_env_pairs


ENV_A = """
# base config
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=abc123
DEBUG=true
"""

ENV_B = """
DB_HOST=prod.example.com
DB_PORT=5432
SECRET_KEY=xyz789
NEW_KEY=hello
"""


def test_parse_env_pairs_basic():
    pairs = _parse_env_pairs("FOO=bar\nBAZ=qux\n")
    assert pairs == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_pairs_ignores_comments_and_blanks():
    pairs = _parse_env_pairs("# comment\n\nFOO=1\n")
    assert pairs == {"FOO": "1"}


def test_parse_env_pairs_ignores_no_equals():
    pairs = _parse_env_pairs("NOEQUALS\nFOO=bar\n")
    assert pairs == {"FOO": "bar"}


def test_parse_env_pairs_strips_whitespace():
    pairs = _parse_env_pairs("  FOO = bar  \n")
    assert pairs == {"FOO": "bar  "}


def test_no_differences_identical_envs():
    result = compare_envs(ENV_A, ENV_A)
    assert not result.has_differences()
    assert result.diffs == []


def test_changed_values_detected():
    result = compare_envs(ENV_A, ENV_B)
    changed_keys = {d.key for d in result.changed()}
    assert "DB_HOST" in changed_keys
    assert "SECRET_KEY" in changed_keys


def test_added_key_detected():
    result = compare_envs(ENV_A, ENV_B)
    added_keys = {d.key for d in result.added()}
    assert "NEW_KEY" in added_keys


def test_removed_key_detected():
    result = compare_envs(ENV_A, ENV_B)
    removed_keys = {d.key for d in result.removed()}
    assert "DEBUG" in removed_keys


def test_unchanged_key_not_in_diffs():
    result = compare_envs(ENV_A, ENV_B)
    diff_keys = {d.key for d in result.diffs}
    assert "DB_PORT" not in diff_keys


def test_ignore_keys_excluded():
    result = compare_envs(ENV_A, ENV_B, ignore_keys=["SECRET_KEY", "NEW_KEY"])
    diff_keys = {d.key for d in result.diffs}
    assert "SECRET_KEY" not in diff_keys
    assert "NEW_KEY" not in diff_keys


def test_str_no_differences():
    result = compare_envs(ENV_A, ENV_A)
    assert "No differences" in str(result)


def test_str_with_differences():
    result = compare_envs(ENV_A, ENV_B)
    output = str(result)
    assert "DB_HOST" in output


def test_value_diff_str_missing_a():
    d = ValueDiff(key="FOO", value_a=None, value_b="bar")
    assert "<missing>" in str(d)
    assert "bar" in str(d)
