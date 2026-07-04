"""Tests for dotenv loading in the leitum claude command."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from leitum.commands.claude import run_claude

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_run_claude_kwargs(**overrides: Any) -> dict[str, Any]:
    """Return a minimal valid kwargs dict for run_claude."""
    defaults: dict[str, Any] = {
        "pass_through": [],
        "provider_flag": "requesty",
        "use_last_provider": False,
        "model_flag": "anthropic/claude-sonnet-4-5",
        "use_last_model": False,
        "opus_flag": None,
        "use_last_opus": False,
        "sonnet_flag": None,
        "use_last_sonnet": False,
        "haiku_flag": None,
        "use_last_haiku": False,
        "refresh": False,
        "no_project_config": True,
        "project_config_path": None,
        "save_local": False,
        "dry_run": False,
        "verbose": False,
        "no_dotenv": False,
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDotenvInRunClaude:
    """Test dotenv loading behaviour in run_claude."""

    def test_dotenv_vars_injected_into_environ(
        self,
        tmp_path: Path,
        minimal_providers_yaml: Path,
        tmp_state_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Vars from .leitumenv in CWD are set in os.environ before exec."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".leitumenv").write_text("LEITUM_TEST_VAR=from_dotenv\n", encoding="utf-8")
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key")
        monkeypatch.delenv("LEITUM_TEST_VAR", raising=False)

        captured_env: dict[str, str] = {}

        def fake_exec(**kwargs: Any) -> None:
            captured_env.update(os.environ)

        with patch("leitum.commands.claude.exec_claude", side_effect=fake_exec):
            run_claude(**_make_run_claude_kwargs())

        assert captured_env.get("LEITUM_TEST_VAR") == "from_dotenv"

    def test_no_dotenv_flag_skips_loading(
        self,
        tmp_path: Path,
        minimal_providers_yaml: Path,
        tmp_state_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """With --no-dotenv, .leitumenv is ignored even if present."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".leitumenv").write_text("LEITUM_SKIP_ME=should_not_appear\n", encoding="utf-8")
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key")
        monkeypatch.delenv("LEITUM_SKIP_ME", raising=False)

        captured_env: dict[str, str] = {}

        def fake_exec(**kwargs: Any) -> None:
            captured_env.update(os.environ)

        with patch("leitum.commands.claude.exec_claude", side_effect=fake_exec):
            run_claude(**_make_run_claude_kwargs(no_dotenv=True))

        assert "LEITUM_SKIP_ME" not in captured_env

    def test_shell_env_takes_precedence_over_dotenv(
        self,
        tmp_path: Path,
        minimal_providers_yaml: Path,
        tmp_state_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Shell env var is not overwritten by .leitumenv."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".leitumenv").write_text("MY_VAR=from_dotenv\n", encoding="utf-8")
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key")
        monkeypatch.setenv("MY_VAR", "from_shell")

        captured_env: dict[str, str] = {}

        def fake_exec(**kwargs: Any) -> None:
            captured_env.update(os.environ)

        with patch("leitum.commands.claude.exec_claude", side_effect=fake_exec):
            run_claude(**_make_run_claude_kwargs())

        assert captured_env.get("MY_VAR") == "from_shell"

    def test_verbose_logs_set_keys(
        self,
        tmp_path: Path,
        minimal_providers_yaml: Path,
        tmp_state_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verbose mode logs which keys were actually set, not just found in file."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".leitumenv").write_text(
            "NEW_VAR=injected\nEXISTING_VAR=from_dotenv\n", encoding="utf-8"
        )
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key")
        monkeypatch.delenv("NEW_VAR", raising=False)
        monkeypatch.setenv("EXISTING_VAR", "from_shell")

        with patch("leitum.commands.claude.exec_claude"):
            run_claude(**_make_run_claude_kwargs(verbose=True))

        captured = capsys.readouterr()
        assert "NEW_VAR" in captured.err
        assert "EXISTING_VAR" not in captured.err  # was already in env, not set

    def test_missing_dotenv_causes_no_error(
        self,
        tmp_path: Path,
        minimal_providers_yaml: Path,
        tmp_state_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When .leitumenv is absent, run_claude proceeds without error."""
        monkeypatch.chdir(tmp_path)
        assert not (tmp_path / ".leitumenv").exists()
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key")

        with patch("leitum.commands.claude.exec_claude"):
            # Should not raise
            run_claude(**_make_run_claude_kwargs())


class TestEffectiveSaveLocal:
    """Tests for effective_save_local logic in run_claude."""

    def test_dialog_armed_saves_to_project_not_state(
        self,
        tmp_path: Path,
        minimal_providers_yaml: Path,
        tmp_state_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When dialog arms save_local, leitum.yaml is written and state is not."""
        from unittest.mock import patch

        from leitum.selection.resolver import ResolvedModels

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key")

        resolved = ResolvedModels(
            start="anthropic/claude-sonnet-4-5",
            save_local=True,
            dialog_shown=True,
        )

        saved_project_paths: list[Path] = []

        def _fake_save_project(path: Path, *, provider: str, models: dict[str, str]) -> None:
            saved_project_paths.append(path)

        with (
            patch("leitum.commands.claude.resolve_models", return_value=resolved),
            patch("leitum.commands.claude.exec_claude"),
            patch("leitum.commands.claude.save_project_config", side_effect=_fake_save_project),
            patch("leitum.commands.claude.save_state") as mock_save_state,
        ):
            run_claude(
                **_make_run_claude_kwargs(
                    no_project_config=False,
                    save_local=False,  # CLI flag NOT set, but dialog arms it
                )
            )

        assert len(saved_project_paths) == 1  # project was written
        mock_save_state.assert_not_called()  # global state was NOT written

    def test_no_dialog_uses_cli_flag_for_save(
        self,
        tmp_path: Path,
        minimal_providers_yaml: Path,
        tmp_state_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When no dialog ran, the CLI --save-local flag governs."""
        from unittest.mock import patch

        from leitum.selection.resolver import ResolvedModels

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key")

        resolved = ResolvedModels(
            start="anthropic/claude-sonnet-4-5",
            save_local=False,  # dialog was not shown, so this field is irrelevant
            dialog_shown=False,
        )

        saved_project_paths: list[Path] = []

        def _fake_save_project(path: Path, *, provider: str, models: dict[str, str]) -> None:
            saved_project_paths.append(path)

        with (
            patch("leitum.commands.claude.resolve_models", return_value=resolved),
            patch("leitum.commands.claude.exec_claude"),
            patch("leitum.commands.claude.save_project_config", side_effect=_fake_save_project),
        ):
            run_claude(
                **_make_run_claude_kwargs(
                    no_project_config=False,
                    save_local=True,  # CLI flag IS set
                )
            )

        assert len(saved_project_paths) == 1  # project was written per CLI flag

    def test_dry_run_writes_nothing_even_when_armed(
        self,
        tmp_path: Path,
        minimal_providers_yaml: Path,
        tmp_state_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Under --dry-run, nothing is written regardless of save_local state."""
        from unittest.mock import patch

        from leitum.selection.resolver import ResolvedModels

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("REQUESTY_API_KEY", "test-key")

        resolved = ResolvedModels(
            start="anthropic/claude-sonnet-4-5",
            save_local=True,
            dialog_shown=True,
        )

        with (
            patch("leitum.commands.claude.resolve_models", return_value=resolved),
            patch("leitum.commands.claude.exec_claude"),
            patch("leitum.commands.claude.save_project_config") as mock_save_project,
            patch("leitum.commands.claude.save_state") as mock_save_state,
        ):
            run_claude(
                **_make_run_claude_kwargs(
                    no_project_config=False,
                    save_local=False,
                    dry_run=True,
                )
            )

        mock_save_project.assert_not_called()
        mock_save_state.assert_not_called()
