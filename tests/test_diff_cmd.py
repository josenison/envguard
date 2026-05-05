"""Tests for envguard.commands.diff_cmd."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envguard.commands.diff_cmd import run_diff
from envguard.differ import DiffResult


def _make_args(env_a: str, env_b: str, against_schema: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        env_a=env_a,
        env_b_or_schema=env_b,
        against_schema=against_schema,
    )


def test_run_diff_missing_env_a(tmp_path: Path):
    args = _make_args(str(tmp_path / "missing.env"), str(tmp_path / "b.env"))
    assert run_diff(args) == 2


def test_run_diff_missing_env_b(tmp_path: Path):
    a = tmp_path / "a.env"
    a.write_text("KEY=val\n")
    args = _make_args(str(a), str(tmp_path / "missing.env"))
    assert run_diff(args) == 2


def test_run_diff_two_identical_envs(tmp_path: Path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text("KEY=1\nOTHER=2\n")
    b.write_text("KEY=1\nOTHER=2\n")
    args = _make_args(str(a), str(b))
    assert run_diff(args) == 0


def test_run_diff_two_different_envs(tmp_path: Path, capsys):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text("KEY=1\n")
    b.write_text("KEY=1\nEXTRA=2\n")
    args = _make_args(str(a), str(b))
    code = run_diff(args)
    assert code == 1
    captured = capsys.readouterr()
    assert "EXTRA" in captured.out


def test_run_diff_against_schema_no_diff(tmp_path: Path):
    env = tmp_path / "a.env"
    schema_file = tmp_path / "schema.yaml"
    env.write_text("DB_HOST=localhost\n")

    fake_schema = MagicMock()
    fake_schema.fields = [MagicMock(name_attr="DB_HOST")]
    fake_schema.fields[0].name = "DB_HOST"

    with patch("envguard.commands.diff_cmd.load_schema", return_value=fake_schema), \
         patch(
             "envguard.commands.diff_cmd.diff_env_against_schema",
             return_value=DiffResult(common=["DB_HOST"]),
         ):
        schema_file.write_text("fields:\n  - name: DB_HOST\n")
        args = _make_args(str(env), str(schema_file), against_schema=True)
        assert run_diff(args) == 0
