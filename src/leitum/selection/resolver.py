"""Pure resolution logic — no I/O, no dialogs."""

from dataclasses import dataclass

from leitum.config.models import ModelDefaults, ModelSlot, Provider, ProvidersConfig
from leitum.providers.discovery import ModelInfo
from leitum.state import State


@dataclass
class ResolvedModels:
    start: str | None = None
    opus: str | None = None
    sonnet: str | None = None
    haiku: str | None = None

    def get(self, slot: ModelSlot) -> str | None:
        if slot == "start":
            return self.start
        if slot == "opus":
            return self.opus
        if slot == "sonnet":
            return self.sonnet
        return self.haiku

    def set(self, slot: ModelSlot, value: str | None) -> None:
        setattr(self, slot, value)


_SLOTS: list[ModelSlot] = ["start", "opus", "sonnet", "haiku"]


def resolve_provider(
    *,
    flag: str | None,
    use_last: bool,
    project_provider: str | None,
    state: State,
    config: ProvidersConfig,
    verbose: bool = False,
) -> Provider:
    """Resolve which provider to use. Returns Provider or raises SystemExit."""
    import sys

    name: str | None = None

    if flag is not None:
        name = flag
    elif use_last:
        if state.last_provider:
            name = state.last_provider
        else:
            print(
                "Warning: --use-last-provider (-P) set but no last provider in state,"
                " falling back to selection.",
                file=sys.stderr,
            )
    elif project_provider is not None:
        name = project_provider

    if name is not None:
        provider = config.get_provider(name)
        if provider is None:
            known = ", ".join(p.name for p in config.providers)
            print(
                f"Error: unknown provider '{name}'. Known providers: {known}",
                file=sys.stderr,
            )
            raise SystemExit(flag_exit_code(flag is not None))
        if verbose:
            print(f"Provider: {provider.name} ({provider.base_url})", file=sys.stderr)
        return provider

    # Single-provider auto-select
    if len(config.providers) == 1:
        return config.providers[0]

    return _interactive_provider(config, state, verbose)


def flag_exit_code(from_flag: bool) -> int:
    return 2 if from_flag else 3


def _interactive_provider(config: ProvidersConfig, state: State, verbose: bool) -> Provider:
    import sys

    from leitum.selection.interactive import select_provider

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print(
            "Error: cannot select provider non-interactively. "
            "Use --provider / -p or configure a single provider.",
            file=sys.stderr,
        )
        raise SystemExit(4)

    provider = select_provider(config.providers, state.last_provider)
    if provider is None:
        raise SystemExit(130)
    return provider


def _get_preselected(
    slot: ModelSlot,
    *,
    explicit_flag: str | None,
    use_last: bool,
    project_models: ModelDefaults | None,
    state: State,
    provider: Provider,
    model_infos: list[ModelInfo],
) -> tuple[str | None, bool]:
    """
    Returns (value, is_pinned).
    is_pinned=True means no dialog needed for this slot.
    """
    if explicit_flag is not None:
        return explicit_flag, True

    if use_last:
        val = state.get_model(provider.name, slot)
        if val is not None:
            return val, True
        return None, False

    if project_models is not None:
        val = project_models.get(slot)
        if val is not None:
            return val, True

    # State as pre-fill
    state_val = state.get_model(provider.name, slot)
    if state_val is not None:
        return state_val, False

    # Provider defaults
    if provider.defaults is not None:
        def_val = provider.defaults.get(slot)
        if def_val is not None:
            return def_val, False

    # First model with matching role
    for m in model_infos:
        if slot in m.roles:
            return m.id, False

    # For YAML-sourced models, first entry
    if provider.models:
        if model_infos:
            return model_infos[0].id, False

    return None, False


def resolve_models(
    *,
    flags: dict[ModelSlot, str | None],
    use_last: dict[ModelSlot, bool],
    project_models: ModelDefaults | None,
    state: State,
    provider: Provider,
    model_infos: list[ModelInfo],
    verbose: bool = False,
    no_tty_ok: bool = False,
) -> ResolvedModels:
    """
    Resolve all four model slots. May trigger interactive dialog.
    Returns ResolvedModels.
    """
    import sys

    result = ResolvedModels()
    need_dialog: list[ModelSlot] = []
    preselected: dict[ModelSlot, str | None] = {}

    for slot in _SLOTS:
        val, pinned = _get_preselected(
            slot,
            explicit_flag=flags.get(slot),
            use_last=use_last.get(slot, False),
            project_models=project_models,
            state=state,
            provider=provider,
            model_infos=model_infos,
        )
        preselected[slot] = val

        if pinned:
            result.set(slot, val)
            if verbose:
                print(f"  {slot}: {val} (pinned)", file=sys.stderr)
        elif len(model_infos) == 1:
            # single model, auto-select
            result.set(slot, model_infos[0].id)
            if verbose:
                print(f"  {slot}: {model_infos[0].id} (auto, single option)", file=sys.stderr)
        elif len(model_infos) == 0:
            result.set(slot, val)
            if verbose:
                print(f"  {slot}: {val or '(not set)'}", file=sys.stderr)
        else:
            need_dialog.append(slot)

    if need_dialog:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            # Non-interactive: fall back to preselected or None
            for slot in need_dialog:
                val = preselected.get(slot)
                result.set(slot, val)
                if verbose:
                    print(
                        f"  {slot}: {val or '(not set)'} (non-interactive fallback)",
                        file=sys.stderr,
                    )
        else:
            from leitum.selection.interactive import select_models

            chosen = select_models(
                provider_name=provider.name,
                model_infos=model_infos,
                slots=need_dialog,
                preselected=preselected,
                provider=provider,
            )
            if chosen is None:
                raise SystemExit(130)
            for slot in need_dialog:
                result.set(slot, chosen.get(slot))
                if verbose:
                    print(f"  {slot}: {chosen.get(slot) or '(not set)'}", file=sys.stderr)

    return result
