"""Tests for envguard.commands.rename_cmd."""
import argparse
import json
from pathlib import Path

import pytest

from envguard.commands.rename_cmd import run_rename


ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\n"


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "env_file": "nonexistent.env",
        "map": '{"DB_HOST": "DATABASE_HOST"}',
        "in_place": False,
        "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_rename_missing_env_file(tmp_path):
    args = _make_args(env_file=str(tmp_path / "missing.env"))
    assert run_rename(args) == 1


def test_run_rename_invalid_json(tmp_path):
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env), map="not-json")
    assert run_rename(args) == 1


def test_run_rename_map_not_object(tmp_path):
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env), map=json.dumps(["list"]))
    assert run_rename(args) == 1


def test_run_rename_dry_run_prints_output(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env), dry_run=True)
    rc = run_rename(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DATABASE_HOST" in out
    # File must NOT be modified
    assert env.read_text() == ENV_CONTENT


def test_run_rename_in_place_writes_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env), in_place=True)
    rc = run_rename(args)
    assert rc == 0
    new_content = env.read_text()
    assert "DATABASE_HOST=localhost" in new_content
    assert "DB_HOST" not in new_content


def test_run_rename_skipped_key_warning(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    args = _make_args(
        env_file=str(env),
        map=json.dumps({"NONEXISTENT": "NEW_KEY"}),
    )
    rc = run_rename(args)
    assert rc == 0
    err = capsys.readouterr().err
    assert "NONEXISTENT" in err
    assert "skipped" in err
