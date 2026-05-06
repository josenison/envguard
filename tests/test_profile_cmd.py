"""Tests for envguard.commands.profile_cmd."""
import argparse
import os
import textwrap
import pytest

from envguard.commands.profile_cmd import run_profile, _parse_env_file


def _make_args(env_file: str, show_types: bool = False) -> argparse.Namespace:
    return argparse.Namespace(env_file=env_file, show_types=show_types)


# ---------------------------------------------------------------------------
# _parse_env_file
# ---------------------------------------------------------------------------

def test_parse_env_file_basic(tmp_path):
    env = tmp_path / ".env"
    env.write_text("APP_NAME=myapp\nPORT=8080\n")
    pairs = _parse_env_file(str(env))
    assert pairs == {"APP_NAME": "myapp", "PORT": "8080"}


def test_parse_env_file_ignores_comments_and_blanks(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comment\n\nKEY=val\n")
    pairs = _parse_env_file(str(env))
    assert pairs == {"KEY": "val"}


def test_parse_env_file_missing_returns_empty(tmp_path):
    pairs = _parse_env_file(str(tmp_path / "nonexistent.env"))
    assert pairs == {}


# ---------------------------------------------------------------------------
# run_profile
# ---------------------------------------------------------------------------

def test_run_profile_missing_env_file(tmp_path):
    args = _make_args(str(tmp_path / "missing.env"))
    assert run_profile(args) == 1


def test_run_profile_clean_env(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("APP=hello\nPORT=3000\n")
    args = _make_args(str(env))
    code = run_profile(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "Total keys" in out
    assert "2" in out


def test_run_profile_shows_empty_values(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("API_KEY=\nAPP=hello\n")
    args = _make_args(str(env))
    run_profile(args)
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "Empty values" in out


def test_run_profile_show_types_flag(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("DEBUG=true\nPORT=8080\n")
    args = _make_args(str(env), show_types=True)
    run_profile(args)
    out = capsys.readouterr().out
    assert "boolean" in out
    assert "integer" in out


def test_run_profile_sensitive_keys_reported(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("DB_PASSWORD=hunter2\nAPP=ok\n")
    args = _make_args(str(env))
    run_profile(args)
    out = capsys.readouterr().out
    assert "Sensitive keys" in out
    assert "DB_PASSWORD" in out
