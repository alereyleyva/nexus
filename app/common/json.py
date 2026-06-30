from __future__ import annotations

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


def json_object(value: JsonObject | None = None) -> JsonObject:
    return {} if value is None else dict(value)
