"""Tests for envguard.pinner."""
import json
import pytest

from envguard.pinner import (
    PinEntry,
    PinResult,
    _hash_value,
    _is_sensitive,
    _preview,
    compare_pin,
    lockfile_to_dict,
    pin_env,
)


SAMPLE_ENV = """
# comment
DB_HOST=localhost
DB_PASSWORD=supersecret
APP_PORT=8080
API_KEY=abc123
"""


def test_is_sensitive_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_api_key():
    assert _is_sensitive("API_KEY") is True


def test_is_sensitive_plain_key():
    assert _is_sensitive("APP_PORT") is False


def test_is_sensitive_case_insensitive():
    assert _is_sensitive("db_secret") is True


def test_preview_sensitive_is_masked():
    assert _preview("DB_PASSWORD", "supersecret") == "****"


def test_preview_non_sensitive_short():
    assert _preview("APP_PORT", "808") == "808"


def test_preview_non_sensitive_long():
    result = _preview("APP_PORT", "80808")
    assert result == "8080\u2026"


def test_pin_env_returns_sorted_entries():
    entries = pin_env(SAMPLE_ENV)
    keys = [e.key for e in entries]
    assert keys == sorted(keys)


def test_pin_env_ignores_comments_and_blanks():
    entries = pin_env(SAMPLE_ENV)
    assert all(not e.key.startswith("#") for e in entries)


def test_pin_env_hashes_values():
    entries = pin_env("FOO=bar")
    assert len(entries) == 1
    assert entries[0].value_hash == _hash_value("bar")


def test_lockfile_to_dict_structure():
    entries = pin_env("FOO=bar\nBAZ=qux")
    data = lockfile_to_dict(entries)
    assert "entries" in data
    assert all("key" in e and "value_hash" in e and "value_preview" in e for e in data["entries"])


def test_compare_pin_no_drift():
    entries = pin_env(SAMPLE_ENV)
    lockfile = lockfile_to_dict(entries)
    result = compare_pin(SAMPLE_ENV, lockfile)
    assert not result.has_drift()
    assert result.drifted == []
    assert result.new_keys == []
    assert result.removed_keys == []


def test_compare_pin_detects_changed_value():
    entries = pin_env(SAMPLE_ENV)
    lockfile = lockfile_to_dict(entries)
    modified_env = SAMPLE_ENV.replace("APP_PORT=8080", "APP_PORT=9090")
    result = compare_pin(modified_env, lockfile)
    assert result.has_drift()
    assert "APP_PORT" in result.drifted


def test_compare_pin_detects_new_key():
    entries = pin_env(SAMPLE_ENV)
    lockfile = lockfile_to_dict(entries)
    result = compare_pin(SAMPLE_ENV + "\nNEW_VAR=hello", lockfile)
    assert "NEW_VAR" in result.new_keys


def test_compare_pin_detects_removed_key():
    entries = pin_env(SAMPLE_ENV)
    lockfile = lockfile_to_dict(entries)
    reduced_env = "DB_HOST=localhost\nAPP_PORT=8080"
    result = compare_pin(reduced_env, lockfile)
    assert "DB_PASSWORD" in result.removed_keys
    assert "API_KEY" in result.removed_keys


def test_pin_result_str_no_drift():
    result = PinResult()
    assert "No drift" in str(result)


def test_pin_result_str_with_drift():
    result = PinResult(drifted=["FOO"], new_keys=["BAR"], removed_keys=["BAZ"])
    text = str(result)
    assert "FOO" in text
    assert "BAR" in text
    assert "BAZ" in text
