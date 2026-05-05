"""Tests for schema loading and FieldRule validation."""

import json
import pytest
from pathlib import Path

from envguard.schema import FieldRule, Schema, load_schema


def test_field_rule_defaults():
    rule = FieldRule(name="DATABASE_URL")
    assert rule.required is True
    assert rule.type == "string"
    assert rule.pattern is None
    assert rule.default is None


def test_field_rule_invalid_type():
    with pytest.raises(ValueError, match="Invalid type"):
        FieldRule(name="FOO", type="uuid")


def test_schema_get_field():
    schema = Schema(fields=[FieldRule(name="PORT", type="integer")])
    assert schema.get_field("PORT") is not None
    assert schema.get_field("MISSING") is None


def test_load_schema_valid(tmp_path: Path):
    data = {
        "fields": [
            {"name": "APP_ENV", "required": True, "type": "string"},
            {"name": "PORT", "type": "integer", "default": "8080"},
        ]
    }
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(data))

    schema = load_schema(str(schema_file))
    assert len(schema.fields) == 2
    assert schema.get_field("PORT").default == "8080"


def test_load_schema_missing_fields_key(tmp_path: Path):
    schema_file = tmp_path / "bad_schema.json"
    schema_file.write_text(json.dumps({"rules": []}))
    with pytest.raises(ValueError, match="'fields' key"):
        load_schema(str(schema_file))


def test_load_schema_entry_missing_name(tmp_path: Path):
    schema_file = tmp_path / "bad_schema.json"
    schema_file.write_text(json.dumps({"fields": [{"type": "string"}]}))
    with pytest.raises(ValueError, match="'name' key"):
        load_schema(str(schema_file))
