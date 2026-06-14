"""Interactive selection dialogs using questionary."""

import questionary

from leitum.config.models import ModelSlot, Provider
from leitum.providers.discovery import ModelInfo

_SLOTS: list[ModelSlot] = ["start", "opus", "sonnet", "haiku"]
_SLOT_LABELS: dict[ModelSlot, str] = {
    "start": "Start  (--model)",
    "opus": "Opus   (ANTHROPIC_DEFAULT_OPUS_MODEL)",
    "sonnet": "Sonnet (ANTHROPIC_DEFAULT_SONNET_MODEL)",
    "haiku": "Haiku  (ANTHROPIC_DEFAULT_HAIKU_MODEL)",
}
_NOT_SET_LABEL_START = "(use Claude default)"
_NOT_SET_LABEL = "(do not set)"
_NOT_SET_VALUE = ""


def select_provider(providers: list[Provider], last_provider: str | None) -> Provider | None:
    choices = [
        questionary.Choice(
            title=f"{p.name} — {p.base_url}",
            value=p,
        )
        for p in providers
    ]
    default: Provider | None = None
    if last_provider:
        for p in providers:
            if p.name == last_provider:
                default = p
                break

    result = questionary.select(
        "Select API provider",
        choices=choices,
        default=default,  # type: ignore[arg-type]
    ).ask()
    return result  # type: ignore[no-any-return]


def _sorted_choices(
    model_infos: list[ModelInfo],
    slot: ModelSlot,
    not_set_label: str,
    preselect: str | None,
) -> tuple[list[questionary.Choice], object | None]:
    role_models = [m for m in model_infos if slot in m.roles]
    other_models = [m for m in model_infos if slot not in m.roles]

    choices: list[questionary.Choice] = [
        questionary.Choice(title=not_set_label, value=_NOT_SET_VALUE)
    ]
    for m in role_models + other_models:
        choices.append(questionary.Choice(title=m.display, value=m.id))

    default: object | None = _NOT_SET_VALUE
    if preselect:
        for c in choices:
            if c.value == preselect:
                default = c.value
                break

    return choices, default


def select_models(
    *,
    provider_name: str,
    model_infos: list[ModelInfo],
    slots: list[ModelSlot],
    preselected: dict[ModelSlot, str | None],
    provider: Provider,
) -> dict[ModelSlot, str | None] | None:
    """Interactive model selection for required slots. Returns dict or None on cancel."""
    result: dict[ModelSlot, str | None] = {}

    # Build answers one slot at a time via questionary.select
    for slot in _SLOTS:
        if slot not in slots:
            continue

        not_set_label = _NOT_SET_LABEL_START if slot == "start" else _NOT_SET_LABEL
        choices, default = _sorted_choices(model_infos, slot, not_set_label, preselected.get(slot))

        answer = questionary.select(
            f"Select models for {provider_name} — {_SLOT_LABELS[slot]}",
            choices=choices,
            default=default,  # type: ignore[arg-type]
        ).ask()

        if answer is None:
            return None

        result[slot] = answer if answer != _NOT_SET_VALUE else None

    return result
