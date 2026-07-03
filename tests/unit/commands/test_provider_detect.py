"""Unit tests for leitum provider detect."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import respx
from httpx import Response
from ruamel.yaml import YAML

from leitum.commands.provider import run_provider_detect


def test_provider_detect_none_found(tmp_config_dir: Path) -> None:
    # Use respx to mock requests failing/timing out
    with respx.mock:
        # All requests to localhost ports should fail
        respx.get(url__regex=r"http://localhost:.*").mock(side_effect=Exception("Connection refused"))

        with patch("sys.stdout") as mock_stdout:
            # We don't have configuration here, but detect should still handle it or we can pass a mocked config
            from leitum.config.models import ProvidersConfig
            config = ProvidersConfig(
                schema_version=1,
                providers=[
                    {
                        "name": "existing",
                        "base_url": "https://existing.example",
                        "auth": {"token": "dummy"},
                    }
                ]
            )
            run_provider_detect(json_output=False, config=config)

            # Let's verify stdout calls
            # "No local server is running on the known ports." should be printed
            stdout_calls = "".join(call[0][0] for call in mock_stdout.write.call_args_list)
            assert "No local server is running on the known ports." in stdout_calls


def test_provider_detect_json(tmp_config_dir: Path) -> None:
    with respx.mock:
        # Mock Ollama port returning 200 with 2 models
        respx.get("http://localhost:11434/v1/models").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {"id": "llama3:latest", "name": "llama3:latest"},
                        {"id": "mistral:latest", "name": "mistral:latest"},
                    ]
                },
            )
        )
        # All other ports fail
        respx.get(url__regex=r"http://localhost:(?!11434).*").mock(side_effect=Exception("Refused"))

        with patch("sys.stdout") as mock_stdout:
            run_provider_detect(json_output=True)

            stdout_calls = "".join(call[0][0] for call in mock_stdout.write.call_args_list)
            data = json.loads(stdout_calls)
            assert len(data) == 1
            assert data[0]["key"] == "ollama"
            assert data[0]["model_count"] == 2
            assert data[0]["base_url"] == "http://localhost:11434"


def test_provider_detect_add_flow(tmp_config_dir: Path) -> None:
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

    with respx.mock:
        # Mock Ollama returning 200
        respx.get("http://localhost:11434/v1/models").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {"id": "llama3:latest"},
                    ]
                },
            )
        )
        respx.get(url__regex=r"http://localhost:(?!11434).*").mock(side_effect=Exception("Refused"))

        # We mock questionary checkboxes/confirms:
        # 1. checkbox selection: we select the first (and only) detected server
        # 2. confirm to pin models: True
        with (
            patch("questionary.checkbox") as mock_checkbox,
            patch("questionary.confirm") as mock_confirm,
        ):
            # Create a mock ask that returns the first choice's value
            mock_ask = MagicMock()
            mock_checkbox.return_value.ask = mock_ask

            # Since choices is a keyword argument or positional, let's extract it from mock call
            def side_effect():
                choices = mock_checkbox.call_args[1].get("choices") or mock_checkbox.call_args[0][1]
                return [choices[0].value]

            mock_ask.side_effect = side_effect
            mock_confirm.return_value.ask.return_value = True

            run_provider_detect(json_output=False)

    with path.open("r", encoding="utf-8") as f:
        doc = y.load(f)

    assert len(doc["providers"]) == 2
    prov = doc["providers"][1]
    assert prov["name"] == "ollama"
    assert prov["base_url"] == "http://localhost:11434"
    assert prov["auth"]["token"] == "ollama"
    assert len(prov["models"]) == 1
    assert prov["models"][0]["id"] == "llama3:latest"
