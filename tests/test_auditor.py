"""Tests for envguard.auditor module."""
import pytest
from envguard.auditor import audit_env, AuditIssue, AuditResult


def test_clean_env_no_issues():
    env = {"APP_NAME": "myapp", "PORT": "8080", "DEBUG": "false"}
    result = audit_env(env)
    assert not result.has_errors()
    assert not result.has_warnings()
    assert result.issues == []


def test_empty_sensitive_value_is_error():
    env = {"DB_PASSWORD": ""}
    result = audit_env(env)
    assert result.has_errors()
    errors = [i for i in result.issues if i.severity == "error"]
    assert any("empty" in i.message.lower() for i in errors)


def test_weak_password_is_warning():
    env = {"DB_PASSWORD": "password"}
    result = audit_env(env)
    assert result.has_warnings()
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("weak" in i.message.lower() for i in warnings)


def test_weak_secret_placeholder_is_warning():
    env = {"API_SECRET": "changeme"}
    result = audit_env(env)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert len(warnings) >= 1


def test_strong_password_no_issue():
    env = {"DB_PASSWORD": "xK9#mP2$qR7!nL4@"}
    result = audit_env(env)
    assert not result.has_errors()
    assert not result.has_warnings()


def test_token_empty_is_error():
    env = {"AUTH_TOKEN": "   "}
    result = audit_env(env)
    assert result.has_errors()


def test_audit_issue_str():
    issue = AuditIssue(key="DB_PASSWORD", message="Empty value.", severity="error")
    assert str(issue) == "[ERROR] DB_PASSWORD: Empty value."


def test_audit_result_add():
    result = AuditResult()
    issue = AuditIssue(key="X", message="test", severity="warning")
    result.add(issue)
    assert len(result.issues) == 1
    assert result.has_warnings()
    assert not result.has_errors()


def test_multiple_sensitive_keys():
    env = {
        "DB_PASSWORD": "secret",
        "API_KEY": "",
        "APP_NAME": "myapp",
    }
    result = audit_env(env)
    keys_with_issues = {i.key for i in result.issues}
    assert "DB_PASSWORD" in keys_with_issues
    assert "API_KEY" in keys_with_issues
    assert "APP_NAME" not in keys_with_issues
