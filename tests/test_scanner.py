"""Tests for envguard.scanner."""
import pytest
from envguard.scanner import ScanIssue, ScanResult, scan_env, _parse_key_locations


def test_clean_env_no_issues():
    text = "DB_HOST=localhost\nDB_PORT=5432\nDEBUG=true\n"
    result = scan_env(text)
    assert not result.issues
    assert not result.has_errors()
    assert str(result) == "No duplicate keys found."


def test_blank_lines_and_comments_ignored():
    text = "# comment\n\nDB_HOST=localhost\n"
    result = scan_env(text)
    assert not result.issues


def test_duplicate_key_detected():
    text = "DB_HOST=localhost\nDB_HOST=remotehost\n"
    result = scan_env(text)
    assert result.has_errors()
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.key == "DB_HOST"
    assert issue.lines == [1, 2]
    assert issue.severity == "error"


def test_duplicate_key_on_non_consecutive_lines():
    text = "A=1\nB=2\nA=3\n"
    result = scan_env(text)
    assert len(result.issues) == 1
    assert result.issues[0].key == "A"
    assert result.issues[0].lines == [1, 3]


def test_multiple_duplicate_keys():
    text = "X=1\nY=2\nX=3\nY=4\n"
    result = scan_env(text)
    keys = {i.key for i in result.issues}
    assert keys == {"X", "Y"}


def test_triple_duplicate_records_all_lines():
    text = "KEY=a\nKEY=b\nKEY=c\n"
    result = scan_env(text)
    assert result.issues[0].lines == [1, 2, 3]


def test_issue_str_representation():
    issue = ScanIssue(key="FOO", lines=[2, 5])
    assert "FOO" in str(issue)
    assert "2" in str(issue)
    assert "5" in str(issue)
    assert "ERROR" in str(issue)


def test_scan_result_str_with_issues():
    text = "A=1\nA=2\n"
    result = scan_env(text)
    output = str(result)
    assert "A" in output
    assert "1" in output


def test_parse_key_locations_handles_spaces_around_equals():
    text = "  MY_KEY  =  value  \n"
    locs = _parse_key_locations(text)
    assert "MY_KEY" in locs


def test_parse_key_locations_skips_line_without_equals():
    text = "NOEQUALS\nGOOD=yes\n"
    locs = _parse_key_locations(text)
    assert "NOEQUALS" not in locs
    assert "GOOD" in locs


def test_no_warnings_by_default():
    text = "A=1\nA=2\n"
    result = scan_env(text)
    assert not result.has_warnings()
