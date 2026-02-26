"""Config management for LAM.

Storage: ~/.config/langzeitarchiv-manager/config.toml
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomli_w

CONFIG_DIR = Path.home() / ".config" / "langzeitarchiv-manager"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULTS: dict[str, Any] = {
    "pack": {
        "redundancy_percent": 15,
        "par2_volumes": 1,
        "output_dir": str(Path.home() / "LAM" / "staging"),
        "default_format": "tar",
    }
}


def _load_raw() -> dict[str, Any]:
    """Load the raw TOML config, returning an empty dict if the file doesn't exist."""
    if not CONFIG_FILE.exists():
        return {}
    with CONFIG_FILE.open("rb") as fh:
        return tomllib.load(fh)


def _save_raw(data: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("wb") as fh:
        tomli_w.dump(data, fh)


def _get_nested(data: dict[str, Any], key: str) -> Any:
    """Retrieve a value by dotted key (e.g. 'pack.redundancy_percent')."""
    parts = key.split(".")
    node: Any = data
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _set_nested(data: dict[str, Any], key: str, value: Any) -> None:
    """Set a value by dotted key, creating intermediate dicts as needed."""
    parts = key.split(".")
    node = data
    for part in parts[:-1]:
        if part not in node or not isinstance(node[part], dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value


def get(key: str) -> Any:
    """Return the value for *key*, falling back to the hard-coded default."""
    data = _load_raw()
    value = _get_nested(data, key)
    if value is None:
        value = _get_nested(DEFAULTS, key)
    return value


def set_value(key: str, raw_value: str) -> None:
    """Persist *raw_value* under *key*.

    Attempts to coerce the string to int or float when possible so that the
    TOML representation preserves the correct type.
    """
    data = _load_raw()
    # Type coercion: try int, then float, else keep as string
    coerced: Any = raw_value
    try:
        coerced = int(raw_value)
    except ValueError:
        try:
            coerced = float(raw_value)
        except ValueError:
            pass
    _set_nested(data, key, coerced)
    _save_raw(data)


def list_all() -> dict[str, Any]:
    """Return merged config (user settings on top of defaults)."""
    import copy

    merged: dict[str, Any] = copy.deepcopy(DEFAULTS)
    user = _load_raw()
    _deep_merge(merged, user)
    return merged


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
