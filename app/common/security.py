from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Final, cast

from app.common.json import JsonObject, JsonValue
from app.common.time import utc_now

_JWT_HEADER: Final[JsonObject] = {"alg": "HS256", "typ": "JWT"}


def generate_token(prefix: str, *, bytes_count: int = 32) -> str:
    return f"{prefix}_{secrets.token_urlsafe(bytes_count)}"


def hash_secret(value: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"sha256:{digest}"


def hash_text(value: str) -> str:
    digest = hashlib.sha256(value.encode()).hexdigest()
    return f"sha256:{digest}"


def encode_access_token(claims: JsonObject, secret: str) -> str:
    header = _base64_json(_JWT_HEADER)
    payload = _base64_json(claims)
    signature = _sign(f"{header}.{payload}", secret)
    return f"{header}.{payload}.{signature}"


def decode_access_token(token: str, secret: str) -> JsonObject | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    signing_input = f"{parts[0]}.{parts[1]}"
    expected_signature = _sign(signing_input, secret)
    if not hmac.compare_digest(expected_signature, parts[2]):
        return None
    payload = _decode_json(parts[1])
    if payload is None:
        return None
    exp = payload.get("exp")
    if (
        not isinstance(exp, int | float)
        or datetime.fromtimestamp(exp, tz=utc_now().tzinfo) <= utc_now()
    ):
        return None
    return payload


def _base64_json(value: JsonObject) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return _base64url(raw)


def _decode_json(value: str) -> JsonObject | None:
    try:
        raw = base64.urlsafe_b64decode(_pad_base64(value))
        decoded: object = json.loads(raw.decode())
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(decoded, dict):
        return None
    mapping = cast(Mapping[object, object], decoded)
    return {str(key): _json_value(item) for key, item in mapping.items()}


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list):
        sequence = cast(Sequence[object], value)
        return [_json_value(item) for item in sequence]
    if isinstance(value, dict):
        mapping = cast(Mapping[object, object], value)
        return {str(key): _json_value(item) for key, item in mapping.items()}
    return str(value)


def _sign(value: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), value.encode(), hashlib.sha256).digest()
    return _base64url(digest)


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _pad_base64(value: str) -> bytes:
    return f"{value}{'=' * (-len(value) % 4)}".encode()
