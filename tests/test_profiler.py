"""Tests for envguard.profiler."""
import pytest
from envguard.profiler import profile_env, _guess_type, _is_sensitive, ProfileResult


# ---------------------------------------------------------------------------
# _guess_type
# ---------------------------------------------------------------------------

def test_guess_type_empty():
    assert _guess_type("") == "empty"


def test_guess_type_boolean():
    assert _guess_type("true") == "boolean"
    assert _guess_type("False") == "boolean"


def test_guess_type_integer():
    assert _guess_type("42") == "integer"


def test_guess_type_float():
    assert _guess_type("3.14") == "float"


def test_guess_type_string():
    assert _guess_type("hello") == "string"


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_token():
    assert _is_sensitive("GITHUB_TOKEN") is True


def test_is_sensitive_non_sensitive():
    assert _is_sensitive("APP_NAME") is False


# ---------------------------------------------------------------------------
# profile_env
# ---------------------------------------------------------------------------

def _sample() -> dict:
    return {
        "APP_NAME": "myapp",
        "APP_PORT": "8080",
        "DEBUG": "true",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "",
        "RATIO": "0.75",
    }


def test_profile_total_keys():
    result = profile_env(_sample())
    assert result.total_keys == 6


def test_profile_empty_values():
    result = profile_env(_sample())
    assert "API_KEY" in result.empty_values


def test_profile_sensitive_keys():
    result = profile_env(_sample())
    assert "DB_PASSWORD" in result.sensitive_keys
    assert "API_KEY" in result.sensitive_keys


def test_profile_no_duplicates():
    result = profile_env(_sample())
    assert result.duplicate_keys == []


def test_profile_type_guesses():
    result = profile_env(_sample())
    assert result.type_guesses["APP_PORT"] == "integer"
    assert result.type_guesses["DEBUG"] == "boolean"
    assert result.type_guesses["RATIO"] == "float"
    assert result.type_guesses["APP_NAME"] == "string"
    assert result.type_guesses["API_KEY"] == "empty"


def test_profile_longest_key():
    result = profile_env(_sample())
    assert result.longest_key == "DB_PASSWORD"


def test_profile_summary_contains_totals():
    result = profile_env(_sample())
    summary = result.summary()
    assert "6" in summary
    assert "Total keys" in summary
