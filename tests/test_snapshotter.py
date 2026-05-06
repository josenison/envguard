"""Tests for envguard.snapshotter."""
import json
import os
import tempfile

import pytest

from envguard.snapshotter import (
    SnapshotDiff,
    compare_snapshots,
    create_snapshot,
    load_snapshot,
    save_snapshot,
)


def test_create_snapshot_captures_keys():
    env = {"APP_ENV": "production", "PORT": "8080"}
    snap = create_snapshot(env)
    assert snap.keys == env
    assert snap.timestamp  # non-empty ISO string


def test_snapshot_round_trip(tmp_path):
    env = {"KEY": "value", "OTHER": "123"}
    snap = create_snapshot(env)
    path = str(tmp_path / "snap.json")
    save_snapshot(snap, path)
    loaded = load_snapshot(path)
    assert loaded.keys == snap.keys
    assert loaded.timestamp == snap.timestamp


def test_save_snapshot_creates_valid_json(tmp_path):
    snap = create_snapshot({"A": "1"})
    path = str(tmp_path / "snap.json")
    save_snapshot(snap, path)
    with open(path) as fh:
        data = json.load(fh)
    assert "timestamp" in data
    assert "keys" in data
    assert data["keys"]["A"] == "1"


def test_compare_no_differences():
    env = {"X": "1", "Y": "2"}
    old = create_snapshot(env)
    new = create_snapshot(env)
    diff = compare_snapshots(old, new)
    assert not diff.has_differences()


def test_compare_added_key():
    old = create_snapshot({"A": "1"})
    new = create_snapshot({"A": "1", "B": "2"})
    diff = compare_snapshots(old, new)
    assert "B" in diff.added
    assert diff.has_differences()


def test_compare_removed_key():
    old = create_snapshot({"A": "1", "B": "2"})
    new = create_snapshot({"A": "1"})
    diff = compare_snapshots(old, new)
    assert "B" in diff.removed


def test_compare_changed_value():
    old = create_snapshot({"PORT": "8080"})
    new = create_snapshot({"PORT": "9090"})
    diff = compare_snapshots(old, new)
    assert "PORT" in diff.changed


def test_snapshot_diff_str_no_differences():
    diff = SnapshotDiff()
    assert str(diff) == "No differences."


def test_snapshot_diff_str_with_changes():
    diff = SnapshotDiff(added=["NEW"], removed=["OLD"], changed=["MOD"])
    text = str(diff)
    assert "+ NEW" in text
    assert "- OLD" in text
    assert "~ MOD" in text
