"""Tests for envguard.renamer."""
import pytest

from envguard.renamer import RenameResult, rename_keys, _parse_key


# ---------------------------------------------------------------------------
# _parse_key helpers
# ---------------------------------------------------------------------------

def test_parse_key_normal_line():
    assert _parse_key("DB_HOST=localhost") == "DB_HOST"


def test_parse_key_with_spaces():
    assert _parse_key("  DB_HOST = localhost  ") == "DB_HOST"


def test_parse_key_blank_line():
    assert _parse_key("") is None


def test_parse_key_comment():
    assert _parse_key("# this is a comment") is None


def test_parse_key_no_equals():
    assert _parse_key("MALFORMED") is None


# ---------------------------------------------------------------------------
# rename_keys
# ---------------------------------------------------------------------------

ENV_TEXT = """# database settings
DB_HOST=localhost
DB_PORT=5432
DB_USER=admin
"""


def test_rename_single_key():
    result = rename_keys(ENV_TEXT, {"DB_HOST": "DATABASE_HOST"})
    assert result.was_changed
    assert ("DB_HOST", "DATABASE_HOST") in result.applied
    assert any("DATABASE_HOST=" in l for l in result.renamed_lines)


def test_rename_preserves_value():
    result = rename_keys(ENV_TEXT, {"DB_HOST": "DATABASE_HOST"})
    assert any("DATABASE_HOST=localhost" in l for l in result.renamed_lines)


def test_rename_multiple_keys():
    result = rename_keys(ENV_TEXT, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
    assert len(result.applied) == 2
    assert result.skipped == []


def test_rename_missing_key_reported_as_skipped():
    result = rename_keys(ENV_TEXT, {"MISSING_KEY": "NEW_KEY"})
    assert not result.was_changed
    assert "MISSING_KEY" in result.skipped


def test_rename_comments_and_blanks_preserved():
    result = rename_keys(ENV_TEXT, {"DB_USER": "DATABASE_USER"})
    assert result.renamed_lines[0].startswith("# database")
    assert result.renamed_lines[4] == "" or result.renamed_lines[-1] == ""


def test_rename_no_mapping_no_change():
    result = rename_keys(ENV_TEXT, {})
    assert not result.was_changed
    assert result.renamed_lines == ENV_TEXT.splitlines(keepends=True)


def test_rename_original_lines_unchanged():
    result = rename_keys(ENV_TEXT, {"DB_HOST": "X"})
    assert "DB_HOST=localhost" in "".join(result.original_lines)


def test_rename_partial_mapping():
    result = rename_keys(ENV_TEXT, {"DB_HOST": "HOST", "NOPE": "NOPE2"})
    assert len(result.applied) == 1
    assert len(result.skipped) == 1
    assert result.skipped[0] == "NOPE"
