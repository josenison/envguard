"""Tests for envguard.templater."""

import pytest
from envguard.schema import Schema, FieldRule
from envguard.templater import generate_template, TemplateResult


def make_schema(**fields) -> Schema:
    return Schema(fields=fields)


# ---------------------------------------------------------------------------
# TemplateResult helpers
# ---------------------------------------------------------------------------

def test_template_result_str_joins_lines():
    tr = TemplateResult(lines=["A=1", "B=2"])
    assert str(tr) == "A=1\nB=2"


def test_template_result_write(tmp_path):
    tr = TemplateResult(lines=["KEY=value"])
    dest = tmp_path / ".env.example"
    tr.write(str(dest))
    assert dest.read_text() == "KEY=value\n"


# ---------------------------------------------------------------------------
# generate_template
# ---------------------------------------------------------------------------

def test_required_field_uses_placeholder():
    schema = make_schema(DATABASE_URL=FieldRule(required=True, type="str"))
    result = generate_template(schema)
    text = str(result)
    assert "DATABASE_URL=your_value_here" in text


def test_optional_field_annotated():
    schema = make_schema(LOG_LEVEL=FieldRule(required=False, default="info", type="str"))
    result = generate_template(schema, mark_optional=True)
    text = str(result)
    assert "optional" in text
    assert "default: info" in text
    assert "LOG_LEVEL=info" in text


def test_description_appears_as_comment():
    schema = make_schema(
        PORT=FieldRule(required=True, type="int", description="HTTP server port")
    )
    result = generate_template(schema, include_descriptions=True)
    text = str(result)
    assert "# HTTP server port" in text


def test_no_description_when_disabled():
    schema = make_schema(
        PORT=FieldRule(required=True, type="int", description="HTTP server port")
    )
    result = generate_template(schema, include_descriptions=False)
    text = str(result)
    assert "# HTTP server port" not in text
    assert "PORT=" in text


def test_int_type_placeholder():
    schema = make_schema(WORKERS=FieldRule(required=True, type="int"))
    result = generate_template(schema)
    assert "WORKERS=0" in str(result)


def test_bool_type_placeholder():
    schema = make_schema(DEBUG=FieldRule(required=True, type="bool"))
    result = generate_template(schema)
    assert "DEBUG=false" in str(result)


def test_type_annotation_shown_for_non_str():
    schema = make_schema(TIMEOUT=FieldRule(required=True, type="float"))
    result = generate_template(schema)
    assert "type: float" in str(result)


def test_no_type_annotation_for_str():
    schema = make_schema(NAME=FieldRule(required=True, type="str"))
    result = generate_template(schema)
    # str type should not clutter the output with a type annotation
    assert "type: str" not in str(result)


def test_multiple_fields_separated_by_blank_lines():
    schema = make_schema(
        A=FieldRule(required=True, type="str"),
        B=FieldRule(required=True, type="str"),
    )
    result = generate_template(schema, include_descriptions=False)
    text = str(result)
    # There should be a blank line between the two keys
    assert "\n\n" in text


def test_no_trailing_blank_line():
    schema = make_schema(ONLY=FieldRule(required=True, type="str"))
    result = generate_template(schema, include_descriptions=False)
    assert not str(result).endswith("\n")
