from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final

_TIMEOUT_SECONDS: Final = 30


class HttpError(Exception):
    """Raised when the transport cannot reach the API at all (network failure)."""


@dataclass(frozen=True)
class Response:
    status: int
    body: object


# A transport turns a request into a Response. Injecting it keeps the client testable.
Transport = Callable[[str, str, Mapping[str, str], object | None], Response]


def urllib_transport(
    method: str, url: str, headers: Mapping[str, str], json_body: object | None
) -> Response:
    data = None if json_body is None else json.dumps(json_body).encode()
    request_headers = dict(headers)
    if data is not None:
        request_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(  # noqa: S310 - API base URL is operator-configured.
        url, data=data, headers=request_headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # noqa: S310
            return Response(status=response.status, body=_read_json(response.read()))
    except urllib.error.HTTPError as error:
        return Response(status=error.code, body=_read_json(error.read()))
    except urllib.error.URLError as error:
        raise HttpError(f"Could not reach the Nexus API: {error.reason}") from error


def _read_json(raw: bytes) -> object:
    if not raw:
        return None
    try:
        return json.loads(raw.decode())
    except (ValueError, json.JSONDecodeError):
        return None
