"""Integration tests using fake claude binary."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
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

    def test_dry_run_does_not_create_state(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key-123")
        from leitum.config.paths import state_path

        assert not state_path().exists(), "pre-condition: state file must not exist"
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
        assert not state_path().exists(), "dry-run must not create state.yaml"

    def test_dry_run_does_not_mutate_existing_state(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key-123")
        from leitum.config.paths import state_path

        # Pre-write a state with a known provider/model
        state_file = state_path()
        original_content = (
            "schema_version: 1\n"
            "last_provider: other\n"
            "providers:\n"
            "  other:\n"
            "    models:\n"
            "      start: keep-me\n"
            "    last_used: '2025-01-01T00:00:00+00:00'\n"
        )
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(original_content, encoding="utf-8")
        state_file.chmod(0o600)
        original_mtime = state_file.stat().st_mtime

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
        assert state_file.read_text(encoding="utf-8") == original_content, (
            "dry-run must not change existing state file contents"
        )
        assert state_file.stat().st_mtime == original_mtime, (
            "dry-run must not touch (update mtime of) existing state file"
        )

    def test_dry_run_refresh_does_not_clear_cache(
        self,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        tmp_cache_dir: Path,
        minimal_providers_yaml: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key-123")
        from leitum.config.paths import model_cache_path

        # Pre-populate the model cache
        cache_file = model_cache_path("requesty")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        original_cache = json.dumps(
            {
                "schema_version": 1,
                "fetched_at": datetime.now(tz=UTC).isoformat(),
                "base_url": "https://router.requesty.ai",
                "models": [{"id": "anthropic/claude-sonnet-4-5", "display": None}],
            },
            indent=2,
        )
        cache_file.write_text(original_cache, encoding="utf-8")

        result = _run_leitum(
            "--dry-run",
            "--refresh",
            "-p",
            "requesty",
            "-m",
            "anthropic/claude-sonnet-4-5",
            "claude",
            env={"REQUESTY_API_KEY": "test-key-123"},
        )
        assert result.returncode == 0
        assert cache_file.exists(), "dry-run --refresh must not delete the cache file"
        assert cache_file.read_text(encoding="utf-8") == original_cache, (
            "dry-run --refresh must not modify the cache file"
        )


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
