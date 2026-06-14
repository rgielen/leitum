"""Shared pytest fixtures."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temp config dir wired via XDG_CONFIG_HOME."""
    config_base = tmp_path / "config"
    config_base.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_base))
    leitum_dir = config_base / "leitum"
    leitum_dir.mkdir()
    leitum_dir.chmod(0o700)
    return leitum_dir


@pytest.fixture()
def tmp_state_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temp state dir wired via XDG_STATE_HOME."""
    state_base = tmp_path / "state"
    state_base.mkdir()
    monkeypatch.setenv("XDG_STATE_HOME", str(state_base))
    leitum_dir = state_base / "leitum"
    leitum_dir.mkdir()
    leitum_dir.chmod(0o700)
    return leitum_dir


@pytest.fixture()
def tmp_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temp cache dir wired via XDG_CACHE_HOME."""
    cache_base = tmp_path / "cache"
    cache_base.mkdir()
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_base))
    leitum_dir = cache_base / "leitum"
    leitum_dir.mkdir()
    leitum_dir.chmod(0o700)
    return leitum_dir


@pytest.fixture()
def fake_claude(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Executable 'claude' script that dumps argv+env as JSON to stdout."""
    bin_dir = tmp_path / "fake_bin"
    bin_dir.mkdir()
    script = bin_dir / "claude"
    script.write_text(
        textwrap.dedent("""\
            #!/usr/bin/env python3
            import json, os, sys
            print(json.dumps({"argv": sys.argv, "env": dict(os.environ)}))
        """)
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + ":" + os.environ.get("PATH", ""))
    return script


@pytest.fixture()
def requesty_provider_dict() -> dict:
    return {
        "name": "requesty",
        "base_url": "https://router.requesty.ai",
        "auth": {
            "token": "${REQUESTY_API_KEY}",
        },
        "models": [
            {
                "id": "anthropic/claude-sonnet-4-5",
                "display": "Sonnet 4.5",
                "roles": ["sonnet", "start"],
            },  # noqa: E501
            {"id": "anthropic/claude-opus-4-5", "display": "Opus 4.5", "roles": ["opus"]},
            {"id": "anthropic/claude-haiku-4-5", "display": "Haiku 4.5", "roles": ["haiku"]},
        ],
    }


@pytest.fixture()
def minimal_providers_yaml(tmp_config_dir: Path, requesty_provider_dict: dict) -> Path:
    """Write a minimal api-providers.yaml and return its path."""
    from io import StringIO

    from ruamel.yaml import YAML

    y = YAML()
    doc = {
        "schema_version": 1,
        "providers": [requesty_provider_dict],
    }
    buf = StringIO()
    y.dump(doc, buf)
    p = tmp_config_dir / "api-providers.yaml"
    p.write_text(buf.getvalue())
    p.chmod(0o600)
    return p


@pytest.fixture()
def frozen_now(freezer):  # type: ignore[no-untyped-def]
    """Freeze time at a reproducible point (requires freezegun)."""
    return freezer
