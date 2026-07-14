"""Tests for the POSTGRES_CONFIG_FILE loader."""

import pytest

from postgres_mcp.config_file import ConnectionFile
from postgres_mcp.config_file import load_connection_file
from postgres_mcp.config_file import resolve_config_path


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_loads_yaml(tmp_path):
    path = _write(
        tmp_path,
        "connections.yaml",
        """
default: prod
connections:
  prod: postgresql://u:p@host/prod
  analytics: postgresql://u:p@host2/analytics
""",
    )
    result = load_connection_file(path)
    assert isinstance(result, ConnectionFile)
    assert result.default == "prod"
    assert result.connections == {
        "prod": "postgresql://u:p@host/prod",
        "analytics": "postgresql://u:p@host2/analytics",
    }


def test_loads_json(tmp_path):
    path = _write(
        tmp_path,
        "connections.json",
        '{"connections": {"only": "postgresql://u:p@host/db"}}',
    )
    result = load_connection_file(path)
    assert result.default is None
    assert result.connections == {"only": "postgresql://u:p@host/db"}


def test_missing_file_raises(tmp_path):
    with pytest.raises(ValueError, match="Could not read POSTGRES_CONFIG_FILE"):
        load_connection_file(str(tmp_path / "nope.yaml"))


def test_invalid_yaml_raises(tmp_path):
    path = _write(tmp_path, "bad.yaml", "connections: [unclosed")
    with pytest.raises(ValueError, match="not valid JSON/YAML"):
        load_connection_file(path)


def test_missing_connections_key_raises(tmp_path):
    path = _write(tmp_path, "c.yaml", "default: prod\n")
    with pytest.raises(ValueError, match='non-empty "connections" mapping'):
        load_connection_file(path)


def test_empty_connections_raises(tmp_path):
    path = _write(tmp_path, "c.yaml", "connections: {}\n")
    with pytest.raises(ValueError, match='non-empty "connections" mapping'):
        load_connection_file(path)


def test_non_string_url_raises(tmp_path):
    path = _write(tmp_path, "c.yaml", "connections:\n  prod: 12345\n")
    with pytest.raises(ValueError, match="must map to a connection URI string"):
        load_connection_file(path)


def test_default_not_in_connections_raises(tmp_path):
    path = _write(
        tmp_path,
        "c.yaml",
        "default: missing\nconnections:\n  prod: postgresql://u:p@host/db\n",
    )
    with pytest.raises(ValueError, match="not one of the defined connections"):
        load_connection_file(path)


def test_top_level_not_mapping_raises(tmp_path):
    path = _write(tmp_path, "c.yaml", "- just\n- a\n- list\n")
    with pytest.raises(ValueError, match='must be a mapping with a "connections" key'):
        load_connection_file(path)


def test_resolve_expands_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    resolved = resolve_config_path("~/connections.yaml")
    assert resolved.endswith("connections.yaml")
    assert "~" not in resolved
