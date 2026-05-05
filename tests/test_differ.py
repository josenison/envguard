"""Tests for envguard.differ."""
from __future__ import annotations

import pytest

from envguard.differ import (
    DiffResult,
    diff_env_against_schema,
    diff_two_envs,
    parse_env_keys,
)
from envguard.schema import FieldRule, Schema


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_schema(*names: str) -> Schema:
    fields = [FieldRule(name=n, required=True, type="string") for n in names]
    return Schema(fields=fields)


# ---------------------------------------------------------------------------
# parse_env_keys
# ---------------------------------------------------------------------------

def test_parse_env_keys_basic():
    text = "DB_HOST=localhost\nDB_PORT=5432\n"
    assert parse_env_keys(text) == {"DB_HOST", "DB_PORT"}


def test_parse_env_keys_ignores_comments_and_blanks():
    text = "# comment\n\nAPI_KEY=secret\n"
    assert parse_env_keys(text) == {"API_KEY"}


def test_parse_env_keys_handles_spaces_around_equals():
    text = "KEY = value\n"
    assert parse_env_keys(text) == {"KEY"}


def test_parse_env_keys_empty_text():
    assert parse_env_keys("") == set()


# ---------------------------------------------------------------------------
# diff_env_against_schema
# ---------------------------------------------------------------------------

def test_diff_no_differences():
    schema = make_schema("A", "B")
    result = diff_env_against_schema({"A", "B"}, schema)
    assert not result.has_differences()
    assert result.common == ["A", "B"]


def test_diff_missing_in_env():
    schema = make_schema("A", "B", "C")
    result = diff_env_against_schema({"A"}, schema)
    assert "B" in result.missing_in_env
    assert "C" in result.missing_in_env
    assert result.has_differences()


def test_diff_extra_in_env():
    schema = make_schema("A")
    result = diff_env_against_schema({"A", "EXTRA"}, schema)
    assert result.extra_in_env == ["EXTRA"]
    assert result.has_differences()


# ---------------------------------------------------------------------------
# diff_two_envs
# ---------------------------------------------------------------------------

def test_diff_two_envs_identical():
    result = diff_two_envs({"X", "Y"}, {"X", "Y"})
    assert not result.has_differences()


def test_diff_two_envs_asymmetric():
    result = diff_two_envs({"X", "Y"}, {"Y", "Z"})
    # X is extra in env_a (not in env_b)
    assert "X" in result.extra_in_env
    # Z is missing from env_a (present in env_b)
    assert "Z" in result.missing_in_env


# ---------------------------------------------------------------------------
# DiffResult.__str__ smoke test
# ---------------------------------------------------------------------------

def test_diff_result_str_no_diff():
    r = DiffResult()
    assert str(r) == "(no differences)"
