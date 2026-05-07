"""Tests for envguard.masker."""
import pytest
from envguard.masker import MaskResult, _is_sensitive, mask_env


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_token():
    assert _is_sensitive("ACCESS_TOKEN") is True


def test_is_sensitive_api_key():
    assert _is_sensitive("STRIPE_API_KEY") is True


def test_is_sensitive_non_sensitive():
    assert _is_sensitive("APP_NAME") is False


def test_is_sensitive_case_insensitive():
    assert _is_sensitive("db_secret") is True


# ---------------------------------------------------------------------------
# mask_env
# ---------------------------------------------------------------------------

ENV_TEXT = """APP_NAME=myapp
DB_PASSWORD=supersecret
DEBUG=true
API_KEY=abc123
"""


def test_non_sensitive_keys_unchanged():
    result = mask_env(ENV_TEXT)
    assert "APP_NAME=myapp" in result.lines
    assert "DEBUG=true" in result.lines


def test_sensitive_keys_are_masked():
    result = mask_env(ENV_TEXT)
    assert "DB_PASSWORD=***" in result.lines
    assert "API_KEY=***" in result.lines


def test_masked_keys_recorded():
    result = mask_env(ENV_TEXT)
    assert "DB_PASSWORD" in result.masked_keys
    assert "API_KEY" in result.masked_keys


def test_was_masked_true():
    result = mask_env(ENV_TEXT)
    assert result.was_masked is True


def test_was_masked_false_for_clean_env():
    result = mask_env("APP_NAME=myapp\nDEBUG=true\n")
    assert result.was_masked is False
    assert result.masked_keys == []


def test_reveal_keys_skips_masking():
    result = mask_env(ENV_TEXT, reveal_keys=["DB_PASSWORD"])
    assert "DB_PASSWORD=supersecret" in result.lines
    assert "DB_PASSWORD" not in result.masked_keys


def test_blank_lines_and_comments_preserved():
    text = "# comment\n\nAPP=val\n"
    result = mask_env(text)
    assert "# comment" in result.lines
    assert "" in result.lines


def test_str_joins_lines():
    result = mask_env("APP=val\n")
    assert str(result) == "APP=val"


def test_line_without_equals_preserved():
    text = "EXPORT APP_NAME\nKEY=value\n"
    result = mask_env(text)
    assert "EXPORT APP_NAME" in result.lines
