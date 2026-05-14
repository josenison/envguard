"""Tests for envguard.normalizer."""
import pytest
from envguard.normalizer import normalize_env, _strip_quotes, _normalize_bool


# --- unit tests for helpers ---

def test_strip_quotes_double():
    assert _strip_quotes('"hello world"') == "hello world"


def test_strip_quotes_single():
    assert _strip_quotes("'hello world'") == "hello world"


def test_strip_quotes_unquoted():
    assert _strip_quotes("hello") == "hello"


def test_strip_quotes_unescape_newline():
    assert _strip_quotes('"line1\\nline2"') == "line1\nline2"


def test_normalize_bool_true_variants():
    for v in ("true", "True", "TRUE", "yes", "YES", "1", "on", "ON"):
        assert _normalize_bool(v) == "true", f"Expected 'true' for {v!r}"


def test_normalize_bool_false_variants():
    for v in ("false", "False", "FALSE", "no", "NO", "0", "off", "OFF"):
        assert _normalize_bool(v) == "false", f"Expected 'false' for {v!r}"


def test_normalize_bool_non_bool_unchanged():
    assert _normalize_bool("maybe") == "maybe"


# --- integration tests for normalize_env ---

def test_clean_env_no_changes():
    text = "KEY=value\nOTHER=123"
    result = normalize_env(text)
    assert not result.was_changed()
    assert result.lines == ["KEY=value", "OTHER=123"]


def test_blank_lines_and_comments_preserved():
    text = "# comment\n\nKEY=value"
    result = normalize_env(text)
    assert result.lines[0] == "# comment"
    assert result.lines[1] == ""
    assert result.lines[2] == "KEY=value"


def test_double_quoted_value_unquoted():
    result = normalize_env('KEY="hello world"')
    assert result.lines == ["KEY=hello world"]
    assert result.was_changed()
    assert result.changes[0] == ("KEY", '"hello world"', "hello world")


def test_single_quoted_value_unquoted():
    result = normalize_env("KEY='hello'")
    assert result.lines == ["KEY=hello"]
    assert result.was_changed()


def test_boolean_normalized_to_canonical():
    result = normalize_env("FEATURE_FLAG=YES\nDEBUG=False")
    assert "FEATURE_FLAG=true" in result.lines
    assert "DEBUG=false" in result.lines
    assert result.was_changed()


def test_unquote_disabled():
    result = normalize_env('KEY="value"', unquote_values=False)
    assert result.lines == ['KEY="value"']
    assert not result.was_changed()


def test_normalize_booleans_disabled():
    result = normalize_env("ENABLED=yes", normalize_booleans=False)
    assert result.lines == ["ENABLED=yes"]
    assert not result.was_changed()


def test_str_representation():
    result = normalize_env("A=1\nB=2")
    assert str(result) == "A=1\nB=2"


def test_multiple_changes_tracked():
    text = 'A="foo"\nB=TRUE\nC=plain'
    result = normalize_env(text)
    assert len(result.changes) == 2
    keys_changed = [c[0] for c in result.changes]
    assert "A" in keys_changed
    assert "B" in keys_changed
