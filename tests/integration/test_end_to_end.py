"""Integration tests using fake claude binary."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest


def _run_leitum(
    *args: str, env: dict | None = None, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    import os

    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "leitum", *args],
        capture_output=True,
        text=True,
        env=full_env,
        cwd=str(cwd) if cwd is not None else None,
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


class TestSaveLocal:
    def test_save_local_writes_leitum_yaml_and_skips_state(
        self,
        tmp_path: Path,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
        fake_claude: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from leitum.config.paths import state_path

        work = tmp_path / "work"
        work.mkdir()
        result = _run_leitum(
            "-l",
            "-p",
            "requesty",
            "-m",
            "anthropic/claude-sonnet-4-5",
            "claude",
            env={"REQUESTY_API_KEY": "my-secret-key"},
            cwd=work,
        )
        assert result.returncode == 0

        written = work / "leitum.yaml"
        assert written.exists(), "--save-local must write leitum.yaml in the cwd"
        text = written.read_text(encoding="utf-8")
        assert "provider: requesty" in text
        assert "anthropic/claude-sonnet-4-5" in text
        # The selection file must never carry the token.
        assert "my-secret-key" not in text

        assert not state_path().exists(), "--save-local must not write global state"

    def test_save_local_target_project_config_path(
        self,
        tmp_path: Path,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
        fake_claude: Path,
    ) -> None:
        work = tmp_path / "work"
        work.mkdir()
        alt = work / "custom.yaml"
        result = _run_leitum(
            "-l",
            "--project-config",
            str(alt),
            "-p",
            "requesty",
            "-m",
            "anthropic/claude-sonnet-4-5",
            "claude",
            env={"REQUESTY_API_KEY": "k"},
            cwd=work,
        )
        assert result.returncode == 0
        assert alt.exists()
        assert not (work / "leitum.yaml").exists()

    def test_save_local_with_no_project_config_exits_2(
        self,
        tmp_path: Path,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
    ) -> None:
        work = tmp_path / "work"
        work.mkdir()
        result = _run_leitum(
            "-l",
            "--no-project-config",
            "-p",
            "requesty",
            "claude",
            env={"REQUESTY_API_KEY": "k"},
            cwd=work,
        )
        assert result.returncode == 2

    def test_dry_run_save_local_writes_nothing(
        self,
        tmp_path: Path,
        tmp_config_dir: Path,
        tmp_state_dir: Path,
        minimal_providers_yaml: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from leitum.config.paths import state_path

        work = tmp_path / "work"
        work.mkdir()
        result = _run_leitum(
            "--dry-run",
            "-l",
            "-p",
            "requesty",
            "-m",
            "anthropic/claude-sonnet-4-5",
            "claude",
            env={"REQUESTY_API_KEY": "k"},
            cwd=work,
        )
        assert result.returncode == 0
        assert not (work / "leitum.yaml").exists(), "dry-run --save-local must not write"
        assert not state_path().exists()


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
