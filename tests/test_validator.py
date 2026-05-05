"""Tests for the core validation logic."""

import pytest
from envguard.schema import FieldRule, Schema
from envguard.validator import validate, ValidationResult


def make_schema(*rules: FieldRule) -> Schema:
    return Schema(fields=list(rules))


def test_valid_env_passes():
    schema = make_schema(
        FieldRule(name="DATABASE_URL", type="url"),
        FieldRule(name="PORT", type="integer"),
    )
    env = {"DATABASE_URL": "http://localhost:5432", "PORT": "5432"}
    result = validate(env, schema)
    assert result.is_valid
    assert result.errors == []


def test_missing_required_field():
    schema = make_schema(FieldRule(name="SECRET_KEY", required=True))
    result = validate({}, schema)
    assert not result.is_valid
    assert any("missing" in e.message.lower() for e in result.errors)


def test_optional_missing_produces_warning():
    schema = make_schema(FieldRule(name="LOG_LEVEL", required=False))
    result = validate({}, schema)
    assert result.is_valid  # warnings don't fail validation
    assert any(e.severity == "warning" for e in result.errors)


def test_default_covers_missing():
    schema = make_schema(FieldRule(name="TIMEOUT", type="integer", default="30"))
    result = validate({}, schema)
    assert result.is_valid
    assert result.errors == []


def test_invalid_integer_type():
    schema = make_schema(FieldRule(name="PORT", type="integer"))
    result = validate({"PORT": "not_a_number"}, schema)
    assert not result.is_valid


def test_invalid_url_type():
    schema = make_schema(FieldRule(name="API_URL", type="url"))
    result = validate({"API_URL": "ftp://bad-scheme.com"}, schema)
    assert not result.is_valid


def test_pattern_match_passes():
    schema = make_schema(FieldRule(name="ENV", pattern="^(development|staging|production)$"))
    result = validate({"ENV": "production"}, schema)
    assert result.is_valid


def test_pattern_match_fails():
    schema = make_schema(FieldRule(name="ENV", pattern="^(development|staging|production)$"))
    result = validate({"ENV": "local"}, schema)
    assert not result.is_valid
    assert any("pattern" in e.message for e in result.errors)


def test_boolean_type_valid_values():
    schema = make_schema(FieldRule(name="DEBUG", type="boolean"))
    for val in ["true", "false", "1", "0", "yes", "no", "True", "FALSE"]:
        result = validate({"DEBUG": val}, schema)
        assert result.is_valid, f"Expected '{val}' to be valid boolean"
