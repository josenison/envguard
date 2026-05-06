"""Tests for envguard.interpolator and the interpolate_cmd."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envguard.interpolator import interpolate_env, InterpolationResult
from envguard.commands.interpolate_cmd import run_interpolate, _parse_env_file


# ---------------------------------------------------------------------------
# interpolator unit tests
# ---------------------------------------------------------------------------

def test_no_references_unchanged():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = interpolate_env(env)
    assert result.resolved == env
    assert not result.has_warnings


def test_brace_reference_resolved():
    env = {"BASE": "http://example.com", "URL": "${BASE}/api"}
    result = interpolate_env(env)
    assert result.resolved["URL"] == "http://example.com/api"
    assert not result.has_warnings


def test_bare_reference_resolved():
    env = {"HOST": "db", "DSN": "postgres://$HOST/mydb"}
    result = interpolate_env(env)
    assert result.resolved["DSN"] == "postgres://db/mydb"


def test_unresolved_ref_produces_warning():
    env = {"URL": "${MISSING}/path"}
    result = interpolate_env(env, use_os_env=False)
    assert result.has_warnings
    assert result.warnings[0].ref == "MISSING"
    assert "${MISSING}/path" in result.resolved["URL"]  # token left in place


def test_fallback_to_os_environ(monkeypatch):
    monkeypatch.setenv("OS_VAR", "from_os")
    env = {"GREETING": "hello ${OS_VAR}"}
    result = interpolate_env(env, use_os_env=True)
    assert result.resolved["GREETING"] == "hello from_os"
    assert not result.has_warnings


def test_no_os_fallback_warns(monkeypatch):
    monkeypatch.setenv("OS_VAR", "from_os")
    env = {"GREETING": "hello ${OS_VAR}"}
    result = interpolate_env(env, use_os_env=False)
    assert result.has_warnings


def test_warning_str():
    env = {"A": "${NOPE}"}
    result = interpolate_env(env, use_os_env=False)
    assert "NOPE" in str(result.warnings[0])


# ---------------------------------------------------------------------------
# interpolate_cmd integration tests
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"env_file": "", "no_os_env": False, "strict": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_interpolate_missing_file(tmp_path):
    args = _make_args(env_file=str(tmp_path / "missing.env"))
    assert run_interpolate(args) == 1


def test_run_interpolate_clean_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("HOST=localhost\nPORT=5432\n")
    args = _make_args(env_file=str(env_file))
    assert run_interpolate(args) == 0


def test_run_interpolate_strict_with_warning(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("URL=${UNDEFINED}/path\n")
    args = _make_args(env_file=str(env_file), no_os_env=True, strict=True)
    assert run_interpolate(args) == 1


def test_run_interpolate_no_strict_with_warning(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("URL=${UNDEFINED}/path\n")
    args = _make_args(env_file=str(env_file), no_os_env=True, strict=False)
    assert run_interpolate(args) == 0
