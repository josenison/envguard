"""Tests for envguard.trimmer."""
from __future__ import annotations

import pytest

from envguard.schema import FieldRule, Schema
from envguard.trimmer import TrimResult, _parse_key, trim_env


def make_schema(*names: str) -> Schema:
    return Schema(fields=[FieldRule(name=n) for n in names])


# ---------------------------------------------------------------------------
# _parse_key
# ---------------------------------------------------------------------------

def test_parse_key_normal_line():
    assert _parse_key("FOO=bar") == "FOO"


def test_parse_key_with_spaces():
    assert _parse_key("  FOO = bar  ") == "FOO"


def test_parse_key_blank_line():
    assert _parse_key("") is None


def test_parse_key_comment():
    assert _parse_key("# comment") is None


def test_parse_key_no_equals():
    assert _parse_key("JUSTKEY") is None


# ---------------------------------------------------------------------------
# trim_env
# ---------------------------------------------------------------------------

def test_trim_no_undeclared_keys():
    text = "FOO=1\nBAR=2\n"
    schema = make_schema("FOO", "BAR")
    result = trim_env(text, schema)
    assert not result.was_changed()
    assert result.removed_keys == []
    assert "FOO=1" in result.kept_lines
    assert "BAR=2" in result.kept_lines


def test_trim_removes_undeclared_key():
    text = "FOO=1\nUNKNOWN=99\nBAR=2\n"
    schema = make_schema("FOO", "BAR")
    result = trim_env(text, schema)
    assert result.was_changed()
    assert "UNKNOWN" in result.removed_keys
    assert "UNKNOWN=99" not in result.kept_lines


def test_trim_preserves_comments_and_blanks():
    text = "# header\n\nFOO=1\nBAD=x\n"
    schema = make_schema("FOO")
    result = trim_env(text, schema)
    assert "# header" in result.kept_lines
    assert "" in result.kept_lines
    assert "BAD=x" not in result.kept_lines


def test_trim_result_str_joins_kept_lines():
    text = "FOO=1\nBAR=2\n"
    schema = make_schema("FOO")
    result = trim_env(text, schema)
    assert str(result) == "FOO=1"


def test_trim_empty_env():
    result = trim_env("", make_schema("FOO"))
    assert not result.was_changed()
    assert result.kept_lines == [""]


def test_trim_all_keys_removed():
    text = "A=1\nB=2\n"
    schema = make_schema("C")
    result = trim_env(text, schema)
    assert result.removed_keys == ["A", "B"]
    assert result.was_changed()
