"""Tests for envguard.sorter."""
from envguard.sorter import SortResult, _parse_pairs, sort_env


# ---------------------------------------------------------------------------
# _parse_pairs
# ---------------------------------------------------------------------------

def test_parse_pairs_basic():
    text = "B=2\nA=1\n"
    pairs = _parse_pairs(text)
    assert pairs == [("B", "B=2"), ("A", "A=1")]


def test_parse_pairs_ignores_comments_and_blanks():
    text = "# comment\n\nKEY=val\n"
    pairs = _parse_pairs(text)
    assert len(pairs) == 1
    assert pairs[0][0] == "KEY"


def test_parse_pairs_ignores_lines_without_equals():
    text = "NOEQUALS\nKEY=val\n"
    pairs = _parse_pairs(text)
    assert len(pairs) == 1


def test_parse_pairs_handles_spaces_around_equals():
    text = "KEY = value\n"
    pairs = _parse_pairs(text)
    assert pairs[0][0] == "KEY"


# ---------------------------------------------------------------------------
# sort_env — no groups
# ---------------------------------------------------------------------------

def test_sort_no_groups_alphabetical():
    text = "ZEBRA=1\nAPPLE=2\nMIDDLE=3\n"
    result = sort_env(text)
    assert result.ungrouped == ["ZEBRA=1", "APPLE=2", "MIDDLE=3"]
    output = str(result)
    lines = [l for l in output.splitlines() if l.strip()]
    assert lines == ["APPLE=2", "MIDDLE=3", "ZEBRA=1"]


def test_sort_empty_input():
    result = sort_env("")
    assert result.ungrouped == []
    assert str(result).strip() == ""


# ---------------------------------------------------------------------------
# sort_env — with groups
# ---------------------------------------------------------------------------

def test_sort_with_groups_buckets_correctly():
    text = "DB_HOST=localhost\nAPP_NAME=myapp\nDB_PORT=5432\nSECRET=xyz\n"
    result = sort_env(text, groups={"database": ["DB_"], "app": ["APP_"]})
    assert "DB_HOST=localhost" in result.groups["database"]
    assert "DB_PORT=5432" in result.groups["database"]
    assert "APP_NAME=myapp" in result.groups["app"]
    assert "SECRET=xyz" in result.ungrouped


def test_sort_with_groups_output_has_headers():
    text = "DB_HOST=localhost\nAPP_NAME=myapp\n"
    result = sort_env(text, groups={"database": ["DB_"], "app": ["APP_"]})
    output = str(result)
    assert "# --- database ---" in output
    assert "# --- app ---" in output


def test_sort_exact_key_match_in_group():
    text = "SECRET_KEY=abc\nOTHER=1\n"
    result = sort_env(text, groups={"secrets": ["SECRET_KEY"]})
    assert "SECRET_KEY=abc" in result.groups["secrets"]
    assert "OTHER=1" in result.ungrouped


def test_sort_ungrouped_shown_under_other_header():
    text = "ORPHAN=1\n"
    result = sort_env(text, groups={"db": ["DB_"]})
    output = str(result)
    assert "# --- other ---" in output
    assert "ORPHAN=1" in output


def test_sort_result_str_ends_with_newline():
    text = "KEY=val\n"
    result = sort_env(text)
    assert str(result).endswith("\n")
