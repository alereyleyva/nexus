from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True)
class Credentials:
    api_url: str
    refresh_token: str
    session_id: str
    org_id: str
    user_id: str


def credentials_path() -> Path:
    override = os.environ.get("NEXUS_CREDENTIALS_FILE")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CONFIG_HOME")
    root = Path(base) if base else Path.home() / ".config"
    return root / "nexus" / "credentials.json"


def load_credentials() -> Credentials | None:
    path = credentials_path()
    if not path.exists():
        return None
    try:
        raw = cast(object, json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(raw, Mapping):
        return None
    data = cast(Mapping[str, object], raw)
    fields = ("api_url", "refresh_token", "session_id", "org_id", "user_id")
    if not all(isinstance(data.get(field), str) for field in fields):
        return None
    return Credentials(
        api_url=cast(str, data["api_url"]),
        refresh_token=cast(str, data["refresh_token"]),
        session_id=cast(str, data["session_id"]),
        org_id=cast(str, data["org_id"]),
        user_id=cast(str, data["user_id"]),
    )


def save_credentials(credentials: Credentials) -> None:
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Create/truncate with owner-only permissions before writing the refresh token.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(asdict(credentials), handle)
    # Re-assert owner-only perms in case the file pre-existed with a looser mode.
    path.chmod(0o600)


def clear_credentials() -> None:
    path = credentials_path()
    path.unlink(missing_ok=True)
