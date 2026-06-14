"""Unit tests for the resolution logic."""

import pytest

from leitum.config.models import ModelDefaults, Provider, ProviderAuth
from leitum.providers.discovery import ModelInfo
from leitum.selection.resolver import resolve_models
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
