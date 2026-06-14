import os
from pathlib import Path


def get_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "leitum"


def get_state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "leitum"


def get_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "leitum"


def providers_config_path() -> Path:
    return get_config_dir() / "api-providers.yaml"


def state_path() -> Path:
    return get_state_dir() / "state.yaml"


def model_cache_path(provider_name: str) -> Path:
    return get_cache_dir() / "models" / f"{provider_name}.json"


def ensure_dirs() -> None:
    for d in (get_config_dir(), get_state_dir(), get_cache_dir() / "models"):
        d.mkdir(parents=True, exist_ok=True)
        d.chmod(0o700)
