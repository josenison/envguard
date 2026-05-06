"""Tests for envguard.merger and envguard.commands.merge_cmd."""
from __future__ import annotations

import argparse
import os

import pytest

from envguard.merger import MergeConflict, MergeResult, merge_envs
from envguard.commands.merge_cmd import run_merge


# ---------------------------------------------------------------------------
# merge_envs unit tests
# ---------------------------------------------------------------------------

ENV_A = "DB_HOST=localhost\nDB_PORT=5432\nAPP_ENV=development\n"
ENV_B = "DB_HOST=prod-db\nSECRET_KEY=abc123\n"


def test_merge_no_conflicts():
    result = merge_envs([("a", "FOO=1\nBAR=2\n"), ("b", "BAZ=3\n")])
    assert result.merged == {"FOO": "1", "BAR": "2", "BAZ": "3"}
    assert not result.has_conflicts()


def test_merge_detects_conflict():
    result = merge_envs([("a", ENV_A), ("b", ENV_B)])
    assert result.has_conflicts()
    conflict_keys = [c.key for c in result.conflicts]
    assert "DB_HOST" in conflict_keys


def test_merge_conflict_str():
    conflict = MergeConflict(key="DB_HOST", values=[("a", "localhost"), ("b", "prod-db")])
    assert "DB_HOST" in str(conflict)
    assert "localhost" in str(conflict)
    assert "prod-db" in str(conflict)


def test_merge_override_no_conflict():
    result = merge_envs([("a", ENV_A), ("b", ENV_B)], override=True)
    assert not result.has_conflicts()
    assert result.merged["DB_HOST"] == "prod-db"  # last wins


def test_merge_override_last_wins():
    result = merge_envs([("a", "X=1\n"), ("b", "X=2\n"), ("c", "X=3\n")], override=True)
    assert result.merged["X"] == "3"


def test_merge_skips_comments_and_blanks():
    text = "# comment\n\nFOO=bar\n"
    result = merge_envs([("a", text)])
    assert "FOO" in result.merged
    assert len(result.merged) == 1


def test_merge_result_str_no_conflicts():
    result = merge_envs([("a", "A=1\n")])
    assert "1 keys" in str(result)
    assert "conflict" not in str(result)


def test_merge_result_str_with_conflicts():
    result = merge_envs([("a", "X=1\n"), ("b", "X=2\n")])
    assert "conflict" in str(result).lower()


def test_merge_sources_recorded():
    result = merge_envs([("file1", "A=1\n"), ("file2", "B=2\n")])
    assert result.sources == ["file1", "file2"]


# ---------------------------------------------------------------------------
# run_merge integration tests
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"env_files": [], "override": False, "output": None, "fmt": "env"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_merge_missing_file(tmp_path):
    args = _make_args(env_files=[str(tmp_path / "missing.env")])
    assert run_merge(args) == 1


def test_run_merge_clean_returns_zero(tmp_path):
    f1 = tmp_path / "a.env"
    f2 = tmp_path / "b.env"
    f1.write_text("FOO=1\n")
    f2.write_text("BAR=2\n")
    args = _make_args(env_files=[str(f1), str(f2)])
    assert run_merge(args) == 0


def test_run_merge_conflict_returns_one(tmp_path):
    f1 = tmp_path / "a.env"
    f2 = tmp_path / "b.env"
    f1.write_text("KEY=val1\n")
    f2.write_text("KEY=val2\n")
    args = _make_args(env_files=[str(f1), str(f2)])
    assert run_merge(args) == 1


def test_run_merge_writes_output_file(tmp_path):
    f1 = tmp_path / "a.env"
    f1.write_text("FOO=bar\n")
    out = tmp_path / "merged.env"
    args = _make_args(env_files=[str(f1)], output=str(out))
    run_merge(args)
    assert out.exists()
    assert "FOO=bar" in out.read_text()


def test_run_merge_json_format(tmp_path, capsys):
    f1 = tmp_path / "a.env"
    f1.write_text("FOO=bar\n")
    args = _make_args(env_files=[str(f1)], fmt="json")
    run_merge(args)
    captured = capsys.readouterr()
    import json
    data = json.loads(captured.out)
    assert data["FOO"] == "bar"
