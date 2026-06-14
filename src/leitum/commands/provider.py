"""leitum provider subcommands."""

from __future__ import annotations

import json
import sys

import httpx
from rich.console import Console
from rich.table import Table

from leitum.config.io import load_providers_config
from leitum.config.models import Provider, ProvidersConfig
from leitum.config.paths import model_cache_path, providers_config_path
from leitum.providers.cache import clear_cache
from leitum.state import load_state

console = Console()


def _load_config() -> ProvidersConfig:
    p = providers_config_path()
    if not p.exists():
        print("Error: no api-providers.yaml found. Run 'leitum init' first.", file=sys.stderr)
        raise SystemExit(3)
    return load_providers_config(p)


def _model_source(provider: Provider) -> str:
    if provider.models:
        return f"{len(provider.models)} (yaml)"
    cache_p = model_cache_path(provider.name)
    if cache_p.exists():
        try:
            data = json.loads(cache_p.read_text())
            count = len(data.get("models", []))
            return f"{count} (cached)"
        except Exception:
            pass
        return "? (cache corrupt)"
    return "api"


def run_provider_list() -> None:
    config = _load_config()
    state = load_state()

    table = Table(show_header=True, header_style="bold")
    table.add_column("NAME")
    table.add_column("BASE URL")
    table.add_column("AUTH ENV VAR")
    table.add_column("MODELS")

    for p in config.providers:
        marker = " *" if p.name == state.last_provider else ""
        table.add_row(p.name + marker, p.base_url, p.auth.env_var, _model_source(p))

    console.print(table)


def run_provider_show(name: str, reveal_token: bool = False) -> None:
    config = _load_config()
    provider = config.get_provider(name)
    if provider is None:
        known = ", ".join(p.name for p in config.providers)
        print(f"Error: unknown provider '{name}'. Known: {known}", file=sys.stderr)
        raise SystemExit(2)

    if reveal_token:
        print("WARNING: displaying token in plaintext.", file=sys.stderr)
        answer = input("Are you sure? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            raise SystemExit(0)
        from leitum.config.env import interpolate

        token = interpolate(provider.auth.token)
    else:
        token = "***redacted***"

    print(f"name: {provider.name}")
    print(f"base_url: {provider.base_url}")
    print("auth:")
    print(f"  token: {token}")
    print(f"  env_var: {provider.auth.env_var}")
    if provider.defaults:
        print("defaults:")
        from leitum.selection.resolver import _SLOTS as _MODEL_SLOTS

        for slot in _MODEL_SLOTS:
            val = provider.defaults.get(slot)
            if val:
                print(f"  {slot}: {val}")
    if provider.models:
        print(f"models: ({len(provider.models)} entries)")
        for m in provider.models:
            print(f"  - {m.id}")
    if provider.extra_env:
        print(f"extra_env: {provider.extra_env}")
    print(f"\nSource: {providers_config_path()}")
    print(f"Model source: {_model_source(provider)}")

    cache_p = model_cache_path(provider.name)
    if cache_p.exists():
        try:
            data = json.loads(cache_p.read_text())
            fetched = data.get("fetched_at", "unknown")
            print(f"Cache age: {fetched}")
        except Exception:
            pass


def run_provider_add() -> None:
    import questionary

    config = _load_config()

    name = questionary.text(
        "Provider name (lowercase, kebab-case):",
        validate=lambda v: (
            bool(__import__("re").match(r"^[a-z][a-z0-9-]*$", v)) or "Must match ^[a-z][a-z0-9-]*$"
        ),
    ).ask()
    if name is None:
        raise SystemExit(130)

    if config.get_provider(name) is not None:
        print(f"Error: provider '{name}' already exists.", file=sys.stderr)
        raise SystemExit(2)

    base_url = questionary.text("Base URL (e.g. https://router.requesty.ai):").ask()
    if base_url is None:
        raise SystemExit(130)

    token_source = questionary.select(
        "Token source:",
        choices=[
            questionary.Choice("Environment variable reference (recommended)", value="env"),
            questionary.Choice("Inline secret (stored in plaintext!)", value="inline"),
        ],
    ).ask()
    if token_source is None:
        raise SystemExit(130)

    default_env_name = name.upper().replace("-", "_") + "_API_KEY"
    if token_source == "env":
        env_name = questionary.text(
            "Environment variable name:",
            default=default_env_name,
        ).ask()
        if env_name is None:
            raise SystemExit(130)
        token = f"${{{env_name}}}"
    else:
        print("WARNING: storing a token inline is not recommended.", file=sys.stderr)
        token = questionary.password("Token value:").ask()
        if token is None:
            raise SystemExit(130)

    auth_env_var = questionary.select(
        "Auth environment variable name (what Claude Code reads):",
        choices=["ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY"],
        default="ANTHROPIC_AUTH_TOKEN",
    ).ask()
    if auth_env_var is None:
        raise SystemExit(130)

    test_now = questionary.confirm("Test the provider now (GET /v1/models)?", default=True).ask()
    if test_now:
        _test_provider(base_url, token)

    _append_provider(name, base_url, token, auth_env_var)
    print(f"Provider '{name}' added to {providers_config_path()}.")


def _test_provider(base_url: str, token: str) -> None:
    from leitum.config.env import interpolate

    try:
        resolved_token = interpolate(token)
    except ValueError as exc:
        print(f"Warning: cannot resolve token for test: {exc}", file=sys.stderr)
        return
    url = base_url.rstrip("/") + "/v1/models"
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, headers={"Authorization": f"Bearer {resolved_token}"})
        if resp.is_success:
            count = len(resp.json().get("data", []))
            print(f"OK — {count} models returned.")
        else:
            print(f"Warning: provider returned HTTP {resp.status_code}.", file=sys.stderr)
    except Exception as exc:
        print(f"Warning: test failed: {exc}", file=sys.stderr)


def _append_provider(name: str, base_url: str, token: str, auth_env_var: str) -> None:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap

    path = providers_config_path()
    y = YAML()
    y.preserve_quotes = True
    with path.open("r") as f:
        doc = y.load(f)

    new_provider: CommentedMap = CommentedMap()
    new_provider["name"] = name
    new_provider["base_url"] = base_url
    auth: CommentedMap = CommentedMap()
    auth["token"] = token
    if auth_env_var != "ANTHROPIC_AUTH_TOKEN":
        auth["env_var"] = auth_env_var
    new_provider["auth"] = auth

    doc["providers"].append(new_provider)
    with path.open("w") as f:
        y.dump(doc, f)


def run_provider_remove(name: str, yes: bool = False) -> None:
    config = _load_config()
    provider = config.get_provider(name)
    if provider is None:
        known = ", ".join(p.name for p in config.providers)
        print(f"Error: unknown provider '{name}'. Known: {known}", file=sys.stderr)
        raise SystemExit(2)

    if not yes:
        answer = input(f"Remove provider '{name}'? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            raise SystemExit(0)

    from ruamel.yaml import YAML

    path = providers_config_path()
    y = YAML()
    y.preserve_quotes = True
    with path.open("r") as f:
        doc = y.load(f)

    doc["providers"] = [p for p in doc["providers"] if p["name"] != name]
    with path.open("w") as f:
        y.dump(doc, f)

    # Clear state if this was last_provider
    state = load_state()
    if state.last_provider == name:
        state.last_provider = None
        from leitum.state import save_state

        save_state(state)

    clear_cache(name)
    print(f"Provider '{name}' removed.")
