"""leitum claude subcommand — launch Claude Code via a configured provider."""

from __future__ import annotations

import sys
from pathlib import Path

from leitum.config.io import load_project_config, load_providers_config
from leitum.config.models import ModelSlot
from leitum.config.paths import providers_config_path
from leitum.launch import exec_claude
from leitum.providers.cache import clear_cache
from leitum.providers.discovery import discover_models
from leitum.selection.resolver import resolve_models, resolve_provider
from leitum.state import load_state, save_state


def run_claude(
    pass_through: list[str],
    *,
    provider_flag: str | None,
    use_last_provider: bool,
    model_flag: str | None,
    use_last_model: bool,
    opus_flag: str | None,
    use_last_opus: bool,
    sonnet_flag: str | None,
    use_last_sonnet: bool,
    haiku_flag: str | None,
    use_last_haiku: bool,
    refresh: bool,
    no_project_config: bool,
    project_config_path: Path | None,
    dry_run: bool,
    verbose: bool,
) -> None:
    # Conflict checks
    _check_conflict("--model/-m", "--use-last-model/-M", model_flag, use_last_model)
    _check_conflict("--opus/-o", "--use-last-opus/-O", opus_flag, use_last_opus)
    _check_conflict("--sonnet/-s", "--use-last-sonnet/-S", sonnet_flag, use_last_sonnet)
    _check_conflict("--haiku/-k", "--use-last-haiku/-K", haiku_flag, use_last_haiku)
    if no_project_config and project_config_path is not None:
        print(
            "Error: --no-project-config and --project-config are mutually exclusive.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    # Load global config
    cfg_path = providers_config_path()
    if not cfg_path.exists():
        print(
            f"Error: providers config not found at {cfg_path}. Run 'leitum init' first.",
            file=sys.stderr,
        )
        raise SystemExit(3)
    try:
        config = load_providers_config(cfg_path)
    except Exception as exc:
        print(f"Error: invalid providers config: {exc}", file=sys.stderr)
        raise SystemExit(3) from exc

    state = load_state()

    # Load project config
    project_cfg = None
    if not no_project_config:
        pc_path = project_config_path or Path("leitum.yaml")
        if pc_path.exists():
            try:
                raw_pc = load_project_config(pc_path)
                # Validate provider reference
                if raw_pc.provider is not None:
                    if config.get_provider(raw_pc.provider) is None:
                        known = ", ".join(p.name for p in config.providers)
                        print(
                            f"Error: leitum.yaml references unknown provider '{raw_pc.provider}'. "
                            f"Known providers: {known}",
                            file=sys.stderr,
                        )
                        raise SystemExit(3)
                project_cfg = raw_pc
            except SystemExit:
                raise
            except Exception as exc:
                print(f"Error: invalid leitum.yaml: {exc}", file=sys.stderr)
                raise SystemExit(3) from exc

    # Resolve provider
    provider = resolve_provider(
        flag=provider_flag,
        use_last=use_last_provider,
        project_provider=project_cfg.provider if project_cfg else None,
        state=state,
        config=config,
        verbose=verbose,
    )

    # Refresh cache if requested
    if refresh:
        if provider.models:
            print(
                f"Warning: --refresh has no effect for provider '{provider.name}' "
                "(models are pinned in YAML).",
                file=sys.stderr,
            )
        else:
            if not dry_run:
                if verbose:
                    print(f"Refreshing model list for {provider.name}...", file=sys.stderr)
                clear_cache(provider.name)

    # Discover models
    force = (refresh and not bool(provider.models)) and not dry_run
    try:
        model_infos = discover_models(provider, force=force)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(4) from exc

    # Resolve models
    flags: dict[ModelSlot, str | None] = {
        "start": model_flag,
        "opus": opus_flag,
        "sonnet": sonnet_flag,
        "haiku": haiku_flag,
    }
    use_last: dict[ModelSlot, bool] = {
        "start": use_last_model,
        "opus": use_last_opus,
        "sonnet": use_last_sonnet,
        "haiku": use_last_haiku,
    }

    # Warn if model not in list
    for slot, flag_val in flags.items():
        if flag_val and model_infos:
            known_ids = {m.id for m in model_infos}
            if flag_val not in known_ids:
                print(
                    f"Warning: model '{flag_val}' for slot '{slot}' not in provider's model list.",
                    file=sys.stderr,
                )

    resolved = resolve_models(
        flags=flags,
        use_last=use_last,
        project_models=project_cfg.models if project_cfg else None,
        state=state,
        provider=provider,
        model_infos=model_infos,
        verbose=verbose,
    )

    # Persist state — skipped in dry-run to remain side-effect-free
    if not dry_run:
        state.last_provider = provider.name
        from leitum.selection.resolver import _SLOTS

        for slot in _SLOTS:
            val = resolved.get(slot)
            if val:
                state.set_model(provider.name, slot, val)
        state.touch_provider(provider.name)
        try:
            save_state(state)
        except Exception as exc:
            print(f"Warning: could not save state: {exc}", file=sys.stderr)

    project_extra = project_cfg.extra_env if project_cfg else {}

    exec_claude(
        provider=provider,
        models=resolved,
        pass_through=pass_through,
        project_extra_env=project_extra,
        dry_run=dry_run,
        verbose=verbose,
    )


def _check_conflict(flag_a: str, flag_b: str, val_a: str | None, use_last_b: bool) -> None:
    if val_a is not None and use_last_b:
        print(f"Error: {flag_a} and {flag_b} are mutually exclusive.", file=sys.stderr)
        raise SystemExit(2)
