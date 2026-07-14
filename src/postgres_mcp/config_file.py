"""Loader for the optional POSTGRES_CONFIG_FILE connections file.

A single ``POSTGRES_CONFIG_FILE`` env var may point at a JSON or YAML file that
describes multiple named connections, as a cleaner alternative to cramming a
JSON map into the ``POSTGRES_DATABASES`` env var. The file is a real file, so it
allows comments (in YAML), avoids JSON-in-a-string escaping, and can live
outside your committed MCP client config.

The file shape is::

    default: prod            # optional; name of the default connection
    connections:
      prod:      postgresql://user:pw@host/prod
      analytics: postgresql://user:pw@host2/analytics

Every failure raises a clear, path-qualified error so misconfiguration surfaces
at startup rather than on the first query.
"""

import json
import os
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import yaml


@dataclass
class ConnectionFile:
    """Parsed and validated contents of a POSTGRES_CONFIG_FILE."""

    connections: dict[str, str]
    default: str | None = field(default=None)


def resolve_config_path(path: str) -> str:
    """Expand a leading ``~`` and resolve a relative path against the CWD."""
    expanded = os.path.expanduser(path)
    return str(Path(expanded).resolve())


def load_connection_file(path: str) -> ConnectionFile:
    """Read, parse (JSON or YAML) and validate the connections config file.

    Raises ValueError with a path-qualified message on any failure.
    """
    resolved = resolve_config_path(path)

    try:
        text = Path(resolved).read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError(f'Could not read POSTGRES_CONFIG_FILE at "{resolved}": {e}') from e

    try:
        # JSON is a subset of YAML, so yaml.safe_load parses both formats.
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ValueError(f'POSTGRES_CONFIG_FILE ("{resolved}") is not valid JSON/YAML: {e}') from e

    if not isinstance(data, dict):
        raise ValueError(f'POSTGRES_CONFIG_FILE ("{resolved}") must be a mapping with a "connections" key.')

    connections = data.get("connections")
    if not isinstance(connections, dict) or not connections:
        raise ValueError(f'POSTGRES_CONFIG_FILE ("{resolved}") must define a non-empty "connections" mapping.')

    for name, url in connections.items():
        if not isinstance(name, str) or not name:
            raise ValueError(f'POSTGRES_CONFIG_FILE ("{resolved}"): connection names must be non-empty strings.')
        if not isinstance(url, str) or not url:
            raise ValueError(
                f'POSTGRES_CONFIG_FILE ("{resolved}"): connection "{name}" must map to a connection URI string.'
            )

    default = data.get("default")
    if default is not None:
        if not isinstance(default, str):
            raise ValueError(f'POSTGRES_CONFIG_FILE ("{resolved}"): "default" must be a string.')
        if default not in connections:
            raise ValueError(
                f'POSTGRES_CONFIG_FILE ("{resolved}"): "default" is "{default}", '
                f"which is not one of the defined connections: {sorted(connections)}."
            )

    return ConnectionFile(connections=dict(connections), default=default)
