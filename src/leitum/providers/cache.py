import json
import sys
from datetime import UTC, datetime, timedelta

from leitum.config.paths import model_cache_path

CACHE_TTL = timedelta(hours=24)
CACHE_SCHEMA_VERSION = 1


class ModelCacheEntry:
    def __init__(self, model_id: str, display: str | None = None) -> None:
        self.id = model_id
        self.display = display


def load_cache(provider_name: str) -> list[ModelCacheEntry] | None:
    path = model_cache_path(provider_name)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        fetched_at = datetime.fromisoformat(data["fetched_at"])
        if datetime.now(tz=UTC) - fetched_at > CACHE_TTL:
            return None
        return [ModelCacheEntry(m["id"], m.get("display")) for m in data["models"]]
    except Exception as exc:
        print(
            f"Warning: model cache for {provider_name} is corrupt ({exc}), ignoring.",
            file=sys.stderr,
        )
        return None


def load_cache_stale(provider_name: str) -> list[ModelCacheEntry] | None:
    """Load cache ignoring TTL (for fallback when API fails)."""
    path = model_cache_path(provider_name)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ModelCacheEntry(m["id"], m.get("display")) for m in data["models"]]
    except Exception:
        return None


def save_cache(provider_name: str, base_url: str, models: list[ModelCacheEntry]) -> None:
    path = model_cache_path(provider_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "fetched_at": datetime.now(tz=UTC).isoformat(),
        "base_url": base_url,
        "models": [{"id": m.id, "display": m.display} for m in models],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def clear_cache(provider_name: str | None = None) -> None:
    from leitum.config.paths import get_cache_dir

    cache_dir = get_cache_dir() / "models"
    if not cache_dir.exists():
        return
    if provider_name is not None:
        p = model_cache_path(provider_name)
        if p.exists():
            p.unlink()
    else:
        for f in cache_dir.glob("*.json"):
            f.unlink()
