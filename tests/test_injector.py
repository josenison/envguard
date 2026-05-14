"""Tests for envguard.injector."""
import pytest

from envguard.injector import InjectionResult, inject_env


def _target() -> dict:
    return {}


# ---------------------------------------------------------------------------
# _parse_env_pairs (tested indirectly through inject_env)
# ---------------------------------------------------------------------------

def test_inject_basic_key_value():
    env: dict = {}
    result = inject_env("FOO=bar\nBAZ=qux\n", target=env)
    assert env == {"FOO": "bar", "BAZ": "qux"}
    assert result.injected == {"FOO": "bar", "BAZ": "qux"}
    assert result.skipped == {}
    assert result.overwritten == {}


def test_inject_ignores_comments_and_blanks():
    env: dict = {}
    text = "# comment\n\nFOO=bar\n"
    result = inject_env(text, target=env)
    assert "FOO" in env
    assert len(result.injected) == 1


def test_inject_ignores_lines_without_equals():
    env: dict = {}
    result = inject_env("NODEQUALS\nFOO=bar\n", target=env)
    assert list(env.keys()) == ["FOO"]


def test_existing_key_skipped_by_default():
    env: dict = {"FOO": "original"}
    result = inject_env("FOO=new\n", target=env)
    assert env["FOO"] == "original"
    assert result.skipped == {"FOO": "new"}
    assert result.injected == {}


def test_existing_key_overwritten_when_flag_set():
    env: dict = {"FOO": "original"}
    result = inject_env("FOO=new\n", overwrite=True, target=env)
    assert env["FOO"] == "new"
    assert result.overwritten == {"FOO": "new"}
    assert result.injected == {}


def test_total_injected_counts_overwritten():
    env: dict = {"A": "old"}
    result = inject_env("A=new\nB=fresh\n", overwrite=True, target=env)
    assert result.total_injected == 2


def test_str_nothing_to_inject():
    result = InjectionResult()
    assert str(result) == "Nothing to inject."


def test_str_shows_sections():
    result = InjectionResult(
        injected={"A": "1"},
        skipped={"B": "2"},
        overwritten={"C": "3"},
    )
    text = str(result)
    assert "Injected" in text
    assert "Skipped" in text
    assert "Overwritten" in text


def test_value_with_equals_in_it():
    env: dict = {}
    inject_env("DB_URL=postgres://user:pass@host/db?ssl=true\n", target=env)
    assert env["DB_URL"] == "postgres://user:pass@host/db?ssl=true"


def test_whitespace_stripped_from_key_and_value():
    env: dict = {}
    inject_env("  FOO  =  bar  \n", target=env)
    assert "FOO" in env
    assert env["FOO"] == "bar"
