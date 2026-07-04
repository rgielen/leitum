"""Unit tests for Ctrl-R (refresh) and Ctrl-S (save-toggle) keybindings in select_models."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock, patch

import questionary

from leitum.config.models import ModelSlot, Provider, ProviderAuth
from leitum.providers.discovery import ModelInfo
from leitum.selection.interactive import (
    _REFRESH,
    _SAVE_TOGGLE,
    ModelSelectionResult,
    select_models,
)


def _provider(**kwargs: object) -> Provider:
    defaults: dict[str, Any] = {
        "name": "requesty",
        "base_url": "https://router.requesty.ai",
        "auth": ProviderAuth(token="tok"),
    }
    defaults.update(kwargs)
    return Provider(**defaults)


def _model_infos(*ids: str) -> list[ModelInfo]:
    return [ModelInfo(mid, mid, []) for mid in ids]


def _make_select_mock(side_effect: list[object]) -> MagicMock:
    """Return a mock that mimics questionary.select(...).ask() with a side_effect sequence."""
    ask_mock = MagicMock(side_effect=side_effect)
    select_result = MagicMock()
    select_result.ask = ask_mock
    return select_result


def _run_select_models(
    ask_side_effect: list[object],
    refresh_return: list[ModelInfo] | None = None,
    **kwargs: object,
) -> tuple[ModelSelectionResult | None, MagicMock]:
    """Helper: run select_models with a mocked questionary.select."""
    provider = _provider()
    refresh_spy = MagicMock(return_value=refresh_return or [])

    with patch("leitum.selection.interactive.questionary") as q_mock:
        q_mock.Choice.side_effect = questionary.Choice
        q_mock.select.return_value = _make_select_mock(ask_side_effect)

        result = select_models(
            provider_name="requesty",
            model_infos=_model_infos("model-a", "model-b"),
            slots=["start"],
            preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
            provider=provider,
            refresh_models=refresh_spy,
            **kwargs,  # type: ignore[arg-type]
        )

    return result, refresh_spy


class TestCtrlRRefresh:
    def test_ctrl_r_triggers_refresh_callback(self) -> None:
        """Ctrl-R sentinel causes refresh_models to be called; slot then uses next ask() value."""
        result, refresh_spy = _run_select_models(
            ask_side_effect=[_REFRESH, "model-b"],
            refresh_return=_model_infos("model-b", "model-c"),
        )
        assert refresh_spy.call_count == 1
        assert isinstance(result, ModelSelectionResult)
        assert result.models.get("start") == "model-b"

    def test_ctrl_r_not_applicable_skips_callback(self, capsys: object) -> None:
        """When refresh_applicable=False, callback is not invoked and note is printed."""
        result, refresh_spy = _run_select_models(
            ask_side_effect=[_REFRESH, "model-a"],
            refresh_return=_model_infos("model-a"),
            refresh_applicable=False,
        )
        assert refresh_spy.call_count == 0
        assert isinstance(result, ModelSelectionResult)
        assert result.models.get("start") == "model-a"

    def test_ctrl_r_dry_run_skips_callback(self, capsys: object) -> None:
        """When refresh_enabled=False (dry-run), callback is not invoked."""
        result, refresh_spy = _run_select_models(
            ask_side_effect=[_REFRESH, "model-a"],
            refresh_return=_model_infos("model-a"),
            refresh_enabled=False,
        )
        assert refresh_spy.call_count == 0
        assert isinstance(result, ModelSelectionResult)

    def test_ctrl_r_resets_stale_chosen_value(self) -> None:
        """After refresh, a slot whose chosen value is gone is reset to None."""
        import io

        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            # First ask on slot "start" → pick "model-a"; then simulate Ctrl-R for "opus" slot
            # We test _do_refresh directly since two-slot testing is complex here.
            from leitum.selection.interactive import _do_refresh

            chosen_so_far: dict[ModelSlot, str | None] = {"start": "stale-model"}
            new_infos = _do_refresh(
                provider_name="requesty",
                refresh_models=lambda: _model_infos("model-b"),
                refresh_applicable=True,
                refresh_enabled=True,
                current_infos=_model_infos("stale-model"),
                chosen_so_far=chosen_so_far,
            )
            stderr_out = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr

        assert chosen_so_far["start"] is None
        assert "reset" in stderr_out
        assert len(new_infos) == 1
        assert new_infos[0].id == "model-b"

    def test_ctrl_r_no_callback_when_none(self, capsys: object) -> None:
        """When refresh_models is None, callback is not invoked (same as YAML-pinned)."""
        provider = _provider()
        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = _make_select_mock([_REFRESH, "model-a"])

            result = select_models(
                provider_name="requesty",
                model_infos=_model_infos("model-a", "model-b"),
                slots=["start"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
                refresh_models=None,
            )

        assert isinstance(result, ModelSelectionResult)
        assert result.models.get("start") == "model-a"

    def test_ctrl_r_callback_failure_keeps_current_list(self) -> None:
        """If refresh_models raises, the current list is kept."""
        import io

        def _fail() -> list[ModelInfo]:
            raise RuntimeError("network error")

        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            from leitum.selection.interactive import _do_refresh

            original = _model_infos("model-a")
            result = _do_refresh(
                provider_name="requesty",
                refresh_models=_fail,
                refresh_applicable=True,
                refresh_enabled=True,
                current_infos=original,
                chosen_so_far={},
            )
            stderr_out = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr

        assert result is original
        assert "Refresh failed" in stderr_out
        assert "kept current list" in stderr_out


class TestCtrlSSaveToggle:
    def test_ctrl_s_toggles_save_local_true(self) -> None:
        """Ctrl-S sentinel flips save_local to True when initially False."""
        result, _ = _run_select_models(
            ask_side_effect=[_SAVE_TOGGLE, "model-a"],
        )
        assert isinstance(result, ModelSelectionResult)
        assert result.save_local is True

    def test_ctrl_s_double_toggle_restores_false(self) -> None:
        """Two Ctrl-S presses restore the initial False state."""
        result, _ = _run_select_models(
            ask_side_effect=[_SAVE_TOGGLE, _SAVE_TOGGLE, "model-a"],
        )
        assert isinstance(result, ModelSelectionResult)
        assert result.save_local is False

    def test_ctrl_s_initial_true_starts_armed(self) -> None:
        """save_local_initial=True starts the dialog armed."""
        result, _ = _run_select_models(
            ask_side_effect=["model-a"],
            save_local_initial=True,
        )
        assert isinstance(result, ModelSelectionResult)
        assert result.save_local is True

    def test_ctrl_s_initial_true_can_be_disarmed(self) -> None:
        """Starting armed, Ctrl-S disarms."""
        result, _ = _run_select_models(
            ask_side_effect=[_SAVE_TOGGLE, "model-a"],
            save_local_initial=True,
        )
        assert isinstance(result, ModelSelectionResult)
        assert result.save_local is False

    def test_ctrl_s_not_bound_when_not_allowed(self) -> None:
        """When save_local_allowed=False, _inject_key_bindings receives save_local_allowed=False."""
        provider = _provider()
        injected_calls: list[tuple[object, bool]] = []

        def _fake_inject(question: object, save_local_allowed: bool) -> None:
            injected_calls.append((question, save_local_allowed))

        with (
            patch("leitum.selection.interactive.questionary") as q_mock,
            patch("leitum.selection.interactive._inject_key_bindings", side_effect=_fake_inject),
        ):
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = _make_select_mock(["model-a"])

            select_models(
                provider_name="requesty",
                model_infos=_model_infos("model-a"),
                slots=["start"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
                save_local_allowed=False,
            )

        assert len(injected_calls) == 1
        assert injected_calls[0][1] is False  # save_local_allowed passed as False

    def test_ctrl_s_bound_when_allowed(self) -> None:
        """When save_local_allowed=True, _inject_key_bindings receives save_local_allowed=True."""
        provider = _provider()
        injected_calls: list[tuple[object, bool]] = []

        def _fake_inject(question: object, save_local_allowed: bool) -> None:
            injected_calls.append((question, save_local_allowed))

        with (
            patch("leitum.selection.interactive.questionary") as q_mock,
            patch("leitum.selection.interactive._inject_key_bindings", side_effect=_fake_inject),
        ):
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = _make_select_mock(["model-a"])

            select_models(
                provider_name="requesty",
                model_infos=_model_infos("model-a"),
                slots=["start"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
                save_local_allowed=True,
            )

        assert len(injected_calls) == 1
        assert injected_calls[0][1] is True  # save_local_allowed passed as True


class TestModelSelectionResult:
    def test_cancel_returns_none(self) -> None:
        """Cancelling (ask returns None) returns None, not a ModelSelectionResult."""
        provider = _provider()
        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = _make_select_mock([None])

            result = select_models(
                provider_name="requesty",
                model_infos=_model_infos("model-a"),
                slots=["start"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
            )

        assert result is None

    def test_result_contains_selected_model(self) -> None:
        """Normal selection returns ModelSelectionResult with correct model."""
        provider = _provider()
        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = _make_select_mock(["model-a"])

            result = select_models(
                provider_name="requesty",
                model_infos=_model_infos("model-a", "model-b"),
                slots=["start"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
            )

        assert isinstance(result, ModelSelectionResult)
        assert result.models.get("start") == "model-a"
        assert result.save_local is False

    def test_instruction_footer_present(self) -> None:
        """The instruction kwarg is passed to questionary.select."""
        provider = _provider()
        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = _make_select_mock(["model-a"])

            select_models(
                provider_name="requesty",
                model_infos=_model_infos("model-a", "model-b"),
                slots=["start"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
            )

        _, kwargs = q_mock.select.call_args
        assert "instruction" in kwargs
        assert "Ctrl-R" in kwargs["instruction"]

    def test_instruction_omits_ctrl_s_when_not_allowed(self) -> None:
        """When save_local_allowed=False, Ctrl-S hint is absent from footer."""
        provider = _provider()
        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = _make_select_mock(["model-a"])

            select_models(
                provider_name="requesty",
                model_infos=_model_infos("model-a", "model-b"),
                slots=["start"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
                save_local_allowed=False,
            )

        _, kwargs = q_mock.select.call_args
        assert "Ctrl-S" not in kwargs.get("instruction", "")

    def test_instruction_shows_save_armed_state(self) -> None:
        """When armed, the footer includes [save->project ON]."""
        provider = _provider()
        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = _make_select_mock(["model-a"])

            select_models(
                provider_name="requesty",
                model_infos=_model_infos("model-a", "model-b"),
                slots=["start"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
                save_local_initial=True,
            )

        _, kwargs = q_mock.select.call_args
        assert "save→project ON" in kwargs.get("instruction", "")
