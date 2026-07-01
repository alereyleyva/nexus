from __future__ import annotations

from pathlib import Path

import pytest

from nexus_cli.cli import main
from nexus_cli.config import (
    DEFAULT_API_URL,
    load_config,
    resolve_api_url,
    resolve_setting,
    save_config,
)


def test_save_and_load_round_trips(config_file: Path) -> None:
    _ = config_file
    save_config({"api_url": "https://api.prod", "source_tool": "codex"})
    assert load_config() == {"api_url": "https://api.prod", "source_tool": "codex"}


def test_load_drops_unknown_keys(config_file: Path) -> None:
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text('{"api_url": "https://api.prod", "bogus": "x"}', encoding="utf-8")
    assert load_config() == {"api_url": "https://api.prod"}


def test_resolve_api_url_precedence(config_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = config_file
    save_config({"api_url": "https://from-config"})

    # config file when no override/env
    assert resolve_api_url() == "https://from-config"
    # environment beats config
    monkeypatch.setenv("NEXUS_API_URL", "https://from-env/")
    assert resolve_api_url() == "https://from-env"
    # explicit flag beats everything, and trailing slashes are trimmed
    assert resolve_api_url("https://from-flag/") == "https://from-flag"


def test_resolve_api_url_default_when_unset(config_file: Path) -> None:
    _ = config_file
    assert resolve_api_url() == DEFAULT_API_URL


def test_resolve_setting_without_env_uses_config(config_file: Path) -> None:
    _ = config_file
    save_config({"source_tool": "codex"})
    assert resolve_setting("source_tool") == "codex"
    assert resolve_setting("source_tool", "override") == "override"
    assert resolve_setting("default_project") is None


def test_cli_config_set_get_unset(config_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _ = config_file
    assert main(["config", "set", "api_url", "https://api.prod"]) == 0
    assert load_config()["api_url"] == "https://api.prod"

    capsys.readouterr()
    assert main(["config", "get", "api_url"]) == 0
    assert capsys.readouterr().out.strip() == "https://api.prod"

    assert main(["config", "unset", "api_url"]) == 0
    assert "api_url" not in load_config()


def test_cli_config_rejects_unknown_key(
    config_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _ = config_file
    assert main(["config", "set", "apiurl", "https://api.prod"]) == 2
    assert "unknown config key" in capsys.readouterr().err


def test_cli_config_list_without_values(
    config_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _ = config_file
    assert main(["config"]) == 0
    assert "(no values set)" in capsys.readouterr().out
