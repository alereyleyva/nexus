from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from nexus_cli.http import Response


@dataclass
class Call:
    method: str
    url: str
    headers: dict[str, str]
    body: object


@dataclass
class ScriptedTransport:
    _scripts: dict[str, list[Response]] = field(default_factory=dict)
    calls: list[Call] = field(default_factory=list)

    def add(self, path_contains: str, status: int, body: object) -> ScriptedTransport:
        self._scripts.setdefault(path_contains, []).append(Response(status=status, body=body))
        return self

    def __call__(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | object,
        json_body: object,
    ) -> Response:
        header_map = dict(headers) if isinstance(headers, dict) else {}
        self.calls.append(Call(method=method, url=url, headers=header_map, body=json_body))
        for key, responses in self._scripts.items():
            if key in url and responses:
                return responses.pop(0)
        raise AssertionError(f"No scripted response for {method} {url}")


@pytest.fixture
def transport() -> ScriptedTransport:
    return ScriptedTransport()


@pytest.fixture
def creds_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "credentials.json"
    monkeypatch.setenv("NEXUS_CREDENTIALS_FILE", str(path))
    return path
