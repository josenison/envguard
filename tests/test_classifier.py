"""Tests for envguard.classifier."""
import pytest
from envguard.classifier import classify_env, ClassifyResult, _classify_key


def test_classify_key_database():
    assert _classify_key("DATABASE_URL") == "database"
    assert _classify_key("DB_HOST") == "database"
    assert _classify_key("POSTGRES_PASSWORD") == "database"


def test_classify_key_cache():
    assert _classify_key("REDIS_URL") == "cache"
    assert _classify_key("CACHE_TTL") == "cache"


def test_classify_key_cloud():
    assert _classify_key("AWS_ACCESS_KEY_ID") == "cloud"
    assert _classify_key("GCP_PROJECT") == "cloud"
    assert _classify_key("S3_BUCKET") == "cloud"


def test_classify_key_security():
    assert _classify_key("SECRET_KEY") == "security"
    assert _classify_key("API_KEY") == "security"
    assert _classify_key("AUTH_TOKEN") == "security"


def test_classify_key_network():
    assert _classify_key("PORT") == "network"
    assert _classify_key("APP_HOST") == "network"
    assert _classify_key("BASE_URL") == "network"


def test_classify_key_logging():
    assert _classify_key("LOG_LEVEL") == "logging"
    assert _classify_key("DEBUG") == "logging"


def test_classify_key_email():
    assert _classify_key("SMTP_HOST") == "email"
    assert _classify_key("EMAIL_FROM") == "email"


def test_classify_key_feature_flag():
    assert _classify_key("FEATURE_DARK_MODE") == "feature_flag"
    assert _classify_key("ENABLE_SIGNUP") == "feature_flag"


def test_classify_key_uncategorized():
    assert _classify_key("APP_NAME") == "uncategorized"
    assert _classify_key("VERSION") == "uncategorized"


def test_classify_env_groups_correctly():
    pairs = {
        "DB_HOST": "localhost",
        "REDIS_URL": "redis://localhost",
        "APP_NAME": "myapp",
        "SECRET_KEY": "abc123",
    }
    result = classify_env(pairs)
    assert "DB_HOST" in result.categories["database"]
    assert "REDIS_URL" in result.categories["cache"]
    assert "SECRET_KEY" in result.categories["security"]
    assert "APP_NAME" in result.categories["uncategorized"]


def test_classify_env_empty():
    result = classify_env({})
    assert result.categories == {}
    assert str(result) == "(no keys)"


def test_classify_result_category_of():
    pairs = {"PORT": "8080", "APP_NAME": "x"}
    result = classify_env(pairs)
    assert result.category_of("PORT") == "network"
    assert result.category_of("APP_NAME") == "uncategorized"
    assert result.category_of("NONEXISTENT") == "uncategorized"


def test_classify_result_str_sorted():
    pairs = {"PORT": "8080", "DB_HOST": "localhost"}
    result = classify_env(pairs)
    output = str(result)
    assert "[database]" in output
    assert "[network]" in output
    db_pos = output.index("[database]")
    net_pos = output.index("[network]")
    assert db_pos < net_pos
