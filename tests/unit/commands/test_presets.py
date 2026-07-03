"""Tests for provider presets and add provider with presets."""

from __future__ import annotations

from pathlib import Path

import pytest
from ruamel.yaml import YAML

from leitum.providers.presets import PRESETS, get_preset


def test_presets_registry() -> None:
    assert len(PRESETS) >= 5
    ollama = get_preset("ollama")
    assert ollama is not None
    assert ollama.display == "Ollama (local)"
    assert ollama.default_name == "ollama"
    assert ollama.base_url == "http://localhost:11434"
    assert ollama.token == "ollama"
    assert ollama.is_local is True
    assert ollama.detect_ports == [11434]

    # Test deep copy mutation protection
    ollama.extra_env["OLLAMA_CONTEXT_LENGTH"] = "99999"
    ollama2 = get_preset("ollama")
    assert ollama2 is not None
    assert ollama2.extra_env["OLLAMA_CONTEXT_LENGTH"] == "32768"

    unknown = get_preset("unknown")
    assert unknown is None


def test_provider_add_with_preset_non_interactive(tmp_config_dir: Path) -> None:
    from leitum.commands.provider import run_provider_add

    # Create config with at least 1 provider because config validation requires min_length=1
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

    # Use ollama preset
    run_provider_add(preset="ollama")

    with path.open("r", encoding="utf-8") as f:
        doc = y.load(f)

    assert len(doc["providers"]) == 2
    prov = doc["providers"][1]
    assert prov["name"] == "ollama"
    assert prov["base_url"] == "http://localhost:11434"
    assert prov["auth"]["token"] == "ollama"
    assert "env_var" not in prov["auth"]
    assert prov["extra_env"]["OLLAMA_CONTEXT_LENGTH"] == "32768"


def test_provider_add_with_preset_invalid_preset(tmp_config_dir: Path) -> None:
    from leitum.commands.provider import run_provider_add

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

    with pytest.raises(SystemExit) as exc:
        run_provider_add(preset="invalid-preset")
    assert exc.value.code == 2


def test_provider_add_with_preset_invalid_name(tmp_config_dir: Path) -> None:
    from leitum.commands.provider import run_provider_add

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

    with pytest.raises(SystemExit) as exc:
        run_provider_add(preset="ollama", name="Ollama_Invalid")
    assert exc.value.code == 2


def test_provider_add_with_preset_duplicate_name(tmp_config_dir: Path) -> None:
    from leitum.commands.provider import run_provider_add

    path = tmp_config_dir / "api-providers.yaml"
    y = YAML()
    y.dump(
        {
            "schema_version": 1,
            "providers": [
                {
                    "name": "ollama",
                    "base_url": "http://localhost:11434",
                    "auth": {"token": "ollama"},
                }
            ],
        },
        path,
    )

    with pytest.raises(SystemExit) as exc:
        run_provider_add(preset="ollama")
    assert exc.value.code == 2
