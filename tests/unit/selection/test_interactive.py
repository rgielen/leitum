"""Unit tests for interactive.py — verifies use_search_filter=True on all select calls."""

from unittest.mock import MagicMock, patch

import questionary

from leitum.config.models import Provider, ProviderAuth
from leitum.providers.discovery import ModelInfo
from leitum.selection.interactive import select_models, select_provider


def _provider(**kwargs) -> Provider:
    defaults: dict = {
        "name": "requesty",
        "base_url": "https://router.requesty.ai",
        "auth": ProviderAuth(token="tok"),
    }
    defaults.update(kwargs)
    return Provider(**defaults)


def _model_infos(*ids: str) -> list[ModelInfo]:
    return [ModelInfo(mid, mid, []) for mid in ids]


def _make_select_mock(return_value: object) -> MagicMock:
    """Return a mock that mimics questionary.select(...).ask() → return_value."""
    ask_mock = MagicMock(return_value=return_value)
    select_result = MagicMock()
    select_result.ask = ask_mock
    return select_result


class TestSelectProviderUsesSearchFilter:
    def test_use_search_filter_true(self) -> None:
        provider = _provider()
        select_mock = _make_select_mock(provider)

        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = select_mock

            select_provider([provider], last_provider=None)

        q_mock.select.assert_called_once()
        _, kwargs = q_mock.select.call_args
        assert kwargs.get("use_search_filter") is True

    def test_show_selected_true(self) -> None:
        provider = _provider()
        select_mock = _make_select_mock(provider)

        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = select_mock

            select_provider([provider], last_provider=None)

        _, kwargs = q_mock.select.call_args
        assert kwargs.get("show_selected") is True

    def test_returns_selected_provider(self) -> None:
        provider = _provider()
        select_mock = _make_select_mock(provider)

        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = select_mock

            result = select_provider([provider], last_provider=None)

        assert result is provider


class TestSelectModelsUsesSearchFilter:
    def test_use_search_filter_true_for_each_slot(self) -> None:
        provider = _provider()
        model_infos = _model_infos("model-a", "model-b")
        select_mock = _make_select_mock("model-a")

        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = select_mock

            select_models(
                provider_name="requesty",
                model_infos=model_infos,
                slots=["start", "opus", "sonnet", "haiku"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
            )

        assert q_mock.select.call_count == 4
        for call in q_mock.select.call_args_list:
            _, kwargs = call
            assert kwargs.get("use_search_filter") is True, (
                f"use_search_filter not set for call: {call}"
            )

    def test_show_selected_true_for_each_slot(self) -> None:
        provider = _provider()
        model_infos = _model_infos("model-a", "model-b")
        select_mock = _make_select_mock("model-a")

        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = select_mock

            select_models(
                provider_name="requesty",
                model_infos=model_infos,
                slots=["start", "opus", "sonnet", "haiku"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
            )

        for call in q_mock.select.call_args_list:
            _, kwargs = call
            assert kwargs.get("show_selected") is True, f"show_selected not set for call: {call}"

    def test_returns_none_on_cancel(self) -> None:
        provider = _provider()
        model_infos = _model_infos("model-a")
        select_mock = _make_select_mock(None)

        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = select_mock

            result = select_models(
                provider_name="requesty",
                model_infos=model_infos,
                slots=["start"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
            )

        assert result is None

    def test_only_requested_slots_are_shown(self) -> None:
        provider = _provider()
        model_infos = _model_infos("model-a")
        select_mock = _make_select_mock("model-a")

        with patch("leitum.selection.interactive.questionary") as q_mock:
            q_mock.Choice.side_effect = questionary.Choice
            q_mock.select.return_value = select_mock

            select_models(
                provider_name="requesty",
                model_infos=model_infos,
                slots=["sonnet"],
                preselected={"start": None, "opus": None, "sonnet": None, "haiku": None},
                provider=provider,
            )

        assert q_mock.select.call_count == 1
