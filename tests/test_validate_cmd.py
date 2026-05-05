"""Tests for the validate CLI subcommand."""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from envguard.commands.validate_cmd import run_validate, add_validate_subparser


def _make_args(tmp_path: Path, env_content: str, schema_content: str, no_lint: bool = False, fmt: str = "text") -> argparse.Namespace:
    env_file = tmp_path / ".env"
    schema_file = tmp_path / "schema.yaml"
    env_file.write_text(env_content, encoding="utf-8")
    schema_file.write_text(schema_content, encoding="utf-8")
    return argparse.Namespace(
        env_file=str(env_file),
        schema_file=str(schema_file),
        no_lint=no_lint,
        format=fmt,
    )


SIMPLE_SCHEMA = textwrap.dedent("""\
    fields:
      - name: APP_ENV
        required: true
        type: str
      - name: PORT
        required: false
        type: int
        default: "8080"
""")


def test_run_validate_missing_env_file(tmp_path: Path) -> None:
    schema_file = tmp_path / "schema.yaml"
    schema_file.write_text(SIMPLE_SCHEMA, encoding="utf-8")
    args = argparse.Namespace(
        env_file=str(tmp_path / "nonexistent.env"),
        schema_file=str(schema_file),
        no_lint=False,
        format="text",
    )
    assert run_validate(args) == 1


def test_run_validate_missing_schema_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=production\n", encoding="utf-8")
    args = argparse.Namespace(
        env_file=str(env_file),
        schema_file=str(tmp_path / "nonexistent.yaml"),
        no_lint=False,
        format="text",
    )
    assert run_validate(args) == 1


def test_run_validate_valid_env_passes(tmp_path: Path) -> None:
    env_content = "APP_ENV=production\nPORT=9000\n"
    args = _make_args(tmp_path, env_content, SIMPLE_SCHEMA)
    assert run_validate(args) == 0


def test_run_validate_missing_required_fails(tmp_path: Path) -> None:
    env_content = "PORT=9000\n"
    args = _make_args(tmp_path, env_content, SIMPLE_SCHEMA)
    assert run_validate(args) == 1


def test_run_validate_no_lint_flag(tmp_path: Path) -> None:
    # lowercase key would normally trigger a lint warning
    env_content = "APP_ENV=production\nport=9000\n"
    args = _make_args(tmp_path, env_content, SIMPLE_SCHEMA, no_lint=True)
    # validation itself should pass (port is optional, APP_ENV present)
    assert run_validate(args) == 0


def test_run_validate_json_format(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    env_content = "APP_ENV=staging\n"
    args = _make_args(tmp_path, env_content, SIMPLE_SCHEMA, fmt="json")
    run_validate(args)
    captured = capsys.readouterr()
    assert "\"passed\"" in captured.out or '"passed"' in captured.out


def test_add_validate_subparser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_validate_subparser(subparsers)
    args = parser.parse_args(["validate", "my.env", "schema.yaml"])
    assert args.env_file == "my.env"
    assert args.schema_file == "schema.yaml"
    assert args.no_lint is False
