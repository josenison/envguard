"""Tests for envguard.commands.audit_cmd module."""
import argparse
from pathlib import Path
import pytest
from envguard.commands.audit_cmd import run_audit


def _make_args(env_file: str, strict: bool = False) -> argparse.Namespace:
    return argparse.Namespace(env_file=env_file, strict=strict)


def test_run_audit_missing_env_file(tmp_path):
    args = _make_args(str(tmp_path / "nonexistent.env"))
    assert run_audit(args) == 1


def test_run_audit_clean_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=myapp\nPORT=8080\n")
    args = _make_args(str(env_file))
    assert run_audit(args) == 0


def test_run_audit_empty_password_returns_error(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_PASSWORD=\nAPP_NAME=myapp\n")
    args = _make_args(str(env_file))
    assert run_audit(args) == 1


def test_run_audit_weak_password_no_strict_returns_zero(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_PASSWORD=admin\n")
    args = _make_args(str(env_file), strict=False)
    result = run_audit(args)
    assert result == 0


def test_run_audit_weak_password_strict_returns_nonzero(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_PASSWORD=admin\n")
    args = _make_args(str(env_file), strict=True)
    result = run_audit(args)
    assert result == 1


def test_run_audit_ignores_comments_and_blanks(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# this is a comment\n\nAPP_NAME=myapp\n")
    args = _make_args(str(env_file))
    assert run_audit(args) == 0


def test_run_audit_strong_secret_passes(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("API_SECRET=xK9#mP2$qR7!nL4@\n")
    args = _make_args(str(env_file))
    assert run_audit(args) == 0
