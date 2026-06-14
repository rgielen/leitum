"""Integration tests using fake claude binary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run_leitum(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    import os

    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "leitum", *args],
        capture_output=True,
        text=True,
        env=full_env,
    )


class TestDryRun:
    def test_dry_run_outputs_env_and_exec(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key-123")
        result = _run_leitum(
            "--dry-run",
            "-p",
            "requesty",
            "-m",
            "anthropic/claude-sonnet-4-5",
            "claude",
            env={"REQUESTY_API_KEY": "test-key-123"},
        )
        assert result.returncode == 0
        assert "ANTHROPIC_BASE_URL" in result.stdout
        assert "***redacted***" in result.stdout
        assert "claude" in result.stdout

    def test_dry_run_no_claude_binary_needed(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.setenv("REQUESTY_API_KEY", "k")
        result = _run_leitum(
            "--dry-run",
            "-p",
            "requesty",
            "-m",
            "anthropic/claude-sonnet-4-5",
            "claude",
            env={"REQUESTY_API_KEY": "k"},
        )
        # Dry-run should not fail because claude binary is missing
        assert result.returncode == 0


class TestMissingConfig:
    def test_no_config_exits_3(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
    ):
        result = _run_leitum("-p", "requesty", "claude")
        assert result.returncode == 3

    def test_unknown_provider_exits_2_or_3(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.setenv("REQUESTY_API_KEY", "k")
        result = _run_leitum(
            "-p",
            "nonexistent-provider",
            "--dry-run",
            "claude",
            env={"REQUESTY_API_KEY": "k"},
        )
        assert result.returncode in (2, 3)


class TestInitCommand:
    def test_init_creates_config(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
    ):
        cfg = tmp_config_dir / "api-providers.yaml"
        cfg.unlink(missing_ok=True)
        result = _run_leitum("init")
        assert result.returncode == 0
        assert cfg.exists()

    def test_init_idempotent(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
    ):
        result = _run_leitum("init")
        assert result.returncode == 0
        # Should not overwrite
        assert "already exists" in result.stdout


class TestFakeClaude:
    def test_env_passed_to_claude(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
        fake_claude: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        import os

        monkeypatch.setenv("REQUESTY_API_KEY", "my-secret-key")
        env = dict(os.environ)
        env["REQUESTY_API_KEY"] = "my-secret-key"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "leitum",
                "-p",
                "requesty",
                "-m",
                "anthropic/claude-sonnet-4-5",
                "claude",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["env"]["ANTHROPIC_BASE_URL"] == "https://router.requesty.ai"
        assert data["env"]["ANTHROPIC_AUTH_TOKEN"] == "my-secret-key"
        assert "ANTHROPIC_API_KEY" not in data["env"]

    def test_passthrough_args_forwarded(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
        fake_claude: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        import os

        monkeypatch.setenv("REQUESTY_API_KEY", "k")
        env = dict(os.environ)
        env["REQUESTY_API_KEY"] = "k"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "leitum",
                "-p",
                "requesty",
                "-m",
                "anthropic/claude-sonnet-4-5",
                "claude",
                "--resume",
                "--verbose",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "--resume" in data["argv"]
        assert "--verbose" in data["argv"]
