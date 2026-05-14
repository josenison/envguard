"""Tests for envguard.commands.compare_cmd."""
import argparse
import json
from pathlib import Path

import pytest

from envguard.commands.compare_cmd import run_compare


def _make_args(env_a: str, env_b: str, ignore=None, output_json: bool = False):
    ns = argparse.Namespace(
        env_a=env_a,
        env_b=env_b,
        ignore=ignore or [],
        output_json=output_json,
    )
    return ns


ENV_IDENTICAL = "DB_HOST=localhost\nDB_PORT=5432\n"
ENV_DIFFERENT = "DB_HOST=prod.example.com\nDB_PORT=5432\n"


def test_run_compare_missing_env_a(tmp_path):
    args = _make_args(str(tmp_path / "missing.env"), str(tmp_path / "b.env"))
    assert run_compare(args) == 1


def test_run_compare_missing_env_b(tmp_path):
    a = tmp_path / "a.env"
    a.write_text(ENV_IDENTICAL)
    args = _make_args(str(a), str(tmp_path / "missing.env"))
    assert run_compare(args) == 1


def test_run_compare_identical_returns_zero(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text(ENV_IDENTICAL)
    b.write_text(ENV_IDENTICAL)
    args = _make_args(str(a), str(b))
    assert run_compare(args) == 0


def test_run_compare_different_returns_one(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text(ENV_IDENTICAL)
    b.write_text(ENV_DIFFERENT)
    args = _make_args(str(a), str(b))
    assert run_compare(args) == 1


def test_run_compare_json_output(tmp_path, capsys):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text(ENV_IDENTICAL)
    b.write_text(ENV_DIFFERENT)
    args = _make_args(str(a), str(b), output_json=True)
    run_compare(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    keys = {item["key"] for item in data}
    assert "DB_HOST" in keys


def test_run_compare_ignore_key(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text(ENV_IDENTICAL)
    b.write_text(ENV_DIFFERENT)
    args = _make_args(str(a), str(b), ignore=["DB_HOST"])
    assert run_compare(args) == 0
