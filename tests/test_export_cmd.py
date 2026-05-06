"""Unit tests for envguard.commands.export_cmd."""
import argparse
import json
from pathlib import Path

import pytest

from envguard.commands.export_cmd import run_export, _parse_env_file


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "env_file": "test.env",
        "fmt": "shell",
        "no_export": False,
        "output": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


ENV_CONTENT = "DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\n# comment\n"


# ---------------------------------------------------------------------------
# _parse_env_file
# ---------------------------------------------------------------------------

def test_parse_env_file_basic():
    result = _parse_env_file("KEY=VALUE\n")
    assert result == {"KEY": "VALUE"}


def test_parse_env_file_ignores_comments_and_blanks():
    result = _parse_env_file("# comment\n\nKEY=VALUE\n")
    assert result == {"KEY": "VALUE"}


def test_parse_env_file_ignores_no_equals():
    result = _parse_env_file("BADLINE\nGOOD=ok\n")
    assert result == {"GOOD": "ok"}


# ---------------------------------------------------------------------------
# run_export
# ---------------------------------------------------------------------------

def test_run_export_missing_env_file():
    args = _make_args(env_file="nonexistent.env")
    assert run_export(args) == 1


def test_run_export_shell_format(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env_file))
    rc = run_export(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "export DATABASE_URL=" in captured.out


def test_run_export_json_format(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    args = _make_args(env_file=str(env_file), fmt="json")
    rc = run_export(args)
    assert rc == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "DATABASE_URL" in parsed


def test_run_export_to_output_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(ENV_CONTENT)
    out_file = tmp_path / "out.sh"
    args = _make_args(env_file=str(env_file), output=str(out_file))
    rc = run_export(args)
    assert rc == 0
    assert out_file.exists()
    assert "export DATABASE_URL=" in out_file.read_text()


def test_run_export_no_export_flag(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=val\n")
    args = _make_args(env_file=str(env_file), no_export=True)
    run_export(args)
    captured = capsys.readouterr()
    assert "export" not in captured.out
    assert "KEY=" in captured.out
