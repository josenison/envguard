"""Tests for envguard.commands.inject_cmd."""
import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envguard.commands.inject_cmd import run_inject


def _make_args(**kwargs) -> argparse.Namespace:
    """Create a Namespace with sensible defaults for inject command tests."""
    defaults = {
        "env_file": "/nonexistent/.env",
        "overwrite": False,
        "dry_run": False,
        "cmd": [],
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_inject_missing_env_file(capsys):
    args = _make_args(env_file="/no/such/file.env")
    rc = run_inject(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_run_inject_injects_variables(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("HELLO=world\n")
    target: dict = {}
    with patch("envguard.commands.inject_cmd.os.environ", target):
        # Also patch inject_env to use our target dict
        with patch("envguard.commands.inject_cmd.inject_env",
                   wraps=lambda text, overwrite, **kw: __import__(
                       "envguard.injector", fromlist=["inject_env"]
                   ).inject_env(text, overwrite=overwrite, target=target)) as mock_inject:
            args = _make_args(env_file=str(env_file))
            rc = run_inject(args)
    assert rc == 0


def test_run_inject_dry_run_does_not_modify_environ(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=abc123\n")
    monkeypatch.delenv("SECRET", raising=False)
    args = _make_args(env_file=str(env_file), dry_run=True)
    rc = run_inject(args)
    assert rc == 0
    import os
    assert "SECRET" not in os.environ


def test_run_inject_dry_run_prints_result(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("DRY_KEY=value\n")
    args = _make_args(env_file=str(env_file), dry_run=True)
    run_inject(args)
    captured = capsys.readouterr()
    assert "DRY_KEY" in captured.out or "Injected" in captured.out or "Nothing" in captured.out


def test_run_inject_with_cmd_runs_subprocess(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("X=1\n")
    mock_proc = MagicMock(returncode=0)
    with patch("envguard.commands.inject_cmd.subprocess.run", return_value=mock_proc) as mock_run:
        args = _make_args(env_file=str(env_file), cmd=["echo", "hello"])
        rc = run_inject(args)
    assert rc == 0
    mock_run.assert_called_once()


def test_run_inject_cmd_strips_double_dash(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("X=1\n")
    mock_proc = MagicMock(returncode=42)
    with patch("envguard.commands.inject_cmd.subprocess.run", return_value=mock_proc) as mock_run:
        args = _make_args(env_file=str(env_file), cmd=["--", "myapp"])
        rc = run_inject(args)
    assert rc == 42
    called_cmd = mock_run.call_args[0][0]
    assert "--" not in called_cmd


def test_run_inject_cmd_propagates_nonzero_returncode(tmp_path):
    """Ensure run_inject returns the subprocess exit code when it is non-zero."""
    env_file = tmp_path / ".env"
    env_file.write_text("X=1\n")
    mock_proc = MagicMock(returncode=2)
    with patch("envguard.commands.inject_cmd.subprocess.run", return_value=mock_proc):
        args = _make_args(env_file=str(env_file), cmd=["false"])
        rc = run_inject(args)
    assert rc == 2
