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


def run_provider_add(
    preset: str | None = None,
    name: str | None = None,
    base_url: str | None = None,
) -> None:
    import questionary

    from leitum.providers.presets import PRESETS, get_preset

    config = _load_config()

    if preset is not None:
        p_preset = get_preset(preset)
        if p_preset is None:
            valid_presets = ", ".join(p.key for p in PRESETS)
            print(
                f"Error: unknown preset '{preset}'. Valid presets: {valid_presets}", file=sys.stderr
            )
            raise SystemExit(2)

        final_name = name or p_preset.default_name
        import re

        if not re.match(r"^[a-z][a-z0-9-]*$", final_name):
            print(
                f"Error: provider name '{final_name}' is invalid. Must match ^[a-z][a-z0-9-]*$",
                file=sys.stderr,
            )
            raise SystemExit(2)

        if config.get_provider(final_name) is not None:
            print(f"Error: provider '{final_name}' already exists.", file=sys.stderr)
            raise SystemExit(2)

        final_base_url = base_url or p_preset.base_url
        _append_provider(
            name=final_name,
            base_url=final_base_url,
            token=p_preset.token,
            auth_env_var=p_preset.auth_env_var,
            extra_env=p_preset.extra_env,
        )
        print(f"Provider '{final_name}' added to {providers_config_path()}.")
        return

    # Interactive flow
    choices = [questionary.Choice(p.display, value=p.key) for p in PRESETS]
    choices.append(questionary.Choice("Detect local providers…", value="detect"))
    choices.append(questionary.Choice("Custom (manual)", value="custom"))

    provider_type = questionary.select(
        "Provider type:",
        choices=choices,
    ).ask()
    if provider_type is None:
        raise SystemExit(130)

    if provider_type == "detect":
        run_provider_detect(json_output=False, config=config)
        raise SystemExit(0)

    if provider_type == "custom":
        name_val = questionary.text(
            "Provider name (lowercase, kebab-case):",
            validate=lambda v: (
                bool(__import__("re").match(r"^[a-z][a-z0-9-]*$", v))
                or "Must match ^[a-z][a-z0-9-]*$"
            ),
        ).ask()
        if name_val is None:
            raise SystemExit(130)

        if config.get_provider(name_val) is not None:
            print(f"Error: provider '{name_val}' already exists.", file=sys.stderr)
            raise SystemExit(2)

        base_url_val = questionary.text("Base URL (e.g. https://router.requesty.ai):").ask()
        if base_url_val is None:
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

        default_env_name = name_val.upper().replace("-", "_") + "_API_KEY"
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

        extra_env: dict[str, str] = {}

    else:
        p_preset = get_preset(provider_type)
        if p_preset is None:
            print(f"Error: preset for provider type '{provider_type}' not found.", file=sys.stderr)
            raise SystemExit(2)

        name_val = questionary.text(
            "Provider name (lowercase, kebab-case):",
            default=p_preset.default_name,
            validate=lambda v: (
                bool(__import__("re").match(r"^[a-z][a-z0-9-]*$", v))
                or "Must match ^[a-z][a-z0-9-]*$"
            ),
        ).ask()
        if name_val is None:
            raise SystemExit(130)

        if config.get_provider(name_val) is not None:
            print(f"Error: provider '{name_val}' already exists.", file=sys.stderr)
            raise SystemExit(2)

        base_url_val = questionary.text("Base URL:", default=p_preset.base_url).ask()
        if base_url_val is None:
            raise SystemExit(130)

        token = questionary.text("Token value:", default=p_preset.token).ask()
        if token is None:
            raise SystemExit(130)

        auth_env_var = p_preset.auth_env_var
        extra_env = p_preset.extra_env

    test_now = questionary.confirm("Test the provider now (GET /v1/models)?", default=True).ask()
    if test_now:
        _test_provider(base_url_val, token)

    _append_provider(name_val, base_url_val, token, auth_env_var, extra_env)
    print(f"Provider '{name_val}' added to {providers_config_path()}.")


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


def _append_provider(
    name: str,
    base_url: str,
    token: str,
    auth_env_var: str,
    extra_env: dict[str, str] | None = None,
    models: list[dict[str, str | list[str]]] | None = None,
) -> None:
    from io import StringIO

    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap, CommentedSeq

    from leitum.config.io import atomic_write_text

    path = providers_config_path()
    y = YAML()
    y.preserve_quotes = True
    with path.open("r", encoding="utf-8") as f:
        doc = y.load(f)

    new_provider: CommentedMap = CommentedMap()
    new_provider["name"] = name
    new_provider["base_url"] = base_url
    auth: CommentedMap = CommentedMap()
    auth["token"] = token
    if auth_env_var != "ANTHROPIC_AUTH_TOKEN":
        auth["env_var"] = auth_env_var
    new_provider["auth"] = auth

    if extra_env:
        c_env = CommentedMap()
        for k, v in extra_env.items():
            c_env[k] = v
        new_provider["extra_env"] = c_env

    if models is not None:
        c_models = CommentedSeq()
        for m in models:
            m_map = CommentedMap()
            m_map["id"] = m["id"]
            if m.get("display"):
                m_map["display"] = m["display"]
            if m.get("roles"):
                m_roles = CommentedSeq()
                for r in m["roles"]:
                    m_roles.append(r)
                m_map["roles"] = m_roles
            c_models.append(m_map)
        new_provider["models"] = c_models

    doc["providers"].append(new_provider)
    buf = StringIO()
    y.dump(doc, buf)
    atomic_write_text(path, buf.getvalue(), mode=0o600)


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

    from io import StringIO

    from ruamel.yaml import YAML

    from leitum.config.io import atomic_write_text

    path = providers_config_path()
    y = YAML()
    y.preserve_quotes = True
    with path.open("r", encoding="utf-8") as f:
        doc = y.load(f)

    doc["providers"] = [p for p in doc["providers"] if p["name"] != name]
    buf = StringIO()
    y.dump(doc, buf)
    atomic_write_text(path, buf.getvalue(), mode=0o600)

    # Clear state if this was last_provider
    state = load_state()
    if state.last_provider == name:
        state.last_provider = None
        from leitum.state import save_state

        save_state(state)

    clear_cache(name)
    print(f"Provider '{name}' removed.")


def run_provider_detect(json_output: bool = False, config: ProvidersConfig | None = None) -> None:
    import json

    import httpx
    import questionary

    from leitum.providers.presets import PRESETS

    if config is None:
        try:
            config = _load_config()
        except SystemExit:
            # Let's support running even without config if json_output is requested
            if not json_output:
                raise
            # If json_output is requested, we can just detect without config
            pass

    detected = []

    # 1. Probe each preset with detect_ports
    for p_preset in PRESETS:
        if not p_preset.detect_ports:
            continue

        for _port in p_preset.detect_ports:
            # Base URL is from default preset's base_url
            base_url = p_preset.base_url
            url = base_url.rstrip("/") + "/v1/models"
            try:
                # Use a short timeout of ~1.5s as per spec
                with httpx.Client(timeout=1.5) as client:
                    resp = client.get(url, headers={"Authorization": f"Bearer {p_preset.token}"})

                # Tolerate both authenticated (200) and open responses (200 without auth)
                if resp.status_code == 200:
                    data = resp.json()
                    models_list = data.get("data", [])
                    model_count = len(models_list)
                    detected.append(
                        {
                            "preset": p_preset,
                            "base_url": base_url,
                            "model_count": model_count,
                            "models": models_list,
                        }
                    )
            except Exception:
                # Silently ignore connection errors / timeouts
                continue

    # 5. leitum provider detect --json prints detection results machine-readably without writing
    if json_output:
        json_data = []
        for det in detected:
            p_preset = det["preset"]
            json_data.append(
                {
                    "key": p_preset.key,
                    "display": p_preset.display,
                    "base_url": det["base_url"],
                    "model_count": det["model_count"],
                }
            )
        print(json.dumps(json_data, indent=2))
        return

    # 3. Output
    if not detected:
        print("No local server is running on the known ports.")
        print("Point at 'leitum provider add' to configure one manually.")
        return

    # One or more reachable -> interactive multi-select of which to add
    choices = []
    for det in detected:
        p_preset = det["preset"]
        label = f"{p_preset.display} ({det['base_url']}) — {det['model_count']} models found"
        choices.append(questionary.Choice(label, value=det))

    selected = questionary.checkbox(
        "Select local servers to add as providers:",
        choices=choices,
    ).ask()

    if selected is None:
        raise SystemExit(130)

    if not selected:
        print("No servers selected. Aborting.")
        return

    # 4. For each selected server
    for det in selected:
        p_preset = det["preset"]
        base_name = p_preset.default_name

        # Name collision handling
        final_name = base_name
        suffix = 2
        while config is not None and config.get_provider(final_name) is not None:
            cand = f"{base_name}-{suffix}"
            choice = questionary.select(
                f"Provider '{final_name}' already exists. What would you like to do?",
                choices=[
                    questionary.Choice(f"Use name '{cand}' instead", value="rename"),
                    questionary.Choice("Skip this provider", value="skip"),
                ],
            ).ask()
            if choice is None:
                raise SystemExit(130)
            if choice == "skip":
                final_name = None
                break
            else:
                final_name = cand
                suffix += 1

        if final_name is None:
            print(f"Skipped adding {p_preset.display}.")
            continue

        # Optionally pin discovered models
        pin_models = questionary.confirm(
            f"Pin {det['model_count']} discovered models to the config for '{final_name}'?",
            default=True,
        ).ask()
        if pin_models is None:
            raise SystemExit(130)

        models_to_write = None
        if pin_models:
            models_to_write = []
            for m in det["models"]:
                m_id = m.get("id") or m.get("name", "")
                if m_id:
                    models_to_write.append({"id": m_id})

        _append_provider(
            name=final_name,
            base_url=det["base_url"],
            token=p_preset.token,
            auth_env_var=p_preset.auth_env_var,
            extra_env=p_preset.extra_env,
            models=models_to_write,
        )
        print(f"Provider '{final_name}' added to {providers_config_path()}.")
