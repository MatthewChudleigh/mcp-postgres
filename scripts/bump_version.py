#!/usr/bin/env python3
"""Bump the project version across pyproject.toml, uv.lock, and the plugin manifests."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
UV_LOCK = ROOT / "uv.lock"
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = ROOT / ".claude-plugin" / "marketplace.json"

PACKAGE_NAME = "postgres-mcp"
PLUGIN_NAME = "mcp-postgres"

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_version(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.match(value)
    if not match:
        raise ValueError(f"Invalid version: {value!r} (expected n.n.n)")
    return int(match[1]), int(match[2]), int(match[3])


def bump(current: str, part: str) -> str:
    major, minor, patch = parse_version(current)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown bump part: {part}")


def update_pyproject(new_version: str) -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    new_text, count = re.subn(
        r'(?m)^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError("Could not find version line in pyproject.toml")
    PYPROJECT.write_text(new_text, encoding="utf-8")
    return _extract_current(text)


def _extract_current(pyproject_text: str) -> str:
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject_text)
    if not match:
        raise RuntimeError("Could not read current version from pyproject.toml")
    return match[1]


def update_uv_lock(new_version: str) -> None:
    text = UV_LOCK.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(name\s*=\s*"' + re.escape(PACKAGE_NAME) + r'"\s*\nversion\s*=\s*")[^"]+(")'
    )
    new_text, count = pattern.subn(rf"\g<1>{new_version}\g<2>", text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not find {PACKAGE_NAME} entry in uv.lock")
    UV_LOCK.write_text(new_text, encoding="utf-8")


def update_plugin_json(new_version: str) -> None:
    data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    data["version"] = new_version
    PLUGIN_JSON.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def update_marketplace_json(new_version: str) -> None:
    text = MARKETPLACE_JSON.read_text(encoding="utf-8")
    data = json.loads(text)
    found = False
    for plugin in data.get("plugins", []):
        if plugin.get("name") == PLUGIN_NAME:
            plugin["version"] = new_version
            found = True
    if not found:
        raise RuntimeError(f"Could not find plugin {PLUGIN_NAME!r} in marketplace.json")
    MARKETPLACE_JSON.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--major", action="store_true", help="Bump the major version")
    group.add_argument("--minor", action="store_true", help="Bump the minor version")
    group.add_argument("--patch", action="store_true", help="Bump the patch version (default)")
    group.add_argument("--version", metavar="N.N.N", help="Set the version explicitly")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    current = _extract_current(PYPROJECT.read_text(encoding="utf-8"))

    if args.version:
        parse_version(args.version)
        new_version = args.version
    elif args.major:
        new_version = bump(current, "major")
    elif args.minor:
        new_version = bump(current, "minor")
    else:
        new_version = bump(current, "patch")

    update_pyproject(new_version)
    update_uv_lock(new_version)
    update_plugin_json(new_version)
    update_marketplace_json(new_version)

    print(f"Bumped version: {current} -> {new_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
