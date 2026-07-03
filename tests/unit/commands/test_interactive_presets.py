"""Unit tests for the interactive preset flow in provider add."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ruamel.yaml import YAML


def test_provider_add_interactive_preset_flow(tmp_config_dir: Path) -> None:
    path = tmp_config_dir / "api-providers.yaml"
    y = YAML()
    y.dump(
        {
            "schema_version": 1,
            "providers": [
                {
                    "name": "existing",
                    "base_url": "https://existing.example",
                    "auth": {"token": "dummy"},
                }
            ],
        },
        path,
    )

    # Mock questionary inputs to select the "ollama" preset and fill name/base_url/token
    from leitum.commands.provider import run_provider_add

    # We mock the following interactions:
    # 1. Select provider type -> "ollama"
    # 2. Text: name -> "my-ollama"
    # 3. Text: base_url -> "http://localhost:11434"
    # 4. Text: token -> "my-ollama-token"
    # 5. Confirm: Test the provider now? -> False

    with (
        patch("questionary.select") as mock_select,
        patch("questionary.text") as mock_text,
        patch("questionary.confirm") as mock_confirm,
    ):
        # Chain of .ask() for select
        mock_select.return_value.ask.side_effect = ["ollama"]
        # Chain of .ask() for text
        mock_text.return_value.ask.side_effect = [
            "my-ollama",
            "http://localhost:11434",
            "my-ollama-token",
        ]
        # Chain of .ask() for confirm
        mock_confirm.return_value.ask.return_value = False

        run_provider_add()

    with path.open("r", encoding="utf-8") as f:
        doc = y.load(f)

    assert len(doc["providers"]) == 2
    prov = doc["providers"][1]
    assert prov["name"] == "my-ollama"
    assert prov["base_url"] == "http://localhost:11434"
    assert prov["auth"]["token"] == "my-ollama-token"
    assert prov["extra_env"]["OLLAMA_CONTEXT_LENGTH"] == "32768"


def test_provider_add_interactive_custom_flow(tmp_config_dir: Path) -> None:
    path = tmp_config_dir / "api-providers.yaml"
    y = YAML()
    y.dump(
        {
            "schema_version": 1,
            "providers": [
                {
                    "name": "existing",
                    "base_url": "https://existing.example",
                    "auth": {"token": "dummy"},
                }
            ],
        },
        path,
    )

    from leitum.commands.provider import run_provider_add

    # Mock the custom manual flow:
    # 1. Select provider type -> "custom"
    # 2. Text: name -> "custom-prov"
    # 3. Text: base_url -> "https://custom.example"
    # 4. Select: Token source -> "env"
    # 5. Text: Environment variable name -> "CUSTOM_PROV_API_KEY"
    # 6. Select: Auth environment variable name -> "ANTHROPIC_AUTH_TOKEN"
    # 7. Confirm: Test the provider now? -> False

    with (
        patch("questionary.select") as mock_select,
        patch("questionary.text") as mock_text,
        patch("questionary.confirm") as mock_confirm,
    ):
        mock_select.return_value.ask.side_effect = ["custom", "env", "ANTHROPIC_AUTH_TOKEN"]
        mock_text.return_value.ask.side_effect = [
            "custom-prov",
            "https://custom.example",
            "CUSTOM_PROV_API_KEY",
        ]
        mock_confirm.return_value.ask.return_value = False

        run_provider_add()

    with path.open("r", encoding="utf-8") as f:
        doc = y.load(f)

    assert len(doc["providers"]) == 2
    prov = doc["providers"][1]
    assert prov["name"] == "custom-prov"
    assert prov["base_url"] == "https://custom.example"
    assert prov["auth"]["token"] == "${CUSTOM_PROV_API_KEY}"
    assert "env_var" not in prov["auth"]
