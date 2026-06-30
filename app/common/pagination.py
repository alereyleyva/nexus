from __future__ import annotations

import base64
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from app.common.errors import BadRequestError
from app.common.json import JsonObject, JsonValue


class PageInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    next_cursor: str | None
    has_more: bool


@dataclass(frozen=True)
class Cursor:
    sort_values: list[str]
    filter_hash: str


class LimitParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=50, ge=1, le=100)
    cursor: str | None = None


def encode_cursor(cursor: Cursor) -> str:
    sort_values: list[JsonValue] = []
    sort_values.extend(cursor.sort_values)
    payload: JsonObject = {"v": 1, "k": sort_values, "f": cursor.filter_hash}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(value: str, *, expected_filter_hash: str) -> Cursor:
    try:
        raw = base64.urlsafe_b64decode(f"{value}{'=' * (-len(value) % 4)}")
        payload_object: object = json.loads(raw.decode())
    except (ValueError, json.JSONDecodeError) as exc:
        raise BadRequestError("Invalid cursor.") from exc
    if not isinstance(payload_object, dict):
        raise BadRequestError("Invalid cursor.")
    payload = cast(Mapping[str, object], payload_object)
    version = payload.get("v")
    sort_values = payload.get("k")
    filter_hash = payload.get("f")
    if version != 1 or not isinstance(sort_values, list) or not isinstance(filter_hash, str):
        raise BadRequestError("Invalid cursor.")
    if filter_hash != expected_filter_hash:
        raise BadRequestError("Cursor does not match the request filters.")
    sort_items = cast(Sequence[object], sort_values)
    return Cursor(sort_values=[str(item) for item in sort_items], filter_hash=filter_hash)


def page_from_items(item_count: int, limit: int, next_cursor: str | None) -> PageInfo:
    return PageInfo(next_cursor=next_cursor, has_more=item_count > limit)


def sort_direction(value: str) -> Literal["asc", "desc"]:
    return "asc" if value == "asc" else "desc"


def filter_hash(payload: JsonObject) -> str:
    normalized = json.dumps(_normalize_json(payload), separators=(",", ":"), sort_keys=True)
    return base64.urlsafe_b64encode(normalized.encode()).decode().rstrip("=")


def _normalize_json(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return {key: _normalize_json(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_normalize_json(item) for item in value]
    return value
