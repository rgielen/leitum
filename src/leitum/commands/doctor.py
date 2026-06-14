"""leitum doctor command — sanity check suite."""

from __future__ import annotations

import re
import shutil
import stat
import subprocess
from pathlib import Path

from leitum.config.paths import get_config_dir, model_cache_path, providers_config_path, state_path

_SECRET_RE = re.compile(r"^[A-Za-z0-9+/=_\-]{24,}$")


def _ok(msg: str) -> None:
    print(f"[ ok ] {msg}")


def _warn(msg: str) -> None:
    print(f"[warn] {msg}")


def _fail(msg: str) -> None:
    print(f"[fail] {msg}")


def run_doctor(project_config_path: Path | None = None) -> None:
    failures = 0
    warnings = 0

    # 1. Paths & permissions
    print("--- Paths & Permissions ---")
    config_dir = get_config_dir()
    if config_dir.exists():
        mode = config_dir.stat().st_mode
        if stat.S_IMODE(mode) == 0o700:
            _ok(f"Config dir {config_dir} has mode 0700")
        else:
            _warn(f"Config dir {config_dir} has mode {oct(stat.S_IMODE(mode))} (expected 0700)")
            warnings += 1
    else:
        _fail(f"Config dir {config_dir} does not exist. Run 'leitum init'.")
        failures += 1

    cfg_path = providers_config_path()
    if cfg_path.exists():
        mode = cfg_path.stat().st_mode
        if stat.S_IMODE(mode) <= 0o600:
            _ok(f"api-providers.yaml has mode {oct(stat.S_IMODE(mode))}")
        else:
            _warn(
                f"api-providers.yaml has mode {oct(stat.S_IMODE(mode))}"
                f" (recommend chmod 600 {cfg_path})"
            )
            warnings += 1
    else:
        _fail(f"api-providers.yaml not found at {cfg_path}. Run 'leitum init'.")
        failures += 1

    # 2. Config validation
    print("\n--- Config Validation ---")
    config = None
    if cfg_path.exists():
        try:
            from leitum.config.io import load_providers_config

            config = load_providers_config(cfg_path)
            _ok(f"api-providers.yaml is valid ({len(config.providers)} provider(s))")
        except Exception as exc:
            _fail(f"api-providers.yaml parse error: {exc}")
            failures += 1

    pc_path = project_config_path or Path("leitum.yaml")
    if pc_path.exists():
        try:
            from leitum.config.io import load_project_config

            pc = load_project_config(pc_path)
            _ok("leitum.yaml is valid")
            if pc.provider and config:
                if config.get_provider(pc.provider) is None:
                    _fail(f"leitum.yaml references unknown provider '{pc.provider}'")
                    failures += 1
                else:
                    _ok(f"leitum.yaml provider '{pc.provider}' found in config")
            # Heuristic secret check in extra_env
            for k, v in (pc.extra_env or {}).items():
                if _SECRET_RE.match(v) and "${" not in v:
                    _warn(
                        f"leitum.yaml extra_env['{k}'] looks like a secret"
                        f" (length {len(v)}, no interpolation)."
                        " Do not commit secrets to version control."
                    )
                    warnings += 1
        except Exception as exc:
            _fail(f"leitum.yaml parse error: {exc}")
            failures += 1

    # 3. State file
    print("\n--- State File ---")
    st_path = state_path()
    if st_path.exists():
        try:
            from leitum.state import load_state

            state = load_state()
            _ok("state.yaml is valid")
            if state.last_provider:
                if config and config.get_provider(state.last_provider) is None:
                    _warn(f"last_provider '{state.last_provider}' not in current config")
                    warnings += 1
                else:
                    _ok(f"last_provider '{state.last_provider}' exists")
        except Exception as exc:
            _warn(f"state.yaml could not be read: {exc}")
            warnings += 1
    else:
        _warn("state.yaml not found (will be created on first run)")
        warnings += 1

    # 4. ENV variables
    print("\n--- Environment Variables ---")
    if config:
        import os

        from leitum.config.env import _INTERPOLATION_RE

        for p in config.providers:
            for match in _INTERPOLATION_RE.finditer(p.auth.token):
                expr = match.group(1)
                var_name = expr.split(":-")[0].strip()
                if var_name in os.environ:
                    _ok(f"Provider '{p.name}': {var_name} is set")
                else:
                    _fail(f"Provider '{p.name}': {var_name} is NOT set")
                    failures += 1

    # 5. Model discovery
    print("\n--- Model Discovery ---")
    if config:
        import httpx

        for p in config.providers:
            if p.models:
                _ok(f"Provider '{p.name}': {len(p.models)} models from YAML")
            else:
                cache_p = model_cache_path(p.name)
                if cache_p.exists():
                    _ok(f"Provider '{p.name}': cache exists at {cache_p}")
                else:
                    # Lightweight reachability check
                    try:
                        url = p.base_url.rstrip("/")
                        with httpx.Client(timeout=5) as client:
                            client.head(url)
                        _ok(f"Provider '{p.name}': reachable (no cache yet; run 'leitum refresh')")
                    except Exception as exc:
                        _warn(f"Provider '{p.name}': no cache and unreachable ({exc})")
                        warnings += 1

    # 6. Claude binary
    print("\n--- Claude Binary ---")
    claude_path = shutil.which("claude")
    if claude_path is None:
        _fail(
            "'claude' not found in PATH. Install from https://docs.claude.com/en/docs/claude-code/quickstart"
        )
        failures += 1
    else:
        _ok(f"'claude' found at {claude_path}")
        try:
            result = subprocess.run(
                ["claude", "--version"], capture_output=True, text=True, timeout=5
            )
            version = (result.stdout or result.stderr).strip()
            _ok(f"claude version: {version}")
        except Exception as exc:
            _warn(f"Could not determine claude version: {exc}")
            warnings += 1

    # Summary
    print(f"\n--- Summary: {failures} failure(s), {warnings} warning(s) ---")
    if failures > 0:
        raise SystemExit(1)
