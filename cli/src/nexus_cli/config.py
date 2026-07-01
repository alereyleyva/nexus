from __future__ import annotations

import os
from typing import Final

DEFAULT_API_URL: Final = "http://localhost:8000"

DEFAULT_CAPABILITIES: Final = [
    "memory:create",
    "memory:read",
    "memory:update",
    "search:read",
    "context_pack:generate",
]


def resolve_api_url() -> str:
    return os.environ.get("NEXUS_API_URL", DEFAULT_API_URL).rstrip("/")
