"""Tests for envguard.deduplicator."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envguard.deduplicator import DeduplicateResult, _parse_key, deduplicate_env
from envguard.commands.deduplicate_cmd import run_deduplicate


# ---------------------------------------------------------------------------
# _parse_key
# ---------------------------------------------------------------------------

def test_parse_key_normal_line():
    assert _parse_key("FOO=bar") == "FOO"


def test_parse_key_with_spaces():
    assert _parse_key("  MY_KEY = value  ") == "MY_KEY"


def test_parse_key_blank_line():
    assert _parse_key("") is None
    assert _parse_key("   ") is None


def test_parse_key_comment():
    assert _parse_key("# comment") is None


def test_parse_key_no_equals():
    assert _parse_key("JUST_A_WORD") is None


# ---------------------------------------------------------------------------
# deduplicate_env — keep last (default)
# ---------------------------------------------------------------------------

def test_no_duplicates_unchanged():
    text = "A=1\nB=2\nC=3\n"
    result = deduplicate_env(text)
    assert not result.was_changed()
    assert result.removed == []
    assert result.lines == ["A=1", "B=2", "C=3", ""]


def test_duplicate_key_keep_last():
    text = "A=1\nB=2\nA=3\n"
    result = deduplicate_env(text, keep="last")
    assert result.was_changed()
    assert len(result.removed) == 1
    assert result.removed[0] == (1, "A")
    assert "A=3" in result.lines
    assert "A=1" not in result.lines


def test_duplicate_key_keep_first():
    text = "A=1\nB=2\nA=3\n"
    result = deduplicate_env(text, keep="first")
    assert result.was_changed()
    assert result.removed[0] == (3, "A")
    assert "A=1" in result.lines
    assert "A=3" not in result.lines


def test_triple_duplicate_keep_last():
    text = "X=one\nX=two\nX=three\n"
    result = deduplicate_env(text, keep="last")
    assert len(result.removed) == 2
    assert "X=three" in result.lines
    assert "X=one" not in result.lines
    assert "X=two" not in result.lines


def test_comments_and_blanks_preserved():
    text = "# header\nFOO=1\n\nFOO=2\n"
    result = deduplicate_env(text, keep="last")
    assert "# header" in result.lines
    assert "" in result.lines
    assert "FOO=2" in result.lines
    assert "FOO=1" not in result.lines


# ---------------------------------------------------------------------------
# run_deduplicate command
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"keep": "last", "dry_run": False, "quiet": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_deduplicate_missing_file(tmp_path):
    args = _make_args(env_file=str(tmp_path / "missing.env"))
    assert run_deduplicate(args) == 1


def test_run_deduplicate_no_duplicates(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1\nB=2\n")
    args = _make_args(env_file=str(env))
    assert run_deduplicate(args) == 0
    assert env.read_text() == "A=1\nB=2\n"


def test_run_deduplicate_writes_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1\nA=2\n")
    args = _make_args(env_file=str(env))
    assert run_deduplicate(args) == 0
    content = env.read_text()
    assert "A=2" in content
    assert "A=1" not in content


def test_run_deduplicate_dry_run_does_not_modify(tmp_path):
    env = tmp_path / ".env"
    original = "A=1\nA=2\n"
    env.write_text(original)
    args = _make_args(env_file=str(env), dry_run=True)
    assert run_deduplicate(args) == 0
    assert env.read_text() == original
