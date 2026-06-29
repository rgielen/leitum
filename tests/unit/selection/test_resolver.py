"""Unit tests for the resolution logic."""

import pytest

from leitum.config.models import ModelDefaults, Provider, ProviderAuth, ProvidersConfig
from leitum.providers.discovery import ModelInfo
from leitum.selection.resolver import resolve_models, resolve_provider
from leitum.state import State


def _provider(name="requesty", **kwargs):
    return Provider(
        name=name,
        base_url="https://example.com",
        auth=ProviderAuth(token="tok"),
        **kwargs,
    )


def _models(*ids_and_roles):
    infos = []
    for item in ids_and_roles:
        if isinstance(item, str):
            infos.append(ModelInfo(item, item, []))
        else:
            mid, roles = item
            infos.append(ModelInfo(mid, mid, roles))
    return infos


def _resolve(
    flags=None,
    use_last=None,
    project_models=None,
    state=None,
    provider=None,
    model_infos=None,
):
    return resolve_models(
        flags=flags or {"start": None, "opus": None, "sonnet": None, "haiku": None},
        use_last=use_last or {"start": False, "opus": False, "sonnet": False, "haiku": False},
        project_models=project_models,
        state=state or State(),
        provider=provider or _provider(),
        model_infos=model_infos or _models("m1", "m2"),
        no_tty_ok=True,
    )


def _providers_config(*names: str) -> ProvidersConfig:
    return ProvidersConfig(
        schema_version=1,
        providers=[
            Provider(
                name=n,
                base_url=f"https://{n}.example.com",
                auth=ProviderAuth(token="tok"),
            )
            for n in names
        ],
    )


class TestResolveProvider:
    def test_use_last_provider_falls_back_to_project_config(self):
        """Empty state + use_last + project_provider → project config honored."""
        config = _providers_config("requesty", "openrouter")
        result = resolve_provider(
            flag=None,
            use_last=True,
            project_provider="requesty",
            state=State(),
            config=config,
        )
        assert result.name == "requesty"

    def test_use_last_provider_state_wins_over_project_config(self):
        """State present + use_last + project_provider → state wins."""
        config = _providers_config("requesty", "openrouter")
        state = State()
        state.last_provider = "openrouter"
        result = resolve_provider(
            flag=None,
            use_last=True,
            project_provider="requesty",
            state=state,
            config=config,
        )
        assert result.name == "openrouter"

    def test_use_last_provider_empty_and_no_project_falls_to_single(self):
        """Empty state + use_last + single provider + no project_provider → auto-select."""
        config = _providers_config("requesty")
        result = resolve_provider(
            flag=None,
            use_last=True,
            project_provider=None,
            state=State(),
            config=config,
        )
        assert result.name == "requesty"


class TestResolutionOrder:
    def test_explicit_flag_wins_over_all(self):
        state = State()
        state.set_model("requesty", "start", "state-model")
        result = _resolve(
            flags={"start": "flag-model", "opus": None, "sonnet": None, "haiku": None},
            state=state,
            model_infos=_models("m1", "m2"),
        )
        assert result.start == "flag-model"

    def test_project_config_wins_over_state(self):
        state = State()
        state.set_model("requesty", "start", "state-model")
        result = _resolve(
            project_models=ModelDefaults(start="project-model"),
            state=state,
            model_infos=_models("m1", "m2"),
        )
        assert result.start == "project-model"

    def test_state_used_as_preselect(self):
        state = State()
        state.set_model("requesty", "start", "state-model")
        # No flag, no project config — state should be used as default
        # (in non-interactive mode it's used as the resolved value)
        result = _resolve(
            state=state,
            model_infos=_models("state-model", "m2"),
        )
        assert result.start == "state-model"

    def test_no_tty_uses_preselected_or_none(self):
        result = _resolve(model_infos=_models("m1", "m2"))
        # No preselection → None for all slots in non-interactive mode
        # (unless roles match)
        assert result.start is None or result.start == "m1"

    def test_single_model_auto_selected(self):
        result = _resolve(model_infos=_models("only-model"))
        assert result.start == "only-model"
        assert result.opus == "only-model"

    def test_empty_model_list(self):
        result = _resolve(model_infos=[])
        assert result.start is None

    def test_flag_and_use_last_mutual_exclusion(self):
        with pytest.raises(SystemExit):
            from leitum.commands.claude import _check_conflict

            _check_conflict("--model/-m", "--use-last-model/-M", "foo", True)

    def test_project_config_pinned_no_dialog(self):
        result = _resolve(
            project_models=ModelDefaults(start="pinned"),
            model_infos=_models("m1", "m2"),
        )
        assert result.start == "pinned"

    def test_cli_flag_overrides_project_config(self):
        result = _resolve(
            flags={"start": "cli-model", "opus": None, "sonnet": None, "haiku": None},
            project_models=ModelDefaults(start="project-model"),
            model_infos=_models("m1", "m2"),
        )
        assert result.start == "cli-model"

    def test_use_last_model_falls_back_to_project_config(self):
        """Empty state + use_last + project_models → project value used."""
        result = _resolve(
            use_last={"start": False, "opus": False, "sonnet": True, "haiku": False},
            project_models=ModelDefaults(sonnet="pinned-sonnet"),
            state=State(),
            model_infos=_models("m1", "m2"),
        )
        assert result.sonnet == "pinned-sonnet"

    def test_use_last_model_state_wins_over_project_config(self):
        """State present + use_last + project_models → state wins."""
        state = State()
        state.set_model("requesty", "sonnet", "state-sonnet")
        result = _resolve(
            use_last={"start": False, "opus": False, "sonnet": True, "haiku": False},
            project_models=ModelDefaults(sonnet="pinned-sonnet"),
            state=state,
            model_infos=_models("m1", "m2"),
        )
        assert result.sonnet == "state-sonnet"

    def test_use_last_model_empty_no_project_falls_to_roles(self):
        """Empty state + use_last + no project + role-matching model → role match used."""
        infos = _models(("sonnet-model", ["sonnet"]), ("other-model", []))
        result = _resolve(
            use_last={"start": False, "opus": False, "sonnet": True, "haiku": False},
            project_models=None,
            state=State(),
            model_infos=infos,
        )
        assert result.sonnet == "sonnet-model"


class TestRoleBasedPreselection:
    def test_role_model_preferred(self):
        state = State()
        infos = _models(("sonnet-model", ["sonnet"]), ("other-model", []))
        result = _resolve(
            state=state,
            model_infos=infos,
        )
        # In non-interactive mode with two models, preselect picks first role-matching model
        assert result.sonnet == "sonnet-model"
