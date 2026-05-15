"""Tests for envguard.typecheck and envguard.commands.typecheck_cmd."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envguard.schema import FieldRule, Schema
from envguard.typecheck import TypeCheckResult, TypeIssue, _check_value, typecheck_env
from envguard.commands.typecheck_cmd import _parse_env_file, run_typecheck


def make_schema(*rules: FieldRule) -> Schema:
    return Schema(fields=list(rules))


# --- unit: _check_value ---

def test_check_value_int_valid():
    assert _check_value("PORT", "8080", "int") is None


def test_check_value_int_invalid():
    issue = _check_value("PORT", "abc", "int")
    assert issue is not None
    assert issue.expected == "int"


def test_check_value_float_valid():
    assert _check_value("RATIO", "3.14", "float") is None


def test_check_value_float_invalid():
    issue = _check_value("RATIO", "not-a-float", "float")
    assert issue is not None


def test_check_value_bool_valid_variants():
    for val in ("true", "false", "1", "0", "yes", "no", "True", "YES"):
        assert _check_value("FLAG", val, "bool") is None


def test_check_value_bool_invalid():
    issue = _check_value("FLAG", "maybe", "bool")
    assert issue is not None


def test_check_value_url_valid():
    assert _check_value("ENDPOINT", "https://example.com", "url") is None
    assert _check_value("ENDPOINT", "http://example.com", "url") is None


def test_check_value_url_invalid():
    issue = _check_value("ENDPOINT", "ftp://example.com", "url")
    assert issue is not None


def test_check_value_str_always_passes():
    assert _check_value("NAME", "anything", "str") is None


# --- unit: typecheck_env ---

def test_clean_env_no_issues():
    schema = make_schema(
        FieldRule(name="PORT", type="int", required=True),
        FieldRule(name="DEBUG", type="bool", required=False),
    )
    env = {"PORT": "5000", "DEBUG": "true"}
    result = typecheck_env(env, schema)
    assert not result.has_issues()
    assert "no issues" in str(result)


def test_type_mismatch_detected():
    schema = make_schema(FieldRule(name="PORT", type="int", required=True))
    result = typecheck_env({"PORT": "not-a-number"}, schema)
    assert result.has_issues()
    assert result.issues[0].key == "PORT"


def test_missing_key_skipped():
    """Missing keys are the validator's job; typecheck should ignore them."""
    schema = make_schema(FieldRule(name="PORT", type="int", required=True))
    result = typecheck_env({}, schema)
    assert not result.has_issues()


def test_no_type_field_skipped():
    schema = make_schema(FieldRule(name="NAME", required=True))
    result = typecheck_env({"NAME": "alice"}, schema)
    assert not result.has_issues()


# --- integration: run_typecheck ---

def _make_args(env_file, schema_file, fmt="text"):
    ns = argparse.Namespace()
    ns.env_file = env_file
    ns.schema_file = schema_file
    ns.format = fmt
    return ns


def test_run_typecheck_missing_env_file(tmp_path):
    schema = tmp_path / "schema.yaml"
    schema.write_text("fields:\n  - name: PORT\n    type: int\n    required: true\n")
    args = _make_args(str(tmp_path / "missing.env"), str(schema))
    assert run_typecheck(args) == 2


def test_run_typecheck_valid_env_passes(tmp_path):
    env = tmp_path / ".env"
    env.write_text("PORT=8080\nDEBUG=true\n")
    schema = tmp_path / "schema.yaml"
    schema.write_text(
        "fields:\n  - name: PORT\n    type: int\n    required: true\n"
        "  - name: DEBUG\n    type: bool\n    required: false\n"
    )
    args = _make_args(str(env), str(schema))
    assert run_typecheck(args) == 0


def test_run_typecheck_invalid_type_returns_one(tmp_path):
    env = tmp_path / ".env"
    env.write_text("PORT=not-a-port\n")
    schema = tmp_path / "schema.yaml"
    schema.write_text("fields:\n  - name: PORT\n    type: int\n    required: true\n")
    args = _make_args(str(env), str(schema))
    assert run_typecheck(args) == 1


def test_run_typecheck_json_output(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("PORT=bad\n")
    schema = tmp_path / "schema.yaml"
    schema.write_text("fields:\n  - name: PORT\n    type: int\n    required: true\n")
    args = _make_args(str(env), str(schema), fmt="json")
    run_typecheck(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["passed"] is False
    assert data["issues"][0]["key"] == "PORT"
