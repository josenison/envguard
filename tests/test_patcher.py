"""Tests for envguard.patcher and envguard.commands.patch_cmd."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envguard.patcher import patch_env
from envguard.commands.patch_cmd import run_patch


# ---------------------------------------------------------------------------
# patcher unit tests
# ---------------------------------------------------------------------------

def test_update_existing_key():
    source = "FOO=old\nBAR=keep\n"
    result = patch_env(source, {"FOO": "new"})
    assert "FOO=new" in result.lines
    assert "BAR=keep" in result.lines
    assert result.updated == ["FOO"]
    assert result.added == []


def test_add_new_key():
    source = "FOO=bar\n"
    result = patch_env(source, {"NEW_KEY": "value"})
    assert "NEW_KEY=value" in result.lines
    assert result.added == ["NEW_KEY"]
    assert result.updated == []


def test_update_and_add_together():
    source = "EXISTING=old\n"
    result = patch_env(source, {"EXISTING": "new", "BRAND_NEW": "hello"})
    assert "EXISTING=new" in result.lines
    assert "BRAND_NEW=hello" in result.lines
    assert "EXISTING" in result.updated
    assert "BRAND_NEW" in result.added


def test_comments_and_blanks_preserved():
    source = "# comment\n\nFOO=bar\n"
    result = patch_env(source, {"FOO": "baz"})
    assert "# comment" in result.lines
    assert "" in result.lines
    assert "FOO=baz" in result.lines


def test_no_patches_returns_original_lines():
    source = "A=1\nB=2\n"
    result = patch_env(source, {})
    assert result.lines == ["A=1", "B=2", ""]
    assert not result.was_changed()


def test_was_changed_false_when_nothing_patched():
    result = patch_env("X=1\n", {})
    assert result.was_changed() is False


def test_was_changed_true_when_updated():
    result = patch_env("X=1\n", {"X": "2"})
    assert result.was_changed() is True


# ---------------------------------------------------------------------------
# patch_cmd integration tests
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"env_file": "", "set": "{}", "dry_run": False, "quiet": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_patch_missing_env_file(tmp_path):
    args = _make_args(env_file=str(tmp_path / "missing.env"))
    assert run_patch(args) == 1


def test_run_patch_invalid_json(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    args = _make_args(env_file=str(env_file), set="not-json")
    assert run_patch(args) == 1


def test_run_patch_set_not_object(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    args = _make_args(env_file=str(env_file), set='["list"]')
    assert run_patch(args) == 1


def test_run_patch_writes_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=old\n")
    args = _make_args(env_file=str(env_file), set='{"FOO": "new"}', quiet=True)
    code = run_patch(args)
    assert code == 0
    assert "FOO=new" in env_file.read_text()


def test_run_patch_dry_run_does_not_write(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=old\n")
    args = _make_args(env_file=str(env_file), set='{"FOO": "new"}', dry_run=True, quiet=True)
    run_patch(args)
    assert "FOO=old" in env_file.read_text()  # file unchanged
    captured = capsys.readouterr()
    assert "FOO=new" in captured.out
