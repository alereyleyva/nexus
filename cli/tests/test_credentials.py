from __future__ import annotations

import stat
from pathlib import Path

from nexus_cli.credentials import (
    Credentials,
    clear_credentials,
    load_credentials,
    save_credentials,
)

_SAMPLE = Credentials(
    api_url="http://localhost:8000",
    refresh_token="nxs_rt_secret",
    session_id="11111111-1111-4111-8111-111111111111",
    org_id="22222222-2222-4222-8222-222222222222",
    user_id="33333333-3333-4333-8333-333333333333",
)


def test_save_then_load_round_trips(creds_file: Path) -> None:
    assert not creds_file.exists()
    save_credentials(_SAMPLE)
    assert load_credentials() == _SAMPLE


def test_saved_file_is_owner_only(creds_file: Path) -> None:
    save_credentials(_SAMPLE)
    mode = stat.S_IMODE(creds_file.stat().st_mode)
    assert mode == 0o600


def test_load_missing_returns_none(creds_file: Path) -> None:
    assert not creds_file.exists()
    assert load_credentials() is None


def test_load_malformed_returns_none(creds_file: Path) -> None:
    creds_file.parent.mkdir(parents=True, exist_ok=True)
    creds_file.write_text("{not json", encoding="utf-8")
    assert load_credentials() is None


def test_clear_removes_file(creds_file: Path) -> None:
    save_credentials(_SAMPLE)
    clear_credentials()
    assert not creds_file.exists()
    clear_credentials()  # idempotent
