from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Final, cast

DEFAULT_API_URL: Final = "http://localhost:8000"

DEFAULT_CAPABILITIES: Final = [
    "memory:create",
    "memory:read",
    "memory:update",
    "search:read",
    "context_pack:generate",
]

# User-configurable keys stored in config.json. Values are plain strings.
KNOWN_KEYS: Final = ("api_url", "source_tool", "default_project")

# Keys that also accept an environment override, and the variable that provides it.
_ENV_OVERRIDES: Final = {"api_url": "NEXUS_API_URL"}


def config_path() -> Path:
    override = os.environ.get("NEXUS_CONFIG_FILE")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CONFIG_HOME")
    root = Path(base) if base else Path.home() / ".config"
    return root / "nexus" / "config.json"


def load_config() -> dict[str, str]:
    path = config_path()
    if not path.exists():
        return {}
    try:
        raw = cast(object, json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(raw, Mapping):
        return {}
    data = cast(Mapping[str, object], raw)
    return {
        key: value for key, value in data.items() if key in KNOWN_KEYS and isinstance(value, str)
    }


def save_config(config: Mapping[str, str]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(config), indent=2, sort_keys=True), encoding="utf-8")


def resolve_setting(key: str, override: str | None = None) -> str | None:
    """Resolve a value by precedence: flag > environment > config file > None."""
    if override:
        return override
    env_name = _ENV_OVERRIDES.get(key)
    if env_name:
        env_value = os.environ.get(env_name)
        if env_value:
            return env_value
    return load_config().get(key)


def resolve_api_url(override: str | None = None) -> str:
    value = resolve_setting("api_url", override) or DEFAULT_API_URL
    return value.rstrip("/")
