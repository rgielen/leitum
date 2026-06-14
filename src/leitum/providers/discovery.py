import sys

import httpx

from leitum.config.env import interpolate
from leitum.config.models import Provider
from leitum.providers.cache import (
    ModelCacheEntry,
    load_cache,
    load_cache_stale,
    save_cache,
)

DISCOVERY_TIMEOUT = 10.0


class ModelInfo:
    def __init__(self, model_id: str, display: str | None, roles: list[str]) -> None:
        self.id = model_id
        self.display = display or model_id
        self.roles = roles


def _fetch_models(provider: Provider) -> list[ModelCacheEntry]:
    token = interpolate(provider.auth.token)
    url = provider.base_url.rstrip("/") + "/v1/models"
    with httpx.Client(timeout=DISCOVERY_TIMEOUT) as client:
        resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
    data = resp.json()
    entries = []
    for item in data.get("data", []):
        model_id = item.get("id") or item.get("name", "")
        if model_id:
            entries.append(ModelCacheEntry(model_id, item.get("name")))
    return entries


def discover_models(provider: Provider, force: bool = False) -> list[ModelInfo]:
    """Return model list for provider. Uses YAML list > cache > API."""
    if provider.models:
        return [ModelInfo(m.id, m.display, list(m.roles)) for m in provider.models]

    if not force:
        cached = load_cache(provider.name)
        if cached is not None:
            return [ModelInfo(m.id, m.display, []) for m in cached]

    try:
        entries = _fetch_models(provider)
        save_cache(provider.name, provider.base_url, entries)
        return [ModelInfo(m.id, m.display, []) for m in entries]
    except Exception as exc:
        stale = load_cache_stale(provider.name)
        if stale is not None:
            print(
                f"Warning: model discovery failed ({exc}), using stale cache.",
                file=sys.stderr,
            )
            return [ModelInfo(m.id, m.display, []) for m in stale]
        raise RuntimeError(
            f"Model discovery failed for provider '{provider.name}': {exc}. "
            "Add a 'models:' list to the provider in api-providers.yaml to avoid API calls."
        ) from exc
