"""Tests for envguard.commands.group_cmd."""
import argparse
import json
from pathlib import Path

import pytest

from envguard.commands.group_cmd import run_group


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "env_file": "",
        "prefixes": None,
        "separator": "_",
        "output_json": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nDEBUG=true\n"


def test_run_group_missing_env_file(tmp_path):
    args = _make_args(env_file=str(tmp_path / "missing.env"))
    assert run_group(args) == 1


def test_run_group_text_output(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env_file))
    rc = run_group(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "[DB]" in captured.out
    assert "DB_HOST=localhost" in captured.out


def test_run_group_json_output(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env_file), output_json=True)
    rc = run_group(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "groups" in data
    assert "ungrouped" in data
    assert "DB" in data["groups"]


def test_run_group_invalid_prefixes_json(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env_file), prefixes="not-json")
    rc = run_group(args)
    assert rc == 1


def test_run_group_prefixes_not_array(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env_file), prefixes='{"a": 1}')
    rc = run_group(args)
    assert rc == 1


def test_run_group_explicit_prefixes(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nAWS_KEY=abc\nDEBUG=true\n")
    args = _make_args(env_file=str(env_file), prefixes='["DB"]')
    rc = run_group(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "[DB]" in out
    # AWS and DEBUG are ungrouped
    assert "[ungrouped]" in out
