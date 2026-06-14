"""leitum refresh command."""

import sys

from leitum.config.io import load_providers_config
from leitum.config.paths import providers_config_path
from leitum.providers.cache import clear_cache
from leitum.providers.discovery import discover_models


def run_refresh(provider_name: str | None = None) -> None:
    cfg_path = providers_config_path()
    if not cfg_path.exists():
        print("Error: no api-providers.yaml found. Run 'leitum init' first.", file=sys.stderr)
        raise SystemExit(3)

    config = load_providers_config(cfg_path)

    if provider_name is not None:
        provider = config.get_provider(provider_name)
        if provider is None:
            known = ", ".join(p.name for p in config.providers)
            print(f"Error: unknown provider '{provider_name}'. Known: {known}", file=sys.stderr)
            raise SystemExit(2)
        providers = [provider]
    else:
        providers = list(config.providers)

    any_success = False
    for p in providers:
        if p.models:
            print(f"  {p.name}: skipped (models pinned in YAML)")
            any_success = True
            continue
        clear_cache(p.name)
        try:
            models = discover_models(p, force=True)
            print(f"  {p.name}: {len(models)} models fetched and cached")
            any_success = True
        except Exception as exc:
            print(f"  {p.name}: failed — {exc}", file=sys.stderr)

    if not any_success:
        raise SystemExit(1)
