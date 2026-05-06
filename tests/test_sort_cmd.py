"""Tests for envguard.commands.sort_cmd."""
import argparse
import json
from pathlib import Path

import pytest

from envguard.commands.sort_cmd import run_sort


def _make_args(
    env_file: str,
    groups: str | None = None,
    in_place: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(env_file=env_file, groups=groups, in_place=in_place)


def test_run_sort_missing_env_file(tmp_path):
    args = _make_args(str(tmp_path / "missing.env"))
    assert run_sort(args) == 1


def test_run_sort_no_groups_prints_sorted(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("ZEBRA=1\nAPPLE=2\n")
    args = _make_args(str(env))
    rc = run_sort(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert out.index("APPLE") < out.index("ZEBRA")


def test_run_sort_invalid_groups_json(tmp_path):
    env = tmp_path / ".env"
    env.write_text("KEY=val\n")
    args = _make_args(str(env), groups="not-json")
    assert run_sort(args) == 1


def test_run_sort_with_groups_output_has_headers(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nAPP_NAME=myapp\n")
    groups_json = json.dumps({"database": ["DB_"], "app": ["APP_"]})
    args = _make_args(str(env), groups=groups_json)
    rc = run_sort(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "# --- database ---" in out
    assert "# --- app ---" in out


def test_run_sort_in_place_overwrites_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("ZEBRA=1\nAPPLE=2\n")
    args = _make_args(str(env), in_place=True)
    rc = run_sort(args)
    assert rc == 0
    content = env.read_text()
    assert content.index("APPLE") < content.index("ZEBRA")


def test_run_sort_in_place_prints_confirmation(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("KEY=val\n")
    args = _make_args(str(env), in_place=True)
    run_sort(args)
    out = capsys.readouterr().out
    assert "Sorted" in out
