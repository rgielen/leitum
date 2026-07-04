"""Interactive selection dialogs using questionary."""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass, field

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

# Sentinels returned by key-binding handlers via event.app.exit(result=...)
_REFRESH: object = object()
_SAVE_TOGGLE: object = object()


@dataclass
class ModelSelectionResult:
    models: dict[ModelSlot, str | None] = field(default_factory=dict)
    save_local: bool = False


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
        use_search_filter=True,
        use_jk_keys=False,
        show_selected=True,
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


def _build_instruction(save_local: bool, save_local_allowed: bool) -> str:
    parts = ["↑↓ move", "type to filter", "Ctrl-R refresh"]
    if save_local_allowed:
        parts.append("Ctrl-S save→project")
    parts.append("Enter select")
    base = "(" + " · ".join(parts) + ")"
    if save_local and save_local_allowed:
        base += " [save→project ON]"
    return base


def _inject_key_bindings(
    question: questionary.Question,
    save_local_allowed: bool,
) -> None:
    """Add Ctrl-R and (optionally) Ctrl-S bindings to a questionary select question."""
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys

    try:
        kb = question.application.key_bindings
    except AttributeError:
        return

    if not isinstance(kb, KeyBindings):
        return

    @kb.add(Keys.ControlR, eager=True)
    def _ctrl_r(event: object) -> None:
        from prompt_toolkit.key_binding.key_processor import KeyPressEvent

        if isinstance(event, KeyPressEvent):
            event.app.exit(result=_REFRESH)

    if save_local_allowed:

        @kb.add(Keys.ControlS, eager=True)
        def _ctrl_s(event: object) -> None:
            from prompt_toolkit.key_binding.key_processor import KeyPressEvent

            if isinstance(event, KeyPressEvent):
                event.app.exit(result=_SAVE_TOGGLE)


def _do_refresh(
    *,
    provider_name: str,
    refresh_models: Callable[[], list[ModelInfo]] | None,
    refresh_applicable: bool,
    refresh_enabled: bool,
    current_infos: list[ModelInfo],
    chosen_so_far: dict[ModelSlot, str | None],
) -> list[ModelInfo]:
    """Handle a Ctrl-R refresh request. Returns the (possibly updated) model list."""
    if not refresh_applicable:
        print(
            "(refresh not applicable — provider models are pinned in YAML)",
            file=sys.stderr,
        )
        return current_infos

    if not refresh_enabled:
        print("(refresh skipped in --dry-run)", file=sys.stderr)
        return current_infos

    if refresh_models is None:
        print(
            "(refresh not applicable — provider models are pinned in YAML)",
            file=sys.stderr,
        )
        return current_infos

    print(f"Refreshing models from {provider_name}...", file=sys.stderr)
    try:
        new_infos = refresh_models()
    except Exception as exc:
        print(f"Refresh failed: {exc} — kept current list", file=sys.stderr)
        return current_infos

    new_ids = {m.id for m in new_infos}
    for slot, val in chosen_so_far.items():
        if val is not None and val not in new_ids:
            print(
                f"slot '{slot}' reset: previous model not in refreshed list",
                file=sys.stderr,
            )
            chosen_so_far[slot] = None

    return new_infos


def select_models(
    *,
    provider_name: str,
    model_infos: list[ModelInfo],
    slots: list[ModelSlot],
    preselected: dict[ModelSlot, str | None],
    provider: Provider,
    refresh_models: Callable[[], list[ModelInfo]] | None = None,
    refresh_applicable: bool = True,
    refresh_enabled: bool = True,
    save_local_allowed: bool = True,
    save_local_initial: bool = False,
) -> ModelSelectionResult | None:
    """Interactive model selection for required slots.

    Returns ModelSelectionResult or None on cancel.
    """
    current_infos = list(model_infos)
    save_local = save_local_initial
    chosen: dict[ModelSlot, str | None] = {}

    active_slots = [s for s in _SLOTS if s in slots]
    idx = 0

    while idx < len(active_slots):
        slot = active_slots[idx]
        not_set_label = _NOT_SET_LABEL_START if slot == "start" else _NOT_SET_LABEL

        preselect = chosen.get(slot) if slot in chosen else preselected.get(slot)
        choices, default = _sorted_choices(current_infos, slot, not_set_label, preselect)

        instruction = _build_instruction(save_local, save_local_allowed)

        question = questionary.select(
            f"Select models for {provider_name} — {_SLOT_LABELS[slot]}",
            choices=choices,
            default=default,  # type: ignore[arg-type]
            use_search_filter=True,
            use_jk_keys=False,
            show_selected=True,
            instruction=instruction,
        )

        _inject_key_bindings(question, save_local_allowed)

        answer = question.ask()

        if answer is None:
            return None

        if answer is _REFRESH:
            current_infos = _do_refresh(
                provider_name=provider_name,
                refresh_models=refresh_models,
                refresh_applicable=refresh_applicable,
                refresh_enabled=refresh_enabled,
                current_infos=current_infos,
                chosen_so_far=chosen,
            )
            # Re-render the same slot — do not advance
            continue

        if answer is _SAVE_TOGGLE:
            save_local = not save_local
            # Re-render the same slot with updated footer — do not advance
            continue

        chosen[slot] = answer if answer != _NOT_SET_VALUE else None
        idx += 1

    return ModelSelectionResult(models=chosen, save_local=save_local)
