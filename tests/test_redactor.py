"""Tests for envguard.redactor module."""

import pytest
from envguard.redactor import (
    REDACT_PLACEHOLDER,
    RedactResult,
    _is_sensitive,
    _partial_mask,
    redact_env,
)


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_password():
    assert _is_sensitive("DB_PASSWORD", ["PASSWORD"]) is True


def test_is_sensitive_case_insensitive():
    assert _is_sensitive("db_secret", ["SECRET"]) is True


def test_is_sensitive_non_sensitive():
    assert _is_sensitive("APP_ENV", ["PASSWORD", "SECRET"]) is False


# ---------------------------------------------------------------------------
# _partial_mask
# ---------------------------------------------------------------------------

def test_partial_mask_long_value():
    result = _partial_mask("supersecret")
    assert result.startswith("su")
    assert result.endswith("et")
    assert "*" in result


def test_partial_mask_short_value_fully_redacted():
    result = _partial_mask("abc")
    assert result == REDACT_PLACEHOLDER


def test_partial_mask_exactly_four_chars_fully_redacted():
    result = _partial_mask("abcd")
    assert result == REDACT_PLACEHOLDER


# ---------------------------------------------------------------------------
# redact_env
# ---------------------------------------------------------------------------

def test_clean_env_no_redaction():
    env = {"APP_ENV": "production", "PORT": "8080"}
    result = redact_env(env)
    assert result.redacted_keys == []
    assert result.values["APP_ENV"] == "production"
    assert result.values["PORT"] == "8080"
    assert result.original_count == 2


def test_sensitive_key_is_redacted():
    env = {"DB_PASSWORD": "s3cr3t", "APP_ENV": "staging"}
    result = redact_env(env)
    assert "DB_PASSWORD" in result.redacted_keys
    assert result.values["DB_PASSWORD"] == REDACT_PLACEHOLDER
    assert result.values["APP_ENV"] == "staging"


def test_partial_redaction_shows_partial_value():
    env = {"API_KEY": "abcdefghij"}
    result = redact_env(env, partial=True)
    assert result.values["API_KEY"] != REDACT_PLACEHOLDER
    assert result.values["API_KEY"].startswith("ab")
    assert result.values["API_KEY"].endswith("ij")


def test_custom_sensitive_patterns():
    env = {"MY_CERT": "cert_data", "APP_ENV": "test"}
    result = redact_env(env, sensitive_patterns=["CERT"])
    assert "MY_CERT" in result.redacted_keys
    assert result.values["APP_ENV"] == "test"


def test_redact_result_str_format():
    env = {"APP_ENV": "prod", "DB_PASSWORD": "hunter2"}
    result = redact_env(env)
    output = str(result)
    assert "APP_ENV=prod" in output
    assert f"DB_PASSWORD={REDACT_PLACEHOLDER}" in output


def test_multiple_sensitive_keys_all_redacted():
    env = {"DB_PASSWORD": "pass", "API_TOKEN": "tok", "HOST": "localhost"}
    result = redact_env(env)
    assert set(result.redacted_keys) == {"DB_PASSWORD", "API_TOKEN"}
    assert result.values["HOST"] == "localhost"
