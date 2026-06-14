"""Unit tests for launch.py."""

from leitum.config.models import Provider, ProviderAuth
from leitum.launch import build_argv, build_env
from leitum.selection.resolver import ResolvedModels


def _provider(**kwargs):
    defaults: dict = {
        "name": "requesty",
        "base_url": "https://router.requesty.ai",
        "auth": ProviderAuth(token="tok"),
    }
    defaults.update(kwargs)
    return Provider(**defaults)


class TestBuildEnv:
    def _build(self, provider=None, models=None, project_extra=None, base_env=None):
        return build_env(
            provider=provider or _provider(),
            models=models or ResolvedModels(),
            project_extra_env=project_extra or {},
            base_environ=base_env or {},
        )

    def test_sets_base_url(self):
        env = self._build()
        assert env["ANTHROPIC_BASE_URL"] == "https://router.requesty.ai"

    def test_sets_auth_token(self, monkeypatch):
        monkeypatch.setenv("REQUESTY_API_KEY", "mykey")
        provider = _provider(auth=ProviderAuth(token="${REQUESTY_API_KEY}"))
        env = build_env(
            provider=provider,
            models=ResolvedModels(),
            project_extra_env={},
            base_environ={"REQUESTY_API_KEY": "mykey"},
        )
        assert env["ANTHROPIC_AUTH_TOKEN"] == "mykey"

    def test_removes_anthropic_api_key_when_different_env_var(self):
        base = {"ANTHROPIC_API_KEY": "old-key"}
        env = self._build(base_env=base)
        assert "ANTHROPIC_API_KEY" not in env

    def test_keeps_anthropic_api_key_when_same_env_var(self):
        provider = _provider(auth=ProviderAuth(token="tok", env_var="ANTHROPIC_API_KEY"))
        base = {"ANTHROPIC_API_KEY": "old-key"}
        env = build_env(
            provider=provider,
            models=ResolvedModels(),
            project_extra_env={},
            base_environ=base,
        )
        assert "ANTHROPIC_API_KEY" in env

    def test_sets_model_env_vars(self):
        models = ResolvedModels(opus="op-model", sonnet="son-model", haiku="ha-model")
        env = self._build(models=models)
        assert env["ANTHROPIC_DEFAULT_OPUS_MODEL"] == "op-model"
        assert env["ANTHROPIC_DEFAULT_SONNET_MODEL"] == "son-model"
        assert env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == "ha-model"

    def test_unset_model_slots_not_in_env(self):
        env = self._build(models=ResolvedModels())
        assert "ANTHROPIC_DEFAULT_OPUS_MODEL" not in env

    def test_project_extra_env_wins_over_provider(self):
        provider = _provider(extra_env={"MY_KEY": "provider-val"})
        env = build_env(
            provider=provider,
            models=ResolvedModels(),
            project_extra_env={"MY_KEY": "project-val"},
            base_environ={},
        )
        assert env["MY_KEY"] == "project-val"

    def test_extra_env_cannot_override_leitum_vars(self, capsys):
        provider = _provider(extra_env={"ANTHROPIC_BASE_URL": "https://evil.com"})
        env = self._build(provider=provider)
        assert env["ANTHROPIC_BASE_URL"] == "https://router.requesty.ai"
        captured = capsys.readouterr()
        assert "Warning" in captured.err


class TestBuildArgv:
    def test_model_injected_when_start_set(self):
        models = ResolvedModels(start="my-model")
        argv = build_argv([], models)
        assert "--model" in argv
        assert "my-model" in argv

    def test_model_not_injected_when_already_in_passthrough(self):
        models = ResolvedModels(start="my-model")
        argv = build_argv(["--model", "other-model"], models)
        # --model should not be added again
        assert argv.count("--model") == 1

    def test_no_model_when_start_not_set(self):
        argv = build_argv(["--resume"], ResolvedModels())
        assert "--model" not in argv

    def test_passthrough_preserved(self):
        argv = build_argv(["--resume", "--verbose"], ResolvedModels())
        assert "--resume" in argv
        assert "--verbose" in argv

    def test_argv_starts_with_claude(self):
        argv = build_argv([], ResolvedModels())
        assert argv[0] == "claude"
