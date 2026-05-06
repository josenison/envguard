"""Unit tests for envguard.exporter."""
import json

import pytest

from envguard.exporter import ExportFormat, ExportResult, export_env, _quote_shell


SAMPLE_ENV = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "SECRET_KEY": "s3cr3t",
    "DEBUG": "false",
}


# ---------------------------------------------------------------------------
# _quote_shell helper
# ---------------------------------------------------------------------------

def test_quote_shell_simple():
    assert _quote_shell("hello") == "'hello'"


def test_quote_shell_with_single_quote():
    result = _quote_shell("it's")
    assert "'" not in result.strip("'")  # inner single quote must be escaped
    assert result == "'it'\\''s'"


# ---------------------------------------------------------------------------
# export_env – SHELL format
# ---------------------------------------------------------------------------

def test_shell_format_contains_export_keyword():
    result = export_env(SAMPLE_ENV, fmt=ExportFormat.SHELL)
    for key in SAMPLE_ENV:
        assert f"export {key}=" in result.content


def test_shell_format_no_export_keyword():
    result = export_env(SAMPLE_ENV, fmt=ExportFormat.SHELL, export_keyword=False)
    assert "export " not in result.content
    assert "DATABASE_URL=" in result.content


def test_shell_format_keys_sorted():
    result = export_env(SAMPLE_ENV, fmt=ExportFormat.SHELL)
    assert result.keys_exported == sorted(SAMPLE_ENV.keys())


# ---------------------------------------------------------------------------
# export_env – DOCKER format
# ---------------------------------------------------------------------------

def test_docker_format_no_quotes():
    result = export_env(SAMPLE_ENV, fmt=ExportFormat.DOCKER)
    assert "export" not in result.content
    for key, val in SAMPLE_ENV.items():
        assert f"{key}={val}" in result.content


# ---------------------------------------------------------------------------
# export_env – JSON format
# ---------------------------------------------------------------------------

def test_json_format_valid_json():
    result = export_env(SAMPLE_ENV, fmt=ExportFormat.JSON)
    parsed = json.loads(result.content)
    assert parsed == SAMPLE_ENV


def test_json_format_keys_sorted_in_output():
    result = export_env(SAMPLE_ENV, fmt=ExportFormat.JSON)
    parsed = json.loads(result.content)
    assert list(parsed.keys()) == sorted(SAMPLE_ENV.keys())


# ---------------------------------------------------------------------------
# ExportResult metadata
# ---------------------------------------------------------------------------

def test_export_result_format_stored():
    result = export_env(SAMPLE_ENV, fmt=ExportFormat.JSON)
    assert result.format == ExportFormat.JSON


def test_export_empty_env():
    result = export_env({}, fmt=ExportFormat.SHELL)
    assert result.content == ""
    assert result.keys_exported == []
