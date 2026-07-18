"""Tests for clean_env, which guards against unset/placeholder env values."""

from postgres_mcp.server import clean_env


def test_returns_value_when_set(monkeypatch):
    monkeypatch.setenv("POSTGRES_DATABASES", '{"a": "postgresql://u:p@host/db"}')
    assert clean_env("POSTGRES_DATABASES") == '{"a": "postgresql://u:p@host/db"}'


def test_missing_returns_none(monkeypatch):
    monkeypatch.delenv("POSTGRES_DATABASES", raising=False)
    assert clean_env("POSTGRES_DATABASES") is None


def test_empty_string_returns_none(monkeypatch):
    monkeypatch.setenv("POSTGRES_DATABASES", "")
    assert clean_env("POSTGRES_DATABASES") is None


def test_whitespace_returns_none(monkeypatch):
    monkeypatch.setenv("POSTGRES_DATABASES", "   ")
    assert clean_env("POSTGRES_DATABASES") is None


def test_unexpanded_placeholder_returns_none(monkeypatch):
    # Claude Code plugin .mcp.json substitutes ${VAR} with the literal string
    # when the variable is not defined in the environment.
    monkeypatch.setenv("POSTGRES_DATABASES", "${POSTGRES_DATABASES}")
    assert clean_env("POSTGRES_DATABASES") is None


def test_placeholder_with_surrounding_whitespace_returns_none(monkeypatch):
    monkeypatch.setenv("POSTGRES_DATABASE_URI", "  ${POSTGRES_DATABASE_URI}  ")
    assert clean_env("POSTGRES_DATABASE_URI") is None
